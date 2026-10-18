"""Edge contracts found by a blind mutation round (hand-written, one behaviour each)."""

from __future__ import annotations

import re

import pytest

from mediaparse import MediaTypeError, build, decode_extended, parse, parse_accept


def test_messages_quote_exactly_eighty_characters_of_a_long_input() -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse("x" * 200)
    quoted = re.search(r"'x+\.\.\.", str(caught.value))
    assert quoted is not None and len(quoted.group(0)) == 80


@pytest.mark.parametrize(("text", "position"), [("\x0bx/y", 0), (" \x0bx/y", 1), ("\xa0x/y", 0)])
def test_only_http_whitespace_is_skipped_before_the_type(text: str, position: int) -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse(text)
    assert caught.value.position == position


@pytest.mark.parametrize(
    "mimetype", ["text/plain\r\n", "\x0btext/plain", "text/plain\xa0", "\ntext/plain"]
)
def test_build_drops_only_spaces_and_tabs_around_the_media_type(mimetype: str) -> None:
    with pytest.raises(MediaTypeError):
        build(mimetype)
    assert build(" \ttext/plain\t ") == "text/plain"


@pytest.mark.parametrize("value", ["utf-8''%4G", "utf-8''%G4", "utf-8''%", "utf-8''%4"])
def test_a_bad_percent_escape_is_a_media_type_error(value: str) -> None:
    with pytest.raises(MediaTypeError) as caught:
        decode_extended({"a*": value})
    assert caught.value.position == value.index("%")


def test_a_plain_first_section_makes_utf8_bytes_invalid() -> None:
    with pytest.raises(MediaTypeError, match="us-ascii"):
        decode_extended({"a*0": "x", "a*1*": "%C3%A9"})


@pytest.mark.parametrize("charset", ["utf 8", "utf-8\t", "utf(8)", "utf-8;", "utf/8"])
def test_a_charset_name_outside_the_mime_charset_syntax_is_refused(charset: str) -> None:
    with pytest.raises(MediaTypeError, match="invalid charset name"):
        decode_extended({"a*": charset + "''x"})


def test_plain_names_equal_without_case_keep_the_last_value() -> None:
    assert decode_extended({"A": "1", "a": "2"}) == {"a": "2"}
    assert decode_extended({"a": "2", "A": "1"}) == {"a": "1"}


def test_an_encoded_value_may_hold_a_newline_after_the_prefix() -> None:
    assert decode_extended({"a*": "utf-8''a\nb"}) == {"a": "a\nb"}


@pytest.mark.parametrize("weight", ["1.5", "1.001", "2", "1.0000"])
def test_a_strict_weight_out_of_range_points_at_its_value(weight: str) -> None:
    with pytest.raises(MediaTypeError, match="invalid weight") as caught:
        parse_accept(f"a/b;q={weight}", strict=True)
    assert caught.value.position == 6
