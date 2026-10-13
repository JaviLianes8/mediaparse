from __future__ import annotations

import pytest

from mediaparse import MediaTypeError, matches, normalize


def test_normalize_lower_cases_type_and_param_names() -> None:
    assert normalize("TEXT/HTML; CharSet=utf-8") == "text/html; charset=utf-8"


def test_normalize_lower_cases_the_charset_value() -> None:
    assert normalize("text/html; charset=UTF-8") == "text/html; charset=utf-8"


def test_normalize_keeps_other_value_case() -> None:
    header = 'application/octet-stream; name="My File.TXT"'
    assert normalize(header) == header


def test_normalize_sorts_parameters_by_name() -> None:
    assert normalize("x/y; b=2; a=1") == "x/y; a=1; b=2"


def test_matches_ignores_case_and_order() -> None:
    assert matches("Text/HTML; charset=UTF-8", "text/html; CharSet=utf-8")


def test_matches_is_false_for_different_values() -> None:
    assert not matches("text/html; charset=utf-8", "text/html; charset=ascii")


def test_normalize_reads_like_a_browser_by_default() -> None:
    assert normalize("text/html; charset=UTF-8; charset=ascii; x =1") == "text/html; charset=utf-8"


def test_normalize_strict_rejects_what_the_rfc_rejects() -> None:
    with pytest.raises(MediaTypeError):
        normalize("text/html; x =1", strict=True)


def test_normalize_quotes_latin_1_values_it_has_read() -> None:
    assert normalize('text/plain; name="caf\xe9"') == 'text/plain; name="caf\xe9"'


def test_normalize_lower_cases_charset_in_ascii_only() -> None:
    assert normalize('text/plain; charset="\xc9X"') == 'text/plain; charset="\xc9x"'


def test_matches_raises_on_an_invalid_header() -> None:
    with pytest.raises(MediaTypeError):
        matches("text", "text/plain")
