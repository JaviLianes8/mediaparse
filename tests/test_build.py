import pytest

from mediaparse import MediaTypeError, build, parse


def test_build_simple_type() -> None:
    assert build("text/html") == "text/html"


def test_build_with_a_token_value_stays_unquoted() -> None:
    assert build("text/html", {"charset": "utf-8"}) == "text/html; charset=utf-8"


def test_build_quotes_values_with_special_chars() -> None:
    assert build("application/json", {"title": "a; b"}) == 'application/json; title="a; b"'


def test_build_escapes_quotes_and_backslashes() -> None:
    assert build("text/plain", {"name": 'a"b\\c'}) == r'text/plain; name="a\"b\\c"'


def test_build_quotes_an_empty_value() -> None:
    assert build("text/plain", {"x": ""}) == 'text/plain; x=""'


def test_build_lower_cases_type_and_param_names() -> None:
    assert build("TEXT/Plain", {"CharSet": "utf-8"}) == "text/plain; charset=utf-8"


def test_build_rejects_an_invalid_mimetype() -> None:
    with pytest.raises(MediaTypeError):
        build("texthtml")


def test_build_rejects_an_invalid_param_name() -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"bad name": "x"})


def test_round_trip_through_build_and_parse() -> None:
    mimetype, params = "multipart/form-data", {"boundary": "a; b=c", "charset": "utf-8"}
    assert parse(build(mimetype, params)) == (mimetype, params)
