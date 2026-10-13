"""Extended parameter values: ``charset'language'percent-encoded`` (RFC 8187, RFC 2231)."""

from __future__ import annotations

from ._errors import MediaTypeError

# attr-char from RFC 8187 section 3.2.1: a token character other than "*", "'" and "%".
ATTR_CHARS = frozenset("!#$&+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_HEX = "0123456789abcdefABCDEF"


def encode_extended(value: str) -> str:
    """Return ``UTF-8''`` followed by the value with every non attr-char byte percent-encoded."""
    try:
        data = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise MediaTypeError(f"value is not encodable as UTF-8: {value!r}") from error
    encoded = "".join(chr(byte) if chr(byte) in ATTR_CHARS else f"%{byte:02X}" for byte in data)
    return f"UTF-8''{encoded}"


def percent_decode(text: str) -> bytes:
    """Decode ``%XX`` escapes; other characters must be ASCII and are kept as they are."""
    out = bytearray()
    index, length = 0, len(text)
    while index < length:
        char = text[index]
        if char == "%":
            pair = text[index + 1 : index + 3]
            if len(pair) != 2 or pair[0] not in _HEX or pair[1] not in _HEX:
                raise MediaTypeError(f"invalid percent escape in {text!r}", position=index)
            out.append(int(pair, 16))
            index += 3
            continue
        if not char.isascii():
            raise MediaTypeError(f"non-ASCII character in encoded value {text!r}", position=index)
        out.append(ord(char))
        index += 1
    return bytes(out)
