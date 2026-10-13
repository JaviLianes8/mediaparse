"""``strict=True``: the RFC 9110 media-type grammar exactly.

Vectors cited from RFC 9110 section 8.3.1, https://www.rfc-editor.org/rfc/rfc9110.txt,
are marked; the rest are hand-written from the grammar in sections 5.6.2 to 5.6.6.
"""

from __future__ import annotations

import pytest

from mediaparse import MediaTypeError, normalize, parse, parse_media_type


@pytest.mark.parametrize(
    "text",
    [
        # RFC 9110 section 8.3.1: four equivalent forms of one media type.
        "text/html;charset=utf-8",
        'Text/HTML;Charset="utf-8"',
        'text/html; charset="utf-8"',
        "text/html;charset=UTF-8",
    ],
)
def test_the_rfc_equivalent_forms_parse_and_normalize_alike(text: str) -> None:
    assert parse(text, strict=True)[0] == "text/html"
    assert normalize(text, strict=True) == "text/html; charset=utf-8"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("text/plain", {}),
        ("text/plain;", {}),
        ("text/plain ; ; a=1 ;", {"a": "1"}),
        ("\t text/plain;a=1 \t", {"a": "1"}),
        ('text/plain;a="x\\"y\\\\z"', {"a": 'x"y\\z'}),
        ('text/plain;a="\\a\\ \\\t"', {"a": "a \t"}),
        ('text/plain;a="tab\there"', {"a": "tab\there"}),
        ('text/plain;a="\xe9"', {"a": "\xe9"}),
        ('text/plain;a="\\\xe9"', {"a": "\xe9"}),
        ('text/plain;a=""', {"a": ""}),
        ('text/plain;a="!#[]~"', {"a": "!#[]~"}),
        ("text/plain;A=Token!#$%&'*+-.^_`|~", {"a": "Token!#$%&'*+-.^_`|~"}),
    ],
)
def test_valid_headers_parse(text: str, expected: dict[str, str]) -> None:
    assert parse(text, strict=True) == ("text/plain", expected)


@pytest.mark.parametrize(
    ("text", "position"),
    [
        ("", 0),
        ("text", 4),
        ("text/", 5),
        ("text /plain", 4),
        ("text/plain a=1", 11),
        ("text/plain;a =1", 12),
        ("text/plain;a= 1", 13),
        ("text/plain;a", 12),
        ("text/plain;a=", 13),
        ("text/plain;=1", 11),
        ("text/plain;a=b c", 15),
        ('text/plain;a="open', 18),
        ('text/plain;a="open\\', 19),
        ('text/plain;a="x"y', 16),
        ('text/plain;a="\x7f"', 14),
        ('text/plain;a="\x00"', 14),
        ('text/plain;a="\\\n"', 15),
        ('text/plain;a="\\\x7f"', 15),
        ('text/plain;a="\N{EURO SIGN}"', 14),
        ('text/plain;a="\\\N{EURO SIGN}"', 15),
        ("text/plain;a=\xe9", 13),
        ("text/plain\r\n", 10),
        ("text/plain;a=1;A=2", 15),
    ],
)
def test_invalid_headers_raise_at_the_first_bad_character(text: str, position: int) -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse_media_type(text, strict=True)
    assert caught.value.position == position


def test_the_message_names_the_position_and_what_was_found() -> None:
    with pytest.raises(MediaTypeError, match="position 12, found ' '"):
        parse("text/plain;a =1", strict=True)
    with pytest.raises(MediaTypeError, match="position 4, found the end"):
        parse("text", strict=True)


def test_a_repeated_parameter_is_named_in_the_error() -> None:
    with pytest.raises(MediaTypeError, match="'a' is given more than once"):
        parse("text/plain;a=1;A=2", strict=True)
