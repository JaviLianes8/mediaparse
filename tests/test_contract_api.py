"""The complete promise of every public name: signature, result and failure types."""

from __future__ import annotations

import dataclasses
import inspect
import pickle

import pytest

import mediaparse
from mediaparse import (
    AcceptItem,
    MediaType,
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

SIGNATURES = {
    "build": "(mimetype: 'str', params: 'Mapping[str, str] | None' = None, *, "
    "extended: 'bool' = False) -> 'str'",
    "decode_extended": "(params: 'Mapping[str, str]') -> 'dict[str, str]'",
    "matches": "(first: 'str', second: 'str') -> 'bool'",
    "negotiate": "(accept: 'str | None', offers: 'Iterable[str]') -> 'str | None'",
    "normalize": "(header: 'str', *, strict: 'bool' = False) -> 'str'",
    "parse": "(header: 'str', *, strict: 'bool' = False) -> 'tuple[str, dict[str, str]]'",
    "parse_accept": "(header: 'str', *, strict: 'bool' = False) -> 'list[AcceptItem]'",
    "parse_media_type": "(text: 'str', *, strict: 'bool' = False) -> 'MediaType'",
    "quality": "(accept: 'str | None', offer: 'str') -> 'float'",
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_function_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(mediaparse, name))) == SIGNATURES[name]


def test_value_classes_are_frozen_dataclasses_with_pinned_fields() -> None:
    fields = [(f.name, f.default) for f in dataclasses.fields(MediaType)]
    assert fields == [
        ("type", dataclasses.MISSING),
        ("subtype", dataclasses.MISSING),
        ("params", ()),
    ]
    fields = [(f.name, f.default) for f in dataclasses.fields(AcceptItem)]
    assert fields == [("media_range", dataclasses.MISSING), ("q", 1.0)]
    for value in (MediaType("a", "b"), AcceptItem(MediaType("a", "b"))):
        with pytest.raises(dataclasses.FrozenInstanceError):
            value.q = 0  # type: ignore[misc,union-attr]
        assert pickle.loads(pickle.dumps(value)) == value
        assert hash(value) == hash(pickle.loads(pickle.dumps(value)))


def test_every_public_name_is_documented_with_an_example() -> None:
    for name in mediaparse.__all__:
        doc = inspect.getdoc(getattr(mediaparse, name)) or ""
        assert ">>> " in doc, name
    for member in ("essence", "suffix", "parameters", "get"):
        assert ">>> " in (inspect.getdoc(getattr(MediaType, member)) or ""), member
    for member in ("specificity", "matches"):
        assert ">>> " in (inspect.getdoc(getattr(AcceptItem, member)) or ""), member


def test_media_type_error_is_a_value_error_with_a_position_that_pickles() -> None:
    error = MediaTypeError("bad", position=3)
    assert isinstance(error, ValueError) and error.position == 3 and str(error) == "bad"
    again = pickle.loads(pickle.dumps(error))
    assert (type(again), str(again), again.position) == (MediaTypeError, "bad", 3)
    assert MediaTypeError("x").position is None
    with pytest.raises(MediaTypeError) as caught:
        parse("text/plain;a=1;A=2", strict=True)
    assert caught.value.position == 15


