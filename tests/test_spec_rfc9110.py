"""Strict parsing and Accept against RFC 9110, read from the fetched text.

The grammar rules and examples are taken from the fetched RFC 9110 and its verified
erratum 7138 (URLs and sha256 in tests/upstream/MANIFEST.json), never retyped. The files
are not committed; these tests skip until `python scripts/fetch_upstream.py` has run.
"""

from __future__ import annotations

import re

import pytest
from conftest import upstream_prose, upstream_text

from mediaparse import MediaTypeError, matches, normalize, parse_accept, parse_media_type, quality

SAMPLE = [chr(code) for code in range(0x300)] + ["\ud800", "\U0001f600"]
# RFC 5234 core rules that RFC 9110 uses by name (hand-written from RFC 5234 appendix B.1).
CORE = {
    "HTAB": "\t",
    "SP": " ",
    "DIGIT": "0123456789",
    "ALPHA": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "VCHAR": "".join(map(chr, range(0x21, 0x7F))),
}


@pytest.fixture(scope="module")
def rfc() -> str:
    return upstream_text("rfc9110.txt")


def rule(text: str, name: str) -> str:
    """The right-hand side of one ABNF rule of the fetched text, comments removed."""
    match = re.search(rf"^ *{re.escape(name)} +=(.*?)(?=\n\s*\n)", text, re.M | re.S)
    assert match is not None, name
    return re.sub(r";[^\n]*", "", match.group(1))


def chars(text: str, body: str) -> set[str]:
    """Expand an alternation of quoted chars, %x values, ranges and named rules."""
    found: set[str] = set()
    for alt in re.findall(r'"[^"]"|%x[0-9A-F]+(?:-[0-9A-F]+)?|[A-Za-z][\w-]*', body):
        if alt.startswith('"'):
            found.add(alt[1])
        elif alt.startswith("%x"):
            low, _, high = alt[2:].partition("-")
            found.update(map(chr, range(int(low, 16), int(high or low, 16) + 1)))
        else:
            found.update(CORE[alt] if alt in CORE else chars(text, rule(text, alt)))
    return found


def _strict(text: str) -> bool:
    try:
        parse_media_type(text, strict=True)
    except MediaTypeError:
        return False
    return True


def test_tokens_are_exactly_tchar(rfc: str) -> None:
    tchar = chars(rfc, rule(rfc, "tchar"))
    assert len(tchar) == 77
    for char in SAMPLE:
        assert _strict(f"a/{char}") == (char in tchar), repr(char)
        assert _strict(f"{char}/a;{char}={char}") == (char in tchar), repr(char)


def test_quoted_strings_are_exactly_qdtext_and_quoted_pair(rfc: str) -> None:
    qdtext = chars(rfc, rule(rfc, "qdtext"))
    escaped = chars(rfc, rule(rfc, "quoted-pair"))
    assert len(qdtext) == 2 + 1 + 57 + 34 + 128
    for char in SAMPLE:
        assert _strict(f'a/b;x="{char}"') == (char in qdtext), repr(char)
        assert _strict(f'a/b;x="\\{char}"') == (char in escaped), repr(char)


def test_the_media_type_rule_and_the_equivalent_examples(rfc: str) -> None:
    assert 'media-type = type "/" subtype parameters' in rfc
    block = rfc[rfc.index("Section 4.1.2):") : rfc.index("Media types ought to be registered")]
    examples = [line.strip() for line in block.splitlines()[1:] if line.strip()]
    assert len(examples) == 4
    assert len({normalize(text, strict=True) for text in examples}) == 1
    assert normalize(examples[1]) == examples[0].replace(";", "; ")
    assert all(matches(examples[0], other) for other in examples)


def test_whitespace_around_equals_is_refused(rfc: str) -> None:
    assert "parameter-name = token" in rfc
    note = upstream_prose_rfc(rfc, "5.6.6")
    assert 'Parameters do not allow whitespace (not even "bad" whitespace) around the "="' in note
    with pytest.raises(MediaTypeError):
        parse_media_type("a/b; c =d", strict=True)
    with pytest.raises(MediaTypeError):
        parse_media_type("a/b; c= d", strict=True)


def upstream_prose_rfc(rfc: str, section: str) -> str:
    start = rfc.index(f"\n{section}.  ")
    return " ".join(rfc[start : rfc.index("\n5.6.7.", start)].replace("|", " ").split())


def test_qvalue_grammar(rfc: str) -> None:
    body = " ".join(rule(rfc, "qvalue").split())
    assert body == '( "0" [ "." 0*3DIGIT ] ) / ( "1" [ "." 0*3("0") ] )'
    # The rule above, written out by hand.
    grammar = re.compile(r"0(\.[0-9]{0,3})?|1(\.0{0,3})?")
    pool = "01.25"
    candidates = {""} | set(pool)
    for _ in range(5):
        candidates |= {text + char for text in candidates for char in pool}
    for weight in sorted(candidates):
        items = parse_accept(f"a/b;q={weight}")
        assert bool(items) == bool(grammar.fullmatch(weight)), weight
        if items:
            assert items[0].q == float(weight)


def _accept_example(rfc: str, start: str) -> str:
    block = rfc[rfc.index(start) :].split("\n\n")[0]
    return " ".join(block.removeprefix("Accept:").split())


def test_table_5_with_erratum_7138(rfc: str) -> None:
    accept = _accept_example(rfc, "Accept: text/*;q=0.3")
    table = rfc[rfc.index("| Media Type ") : rfc.index("Table 5")]
    rows = dict(re.findall(r"\| (\S+) +\| ([0-9.]+) +\|", table))
    erratum = upstream_prose("rfc9110-erratum-7138.html")
    fixed = erratum[erratum.index("It should say:") : erratum.index("Notes:")]
    corrected = dict(re.findall(r"(\S+/\S+) (1|0\.[0-9]+)", fixed.split("Quality Value")[1]))
    assert len(rows) == 6
    assert {k for k in rows if rows[k] != corrected[k]} == {"text/html;level=3"}
    for offer, weight in corrected.items():
        assert quality(accept, offer) == float(weight), offer


def test_precedence_example(rfc: str) -> None:
    accept = _accept_example(rfc, "Accept: text/*, text/plain, text/plain;format=flowed, */*")
    after = rfc[rfc.index("have the following precedence:") :][:400]
    order = re.findall(r"\d\.  (\S+)", after)
    assert len(order) == 4
    ranked = sorted(parse_accept(accept), key=lambda item: item.specificity(), reverse=True)
    assert [str(item.media_range) for item in ranked] == order


def test_the_audio_and_text_examples(rfc: str) -> None:
    from mediaparse import negotiate

    audio = _accept_example(rfc, "Accept: audio/*; q=0.2, audio/basic")
    assert negotiate(audio, ["audio/ogg", "audio/basic"]) == "audio/basic"
    assert quality(audio, "audio/ogg") == 0.2
    text = _accept_example(rfc, "Accept: text/plain; q=0.5, text/html,")
    weights = [quality(text, offer) for offer in ("text/html", "text/x-c", "text/x-dvi")]
    assert weights == [1.0, 1.0, 0.8]
    assert quality(text, "text/plain") == 0.5
