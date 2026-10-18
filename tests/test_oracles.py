"""Independent parsers as oracles: Python's email package, werkzeug, multipart and the
whatwg-mimetype reference implementation (run with Node.js).

None is a dependency. Each test skips when its oracle is missing: `pip install werkzeug
multipart` and `npm install --prefix tests/upstream whatwg-mimetype@5.0.0` (the folder is
ignored by git). Differences found are asserted precisely, so a change on either side shows.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
from email.message import Message
from email.utils import collapse_rfc2231_value
from pathlib import Path

import pytest
from conftest import UPSTREAM, read_upstream
from generators import TCHAR, grammar_header, media_params, noise, unicode_text

from mediaparse import MediaTypeError, build, decode_extended, parse, parse_media_type

ROOT = Path(__file__).resolve().parents[1]


def _ours(text: str) -> str | None:
    try:
        return str(parse_media_type(text))
    except MediaTypeError:
        return None


def _whatwg(texts: list[str]) -> list[str | None]:
    node = shutil.which("node")
    package = UPSTREAM / "node_modules" / "whatwg-mimetype" / "package.json"
    if node is None or not package.is_file():
        pytest.skip("node or whatwg-mimetype is missing")
    assert json.loads(package.read_text(encoding="utf-8"))["version"] == "5.0.0"
    script = str(ROOT / "scripts" / "whatwg_oracle.js")
    data = json.dumps(texts).encode("utf-8")
    done = subprocess.run([node, script, str(UPSTREAM)], input=data, capture_output=True)
    assert done.returncode == 0, done.stderr
    result: list[str | None] = json.loads(done.stdout.decode("utf-8"))
    return result


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_default_parser_agrees_with_the_reference_implementation(seed: int) -> None:
    rng = random.Random(seed)
    texts = [noise(rng) for _ in range(20000)]
    assert [_ours(text) for text in texts] == _whatwg(texts)


def test_the_reference_implementation_agrees_on_the_wpt_corpus() -> None:
    texts = [case["input"] for case in read_upstream("wpt-generated-mime-types.json")[1:]]
    texts += [c["input"] for c in read_upstream("wpt-mime-types.json") if isinstance(c, dict)]
    assert [_ours(text) for text in texts] == _whatwg(texts)


def _corpus(seed: int, names: str = TCHAR) -> list[tuple[str, tuple[str, dict[str, str]]]]:
    """Headers from the whole RFC 9110 grammar (half of them), and from build (half)."""
    rng = random.Random(seed)
    out = []
    for _ in range(4000):
        header = grammar_header(rng, names)
        out.append((header, parse(header, strict=True)))
        built = build(*media_params(rng, names))
        out.append((built, parse(built, strict=True)))
    return out


def _email(header: str) -> tuple[str, dict[str, str]]:
    message = Message()
    message["Content-Type"] = header
    return message.get_content_type(), dict((message.get_params() or [])[1:])


def test_email_agrees_on_headers_without_its_known_differences() -> None:
    compared = 0
    for header, expected in _corpus(4):
        starred = any("*" in name for name in expected[1])
        if "\\" in header or re.search(r";[ \t]*(;|$)", header) or starred:
            continue
        assert _email(header) == expected, header
        compared += 1
    assert compared > 3000
    # Its differences: a quoted value ending in an escaped backslash runs past the quote,
    # other escapes keep their backslash, empty parameters appear, name* is RFC 2231.
    assert _email('a/b; x="a\\\\"; y=1')[1] == {"x": '"a\\\\"; y=1'}
    assert _email('a/b; x="\\G"')[1] == {"x": "\\G"}
    assert "" in _email("a/b; x=1;")[1]
    assert _email("a/b; t*=x")[1] != parse("a/b; t*=x")[1]


def test_werkzeug_agrees_except_on_type_case_and_starred_names() -> None:
    http = pytest.importorskip("werkzeug.http")
    compared = 0
    for header, expected in _corpus(5):
        if any("*" in name for name in expected[1]):
            continue
        essence, params = http.parse_options_header(header)
        assert (essence.lower(), params) == expected, header
        compared += 1
    assert compared > 6000
    assert http.parse_options_header("Text/HTML")[0] == "Text/HTML"
    assert http.parse_options_header("a/b; t*=x")[1] == {"t": "x"}


def test_multipart_agrees_within_its_grammar() -> None:
    multipart = pytest.importorskip("multipart")
    # multipart accepts parameter names made of letters, digits, "-" and "_" only.
    names = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    compared = 0
    for header, expected in _corpus(6, names):
        if "\\" in header or re.search(r";[ \t]*\t", header) or "filename" in expected[1]:
            continue
        assert multipart.parse_options_header(header) == expected, header
        compared += 1
    assert compared > 3000
    # Its differences: a tab after ";" hides the parameter, other escapes keep their
    # backslash, a filename is cut to its last path part, other names are dropped.
    assert multipart.parse_options_header("a/b;\tx=1") == ("a/b", {})
    assert multipart.parse_options_header('a/b; x="\\G"')[1] == {"x": "\\G"}
    assert multipart.parse_options_header('a/b; filename="C:\\\\d\\\\a.txt"')[1] == {
        "filename": "a.txt"
    }
    assert multipart.parse_options_header("a/b; x.y=1")[1] == {}


def _extended_cases(seed: int) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    values = [unicode_text(rng) for _ in range(2000)]
    return [(build("a/b", {"t": value}, extended=True), value) for value in values]


def test_rfc_2231_values_decode_like_email() -> None:
    for header, value in _extended_cases(7):
        message = Message()
        message["Content-Type"] = header
        assert decode_extended(parse(header)[1]) == {"t": value}
        if "t*=" not in header:
            continue  # plain values are covered above
        raw = message.get_param("t")
        assert raw is not None
        assert collapse_rfc2231_value(raw) == value


def test_rfc_2231_values_decode_like_werkzeug() -> None:
    http = pytest.importorskip("werkzeug.http")
    for header, value in _extended_cases(8):
        assert http.parse_options_header(header)[1] == {"t": value}, header
        assert decode_extended(parse(header, strict=True)[1]) == {"t": value}
