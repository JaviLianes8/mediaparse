from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def upstream_bytes(name: str) -> bytes:
    """Return a third-party file, checked against its manifest entry.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body


def read_upstream(name: str) -> Any:
    """Return a fetched third-party JSON file."""
    return json.loads(upstream_bytes(name).decode("utf-8"))


def upstream_text(name: str) -> str:
    """Return a fetched text file (an RFC) as it is."""
    return upstream_bytes(name).decode("utf-8", errors="replace")


def upstream_prose(name: str) -> str:
    """Return a fetched HTML page as plain text: tags removed, whitespace collapsed."""
    text = re.sub(r"<[^>]+>", " ", upstream_bytes(name).decode("utf-8"))
    return re.sub(r"\s+", " ", html.unescape(text))


def sentence(prose: str, start: str) -> str:
    """Return the sentence of ``prose`` that begins with ``start``, up to its full stop."""
    index = prose.find(start)
    assert index >= 0, start
    end = prose.find(". ", index)
    return prose[index:end]


def code_points(text: str) -> set[str]:
    """The code points a spec sentence names: ``U+0021`` singles and ``U+0020 ... U+007E``
    ranges ("in the range X to Y" or "X through Y")."""
    found: set[str] = set()
    pattern = r"range U\+([0-9A-F]{4})[^U]*?(?:to|through) U\+([0-9A-F]{4})"
    for low, high in re.findall(pattern, text):
        found.update(chr(code) for code in range(int(low, 16), int(high, 16) + 1))
    singles = re.sub(pattern, "", text)
    found.update(chr(int(code, 16)) for code in re.findall(r"U\+([0-9A-F]{4})", singles))
    if "ASCII alphanumeric" in text:
        found.update("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return found
