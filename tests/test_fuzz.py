"""Seeded property tests over hostile and generated headers (hand-written properties)."""

from __future__ import annotations

import random
import re

import pytest
from generators import media_params, noise, unicode_text

from mediaparse import (
    MediaTypeError,
    build,
    decode_extended,
    matches,
    negotiate,
    normalize,
    parse,
    parse_accept,
    parse_media_type,
    quality,
)

SEEDS = [11, 12, 13]
# RFC 9110 media-type, written out by hand from sections 5.6.2, 5.6.4, 5.6.6 and 8.3.1,
# with the leading and trailing OWS a field parser removes.
TOKEN = r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+"
QUOTED = r'"(?:[\t !#-\[\]-~\x80-\xff]|\\[\t \x21-\x7e\x80-\xff])*"'
PARAM = rf"[ \t]*;[ \t]*(?:({TOKEN})=(?:{TOKEN}|{QUOTED}))?"
GRAMMAR = re.compile(rf"[ \t]*{TOKEN}/{TOKEN}(?:{PARAM})*[ \t]*")


def _attempt(text: str, strict: bool) -> object:
    try:
        return parse_media_type(text, strict=strict)
    except MediaTypeError as error:
        assert len(str(error)) < 300
        assert error.position is None or 0 <= error.position <= len(text)
        return error


@pytest.mark.parametrize("seed", SEEDS)
def test_parsing_never_crashes_and_is_stable(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(5000):
        text = noise(rng)
        for strict in (False, True):
            media = _attempt(text, strict)
            if isinstance(media, MediaTypeError):
                continue
            assert parse_media_type(str(media)) == media
            assert parse_media_type(str(media), strict=True) == media
            assert normalize(normalize(text, strict=strict)) == normalize(text, strict=strict)
            assert matches(text, str(media)) and matches(str(media), text)


@pytest.mark.parametrize("seed", SEEDS)
def test_strict_accepts_exactly_the_grammar(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(10000):
        text = noise(rng)
        if rng.random() < 0.3:
            essence, params = media_params(rng)
            text = build(essence, params).replace("; ", rng.choice([";", " ; ", "\t;"]))
        accepted = not isinstance(_attempt(text, True), MediaTypeError)
        valid = bool(GRAMMAR.fullmatch(text))
        if valid:
            rest = text[re.match(rf"[ \t]*{TOKEN}/{TOKEN}", text).end() :]  # type: ignore[union-attr]
            names = [n for n in re.findall(PARAM, rest) if n]
            valid = len({name.lower() for name in names}) == len(names)
        assert accepted == valid, repr(text)


@pytest.mark.parametrize("seed", SEEDS)
def test_build_round_trips_through_both_parsers(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        essence, params = media_params(rng)
        header = build(essence, params)
        lowered = (essence.lower(), {name.lower(): value for name, value in params.items()})
        assert parse(header, strict=True) == lowered
        assert parse(header) == lowered


@pytest.mark.parametrize("seed", SEEDS)
def test_extended_values_round_trip_through_decode(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        values = {f"p{index}": unicode_text(rng) for index in range(rng.randint(1, 3))}
        header = build("a/b", values, extended=True)
        assert header.isascii()
        assert decode_extended(parse(header, strict=True)[1]) == values


@pytest.mark.parametrize("seed", SEEDS)
def test_accept_is_total_and_weights_are_consistent(seed: int) -> None:
    rng = random.Random(seed)
    offers = ["text/html", "text/plain;format=flowed", "image/png", "a/b"]
    for _ in range(3000):
        header = ",".join(noise(rng, 12) for _ in range(rng.randint(0, 4)))
        items = parse_accept(header)
        assert all(0 <= item.q <= 1 for item in items)
        weights = [quality(header, offer) for offer in offers]
        assert all(w == 0 or w in {item.q for item in items} for w in weights)
        best = negotiate(header, offers)
        if best is None:
            assert max(weights) == 0
        else:
            assert quality(header, best) == max(weights) > 0
            assert best == offers[weights.index(max(weights))]
        try:
            strict_items = parse_accept(header, strict=True)
        except MediaTypeError as error:
            assert len(str(error)) < 300
        else:
            assert strict_items == items
