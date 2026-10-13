"""Character classes shared by the parsers, the builder and the Accept reader."""

from __future__ import annotations

# tchar from RFC 9110 section 5.6.2; WHATWG calls these HTTP token code points.
TOKEN_CHARS = frozenset(
    "!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
# HTTP whitespace in the WHATWG Fetch standard: tab, LF, CR and space.
HTTP_WHITESPACE = "\t\n\r "
# OWS in RFC 9110 section 5.6.3: space and horizontal tab only.
OWS = " \t"

_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def ascii_lower(text: str) -> str:
    """Lower-case A to Z only; ``str.lower`` would also fold non-ASCII letters into ASCII."""
    return text.translate(_LOWER)


def is_token(value: str) -> bool:
    """Return whether the value is a non-empty RFC 9110 token."""
    return bool(value) and all(char in TOKEN_CHARS for char in value)


def is_quotable(char: str) -> bool:
    """Return whether a quoted string can carry the character (tab, 0x20-0x7E, 0x80-0xFF).

    This is the WHATWG "HTTP quoted-string token code point" set, the same characters that
    RFC 9110 ``qdtext`` and ``quoted-pair`` reach together.
    """
    return char == "\t" or " " <= char <= "~" or "\x80" <= char <= "\xff"


def quote(value: str) -> str:
    """Write a parameter value as a token when it is one, as a quoted string otherwise.

    Only the double quote and the backslash are escaped, as RFC 9110 section 5.6.4 asks.
    """
    if is_token(value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
