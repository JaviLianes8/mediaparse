import pytest

from mediaparse import MediaTypeError, parse


def test_simple_type_has_no_params() -> None:
    assert parse("text/html") == ("text/html", {})


def test_charset_param_is_read() -> None:
    assert parse("text/html; charset=utf-8") == ("text/html", {"charset": "utf-8"})


def test_type_and_param_names_are_lower_cased() -> None:
    mimetype, params = parse("TEXT/HTML; CharSet=UTF-8")
    assert mimetype == "text/html"
    assert params == {"charset": "UTF-8"}


def test_value_case_is_preserved() -> None:
    _, params = parse('application/octet-stream; name="File.TXT"')
    assert params["name"] == "File.TXT"


def test_multiple_params_are_all_read() -> None:
    _, params = parse("multipart/form-data; charset=utf-8; boundary=abc123")
    assert params == {"charset": "utf-8", "boundary": "abc123"}


def test_quoted_value_with_special_chars() -> None:
    _, params = parse('application/json; title="a; b=c, d"')
    assert params["title"] == "a; b=c, d"


def test_quoted_value_unescapes_backslash_sequences() -> None:
    _, params = parse(r'text/plain; name="a\"b\\c"')
    assert params["name"] == 'a"b\\c'


def test_surrounding_whitespace_is_ignored() -> None:
    assert parse("  text/plain ;  charset = ascii ") == ("text/plain", {"charset": "ascii"})


def test_boundary_with_a_semicolon_stays_intact() -> None:
    _, params = parse('multipart/mixed; boundary="a;b"')
    assert params["boundary"] == "a;b"


def test_valueless_parameter_is_tolerated_and_dropped() -> None:
    assert parse("text/plain; charset=utf-8; broken") == ("text/plain", {"charset": "utf-8"})


def test_trailing_semicolon_is_tolerated() -> None:
    assert parse("text/plain; charset=utf-8;") == ("text/plain", {"charset": "utf-8"})


def test_unterminated_quote_is_tolerated() -> None:
    _, params = parse('text/plain; name="open')
    assert params["name"] == "open"


def test_last_value_wins_for_a_repeated_param() -> None:
    _, params = parse("text/plain; charset=ascii; charset=utf-8")
    assert params["charset"] == "utf-8"


def test_missing_subtype_raises() -> None:
    with pytest.raises(MediaTypeError):
        parse("text")


def test_invalid_type_token_raises() -> None:
    with pytest.raises(MediaTypeError):
        parse("te xt/html")
