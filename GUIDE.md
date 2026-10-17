# mediaparse guide

The behaviour of every public name in detail. Each Python block below runs as a test:
a comment line after a `print` holds what it prints.

## Two ways to read a header

`parse`, `parse_media_type`, `normalize` and `parse_accept` read text in one of two modes.

**Default: like a browser.** The WHATWG MIME Sniffing "parse a MIME type" algorithm,
checked against the web-platform-tests corpus and against the `whatwg-mimetype`
reference implementation on 60,000 random hostile strings with no difference.

- Leading and trailing HTTP whitespace (tab, LF, CR, space) is removed.
- A parameter is skipped when its name is not a token, its value is empty (unquoted) or
  holds a character outside tab, U+0020 to U+007E and U+0080 to U+00FF, or when the
  name was already seen: the first of a repeated parameter wins.
- A quoted value ends at its closing quote and anything up to the next `;` is ignored.
- Only a missing or invalid `type/subtype` makes it fail.

**`strict=True`: exactly RFC 9110.** The `media-type` grammar of sections 5.6 and 8.3.1.

- No whitespace around `=`, values are tokens or quoted strings made of `qdtext` and
  `quoted-pair`, and nothing may follow a closing quote but `;` and spaces.
- A repeated parameter (names compared without case) is an error, as RFC 6838 says.
- Spaces and tabs before and after the whole value are allowed, because a field
  parser removes them before the value is read.
- `MediaTypeError.position` is the index of the first character that breaks the grammar.

```python
from mediaparse import MediaTypeError, parse

header = 'text/html;charset="utf-8"junk; Charset=latin1'
print(parse(header))
# ('text/html', {'charset': 'utf-8'})
try:
    parse(header, strict=True)
except MediaTypeError as error:
    print(error.position)
# 25
```

Comments in parentheses (`charset=us-ascii (Plain text)`, RFC 2045) are not part of
HTTP media types: the strict mode refuses them and the default mode keeps them in the
value, as browsers do.

## The `MediaType` value

A frozen dataclass with `type`, `subtype` and `params` (ordered `(name, value)` pairs).
Construction validates every part and lower-cases type, subtype and names (in ASCII
only, so the Kelvin sign never becomes a `k`). Values keep their case.

```python
from mediaparse import MediaType

media = MediaType("Application", "Vnd.API+JSON", (("Charset", "UTF-8"), ("x", "a b")))
print(media.essence, media.suffix, media.get("CHARSET"), media.parameters)
# application/vnd.api+json json UTF-8 {'charset': 'UTF-8', 'x': 'a b'}
print(media)
# application/vnd.api+json;charset=UTF-8;x="a b"
```

`str()` is the WHATWG serialization: `;` without spaces and a value quoted only when it
is empty or not a token. Equality compares parameters in order; `matches` does not.

## Building

`build(mimetype, params=None, *, extended=False)` writes `"; "` between parts and
quotes only what needs quoting. It never writes a character that could split or corrupt
the header: control characters other than tab, and anything outside ASCII, raise
`MediaTypeError`, unless `extended=True`, which writes the value as an RFC 8187 /
RFC 2231 extended value (`name*=UTF-8''...`). Spaces and tabs around the media type and
the names are dropped; two names that are equal without case raise.

```python
from mediaparse import build

print(build("text/plain", {"charset": "utf-8", "title": 'say "hi"'}))
# text/plain; charset=utf-8; title="say \"hi\""
print(build("text/plain", {"title": "\u20ac rates"}, extended=True))
# text/plain; title*=UTF-8''%E2%82%AC%20rates
```

## Comparing

`normalize` returns lower-cased type and names, parameters sorted by name, `charset`
values lower-cased (they are case insensitive, RFC 2046) and `"; "` between parts.
`matches(first, second)` compares two headers that way.

## Accept and negotiation

`parse_accept` splits on commas outside quoted strings and ignores empty elements. The
`q` parameter is the weight wherever it appears; it must match the RFC 9110 `qvalue`
grammar (`0` to `1`, at most three decimals). In the default mode an invalid element is
skipped, including one whose `q` is malformed (`q =0`, `q=`), so a broken weight never
counts as 1; with `strict=True` it raises.

`quality(accept, offer)` is the weight of the most specific range that covers the offer
(more specific: a concrete type, then a concrete subtype, then more parameters; the
earliest range wins a tie). Range parameters must all be present in the offer, `charset`
compared without case. `None` means the request had no Accept field (everything has
weight 1); an empty field accepts nothing. `negotiate(accept, offers)` returns the
offer with the highest non-zero weight, the first one on a tie, exactly as given.

```python
from mediaparse import negotiate, quality

accept = "text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, */*;q=0.5"
print(quality(accept, "text/plain;format=flowed"), quality(accept, "image/png"))
# 1.0 0.5
print(negotiate(accept, ["text/html", "text/plain"]), negotiate("image/*", ["text/html"]))
# text/plain None
```

`AcceptItem(media_range, q=1.0)` refuses a `*/subtype` range, a `q` parameter inside
the range, and a weight outside 0 to 1 or NaN.

## RFC 2231 parameters

`decode_extended(params)` joins `name*0`, `name*1`, ... sections (starting at 0, no gaps,
no leading zeros), decodes `charset'language'percent-encoded` values and drops the
language. Encoded and plain sections may mix and a character may span sections. When
both `name` and an extended form are present the extended form wins. The charset must
be one Python decodes as text; codecs that are not character sets (escape decoders,
`mbcs`, `oem`, `charmap`, `idna`, `punycode`) are refused.

## Errors

- `MediaTypeError`, a `ValueError`, for invalid text or values. `position` is set when
  the error comes from parsing text. Messages quote at most 80 characters of the input.
- `TypeError` for an argument of the wrong type.

## Compared with other parsers

Measured on generated RFC 9110 valid headers (see `tests/test_oracles.py`):

- `werkzeug.http.parse_options_header` (werkzeug 3.1.9) agrees on every header,
  RFC 2231 values included.
- Python's `email.message.Message` (3.13) agrees except where a quoted value ends in an
  escaped backslash (`x="a\\"`): it reads past the closing quote. It also keeps both
  values of a repeated parameter.
- `multipart.parse_options_header` (2.0.1) accepts only letters, digits, `-` and `_` in
  parameter names and drops the other parameters; within that set it agrees.

## Upgrading from 0.2.0

All results are the same, checked on over 50,000 calls against the PyPI release, except:
`MediaType.get` and `AcceptItem.matches` raise `TypeError` (not `AttributeError`) for an
argument of the wrong type; `AcceptItem` refuses `*/subtype` ranges and a `q` inside the
range; `decode_extended` refuses the `charmap` codec; some error messages are shorter.
