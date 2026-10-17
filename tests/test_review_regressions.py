"""Regression tests for defects found in review (hand-written, one behaviour each)."""

from __future__ import annotations

from typing import Any

import pytest

from mediaparse import (
    AcceptItem,
    MediaType,
    MediaTypeError,
    build,
    decode_extended,
    negotiate,
    parse,
    parse_accept,
    quality,
)


def test_extended_build_cannot_write_one_name_twice() -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"title": "caf\xe9", "title*": "x"}, extended=True)


def test_extended_build_refuses_a_star_name_even_with_an_ascii_value() -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"title*": "a b"}, extended=True)


def test_a_star_name_is_plain_text_without_extended() -> None:
    assert build("text/plain", {"title*": "UTF-8''a"}) == "text/plain; title*=UTF-8''a"


@pytest.mark.parametrize(
    "element",
    [
        "text/html; q =0",
        "text/html;Q= 0",
        "text/html;q=",
        "text/html;q=0\x7f",
        "text/html;q=0.\N{ARABIC-INDIC DIGIT FIVE}",
    ],
)
def test_a_malformed_weight_never_becomes_weight_one(element: str) -> None:
    assert negotiate(element, ["text/html"]) is None
    assert parse_accept(f"{element}, image/png") == [AcceptItem(MediaType("image", "png"))]


def test_names_that_only_start_with_q_are_ordinary_parameters() -> None:
    (item,) = parse_accept('text/html;qq=1;x="a;q=0"')
    assert (item.q, item.media_range.get("qq")) == (1.0, "1")


def test_a_line_break_is_not_an_empty_element_in_strict_mode() -> None:
    with pytest.raises(MediaTypeError):
        parse_accept("text/html,\n,image/png", strict=True)
    assert len(parse_accept("text/html,\n,image/png")) == 2


@pytest.mark.parametrize(
    "params",
    [
        {"t*": "undefined''x"},
        {"t*1" + "0" * 5000: "a"},
        {"t*1234567890": "a"},
        {"t*": "a\x00b''x"},
        {"t*": "\udcff''x"},
        {"t*": "unicode_escape''%5Cx0d%5Cx0a"},
        {"t*": "raw_unicode_escape''%5Cu0041"},
        {"t*": "idna''abc"},
        {"t*": "punycode''abc"},
        {"t*": "mbcs''%80"},
        {"t*": "oem''%80"},
    ],
)
def test_decode_extended_only_raises_media_type_error(params: dict[str, str]) -> None:
    with pytest.raises(MediaTypeError):
        decode_extended(params)


def test_decode_extended_accepts_ordinary_charsets() -> None:
    params = {"a*": "iso-8859-1''caf%E9", "b*": "UTF-8''caf%C3%A9", "c*": "windows-1252''%80"}
    assert decode_extended(params) == {"a": "caf\xe9", "b": "caf\xe9", "c": "\N{EURO SIGN}"}


def test_decode_extended_compares_names_case_insensitively() -> None:
    assert decode_extended({"Title*0": "a", "title*1": "b"}) == {"title": "ab"}


def test_decode_extended_keeps_first_appearance_order() -> None:
    result = decode_extended({"a*0": "x", "b": "1", "a*1": "y", "c": "2"})
    assert list(result.items()) == [("a", "xy"), ("b", "1"), ("c", "2")]


def test_decode_extended_on_parsed_header_with_a_huge_section_number() -> None:
    _, params = parse("text/plain;t*1" + "0" * 5000 + "=a")
    with pytest.raises(MediaTypeError):
        decode_extended(params)


@pytest.mark.parametrize("q", [5, -0.1, 1.5])
def test_accept_item_rejects_a_weight_out_of_range(q: float) -> None:
    with pytest.raises(MediaTypeError):
        AcceptItem(MediaType("a", "b"), q)


@pytest.mark.parametrize(
    ("media_range", "q"), [(MediaType("a", "b"), "x"), (MediaType("a", "b"), True), ("a/b", 1.0)]
)
def test_accept_item_rejects_wrong_types(media_range: object, q: object) -> None:
    with pytest.raises(TypeError):
        AcceptItem(media_range, q)  # type: ignore[arg-type]


def test_accept_item_stores_an_integer_weight_as_float() -> None:
    item = AcceptItem(MediaType("a", "b"), 1)
    assert item.q == 1.0 and isinstance(item.q, float)


def test_wrong_container_types_raise_type_error() -> None:
    with pytest.raises(TypeError):
        build("text/plain", [("a", "b")])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        decode_extended([("a", "b")])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        decode_extended({"a": 1})  # type: ignore[dict-item]
    with pytest.raises(TypeError):
        negotiate("*/*", "text/html")


def test_quality_of_a_malformed_weight_is_zero() -> None:
    assert quality("text/html;q=, */*;q=0.2", "text/html") == 0.2


@pytest.mark.parametrize(
    ("call", "position"),
    [
        (lambda: parse("te(t/html"), 2),
        (lambda: parse(" a/b c"), 4),
        (lambda: parse("/x"), 0),
        (lambda: parse("\ta/"), 3),
        (lambda: decode_extended({"a*": "utf-8''ab%zz"}), 9),
        (lambda: decode_extended({"a*0*": "utf-8''a", "a*1*": "%z"}), 0),
    ],
)
def test_positions_point_at_the_offending_character(call: Any, position: int) -> None:
    with pytest.raises(MediaTypeError) as caught:
        call()
    assert caught.value.position == position


@pytest.mark.parametrize(
    "element",
    ["a/b;\nq =0", "a/b;\rQ =0", 'a/b;q=0.5;q="1"', "a/b;q=0.5;q =1", "a/b;q=0.5;q=2", "a/b;q"],
)
def test_every_q_of_an_element_must_be_well_formed(element: str) -> None:
    assert parse_accept(element + ", c/d") == parse_accept("c/d")


def test_a_repeated_well_formed_q_keeps_the_first() -> None:
    assert [item.q for item in parse_accept("a/b;q=0.5;Q=0.7")] == [0.5]


def test_a_non_ascii_character_position_counts_from_the_value_start() -> None:
    with pytest.raises(MediaTypeError) as caught:
        decode_extended({"a*": "utf-8''a\xe9"})
    assert caught.value.position == 8
