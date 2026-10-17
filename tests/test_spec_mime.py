"""Parameters against RFC 2231, RFC 8187, RFC 2045 and RFC 6838, read from the fetched text.

Every header below is cut out of the fetched RFC (or of a verified erratum page); the
expected decoded values come from those same texts, or from Python's own percent
decoder as an independent oracle. URLs and sha256 are in tests/upstream/MANIFEST.json;
the files are not committed and these tests skip until scripts/fetch_upstream.py ran.
"""

from __future__ import annotations

import re
from urllib.parse import unquote

import pytest
from conftest import upstream_prose, upstream_text

from mediaparse import MediaType, MediaTypeError, build, decode_extended, matches, parse


def headers(text: str, field: str) -> list[str]:
    """Every ``field:`` header of the text with its folded lines joined, field name removed."""
    found = re.findall(rf"^ *{field}: ([^\n]*\n(?:[ \t]+\S[^\n]*\n)*)", text, re.M | re.I)
    return [" ".join(value.split()) for value in found]


def _value(header: str, name: str) -> str:
    match = re.search(rf"{re.escape(name)}=(\S+?)(?:;|$)", header)
    assert match is not None, (header, name)
    return match.group(1)


def test_rfc_2231_section_3_continuations_equal_the_joined_form() -> None:
    rfc = upstream_text("rfc2231.txt")
    pieces, joined = [h for h in headers(rfc, "Content-Type") if "external-body" in h]
    assert "URL*0=" in pieces and "URL*1=" in pieces
    assert decode_extended(parse(pieces)[1]) == parse(joined)[1]


def test_rfc_2231_section_4_charset_and_language() -> None:
    rfc = upstream_text("rfc2231.txt")
    (header,) = [h for h in headers(rfc, "Content-Type") if "title*=" in h]
    encoded = _value(header, "title*")
    charset, language, data = encoded.split("'")
    assert (charset, language) == ("us-ascii", "en-us")
    assert decode_extended(parse(header)[1]) == {"title": unquote(data)}


def test_rfc_2231_section_4_1_as_corrected_by_erratum_590() -> None:
    prose = upstream_prose("rfc2231-erratum-590.html")
    fixed = prose[prose.index("It should say:") :]
    header = fixed[fixed.index("Content-Type: ") + 14 : fixed.index('"isn\'t it!"') + 11]
    params = parse(header, strict=True)[1]
    first = params["title*0*"].split("'", 2)[2]
    expected = unquote(first) + unquote(params["title*1*"]) + params["title*2"]
    assert decode_extended(params) == {"title": expected}
    assert expected == "This is even more ***fun*** isn't it!"


def test_rfc_8187_examples() -> None:
    rfc = upstream_text("rfc8187.txt")
    examples = headers(rfc[rfc.index("3.2.3.  Examples\n\n") :], "foo")[:4]
    assert examples[0] == "bar; title=Economy"
    values = [decode_extended(parse("x/" + h)[1])["title"] for h in examples]
    expected = [
        "Economy",
        "US-$ rates",
        unquote(_value(examples[2], "title*").split("'", 2)[2]),
        unquote(_value(examples[3], "title*").split("'", 2)[2]),
    ]
    assert values == expected
    assert values[2:] == ["\xa3 rates", "\xa3 and € rates"]
    for value in values:
        written = build("x/bar", {"title": value}, extended=True)
        assert decode_extended(parse(written, strict=True)[1]) == {"title": value}


def test_rfc_2045_quoted_and_token_values_are_equivalent() -> None:
    rfc = upstream_text("rfc2045.txt")
    found = headers(rfc, "Content-type")
    assert 'text/plain; charset="us-ascii"' in found
    assert "text/plain; charset=us-ascii" in found
    assert matches('text/plain; charset="us-ascii"', "text/plain; charset=us-ascii")


def test_rfc_2045_comments_are_not_part_of_http_media_types() -> None:
    rfc = upstream_text("rfc2045.txt")
    commented = next(h for h in headers(rfc, "Content-type") if "(" in h)
    assert commented == "text/plain; charset=us-ascii (Plain text)"
    with pytest.raises(MediaTypeError):
        parse(commented, strict=True)
    assert parse(commented) == ("text/plain", {"charset": "us-ascii (Plain text)"})


def test_rfc_6838_registrable_names_are_tokens() -> None:
    rfc = upstream_text("rfc6838.txt")
    block = rfc[rfc.index("restricted-name-chars  =") : rfc.index("Note that this syntax")]
    named = set(re.findall(r'"(.)"', block))
    allowed = named | set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert named == set("!#$&-^_.+")
    for char in allowed:
        assert MediaType("a" + char, "b" + char).essence == f"a{char}/b{char}".lower()
    longest = "a" + "b" * 126
    assert "*126restricted-name-chars" in rfc
    assert MediaType(longest, longest).subtype == longest


def test_rfc_6838_a_repeated_parameter_is_an_error() -> None:
    rfc = " ".join(upstream_text("rfc6838.txt").split())
    assert "It is an error for a specific parameter to be specified more than once." in rfc
    with pytest.raises(MediaTypeError):
        parse("text/plain; charset=a; CHARSET=b", strict=True)
    with pytest.raises(MediaTypeError):
        MediaType("text", "plain", (("charset", "a"), ("Charset", "b")))
