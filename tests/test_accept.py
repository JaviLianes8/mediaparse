"""Accept parsing, quality lookup and negotiation.

Vectors marked "RFC 9110" are cited from section 12.5.1 of
https://www.rfc-editor.org/rfc/rfc9110.txt; Table 5 is read with verified erratum 7138
(https://www.rfc-editor.org/errata/eid7138), which changes its last row from 0.7 to 0.3.
The other cases are hand-written from the grammar in sections 12.4.2 and 12.5.1.
"""

from __future__ import annotations

import pytest

from mediaparse import AcceptItem, MediaType, MediaTypeError, negotiate, parse_accept, quality

# RFC 9110 section 12.5.1, the example before Table 5.
TABLE_5_ACCEPT = (
    "text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, "
    "text/plain;format=fixed;q=0.4, */*;q=0.5"
)
TABLE_5 = [
    ("text/plain;format=flowed", 1.0),
    ("text/plain", 0.7),
    ("text/html", 0.3),
    ("image/jpeg", 0.5),
    ("text/plain;format=fixed", 0.4),
    ("text/html;level=3", 0.3),  # 0.7 in the RFC text, 0.3 after erratum 7138
]


@pytest.mark.parametrize(("offer", "weight"), TABLE_5)
def test_rfc_table_5(offer: str, weight: float) -> None:
    assert quality(TABLE_5_ACCEPT, offer) == weight


def test_rfc_precedence_example() -> None:
    # RFC 9110: "text/*, text/plain, text/plain;format=flowed, */*" in precedence order
    # text/plain;format=flowed, text/plain, text/*, */*.
    items = parse_accept("text/*, text/plain, text/plain;format=flowed, */*")
    ranked = sorted(items, key=AcceptItem.specificity, reverse=True)
    assert [str(item.media_range) for item in ranked] == [
        "text/plain;format=flowed",
        "text/plain",
        "text/*",
        "*/*",
    ]


def test_rfc_audio_example() -> None:
    # RFC 9110: "audio/*; q=0.2, audio/basic" prefers audio/basic.
    accept = "audio/*; q=0.2, audio/basic"
    assert negotiate(accept, ["audio/ogg", "audio/basic"]) == "audio/basic"
    assert quality(accept, "audio/ogg") == 0.2


def test_rfc_text_example() -> None:
    # RFC 9110: text/html and text/x-c equal, then text/x-dvi, then text/plain.
    # The RFC wraps the field over two lines; the field value joins them with a space.
    accept = "text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c"
    assert negotiate(accept, ["text/plain", "text/x-dvi"]) == "text/x-dvi"
    assert negotiate(accept, ["text/x-c", "text/html"]) == "text/x-c"
    assert negotiate(accept, ["text/plain"]) == "text/plain"


def test_items_keep_header_order_and_drop_q_from_the_range() -> None:
    items = parse_accept("text/html;level=1;q=0.5;x=y, */*")
    assert items == [
        AcceptItem(MediaType("text", "html", (("level", "1"), ("x", "y"))), 0.5),
        AcceptItem(MediaType("*", "*"), 1.0),
    ]


def test_commas_inside_quoted_strings_do_not_split() -> None:
    (item,) = parse_accept('text/plain;title="a, b";q=0.1')
    assert (item.media_range.get("title"), item.q) == ("a, b", 0.1)


def test_empty_elements_are_ignored() -> None:
    assert len(parse_accept(" , text/html,, ,\t*/*,")) == 2
    assert len(parse_accept(" , text/html,, ,\t*/*,", strict=True)) == 2
    assert parse_accept("") == []


@pytest.mark.parametrize(
    ("weight", "q"),
    [("0", 0.0), ("0.", 0.0), ("0.001", 0.001), ("0.5", 0.5), ("1", 1.0), ("1.000", 1.0)],
)
def test_valid_weights(weight: str, q: float) -> None:
    assert parse_accept(f"text/html;Q={weight}")[0].q == q


@pytest.mark.parametrize("weight", ["1.001", "2", "0.0001", "-0", ".5", "1e0", "abc"])
def test_invalid_weights_skip_the_element_or_raise_in_strict_mode(weight: str) -> None:
    accept = f"text/html;q={weight}, image/png"
    assert [str(item.media_range) for item in parse_accept(accept)] == ["image/png"]
    with pytest.raises(MediaTypeError):
        parse_accept(accept, strict=True)


