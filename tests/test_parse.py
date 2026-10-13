"""``parse`` and ``parse_media_type`` in the default, browser-compatible mode.

Hand-written cases from the WHATWG "parse a MIME type" steps, except where a comment
cites the source of the vector.
"""

from __future__ import annotations

import pytest

from mediaparse import MediaType, MediaTypeError, parse, parse_media_type


def test_simple_type_has_no_params() -> None:
    assert parse("text/html") == ("text/html", {})


def test_charset_param_is_read() -> None:
    assert parse("text/html; charset=utf-8") == ("text/html", {"charset": "utf-8"})


def test_type_and_param_names_are_lower_cased_values_are_not() -> None:
    assert parse("TEXT/HTML; CharSet=UTF-8") == ("text/html", {"charset": "UTF-8"})


def test_multiple_params_keep_their_order() -> None:
    _, params = parse("multipart/form-data; charset=utf-8; boundary=abc123")
    assert list(params.items()) == [("charset", "utf-8"), ("boundary", "abc123")]


def test_quoted_value_keeps_separators() -> None:
    assert parse('application/json; title="a; b=c, d"')[1] == {"title": "a; b=c, d"}


def test_quoted_value_unescapes_backslash_sequences() -> None:
    assert parse('text/plain; name="a\\"b\\\\c"')[1] == {"name": 'a"b\\c'}


def test_text_after_a_closing_quote_is_skipped() -> None:
    # The example given in the WHATWG algorithm, https://mimesniff.spec.whatwg.org/
    assert parse('text/html;charset="shift_jis"iso-2022-jp')[1] == {"charset": "shift_jis"}


def test_unterminated_quote_runs_to_the_end() -> None:
    assert parse('text/plain; name="open')[1] == {"name": "open"}


def test_trailing_backslash_in_an_open_quote_is_kept() -> None:
    assert parse('text/plain; name="a\\')[1] == {"name": "a\\"}


def test_http_whitespace_around_the_value_is_trimmed() -> None:
    header = "\r\n\t text/plain \t;\n charset=ascii \t"
    assert parse(header) == ("text/plain", {"charset": "ascii"})


def test_whitespace_before_equals_drops_the_parameter() -> None:
    assert parse("text/plain; charset =ascii; a=b") == ("text/plain", {"a": "b"})


def test_whitespace_after_equals_stays_in_the_value() -> None:
    assert parse("text/plain; charset= ascii") == ("text/plain", {"charset": " ascii"})
    assert str(parse_media_type("text/plain; charset= ascii")) == 'text/plain;charset=" ascii"'


def test_first_value_wins_for_a_repeated_param() -> None:
    assert parse("text/plain; charset=ascii; CHARSET=utf-8")[1] == {"charset": "ascii"}


def test_a_skipped_duplicate_does_not_hide_a_later_valid_one() -> None:
    assert parse("text/plain; charset=; charset=utf-8")[1] == {"charset": "utf-8"}


def test_valueless_and_empty_parameters_are_dropped() -> None:
    assert parse("text/plain; broken; =x; a=; b=1;;") == ("text/plain", {"b": "1"})


def test_an_empty_quoted_value_is_kept() -> None:
    assert parse('text/plain; a=""')[1] == {"a": ""}


def test_a_value_with_a_character_above_latin_1_is_dropped() -> None:
    assert parse("text/plain; a=\N{EURO SIGN}; b=\xe9")[1] == {"b": "\xe9"}


def test_a_value_with_a_control_character_is_dropped() -> None:
    assert parse('text/plain; a="x\x00y"; b="\x7f"; c=1')[1] == {"c": "1"}


def test_a_non_token_name_is_dropped() -> None:
    assert parse("text/plain; a(b)=1; c=2")[1] == {"c": "2"}


def test_only_ascii_letters_are_lower_cased() -> None:
    # KELVIN SIGN folds to "k" under str.lower, which would turn it into a token.
    assert parse("text/plain; \N{KELVIN SIGN}=1")[1] == {}
    with pytest.raises(MediaTypeError):
        parse("\N{KELVIN SIGN}/plain")


@pytest.mark.parametrize(
    "text", ["", "text", "text/", "/html", "te xt/html", "text/ht ml", "text/html/x(", " ;"]
)
def test_no_valid_type_and_subtype_raises(text: str) -> None:
    with pytest.raises(MediaTypeError):
        parse(text)


@pytest.mark.parametrize(
    ("text", "position"), [("  text/h(tml", 7), ("  te xt/html", 2), (" text", 5)]
)
def test_the_error_points_at_the_bad_part(text: str, position: int) -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse(text)
    assert caught.value.position == position


def test_parse_media_type_returns_the_value_object() -> None:
    media = parse_media_type("Application/Vnd.API+JSON; charset=utf-8")
    assert media == MediaType("application", "vnd.api+json", (("charset", "utf-8"),))


def test_non_string_input_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        parse_media_type(b"text/html")  # type: ignore[arg-type]
