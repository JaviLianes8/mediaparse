"""Huge and adversarial input: no crash, no hang, linear time, short messages (hand-written)."""

from __future__ import annotations

import time
from collections.abc import Callable

import pytest

from mediaparse import (
    AcceptItem,
    MediaType,
    MediaTypeError,
    build,
    decode_extended,
    negotiate,
    normalize,
    parse,
    parse_accept,
    quality,
)

UNIT = 50_000


def _seconds(work: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        work()
        best = min(best, time.perf_counter() - start)
    return best


def _linear(make: Callable[[int], Callable[[], object]]) -> None:
    """Four times the input may take at most about four times as long (with slack)."""
    small = _seconds(make(UNIT))
    large = _seconds(make(4 * UNIT))
    assert large < 10 * max(small, 0.002) + 0.05, (small, large)


SHAPES: dict[str, Callable[[int], str]] = {
    "params": lambda n: "a/b" + ";x=1" * n,
    "semicolons": lambda n: "a/b" + ";" * n,
    "open quote": lambda n: 'a/b;x="' + "\\" * n,
    "escapes": lambda n: 'a/b;x="' + '\\"' * n + '"',
    "whitespace": lambda n: " " * n + "a/b" + " " * n,
    "long token": lambda n: "a/" + "b" * n,
    "commas": lambda n: "," * n + "a/b",
    "quoted commas": lambda n: 'a/b;x="' + "," * n,
    "accept list": lambda n: ", ".join(["text/html;q=0.5"] * (n // 10)),
}


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_parsing_time_grows_linearly(shape: str) -> None:
    def make(n: int) -> Callable[[], object]:
        text = SHAPES[shape](n)

        def work() -> None:
            for call in (
                lambda: parse(text),
                lambda: parse(text, strict=True),
                lambda: parse_accept(text),
                lambda: parse_accept(text, strict=True),
            ):
                try:
                    call()
                except MediaTypeError as error:
                    assert len(str(error)) < 300

        return work

    _linear(make)


def test_decoding_many_sections_is_linear() -> None:
    def make(n: int) -> Callable[[], object]:
        params = {"t*0*": "utf-8''%41", **{f"t*{i}*": "%41" for i in range(1, n // 10)}}
        return lambda: decode_extended(params)

    _linear(make)


def test_building_a_huge_value_is_linear() -> None:
    def make(n: int) -> Callable[[], object]:
        return lambda: build("a/b", {"t": "\u20ac;" * n}, extended=True)

    _linear(make)


@pytest.mark.parametrize(
    "call",
    [
        lambda: build("a/b", {"x": "\ud800" * 10**6}, extended=True),
        lambda: build("a/b", {"x": "\n" * 10**6}),
        lambda: build("a/" + "b" * 10**6 + "/"),
        lambda: parse_accept("*/" + "a" * 10**6, strict=True),
        lambda: parse("a/" + "b" * 10**6 + "?", strict=True),
        lambda: normalize("a" * 10**6),
        lambda: quality("*/*", "*/" + "a" * 10**6),
        lambda: negotiate("*/*", ["a" * 10**6]),
        lambda: decode_extended({"t*": "utf-8''" + "%" * 10**6}),
        lambda: decode_extended({"t*": "x" * 10**6 + "''a"}),
        lambda: AcceptItem(MediaType("a", "b"), 10**5000),
        lambda: MediaType("a" * 10**6 + "/", "b"),
        lambda: MediaType("a", "b", (("x", "\x00" * 10**6),)),
    ],
)
def test_messages_stay_short_for_huge_input(call: Callable[[], object]) -> None:
    with pytest.raises(MediaTypeError) as caught:
        call()
    assert len(str(caught.value)) < 300


def test_a_hundred_thousand_parameters_and_ranges_parse() -> None:
    media = parse("a/b" + "".join(f";p{i}={i}" for i in range(100_000)))
    assert len(media[1]) == 100_000
    items = parse_accept(",".join(f"a/b{i};q=0.{i % 10}" for i in range(100_000)))
    assert len(items) == 100_000
    assert quality(",".join(["a/*;q=0.1"] * 100_000), "a/b") == 0.1


def test_deep_and_odd_text_is_refused_quietly() -> None:
    for text in ["\x00/\x00", "a/b\x00", "\ufeffa/b", "a\u212a/b", "a/b;\ud800=1"]:
        with pytest.raises(MediaTypeError):
            parse(text, strict=True)
    assert parse("a/b;\ud800=1;x=\ud800;y=2") == ("a/b", {"y": "2"})
