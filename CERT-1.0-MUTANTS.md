# mediaparse 1.0.0 author mutation table

The author mutation round of [CERT-1.0-REPORT.md](https://github.com/JaviLianes8/mediaparse/blob/main/CERT-1.0-REPORT.md),
recorded at e981f60 with the fetched sources, werkzeug, multipart and the 0.2.0 oracle but
without the Node.js reference (with it, M11 is caught first by the WPT reference test).
M13, M14, M19, M37, M40 and M43 were written against code that changed later in the round.

| Mutant | Module | Change | Killed by |
| --- | --- | --- | --- |
| M01 | `_tokens.py` | tchar drops the backtick | `test_fuzz.py::test_strict_accepts_exactly_the_grammar[11]` |
| M02 | `_tokens.py` | HTTP whitespace loses CR | `test_parse.py::test_http_whitespace_around_the_value_is_trimmed` |
| M03 | `_tokens.py` | obs-text upper bound off by one | `test_spec_rfc9110.py::test_quoted_strings_are_exactly_qdtext_and_quoted_pair` |
| M04 | `_tokens.py` | quote escapes only the quote | `test_build.py::test_build_escapes_only_quotes_and_backslashes` |
| M05 | `_tokens.py` | ascii_lower uses str.lower | `test_build.py::test_build_rejects_an_invalid_param_name[\u212a]` |
| M06 | `_tokens.py` | empty string counts as a token | `test_build.py::test_build_quotes_an_empty_value` |
| M07 | `_lenient.py` | first duplicate no longer wins | `_parse.py::mediaparse._parse.parse_media_type` |
| M08 | `_lenient.py` | subtype trailing whitespace kept | `test_fuzz.py::test_parsing_never_crashes_and_is_stable[11]` |
| M09 | `_lenient.py` | empty unquoted value kept | `test_parse.py::test_a_skipped_duplicate_does_not_hide_a_later_valid_one` |
| M10 | `_lenient.py` | text after closing quote not skipped | `test_parse.py::test_nothing_between_a_closing_quote_and_the_next_semicolon_is_read` |
| M11 | `_lenient.py` | lone trailing backslash dropped | `test_parse.py::test_trailing_backslash_in_an_open_quote_is_kept` |
| M12 | `_lenient.py` | leading whitespace not trimmed | `_accept.py::mediaparse._accept.parse_accept` |
| M13 | `_lenient.py` | error position off by one | `test_fuzz.py::test_parsing_never_crashes_and_is_stable[11]` |
| M14 | `_strict.py` | duplicate allowed in strict | `test_contract_api.py::test_media_type_error_is_a_value_error_with_a_position_that_pickles` |
| M15 | `_strict.py` | qdtext accepts DEL | `test_strict.py::test_invalid_headers_raise_at_the_first_bad_character[text/plain;a="\x7f"-14]` |
| M16 | `_strict.py` | quoted-pair refuses tab | `test_spec_rfc9110.py::test_quoted_strings_are_exactly_qdtext_and_quoted_pair` |
| M17 | `_strict.py` | OWS before = accepted | `_errors.py::mediaparse._errors.MediaTypeError` |
| M18 | `_strict.py` | empty parameter after ; refused | `test_fuzz.py::test_strict_accepts_exactly_the_grammar[11]` |
| M19 | `_strict.py` | quoted names not recorded | `test_accept.py::test_strict_mode_rejects_a_quoted_weight_and_whitespace_around_equals` |
| M20 | `_mediatype.py` | suffix from first plus | `test_mediatype.py::test_suffix_is_the_part_after_the_last_plus[application/a+b+cbor-cbor]` |
| M21 | `_mediatype.py` | get is case sensitive | `_mediatype.py::mediaparse._mediatype.MediaType.get` |
| M22 | `_mediatype.py` | duplicate names allowed | `test_mediatype.py::test_invalid_parts_raise[text-plain-params8]` |
| M23 | `_mediatype.py` | str uses '; ' | `_mediatype.py::mediaparse._mediatype.MediaType` |
| M24 | `_mediatype.py` | value check skipped | `test_hostile.py::test_messages_stay_short_for_huge_input[<lambda>12]` |
| M25 | `_build.py` | control characters written | `test_build.py::test_build_never_writes_a_control_character` |
| M26 | `_build.py` | duplicate names written | `test_build.py::test_build_rejects_two_names_equal_after_lower_casing` |
| M27 | `_build.py` | name not lower-cased | `test_build.py::test_build_lower_cases_type_and_param_names` |
| M28 | `_extended.py` | space kept unencoded | `test_build.py::test_extended_matches_the_rfc_8187_example` |
| M29 | `_extended.py` | lower-case hex digits refused | `test_spec_mime.py::test_rfc_8187_examples` |
| M30 | `_extended.py` | non-ASCII passes through | `test_rfc2231.py::test_malformed_extended_parameters_raise[params17]` |
| M31 | `_rfc2231.py` | leading zero sections allowed | `test_rfc2231.py::test_malformed_extended_parameters_raise[params2]` |
| M32 | `_rfc2231.py` | gaps allowed | `test_rfc2231.py::test_malformed_extended_parameters_raise[params0]` |
| M33 | `_rfc2231.py` | plain wins over extended | `test_rfc2231.py::test_the_extended_form_wins_over_the_plain_one_and_keeps_its_place` |
| M34 | `_rfc2231.py` | escape codecs allowed | `test_review_regressions.py::test_decode_extended_only_raises_media_type_error[params5]` |
| M35 | `_rfc2231.py` | empty charset not us-ascii | `test_rfc2231.py::test_malformed_extended_parameters_raise[params19]` |
| M36 | `_accept.py` | qvalue allows four decimals | `test_accept.py::test_invalid_weights_skip_the_element_or_raise_in_strict_mode[0.0001]` |
| M37 | `_accept.py` | malformed q read as 1 | `test_review_regressions.py::test_a_malformed_weight_never_becomes_weight_one[text/html;` |
| M38 | `_accept.py` | commas inside quotes split | `test_accept.py::test_commas_inside_quoted_strings_do_not_split` |
| M39 | `_accept.py` | q kept in the range | `_accept.py::mediaparse._accept.parse_accept` |
| M40 | `_accept.py` | strict position not shifted | `test_accept.py::test_strict_errors_point_into_the_whole_header` |
| M41 | `_acceptitem.py` | specificity ignores params | `_acceptitem.py::mediaparse._acceptitem.AcceptItem.specificity` |
| M42 | `_acceptitem.py` | charset compared with case | `test_accept.py::test_charset_matches_case_insensitively_other_values_exactly` |
| M43 | `_acceptitem.py` | q range check upper bound | `test_contract_api.py::test_invalid_values_raise_media_type_error[<lambda>14]` |
| M44 | `_negotiate.py` | tie goes to the last offer | `test_accept.py::test_rfc_text_example` |
| M45 | `_negotiate.py` | latest range wins a tie | `test_accept.py::test_the_earliest_range_wins_between_equally_specific_ones` |
| M46 | `_negotiate.py` | missing Accept accepts nothing | `test_accept.py::test_the_earliest_range_wins_between_equally_specific_ones` |
| M47 | `_negotiate.py` | wildcard offers allowed | `test_accept.py::test_offers_must_be_concrete[text/*]` |
| M48 | `_normalize.py` | charset value case kept | `_normalize.py::mediaparse._normalize.matches` |
| M49 | `_errors.py` | messages not cut | `test_hostile.py::test_parsing_time_grows_linearly[accept list]` |
| M50 | `_parse.py` | strict flag ignored | `_errors.py::mediaparse._errors.MediaTypeError` |
