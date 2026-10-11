# mediaparse

Parse and build HTTP media type and Content-Type headers with correct parameter quoting.

## Install

```
pip install mediaparse
```

## Usage

```python
from mediaparse import parse, build, normalize, matches

# Parse a Content-Type value into its media type and parameters.
parse("text/html; charset=utf-8")
# ('text/html', {'charset': 'utf-8'})

# Quoted values keep their content, even with separators inside.
parse('multipart/form-data; boundary="a; b=c"')
# ('multipart/form-data', {'boundary': 'a; b=c'})

# Build a header back, quoting only the values that need it.
build("text/html", {"charset": "utf-8"})
# 'text/html; charset=utf-8'
build("application/json", {"title": "a; b"})
# 'application/json; title="a; b"'

# Canonicalize for display or comparison.
normalize("TEXT/HTML; CharSet=UTF-8")
# 'text/html; charset=utf-8'
matches("Text/HTML; charset=UTF-8", "text/html; charset=utf-8")
# True
```

The media type and parameter names are lower-cased, parameter values keep their
case (a filename or boundary is significant), and `charset` is treated as case
insensitive by `normalize`. Malformed parameters are tolerated; a value without
a `type/subtype` raises `MediaTypeError`.

## Why

Python 3.13 removed `cgi.parse_header` along with the rest of the `cgi` module.
The documented replacement, the `email.message.Message` machinery, is
parse-oriented with no clean builder, is several times slower per request, and
mishandles repeated parameters, so projects keep copying a parser by hand.
`multipart.parse_options_header` is scoped to form-data and parse-only, and
`ietfparse` is a broad multi-RFC toolkit. `mediaparse` is a small, typed,
zero-dependency library that both parses and builds one header, with correct
token-versus-quoted-string handling in each direction.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
