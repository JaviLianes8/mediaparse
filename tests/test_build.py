"""``build``: quoting, the injection guard and extended values.

Hand-written, except the RFC 8187 section 3.2.3 vector, which is marked with its URL.
"""

from __future__ import annotations

import pytest

from mediaparse import MediaTypeError, build, decode_extended, parse


def test_build_simple_type() -> None:
    assert build("text/html") == "text/html"


def test_build_with_a_token_value_stays_unquoted() -> None:
    assert build("text/html", {"charset": "utf-8"}) == "text/html; charset=utf-8"


def test_build_quotes_values_with_special_chars() -> None:
    assert build("application/json", {"title": "a; b"}) == 'application/json; title="a; b"'


def test_build_escapes_only_quotes_and_backslashes() -> None:
    assert build("text/plain", {"name": 'a"b\\c\td'}) == 'text/plain; name="a\\"b\\\\c\td"'


def test_build_quotes_an_empty_value() -> None:
    assert build("text/plain", {"x": ""}) == 'text/plain; x=""'


def test_build_lower_cases_type_and_param_names() -> None:
    assert build(" TEXT/Plain ", {" CharSet ": "utf-8"}) == "text/plain; charset=utf-8"


@pytest.mark.parametrize("mimetype", ["texthtml", "text/", "/html", "te xt/html", "a/b/c", ""])
def test_build_rejects_an_invalid_mimetype(mimetype: str) -> None:
    with pytest.raises(MediaTypeError):
        build(mimetype)


@pytest.mark.parametrize("name", ["bad name", "", "a=b", "\N{KELVIN SIGN}"])
def test_build_rejects_an_invalid_param_name(name: str) -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {name: "x"})


def test_build_rejects_two_names_equal_after_lower_casing() -> None:
    with pytest.raises(MediaTypeError, match="more than once"):
        build("text/plain", {"a": "1", "A": "2"})


@pytest.mark.parametrize(
    "value", ["a\r\nSet-Cookie: x=y", "a\nb", "a\rb", "a\x00b", "a\x7fb", "\x1b[31m"]
)
def test_build_never_writes_a_control_character(value: str) -> None:
    with pytest.raises(MediaTypeError, match="extended=True"):
        build("text/plain", {"x": value})


@pytest.mark.parametrize("value", ["caf\xe9", "\N{EURO SIGN}", "\N{GRINNING FACE}"])
def test_build_rejects_non_ascii_unless_extended(value: str) -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"title": value})


def test_extended_matches_the_rfc_8187_example() -> None:
    # https://www.rfc-editor.org/rfc/rfc8187.txt section 3.2.3: the value is
    # "\N{POUND SIGN} and \N{EURO SIGN} rates", sent as
    # title*=UTF-8''%c2%a3%20and%20%e2%82%ac%20rates
    built = build("text/plain", {"title": "\N{POUND SIGN} and \N{EURO SIGN} rates"}, extended=True)
    assert built.lower() == "text/plain; title*=utf-8''%c2%a3%20and%20%e2%82%ac%20rates"


def test_extended_leaves_plain_values_alone_and_escapes_controls() -> None:
    built = build("text/plain", {"a": "x y", "b": "1\r\n*'%"}, extended=True)
    assert built == "text/plain; a=\"x y\"; b*=UTF-8''1%0D%0A%2A%27%25"


def test_extended_values_decode_back() -> None:
    value = "na\xefve \N{EURO SIGN} \N{GRINNING FACE}"
    _, params = parse(build("text/plain", {"title": value}, extended=True), strict=True)
    assert decode_extended(params) == {"title": value}


def test_extended_rejects_a_name_that_already_ends_in_a_star() -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"title*": "\xe9"}, extended=True)


def test_extended_rejects_a_lone_surrogate() -> None:
    with pytest.raises(MediaTypeError):
        build("text/plain", {"title": "\udc80"}, extended=True)


def test_build_rejects_non_string_input() -> None:
    with pytest.raises(TypeError, match="mimetype must be a str"):
        build(b"text/plain")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build("text/plain", {"a": 1})  # type: ignore[dict-item]
    with pytest.raises(TypeError):
        build("text/plain", {1: "a"})  # type: ignore[dict-item]


def test_round_trip_through_build_and_parse() -> None:
    mimetype, params = "multipart/form-data", {"boundary": "a; b=c", "charset": "utf-8"}
    assert parse(build(mimetype, params)) == (mimetype, params)
    assert parse(build(mimetype, params), strict=True) == (mimetype, params)


@pytest.mark.parametrize(
    "params",
    [{"T": "\x7f", "t": "x"}, {"t": "x", "T": "\xe9"}, {"title*0": "\xe9"}, {"a*b": "x"}],
)
def test_extended_names_are_unique_and_never_read_as_sections(params: dict[str, str]) -> None:
    with pytest.raises(MediaTypeError):
        build("a/b", params, extended=True)
