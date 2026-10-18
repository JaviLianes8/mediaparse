"""Contracts for robustness defects found by adversarial review (hand-written)."""

from __future__ import annotations

import codecs
import encodings
import encodings.aliases
import pkgutil
import time

import pytest

from mediaparse import AcceptItem, MediaType, MediaTypeError, decode_extended, parse_accept, quality


@pytest.mark.parametrize(
    "element",
    ['a/b;x=a"b;q="', 'a/b;x=a"b;q=""', 'a/b;x=a"b;q =0.3;q=0.7', 'a/b;x=a"b;q=', "a/b;q="],
)
def test_a_quote_inside_an_unquoted_value_hides_no_weight(element: str) -> None:
    assert parse_accept("c/d, " + element) == parse_accept("c/d")
    assert quality(element, "a/b") == 0.0


def test_a_quoted_value_still_hides_its_content() -> None:
    assert [item.q for item in parse_accept('a/b;x="q =1;";q=0.5')] == [0.5]
    assert parse_accept('a/b;x;"a;q =1;"') == []


@pytest.mark.parametrize(
    "charset",
    ["utf-8", "UTF-8", "us-ascii", "iso-8859-1", "ISO_8859-15", "windows-1252", "shift_jis",
     "euc-jp", "gb2312", "big5", "koi8-r", "utf-7", "cp437", "latin1", "ascii", "utf8"],
)  # fmt: skip
def test_common_charsets_are_accepted(charset: str) -> None:
    assert decode_extended({"a*": charset + "''%41"}) == {"a": "A"}


def test_every_standard_charset_name_decodes_like_python() -> None:
    names = set(encodings.aliases.aliases) | {
        m.name for m in pkgutil.iter_modules(encodings.__path__)
    }
    decoded = 0
    for name in sorted(names):
        try:
            info = codecs.lookup(name)
            expected = b"A".decode(name)
        except (LookupError, UnicodeError, ValueError, TypeError):
            continue
        if name.isidentifier() and len(name) <= 40 and info.name.isascii():
            try:
                got = decode_extended({"a*": name.replace("_", "-") + "''%41"})["a"]
            except MediaTypeError:
                continue  # a codec that is not a character set
            assert got == expected, name
            decoded += 1
    assert decoded > 100


def test_unknown_charset_names_leave_no_trace_and_stay_fast() -> None:
    before = len(getattr(encodings, "_cache", {}))
    start = time.perf_counter()
    for index in range(2000):
        with pytest.raises(MediaTypeError):
            decode_extended({"a*": f"x{index}{'y' * 1000}''x"})
        with pytest.raises(MediaTypeError):
            decode_extended({"a*": f"x{index}y''x"})
    assert time.perf_counter() - start < 5
    assert len(getattr(encodings, "_cache", {})) - before < 10


def test_matching_many_parameters_is_linear() -> None:
    def run(n: int) -> float:
        params = tuple((f"p{i}", "v") for i in range(n))
        item = AcceptItem(MediaType("a", "b", params))
        start = time.perf_counter()
        assert item.matches(MediaType("a", "b", params[::-1]))
        return time.perf_counter() - start

    small, large = run(5000), run(20000)
    assert large < 10 * max(small, 0.002) + 0.05


class _Broken:
    def __repr__(self) -> str:
        raise RuntimeError("no repr")


def test_unprintable_arguments_still_give_the_documented_errors() -> None:
    deep: list[object] = []
    for _ in range(100_000):
        deep = [deep]
    for bad in (deep, _Broken()):
        with pytest.raises(TypeError):
            MediaType("a", "b", (bad,))  # type: ignore[arg-type]


class _Liar(float):
    def __le__(self, other: object) -> bool:
        return True

    def __ge__(self, other: object) -> bool:
        return True


class _Shout(str):
    def __str__(self) -> str:
        return "other"

    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return 0


def test_values_are_stored_as_plain_builtins() -> None:
    with pytest.raises(MediaTypeError):
        AcceptItem(MediaType("a", "b"), _Liar(5.0))
    zero = AcceptItem(MediaType("a", "b"), -0.0).q
    assert str(zero) == "0.0" and type(zero) is float
    media = MediaType("a", "b", (("x", _Shout("v")),))
    assert type(media.params[0][1]) is str and media.params[0][1] == "v"
    assert media != MediaType("a", "b", (("x", "w"),))
