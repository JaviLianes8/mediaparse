"""The web-platform-tests MIME type corpus, parsed and serialized like a browser.

Files: `mimesniff/mime-types/resources/mime-types.json` and `generated-mime-types.json`
from web-platform-tests (URL, commit, size and sha256 in tests/upstream/MANIFEST.json).
They are not committed; these tests skip until `python scripts/fetch_upstream.py` has
fetched them. Each case gives an input and the serialization a browser produces, or
null where parsing must fail.
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import read_upstream

from mediaparse import MediaType, MediaTypeError, parse_media_type


def _cases(name: str) -> list[dict[str, Any]]:
    return [case for case in read_upstream(name) if isinstance(case, dict)]


def _serialize(text: str) -> str | None:
    try:
        return str(parse_media_type(text))
    except MediaTypeError:
        return None


@pytest.mark.parametrize("name", ["wpt-mime-types.json", "wpt-generated-mime-types.json"])
def test_every_case_matches_the_browser_serialization(name: str) -> None:
    cases = _cases(name)
    assert len(cases) > 50
    wrong = [case for case in cases if _serialize(case["input"]) != case["output"]]
    assert wrong == []


@pytest.mark.parametrize("name", ["wpt-mime-types.json", "wpt-generated-mime-types.json"])
def test_serialization_is_stable_on_a_second_pass(name: str) -> None:
    for case in _cases(name):
        if case["output"] is not None:
            again = parse_media_type(case["output"])
            assert str(again) == case["output"]
            assert MediaType(again.type, again.subtype, again.params) == again


def test_the_corpus_has_failures_and_successes() -> None:
    cases = _cases("wpt-mime-types.json")
    assert any(case["output"] is None for case in cases)
    assert any(case["output"] is not None for case in cases)
