"""The ``MediaType`` value: validation, accessors and serialization (hand-written)."""

from __future__ import annotations

import pickle

import pytest

from mediaparse import MediaType, MediaTypeError, parse_media_type


def test_parts_are_lower_cased_on_construction() -> None:
    media = MediaType("Text", "HTML", (("CharSet", "UTF-8"),))
    assert (media.type, media.subtype, media.params) == ("text", "html", (("charset", "UTF-8"),))


def test_essence_drops_the_parameters() -> None:
    assert parse_media_type("text/html; charset=utf-8").essence == "text/html"


@pytest.mark.parametrize(
    ("text", "suffix"),
    [
        ("application/vnd.api+json", "json"),
        ("image/svg+xml", "xml"),
        ("application/a+b+cbor", "cbor"),
        ("application/json", None),
        ("application/x+", None),
    ],
)
def test_suffix_is_the_part_after_the_last_plus(text: str, suffix: str | None) -> None:
    assert parse_media_type(text).suffix == suffix


def test_get_is_case_insensitive_and_has_a_default() -> None:
    media = parse_media_type("text/plain; charset=utf-8")
    assert media.get("CHARSET") == "utf-8"
    assert media.get("format") is None
    assert media.get("format", "fixed") == "fixed"


def test_parameters_is_an_ordered_copy() -> None:
    media = parse_media_type("x/y; b=2; a=1")
    copy = media.parameters
    copy["c"] = "3"
    assert list(media.parameters) == ["b", "a"]


def test_str_follows_the_whatwg_serialization() -> None:
    media = MediaType("text", "plain", (("a", "tok"), ("b", ""), ("c", 'x "y" \\z')))
    assert str(media) == 'text/plain;a=tok;b="";c="x \\"y\\" \\\\z"'


def test_str_round_trips_through_both_parsers() -> None:
    media = MediaType("text", "plain", (("a", "x; y=\xe9\t"), ("b", "1")))
    assert parse_media_type(str(media)) == media
    assert parse_media_type(str(media), strict=True) == media


def test_values_are_hashable_and_comparable() -> None:
    first = parse_media_type("TEXT/plain;A=1")
    second = MediaType("text", "plain", (("a", "1"),))
    assert first == second
    assert len({first, second}) == 1


def test_values_pickle() -> None:
    media = parse_media_type("text/plain;a=1")
    assert pickle.loads(pickle.dumps(media)) == media


def test_values_are_frozen() -> None:
    media = parse_media_type("text/plain")
    with pytest.raises(AttributeError):
        media.type = "image"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("main", "subtype", "params"),
    [
        ("", "plain", ()),
        ("text", "", ()),
        ("te xt", "plain", ()),
        ("text", "pl;ain", ()),
        ("text", "plain", (("a b", "1"),)),
        ("text", "plain", (("", "1"),)),
        ("text", "plain", (("a", "x\r\ny"),)),
        ("text", "plain", (("a", "\N{EURO SIGN}"),)),
        ("text", "plain", (("a", "1"), ("A", "2"))),
    ],
)
def test_invalid_parts_raise(main: str, subtype: str, params: tuple[tuple[str, str], ...]) -> None:
    with pytest.raises(MediaTypeError):
        MediaType(main, subtype, params)


@pytest.mark.parametrize(
    ("main", "subtype", "params"),
    [
        (1, "plain", ()),
        ("text", None, ()),
        ("text", "plain", ((1, "x"),)),
        ("text", "plain", (("a", "1", "2"),)),
        ("text", "plain", ("ab",)),
        ("text", "plain", (["a", "b"],)),
        ("text", "plain", {"a": "b"}),
    ],
)
def test_wrong_types_raise_type_error(main: object, subtype: object, params: object) -> None:
    with pytest.raises(TypeError):
        MediaType(main, subtype, params)  # type: ignore[arg-type]


def test_a_non_string_value_raises_type_error() -> None:
    with pytest.raises(TypeError, match="parameter value must be a str"):
        MediaType("text", "plain", (("a", 1),))  # type: ignore[arg-type]


def test_the_error_keeps_its_position_across_pickling() -> None:
    error = MediaTypeError("bad", position=3)
    again = pickle.loads(pickle.dumps(error))
    assert (str(again), again.position) == ("bad", 3)
    assert isinstance(again, ValueError)
    assert MediaTypeError("plain").position is None


def test_a_list_of_pairs_is_accepted_and_stored_as_a_tuple() -> None:
    media = MediaType("text", "plain", [("a", "1")])  # type: ignore[arg-type]
    assert media.params == (("a", "1"),)


def test_equality_is_order_sensitive_matches_is_not() -> None:
    from mediaparse import matches

    first, second = parse_media_type("x/y;a=1;b=2"), parse_media_type("x/y;b=2;a=1")
    assert first != second
    assert matches(str(first), str(second))


def test_error_messages_do_not_embed_a_huge_input() -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse_media_type("x" * 1_000_000)
    assert len(str(caught.value)) < 200
    with pytest.raises(MediaTypeError) as caught:
        parse_media_type("text/plain;" + "a" * 1_000_000, strict=True)
    assert len(str(caught.value)) < 200