@pytest.mark.parametrize("element", ["*/html", "text", "te xt/html", "*"])
def test_invalid_ranges_skip_or_raise(element: str) -> None:
    assert len(parse_accept(f"{element}, text/plain")) == 1
    with pytest.raises(MediaTypeError):
        parse_accept(f"{element}, text/plain", strict=True)


def test_a_quoted_weight_is_malformed_in_both_modes() -> None:
    assert parse_accept('text/html;q="0.5", a/b') == parse_accept("a/b")
    assert parse_accept('text/html;Q="1";q=0.5, a/b') == parse_accept("a/b")
    with pytest.raises(MediaTypeError) as caught:
        parse_accept('a/b, text/html;q="0.5"', strict=True)
    assert caught.value.position == 17
    with pytest.raises(MediaTypeError):
        parse_accept("text/html; q = 0.5", strict=True)


@pytest.mark.parametrize(
    ("header", "position", "message"),
    [
        ("text/html, image/png;q=7", 23, "q='7'"),
        ("text/html, ima ge/png", 14, "at position 14"),
        ("a/b, c/d; =1", 10, "at position 10"),
        ("a/b,  */html", 6, "'*/html'"),
        ("a/b, c/d;x=1;X=2", 13, "more than once"),
    ],
)
def test_strict_errors_point_into_the_whole_header(
    header: str, position: int, message: str
) -> None:
    with pytest.raises(MediaTypeError) as caught:
        parse_accept(header, strict=True)
    assert caught.value.position == position
    assert message in str(caught.value)


def test_a_missing_accept_field_accepts_everything() -> None:
    assert quality(None, "image/png") == 1.0
    assert negotiate(None, ["image/png", "text/html"]) == "image/png"


def test_an_empty_accept_field_accepts_nothing() -> None:
    assert negotiate("", ["text/html"]) is None
    assert quality("", "text/html") == 0.0


def test_q_zero_means_not_acceptable() -> None:
    assert negotiate("text/html;q=0, */*;q=0.1", ["text/html"]) is None
    assert negotiate("*/*;q=0", ["text/html", "image/png"]) is None


def test_the_most_specific_range_wins_even_with_a_lower_weight() -> None:
    assert quality("text/*;q=0.9, text/html;q=0.1", "text/html") == 0.1


def test_the_earliest_range_wins_between_equally_specific_ones() -> None:
    assert quality("text/html;q=0.2, text/html;q=0.8", "text/html") == 0.2


def test_ties_go_to_the_server_order_and_offers_come_back_as_given() -> None:
    assert negotiate("*/*", ["Text/HTML; charset=UTF-8", "image/png"]) == "Text/HTML; charset=UTF-8"
    assert negotiate("text/html, application/json", ["application/json", "text/html"]) == (
        "application/json"
    )


def test_range_parameters_must_all_match_the_offer() -> None:
    accept = "text/html;level=1, text/html;q=0.4"
    assert quality(accept, "text/html;level=1") == 1.0
    assert quality(accept, "text/html;level=2") == 0.4
    assert quality(accept, "text/html") == 0.4


def test_charset_matches_case_insensitively_other_values_exactly() -> None:
    assert quality("text/html;charset=UTF-8", "text/html;charset=utf-8") == 1.0
    assert quality("text/html;level=A", "text/html;level=a") == 0.0


def test_types_match_case_insensitively() -> None:
    assert quality("TEXT/HTML", "text/html") == 1.0


@pytest.mark.parametrize("offer", ["text/*", "*/*", "text", ""])
def test_offers_must_be_concrete(offer: str) -> None:
    with pytest.raises(MediaTypeError):
        quality("*/*", offer)
    with pytest.raises(MediaTypeError):
        negotiate("*/*", [offer])


def test_no_offers_means_no_choice() -> None:
    assert negotiate("*/*", []) is None


def test_non_string_header_is_a_type_error() -> None:
    with pytest.raises(TypeError, match="expected str, got NoneType"):
        parse_accept(None)  # type: ignore[arg-type]
