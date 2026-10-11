# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `parse` splits a Content-Type style header into a media type and its
  parameters, unescaping quoted values and tolerating malformed input.
- `build` renders a media type and parameters back, quoting only the values that
  a token may not hold.
- `normalize` and `matches` canonicalize and compare headers.
- Fills the gap left by `cgi.parse_header`, removed in Python 3.13.
