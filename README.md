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

The default mode is the WHATWG MIME Sniffing algorithm, what browsers do; `strict=True`
is the RFC 9110 grammar exactly. Building never writes a character that could split the
header. The [GUIDE](https://github.com/JaviLianes8/mediaparse/blob/main/GUIDE.md) has
every rule in detail, and the
[CHANGELOG](https://github.com/JaviLianes8/mediaparse/blob/main/CHANGELOG.md) what changed
in each release.

## Why

Python 3.13 removed `cgi.parse_header` along with the rest of the `cgi` module. The
`email.message.Message` machinery that replaces it is built for mail, has no header
builder, and reads a quoted value ending in an escaped backslash (`x="a\\"`) past its
closing quote. `multipart.parse_options_header` drops parameters whose names hold
characters other than letters, digits, `-` and `_`, and `werkzeug` brings a whole web
framework. `mediaparse` is a small, typed, zero-dependency library that parses the way
browsers do, validates the way the RFC says, builds headers that cannot be split, and
negotiates `Accept`. It is tested against the specifications themselves, the IANA
registry and those parsers.

## Development

`python scripts/fetch_upstream.py` downloads the specifications, registries and
web-platform-tests files listed in `tests/upstream/MANIFEST.json` (they are not part of
the repository; their tests skip without them). `pip install werkzeug multipart` and
`npm install --prefix tests/upstream whatwg-mimetype@5.0.0` add the reference parsers.
`scripts/check.ps1` runs format, lint, types and tests. Set `MEDIAPARSE_E2E=1` to also
build the wheel and test the installed package.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/mediaparse/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
