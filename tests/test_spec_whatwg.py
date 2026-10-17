"""The default parser against the WHATWG standards, read from the fetched pages.

The code point classes are taken from the prose of the WHATWG MIME Sniffing standard and
the Fetch standard (commit snapshots, URLs and sha256 in tests/upstream/MANIFEST.json) and
compared, code point by code point, with what the parser accepts. The pages are not
committed; these tests skip until `python scripts/fetch_upstream.py` has fetched them.
"""

from __future__ import annotations

import re

import pytest
from conftest import code_points, sentence, upstream_prose

from mediaparse import MediaTypeError, parse_media_type

# Every code point up to U+02FF, plus a few far ones: surrogates and astral characters.
SAMPLE = [chr(code) for code in range(0x300)] + ["\ud800", "\udfff", "\uffff", "\U0001f600"]


@pytest.fixture(scope="module")
def mimesniff() -> str:
    return upstream_prose("whatwg-mimesniff.html")


@pytest.fixture(scope="module")
def fetch() -> str:
    return upstream_prose("whatwg-fetch.html")


def _parses(text: str) -> bool:
    try:
        parse_media_type(text)
    except MediaTypeError:
        return False
    return True


def test_the_token_code_points_are_those_of_the_standard(mimesniff: str) -> None:
    token = code_points(sentence(mimesniff, "An HTTP token code point is"))
    assert len(token) == 77
    for char in SAMPLE:
        assert _parses("a/" + char) == (char in token), repr(char)
        assert _parses(char + "/a") == (char in token), repr(char)
        named = parse_media_type(f"a/b;{char}=1").params
        assert (named == ((char.lower(), "1"),)) == (char in token), repr(char)


def test_the_quoted_string_code_points_are_those_of_the_standard(mimesniff: str) -> None:
    allowed = code_points(sentence(mimesniff, "An HTTP quoted-string token code point is"))
    assert len(allowed) == 1 + 95 + 128
    for char in SAMPLE:
        if char in '"\\':
            continue
        kept = parse_media_type(f'a/b;x="{char}"').params
        assert (kept == (("x", char),)) == (char in allowed), repr(char)
        bare = parse_media_type(f"a/b;x=a{char}").params
        assert (bare == (("x", "a" + char),)) == (char in allowed and char not in "; \t\r\n")


def test_http_whitespace_is_what_the_fetch_standard_says(fetch: str) -> None:
    tab_or_space = code_points(sentence(fetch, "HTTP tab or space is"))
    whitespace = code_points(sentence(fetch, "HTTP whitespace is")) | tab_or_space
    assert whitespace == set("\t\n\r ")
    for char in SAMPLE:
        if char.isascii() and (char.isalnum() or char in "!#$%&'*+-.^_`|~"):
            continue
        assert _parses(f"{char}a/b{char}") == (char in whitespace), repr(char)


def test_the_algorithm_steps_and_its_example(mimesniff: str) -> None:
    steps = mimesniff[mimesniff.find("To parse a MIME type") :][:3000]
    for phrase, (text, expected) in {
        "Remove any leading and trailing HTTP whitespace from input": (" a/b\r\n", "a/b"),
        "If position is past the end of input , then return failure": ("a", None),
        "Remove any trailing HTTP whitespace from subtype": ("a/b \t;c=d", "a/b;c=d"),
        "If parameterValue is the empty string, then continue": ("a/b;c= ;c=d", "a/b;c=d"),
        "[ parameterName ] does not exist": ("a/b;c=1;C=2", "a/b;c=1"),
        "If the code point at position within input is U+003B (;), then continue": (
            "a/b;c;d=1",
            "a/b;d=1",
        ),
    }.items():
        assert phrase in steps, phrase
        assert _serialized(text) == expected, text
    example = re.search(r"Given (\S+) you end up with (\S+) \.", steps)
    assert example is not None
    assert example.group(1) == 'text/html;charset="shift_jis"iso-2022-jp'
    assert _serialized(example.group(1)) == example.group(2)


def _serialized(text: str) -> str | None:
    try:
        return str(parse_media_type(text))
    except MediaTypeError:
        return None


def test_the_serialization_rule_is_the_one_str_uses(mimesniff: str) -> None:
    rule = mimesniff[mimesniff.find("To serialize a MIME type") :][:1500]
    assert "does not solely contain HTTP token code points or value is the empty string" in rule
    assert str(parse_media_type('a/b;x="";y="a b";z=tok;w="q\\"\\\\"')) == (
        'a/b;x="";y="a b";z=tok;w="q\\"\\\\"'
    )