@pytest.mark.parametrize(
    "call",
    [
        lambda: parse(b"a/b"),  # type: ignore[arg-type]
        lambda: parse_media_type(None),  # type: ignore[arg-type]
        lambda: normalize(1),  # type: ignore[arg-type]
        lambda: matches("a/b", None),  # type: ignore[arg-type]
        lambda: build(b"a/b"),  # type: ignore[arg-type]
        lambda: build("a/b", [("x", "1")]),  # type: ignore[arg-type]
        lambda: build("a/b", {1: "x"}),  # type: ignore[dict-item]
        lambda: build("a/b", {"x": 1}),  # type: ignore[dict-item]
        lambda: parse_accept(None),  # type: ignore[arg-type]
        lambda: quality(1, "a/b"),  # type: ignore[arg-type]
        lambda: quality(None, None),  # type: ignore[arg-type]
        lambda: negotiate(None, "a/b"),
        lambda: negotiate(None, [None]),  # type: ignore[list-item]
        lambda: decode_extended([("a", "b")]),  # type: ignore[arg-type]
        lambda: decode_extended({"a": 1}),  # type: ignore[dict-item]
        lambda: MediaType("a", 1),  # type: ignore[arg-type]
        lambda: MediaType("a", "b", "x=1"),  # type: ignore[arg-type]
        lambda: MediaType("a", "b", (("x",),)),  # type: ignore[arg-type]
        lambda: MediaType("a", "b").get(1),  # type: ignore[arg-type]
        lambda: AcceptItem("a/b"),  # type: ignore[arg-type]
        lambda: AcceptItem(MediaType("a", "b"), True),
        lambda: AcceptItem(MediaType("a", "b"), "1"),  # type: ignore[arg-type]
        lambda: AcceptItem(MediaType("a", "b")).matches("a/b"),  # type: ignore[arg-type]
    ],
)
def test_wrong_argument_types_raise_type_error(call: object) -> None:
    with pytest.raises(TypeError):
        call()  # type: ignore[operator]


@pytest.mark.parametrize(
    "call",
    [
        lambda: parse("a"),
        lambda: parse("a/b c", strict=True),
        lambda: build("a"),
        lambda: build("a/b", {"x": "\r\n"}),
        lambda: build("a/b", {"x*": "\xe9"}, extended=True),
        lambda: build("a/b", {"x": "1", "X": "2"}),
        lambda: parse_accept("a/b;q=2", strict=True),
        lambda: quality("*/*", "text/*"),
        lambda: negotiate("*/*", ["*/*"]),
        lambda: decode_extended({"a*": "nope"}),
        lambda: decode_extended({"a*": "charmap''%41"}),
        lambda: MediaType("a/", "b"),
        lambda: AcceptItem(MediaType("*", "plain")),
        lambda: AcceptItem(MediaType("a", "b", (("Q", "1"),))),
        lambda: AcceptItem(MediaType("a", "b"), 1.5),
        lambda: AcceptItem(MediaType("a", "b"), float("nan")),
        lambda: AcceptItem(MediaType("a", "b"), -0.001),
    ],
)
def test_invalid_values_raise_media_type_error(call: object) -> None:
    with pytest.raises(MediaTypeError):
        call()  # type: ignore[operator]


def test_accept_item_promise() -> None:
    item = AcceptItem(MediaType("text", "*", (("charset", "UTF-8"),)), 1)
    assert type(item.q) is float and item.q == 1.0
    assert AcceptItem(MediaType("*", "*")).q == 1.0
    assert AcceptItem(MediaType("a", "b"), 0).q == 0.0
    assert item.specificity() == (True, False, 1)
    assert item.matches(MediaType("text", "x", (("charset", "utf-8"), ("a", "1"))))
    assert not item.matches(MediaType("text", "x"))
    assert not item.matches(MediaType("image", "x", (("charset", "utf-8"),)))
    exact = AcceptItem(MediaType("a", "b", (("f", "X"),)))
    assert not exact.matches(MediaType("a", "b", (("f", "x"),)))


def test_media_type_promise() -> None:
    media = MediaType("A", "B+Json", [("X", "1"), ("y", "")])  # type: ignore[arg-type]
    assert (media.type, media.subtype, media.params) == ("a", "b+json", (("x", "1"), ("y", "")))
    assert (media.essence, media.suffix, str(media)) == ("a/b+json", "json", 'a/b+json;x=1;y=""')
    assert media.parameters == {"x": "1", "y": ""} and media.parameters is not media.parameters
    assert (media.get("X"), media.get("z"), media.get("z", "d")) == ("1", None, "d")
    assert media == MediaType("a", "b+json", (("x", "1"), ("y", "")))
    assert media != MediaType("a", "b+json", (("y", ""), ("x", "1")))
    assert dataclasses.replace(media, type="C").type == "c"
