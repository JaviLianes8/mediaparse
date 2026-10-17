# mediaparse 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to mediaparse. PyPI has 0.2.0, which is
byte for byte the `main` branch at c692de6 (the wheel's modules compared with the tree), so
every change listed here is a change against the PyPI release.

Progress:
- [x] Branch `release/1.0.0` created from `main` (c692de6, same code as PyPI 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: specifications and registries fetched live, reference parsers (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e and upgrade from PyPI 0.2.0, every Python (items 8, 10, 13, 14)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [ ] Gates (item 15), final run
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

Fresh clone of `release/1.0.0` at c692de6 on the laptop, CPython 3.14: `ruff format --check .`,
`ruff check .` and `mypy --strict src tests` exit 0; `pytest` 282 passed, 1 skipped (the
installed-wheel test, which needs `MEDIAPARSE_E2E=1`); no doctests existed.

Defects found in 0.2.0 by reading and then reproducing:

- `MediaType.get(1)` and `AcceptItem.matches("text/html")` raised `AttributeError`.
- `AcceptItem(MediaType("*", "plain"))` was accepted, although no Accept header can
  hold that range, and so was a `q` parameter inside a hand-built range.
- `AcceptItem(range, 10**5000)` raised `ValueError` from `repr` instead of
  `MediaTypeError`.
- Two error messages quoted the whole input: `build(..., extended=True)` with a
  600 KB message for a 100,000 lone surrogate value, and a strict Accept header with a
  100 KB `*/subtype` element.
- `decode_extended` accepted the `charmap` codec name as a charset.
- No public docstring had a runnable example; the README linked LICENSE relatively,
  which breaks on PyPI; there was no GUIDE.

## API review (item 1)

Kept: the twelve public names of 0.2.0 with their signatures and defaults, now pinned by
`tests/test_contract_api.py`. Changed, all in the CHANGELOG and the GUIDE: `TypeError`
from `MediaType.get` and `AcceptItem.matches` for arguments of the wrong type;
`AcceptItem` refuses `*/subtype` and a `q` inside the range; `charmap` refused as a
charset; bounded messages. Internal: the Accept module split in three (reading, the item,
negotiation) to keep every file under 200 lines with the new examples; the stray
`annotations` name is gone from the package top.

## Ground truth (item 7)

Fetched on 2026-10-17 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence and
the tests check the hash before reading. Nothing fetched is committed or shipped.

- RFC 9110 (`tests/test_spec_rfc9110.py`): the `tchar`, `qdtext`, `quoted-pair` and
  `obs-text` rules are parsed out of the ABNF in the text and compared with the strict
  parser code point by code point (U+0000 to U+02FF, a surrogate, an astral character);
  the `qvalue` rule is read from the text and every weight string of up to six
  characters over `01.25` is checked; the four equivalent forms of section 8.3.1, the
  Accept precedence example, the audio and text examples and Table 5 are cut from the
  text. Table 5 is read with verified erratum 7138 (fetched): only its last row changes.
- RFC 2231 with verified erratum 590, RFC 8187, RFC 2045, RFC 6838
  (`tests/test_spec_mime.py`): every example header is cut from the fetched text; the
  decoded values are checked against Python's own `urllib.parse.unquote`; the RFC 6838
  `restricted-name-chars` rule and its "error for a parameter specified more than once"
  sentence are read from the text.
- WHATWG MIME Sniffing and Fetch (commit snapshots; `tests/test_spec_whatwg.py`): the
  HTTP token, HTTP quoted-string token and HTTP whitespace code points are read from the
  prose and compared with the default parser; each step of the algorithm is located in
  the text and exercised, and its worked example is cut from the page.
- web-platform-tests MIME type corpus (two files, commit ca5384f): every case matches.
- IANA Media Types registry (2,366 templates) and Structured Syntax Suffixes registry
  (`tests/test_iana.py`): every registered name parses in both modes, round trips,
  lower-cases, builds and negotiates; the suffix is checked on every name.
- Reference parsers run live (`tests/test_oracles.py`): the whatwg-mimetype 5.0.0
  reference implementation on 60,000 seeded hostile strings and on the WPT inputs, no
  difference; werkzeug 3.1.9 `parse_options_header` on 3,000 valid headers and 2,000
  RFC 2231 values, no difference; Python's `email` package agrees except where a quoted
  value ends in an escaped backslash (its known misreading, asserted precisely);
  multipart 2.0.1 agrees within the parameter names it accepts.
- PyPI 0.2.0 as an oracle (`tests/test_upgrade.py`, `MEDIAPARSE_V02`): 57,000 calls give
  the same results and the same error families; the documented changes are checked
  case by case.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`: three seeds of 5,000 to 10,000 hostile strings per property
(parsing never raises anything but `MediaTypeError` with a message under 300 characters
and a position inside the input; serialization is stable through both parsers; strict
mode accepts exactly a regular expression written from the RFC 9110 grammar, with
unique names; `build` round trips through both parsers; extended values round trip
through `decode_extended`; Accept weights, `quality` and `negotiate` agree with each
other). `tests/test_hostile.py`: nine input shapes timed at 50,000 and 200,000
characters through both parsers and both Accept modes (linear), 100,000 RFC 2231
sections, 100,000 parameters and ranges, 1 MB values in every error path (messages
under 300 characters), an int past the digit limit as a weight, lone surrogates.

## Author mutation round (item 18)

50 mutants over every module, each applied alone to a fresh clone of the pushed branch on
another machine, the full suite (fetched sources, werkzeug, multipart and the 0.2.0
oracle present) run with `-x` and a 300 s per-test limit. All 50 killed at once.

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
