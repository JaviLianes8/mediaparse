from mediaparse import matches, normalize


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
