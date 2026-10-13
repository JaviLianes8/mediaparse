# mediaparse

Parse and build HTTP media types, `Content-Type` and `Accept` headers, exactly.

## Install

```
pip install mediaparse
```

## Usage

```python
from mediaparse import build, matches, normalize, parse, parse_media_type

# Read a Content-Type value the way a browser does.
print(parse("text/html; charset=utf-8"))
# ('text/html', {'charset': 'utf-8'})

# Quoted values keep separators; text after the closing quote is skipped.
print(parse('multipart/form-data; boundary="a; b=c"'))
# ('multipart/form-data', {'boundary': 'a; b=c'})

# A typed value with the essence, the +suffix and the browser serialization.
media = parse_media_type("Application/Vnd.API+JSON; Charset=UTF-8")
print(media.essence, media.suffix, media.get("charset"))
# application/vnd.api+json json UTF-8
print(media)
# application/vnd.api+json;charset=UTF-8

# Build a header, quoting only the values that need it.
print(build("application/json", {"title": "a; b"}))
# application/json; title="a; b"

# Canonical form for display or comparison.
print(normalize("TEXT/HTML; CharSet=UTF-8"))
# text/html; charset=utf-8
print(matches("Text/HTML; charset=UTF-8", "text/html;charset=utf-8"))
# True
```

### Lenient or strict

```python
from mediaparse import MediaTypeError, parse

# Default: the WHATWG algorithm. The first of a repeated parameter wins and a parameter
# with whitespace before "=" is skipped, exactly as browsers do.
print(parse("text/plain; charset=ascii; charset=utf-8; a =1"))
# ('text/plain', {'charset': 'ascii'})

# strict=True: the RFC 9110 grammar, with the position of the first bad character.
try:
    parse("text/plain; a =1", strict=True)
except MediaTypeError as error:
    print(error.position)
# 13
```

### Building safely

```python
from mediaparse import MediaTypeError, build

# No value can split the header: control characters are refused.
try:
    build("text/plain", {"name": "x\r\nSet-Cookie: a=b"})
except MediaTypeError:
    print("refused")
# refused

# Non-ASCII values travel as RFC 8187 / RFC 2231 extended values on request.
print(build("text/plain", {"title": "caf\xe9"}, extended=True))
# text/plain; title*=UTF-8''caf%C3%A9
```

### Accept and negotiation

```python
from mediaparse import negotiate, parse_accept, quality

accept = "text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, */*;q=0.5"

# The weight comes from the most specific range that covers the offer.
print(quality(accept, "text/plain;format=flowed"), quality(accept, "text/html"))
# 1.0 0.3

# Pick the best offer; ties go to the order you list them in.
print(negotiate(accept, ["image/png", "text/html"]))
# image/png

print([(str(item.media_range), item.q) for item in parse_accept("text/html, */*;q=0.1")])
# [('text/html', 1.0), ('*/*', 0.1)]
```

### RFC 2231 parameters

```python
from mediaparse import decode_extended, parse

header = "application/x-stuff; title*0*=utf-8''r%C3%A9sum; title*1=\"e.pdf\""
print(decode_extended(parse(header)[1]))
# {'title': 'résume.pdf'}
```

## API

| Name | What it does |
| --- | --- |
| `parse(header, *, strict=False)` | `(essence, params)` tuple. |
| `parse_media_type(text, *, strict=False)` | A `MediaType`; raises `MediaTypeError` when there is no valid `type/subtype`. |
| `MediaType` | Frozen value: `type`, `subtype`, `params` pairs, `essence`, `suffix`, `parameters`, `get()`, `str()`. |
| `build(mimetype, params=None, *, extended=False)` | Header value with `"; "` between parts and minimal quoting. |
| `normalize(header, *, strict=False)` | Lower-cased names, sorted parameters, lower-cased `charset`. |
| `matches(first, second)` | Whether two headers normalize to the same text. |
| `parse_accept(header, *, strict=False)` | List of `AcceptItem` in header order. |
| `AcceptItem` | `media_range` (a `MediaType`), `q` (0 to 1), `specificity()`, `matches(media)`. |
| `quality(accept, offer)` | Weight of an offer under an Accept header; `None` means no header. |
| `negotiate(accept, offers)` | Best acceptable offer, returned as given, or `None`. |
| `decode_extended(params)` | Joins RFC 2231 sections and decodes `charset'lang'` values. |
| `MediaTypeError` | `ValueError` subclass with `position` (or `None`). Wrong argument types raise `TypeError`. |

## Rules it follows

- **Default parsing** is the WHATWG MIME Sniffing "parse a MIME type" algorithm, checked
  against the web-platform-tests MIME type corpus. Whitespace (tab, LF, CR, space) is
  trimmed, a parameter whose name is not a token or whose value has a character above
  U+00FF or a control character is skipped, empty values are skipped and the first
  duplicate wins. `str(MediaType)` is the WHATWG serialization.
- **Strict parsing** is the RFC 9110 `media-type` grammar: no whitespace around `=`,
  values are tokens or quoted strings with `qdtext` and `quoted-pair` only, and a repeated
  parameter is an error (RFC 6838 section 4.3). Leading and trailing spaces or tabs are
  allowed because a field parser removes them.
- **Names** are lower-cased in ASCII only, so a character such as the Kelvin sign never
  turns into a token. Values keep their case; `normalize` and `quality` treat `charset`
  as case insensitive.
- **Building** never writes a control character or a non-ASCII character into the
  header: by default such a value raises, and with `extended=True` it is percent-encoded
  as `name*=UTF-8''...` (names may not end in `*` then). Two parameters that would be
  written under one name raise. The output is always one valid header field value.
- **Accept**: elements split on commas outside quoted strings, empty elements are
  ignored, `q` must match the `qvalue` grammar (up to three decimals, at most 1) and may
  appear anywhere among the parameters. In the default mode an invalid element is
  skipped, including one whose `q` is malformed (`q =0`, `q=`), so a broken weight never
  counts as 1. In strict mode only spaces and tabs may surround an element. A missing field (`None`) accepts everything; an empty one accepts nothing; a
  weight of 0 means not acceptable. On equally specific ranges the earliest one counts.
- **RFC 2231**: sections start at 0 without gaps or leading zeros, encoded and plain
  sections may mix, a character may span sections, and `name*` wins over `name`. The
  language tag is dropped. Names compare in ASCII lower case. The charset must be a
  charset name Python can decode as text; escape decoders, host code pages (`mbcs`,
  `oem`), `idna` and `punycode` are refused.

## Why

Python 3.13 removed `cgi.parse_header` along with the rest of the `cgi` module. The
documented replacement, the `email.message.Message` machinery, is parse-oriented with no
clean builder and mishandles repeated parameters, so projects keep copying a parser by
hand. `multipart.parse_options_header` is scoped to form data and parse-only, and
`ietfparse` is a broad multi-RFC toolkit. `mediaparse` is a small, typed,
zero-dependency library that parses the way browsers do, validates the way the RFC says,
builds headers that cannot be split, and negotiates `Accept`.

## Development

`python scripts/fetch_upstream.py` downloads the web-platform-tests MIME type files listed
in `tests/upstream/MANIFEST.json` (they are not part of the repository; their tests skip
without them). `scripts/check.ps1` runs format, lint, types and tests. Set
`MEDIAPARSE_E2E=1` to also build the wheel and test the installed package.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
