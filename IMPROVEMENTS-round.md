# mediaparse improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: RFC 9110, RFC 6838, RFC 2045/2231, WHATWG MIME Sniffing, WPT
- [x] Two parsers: browser-compatible lenient (WHATWG) and exact strict (RFC 9110)
- [x] Typed `MediaType` value with essence, suffix, parameters and serialization
- [x] Safe builder: header injection guard, extended (RFC 2231) values for non-ASCII
- [x] Accept: parse media ranges and weights, quality lookup and negotiation
- [x] RFC 2231 decoding: continuations and charset-encoded values
- [x] Contracts: WPT corpus (local), cited RFC vectors, README examples run, typing
- [x] Docs and packaging: README, CHANGELOG, metadata, installed-wheel e2e test
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Mutation run: removing guarded logic makes the suite fail
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `parse`, `build`, `normalize`, `matches` and `MediaTypeError`. Compared with
the sources below:

- `build` quotes any value that is not a token, but never rejects one. A value holding CR,
  LF or NUL is written inside the quotes, so `build("text/plain", {"x": "a\r\nSet-Cookie:
  y"})` returns a header that splits into two fields: a header injection. Characters above
  U+00FF are written too, although no HTTP field can carry them.
- `parse` follows neither standard. It keeps the last of a repeated parameter (WHATWG keeps
  the first, RFC 6838 calls it an error), accepts whitespace around `=` (RFC 9110 forbids it,
  WHATWG drops the parameter), keeps values with spaces or other non-token characters
  unquoted, accepts characters above U+00FF in values, and reads `text/html;charset=
  "a"junk` as `a` only by accident of its loop. There is no strict mode to validate a header.
- The result is a bare tuple: no essence, no `+json` suffix, no serialization that matches
  what browsers produce.
- Nothing reads an `Accept` header, the field that media types exist for in HTTP, and
  nothing picks a representation from it.
- RFC 2231 parameters (`title*=us-ascii'en'...`, `URL*0=`, `URL*1=`) come back as raw
  pieces.

## Sources (fetched 2026-10-13)

- RFC 9110, HTTP Semantics, https://www.rfc-editor.org/rfc/rfc9110.txt: 5.5 field values,
  5.6.2 tokens, 5.6.4 quoted strings, 5.6.6 parameters (no whitespace around `=`), 8.3.1
  media type, 12.4.2 quality values, 12.5.1 Accept with the precedence example and Table 5.
- RFC 9110 errata, https://www.rfc-editor.org/errata/rfc9110: erratum 7138 (verified)
  corrects the last row of Table 5 from 0.7 to 0.3.
- RFC 6838, https://www.rfc-editor.org/rfc/rfc6838.txt: 4.2.8 structured syntax suffixes,
  4.3 a parameter given more than once is an error.
- RFC 2045, https://www.rfc-editor.org/rfc/rfc2045.txt, 5.1, and RFC 2231,
  https://www.rfc-editor.org/rfc/rfc2231.txt, 3, 4, 4.1 and 7: continuations, charset and
  language, the extended parameter grammar.
- WHATWG MIME Sniffing, https://mimesniff.spec.whatwg.org/ (commit snapshot
  39aa53511b13953d84fef8d4131d6f61d0ccbde6): 3 terminology, 4.4 parse a MIME type, 4.5
  serialize a MIME type. WHATWG Fetch, https://fetch.spec.whatwg.org/ (commit snapshot
  e9460d1b22ead1c6a72eeac37fb2ec0dc01aeb1d): HTTP whitespace and collect an HTTP quoted
  string.
- web-platform-tests at commit ca5384f99ee37dcabfe8078f5afaf419bd4784c0:
  `mimesniff/mime-types/resources/mime-types.json` and `generated-mime-types.json`
  (BSD-3-Clause). Not committed (owner policy: no third-party text or data in the
  repository): `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and
  licence, `scripts/fetch_upstream.py` fetches and checks them into the ignored
  `tests/upstream/` folder, and their tests skip while they are absent.

## Ranked improvements

1. **Safe builder.** Reject any value with a character outside the quoted-string range
   (controls other than tab, DEL, anything above U+00FF), so no input can split a header.
   Non-ASCII values raise unless `extended=True`, which writes them as RFC 2231 / RFC 8187
   `name*=utf-8''...`. Parameter names must be tokens, and a duplicate name after
   lower-casing raises.
2. **Two parsers with one result.** `strict=False` (default) is the WHATWG algorithm step
   by step: it never guesses, skips what browsers skip and keeps the first duplicate.
   `strict=True` is the RFC 9110 grammar exactly and raises `MediaTypeError` with the
   position of the first offending character; a repeated parameter raises (RFC 6838 4.3).
3. **Typed value.** `parse_media_type` returns a frozen `MediaType` with `type`,
   `subtype`, ordered `params`, `essence`, `suffix`, `get()` and `str()` that serializes
   exactly as the WHATWG algorithm (the form browsers expose). `parse` keeps its tuple.
4. **Accept and negotiation.** `parse_accept` reads media ranges and `q` per RFC 9110
   12.5.1 (commas inside quoted strings, `q` anywhere, three decimals at most), `quality`
   finds the weight from the most specific matching range, and `negotiate` picks the best
   offer, ties going to the server's order. Checked against the RFC precedence example and
   Table 5 with erratum 7138.
5. **RFC 2231 decoding.** `decode_extended` joins `name*0`, `name*1*` sections in order,
   decodes `charset'language'percent` values and prefers `name*` over `name`. Gaps,
   leading zeros, bad escapes and unknown charsets raise.
6. **Ground truth contracts.** Every WPT `mime-types` and `generated-mime-types` case
   parses and serializes to the expected output (or fails where it must); cited RFC
   examples are kept as short vectors with their URL; hand-written cases are labelled.
7. **Docs and packaging.** README examples executed by a test, API table checked against
   `__all__`, mypy over a usage snippet, classifiers and keywords, sdist without planning
   notes or fetched files, installed-wheel end-to-end test.

## Out of scope

- A command line: every operation is one call from Python and there is no shell workflow
  that needs it; `python -c` covers the rare debugging case.
- RFC 6838 registration rules (127-character names, the facet trees, the registry itself):
  they govern registering a type, not reading or writing a header.
- MIME sniffing from content bytes and the "minimize" step: they need the payload and a
  table of supported types, which is the job of a sniffing library.
- RFC 2047 encoded words: they are not valid inside parameters.
