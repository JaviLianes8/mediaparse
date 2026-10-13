# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

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

## [0.1.0]

- First release.
- `parse` splits a Content-Type style header into a media type and its
  parameters, unescaping quoted values and tolerating malformed input.
- `build` renders a media type and parameters back, quoting only the values that
  a token may not hold.
- `normalize` and `matches` canonicalize and compare headers.
- Fills the gap left by `cgi.parse_header`, removed in Python 3.13.
