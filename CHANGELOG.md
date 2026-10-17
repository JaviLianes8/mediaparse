# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-17

The public API is now stable: the twelve names in `mediaparse.__all__`, their
signatures, defaults and error types follow Semantic Versioning from this release on.

### Stable

- Parsing: `parse` and `parse_media_type` read like browsers by default (the WHATWG
  MIME Sniffing algorithm) and exactly by the RFC 9110 grammar with `strict=True`;
  `MediaType` is the frozen value they return.
- Building: `build` never writes a value that could split or corrupt the header, and
  writes non-ASCII values as RFC 8187 / RFC 2231 extended values on request.
- Comparing: `normalize` and `matches`.
- Accept: `parse_accept`, `AcceptItem`, `quality` and `negotiate`.
- RFC 2231: `decode_extended`.
- Errors: `MediaTypeError` (a `ValueError`) for invalid text, with `position` when it
  comes from parsing; `TypeError` for arguments of the wrong type.

### Changed

- `MediaType.get` raises `TypeError` for a name that is not a `str` (it raised
  `AttributeError`).
- `AcceptItem.matches` raises `TypeError` for an argument that is not a `MediaType` (it
  raised `AttributeError`).
- `AcceptItem` refuses a `*/subtype` range and a `q` parameter inside the range with
  `MediaTypeError`; both were accepted when built by hand, though no parser produced them.
- `decode_extended` refuses the `charmap` codec as a charset, like the other Python
  codecs that are not character sets.
- `parse_accept` in its default mode skips an element with any `q` not written as
  `q=qvalue`: a quoted `q="0.5"` (which the grammar does not allow; 0.2.0 read it as a
  weight) and a malformed `q` after a valid one (`q=0.5;q =1`; 0.2.0 kept 0.5). The
  strict mode already refused both.
- `MediaTypeError.position`: strict `parse_accept` errors on a weight or a `*/subtype`
  range now carry the position in the header, and the message counts positions the same
  way; the default parser points at the offending character instead of the start of the
  type or subtype; `decode_extended` counts from the start of the parameter value.
- `MediaType.get` has overloads, so `get(name, "default")` is typed `str`.

### Fixed

- Error messages stay short for any input: a huge value that could not be encoded by
  `build(..., extended=True)` and a huge `*/subtype` element in a strict Accept header
  were quoted whole, and an `AcceptItem` weight too large to print raised `ValueError`
  instead of `MediaTypeError`.

### Added

- Runnable examples in every public docstring, run as doctests, and a GUIDE.
- Tests against the specifications fetched at test time (RFC 9110, RFC 6838, RFC 2045,
  RFC 2231, RFC 8187, the WHATWG MIME Sniffing and Fetch standards, the IANA media type
  and structured suffix registries) and against independent parsers (Python's `email`
  package, `werkzeug`, `multipart` and the `whatwg-mimetype` reference implementation),
  plus seeded fuzz and hostile input tests.

## [0.2.0] - 2026-10-16

### Added

- `parse_media_type` and the frozen `MediaType` value: `essence`, the RFC 6838 `suffix`,
  ordered `params`, `parameters`, `get()`, and `str()` with the WHATWG serialization.
- `strict=True` on `parse`, `parse_media_type` and `normalize`: the RFC 9110 grammar
  exactly, a repeated parameter is an error, and `MediaTypeError.position` points at the
  first bad character.
- `parse_accept`, `AcceptItem`, `quality` and `negotiate` for the Accept header (RFC 9110
  sections 12.4.2 and 12.5.1), checked against the RFC examples.
- `build(..., extended=True)` writes non-ASCII values as RFC 8187 / RFC 2231 extended
  values, and `decode_extended` joins RFC 2231 continuations and decodes them.
- Tests against the web-platform-tests MIME type corpus, fetched locally by
  `scripts/fetch_upstream.py`, plus executed README examples, a typing check and an
  installed-wheel test.

### Changed

- The default parser is the WHATWG MIME Sniffing algorithm: the first of a repeated
  parameter wins (it was the last), a parameter with whitespace around `=` or a value
  outside the quoted-string range is skipped, and HTTP whitespace (including CR and LF)
  is trimmed.
- Names are lower-cased in ASCII only.

### Fixed

- `build` no longer writes control characters such as CR and LF into a quoted value,
  which let a parameter value split the header, nor characters a header cannot carry.
  A duplicate name after lower-casing is refused instead of written twice.
- Error messages show at most 80 characters of the input.

## [0.1.0]

- First version (not published to PyPI).
- `parse` splits a Content-Type style header into a media type and its
  parameters, unescaping quoted values and tolerating malformed input.
- `build` renders a media type and parameters back, quoting only the values that
  a token may not hold.
- `normalize` and `matches` canonicalize and compare headers.
- Fills the gap left by `cgi.parse_header`, removed in Python 3.13.
