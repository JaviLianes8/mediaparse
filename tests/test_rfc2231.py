"""``decode_extended``: RFC 2231 continuations and charset-encoded values.

Vectors marked "RFC 2231" are cited from sections 3, 4 and 4.1 of
https://www.rfc-editor.org/rfc/rfc2231.txt (header folding removed); the rest are
hand-written from the grammar in section 7.
"""

from __future__ import annotations

import pytest

from mediaparse import MediaTypeError, decode_extended, parse


def test_rfc_continuation_example() -> None:
    # RFC 2231 section 3.
    header = (
        "message/external-body; access-type=URL; "
        'URL*0="ftp://"; URL*1="cs.utk.edu/pub/moore/bulk-mailer/bulk-mailer.tar"'
    )
    _, params = parse(header, strict=True)
    assert decode_extended(params) == {
        "access-type": "URL",
        "url": "ftp://cs.utk.edu/pub/moore/bulk-mailer/bulk-mailer.tar",
    }


def test_rfc_charset_example() -> None:
    # RFC 2231 section 4.
    _, params = parse(
        "application/x-stuff; title*=us-ascii'en-us'This%20is%20%2A%2A%2Afun%2A%2A%2A"
    )
    assert decode_extended(params) == {"title": "This is ***fun***"}


def test_rfc_combined_example() -> None:
    # RFC 2231 section 4.1.
    header = (
        "application/x-stuff; title*0*=us-ascii'en'This%20is%20even%20more%20; "
        'title*1*=%2A%2A%2Afun%2A%2A%2A%20; title*2="isn\'t it!"'
    )
    _, params = parse(header, strict=True)
    assert decode_extended(params) == {"title": "This is even more ***fun*** isn't it!"}


def test_sections_are_joined_in_numeric_order_whatever_the_header_order() -> None:
    params = {"t*10": "k", "t*2": "c", "t*0": "a", "t*1": "b"}
    params.update({f"t*{n}": chr(ord("a") + n) for n in range(3, 10)})
    assert decode_extended(params) == {"t": "abcdefghijk"}


def test_a_multibyte_character_may_span_sections() -> None:
    params = {"t*0*": "utf-8''%E2%82", "t*1*": "%AC"}
    assert decode_extended(params) == {"t": "\N{EURO SIGN}"}


def test_the_extended_form_wins_over_the_plain_one_and_keeps_its_place() -> None:
    params = {"name": "fallback.txt", "a": "1", "name*": "utf-8''r%C3%A9sum%C3%A9.txt"}
    assert list(decode_extended(params).items()) == [("name", "r\xe9sum\xe9.txt"), ("a", "1")]


def test_blank_charset_and_language_mean_ascii() -> None:
    assert decode_extended({"t*": "''plain%21"}) == {"t": "plain!"}


def test_other_parameters_pass_through() -> None:
    assert decode_extended({"charset": "utf-8", "boundary": "x"}) == {
        "charset": "utf-8",
        "boundary": "x",
    }


@pytest.mark.parametrize(
    "params",
    [
        {"t*0": "a", "t*2": "c"},
        {"t*1": "b"},
        {"t*00": "a"},
        {"t*01": "a"},
        {"t*0": "a", "t*0*": "''b"},
        {"t*": "''a", "t*0": "b"},
        {"t**": "a"},
        {"*": "a"},
        {"t*x": "a"},
        {"t*": "no-quotes"},
        {"t*": "utf-8'only-one"},
        {"t*": "utf-8''%G1"},
        {"t*": "utf-8''%4"},
        {"t*": "utf-8''\xe9"},
        {"t*0": "\xe9", "t*1*": "%41"},
        {"t*": "no-such-charset''a"},
        {"t*": "zlib''a"},
        {"t*": "iso-8859-1''\xe9"},
        {"t*": "utf-8''%FF"},
        {"t*": "''%C3%A9"},
    ],
)
def test_malformed_extended_parameters_raise(params: dict[str, str]) -> None:
    with pytest.raises(MediaTypeError):
        decode_extended(params)
