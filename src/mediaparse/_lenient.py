"""The WHATWG MIME Sniffing "parse a MIME type" algorithm, step by step.

https://mimesniff.spec.whatwg.org/#parse-a-mime-type, with "collect an HTTP quoted
string" from https://fetch.spec.whatwg.org/. Where the algorithm returns failure this
module raises :class:`MediaTypeError`; everything else it tolerates the way browsers do.
"""

from __future__ import annotations

from ._errors import MediaTypeError, show
from ._mediatype import MediaType
from ._tokens import HTTP_WHITESPACE, TOKEN_CHARS, ascii_lower, is_quotable, is_token


def parse_lenient(text: str) -> MediaType:
    """Parse ``text`` exactly as a browser parses a MIME type."""
    data = text.strip(HTTP_WHITESPACE)
    offset = len(text) - len(text.lstrip(HTTP_WHITESPACE))
    slash = data.find("/")
    main = data if slash < 0 else data[:slash]
    if not is_token(main):
        raise MediaTypeError(f"invalid media type: {show(text)}", position=offset + _bad(main))
    if slash < 0:
        raise MediaTypeError(
            f"media type has no subtype: {show(text)}", position=offset + len(data)
        )
    end = _find(data, ";", slash + 1)
    subtype = data[slash + 1 : end].rstrip(HTTP_WHITESPACE)
    if not is_token(subtype):
        where = offset + slash + 1 + _bad(subtype)
        raise MediaTypeError(f"invalid media subtype: {show(text)}", position=where)
    params: dict[str, str] = {}
    position, length = end, len(data)
    while position < length:
        position += 1  # skip the ";"
        while position < length and data[position] in HTTP_WHITESPACE:
            position += 1
        start = position
        while position < length and data[position] not in ";=":
            position += 1
        name = ascii_lower(data[start:position])
        if position < length:
            if data[position] == ";":
                continue
            position += 1  # skip the "="
        if position >= length:
            break
        if data[position] == '"':
            value, position = collect_quoted(data, position)
            position = _find(data, ";", position)
        else:
            stop = _find(data, ";", position)
            value = data[position:stop].rstrip(HTTP_WHITESPACE)
            position = stop
            if not value:
                continue
        if is_token(name) and all(map(is_quotable, value)) and name not in params:
            params[name] = value
    return MediaType(main, subtype, tuple(params.items()))


def collect_quoted(data: str, position: int) -> tuple[str, int]:
    """Collect an HTTP quoted string with extract-value set: ``(value, next position)``."""
    chars: list[str] = []
    position += 1  # skip the opening quote
    length = len(data)
    while position < length:
        char = data[position]
        position += 1
        if char == '"':
            break
        if char == "\\":
            if position >= length:
                chars.append("\\")
                break
            char = data[position]
            position += 1
        chars.append(char)
    return "".join(chars), position


def _bad(part: str) -> int:
    """Index of the first character of ``part`` that is not a token character."""
    return next((i for i, char in enumerate(part) if char not in TOKEN_CHARS), len(part))


def _find(data: str, char: str, start: int) -> int:
    index = data.find(char, start)
    return len(data) if index < 0 else index
