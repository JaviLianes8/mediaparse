"""Token rules and media type normalization shared by the parser and builder."""

from __future__ import annotations

from ._errors import MediaTypeError

# tchar set from RFC 9110 section 5.6.2: the characters a token may contain.
TOKEN_CHARS = frozenset(
    "!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)


def is_token(value: str) -> bool:
    """Return whether the value is a non-empty RFC 9110 token."""
    return bool(value) and all(char in TOKEN_CHARS for char in value)


def normalize_mimetype(mimetype: str) -> str:
    """Return the lower-cased ``type/subtype``, or raise if it is malformed."""
    cleaned = mimetype.strip().lower()
    if "/" not in cleaned:
        raise MediaTypeError(f"media type has no subtype: {mimetype!r}")
    main_type, subtype = cleaned.split("/", 1)
    if not is_token(main_type) or not is_token(subtype):
        raise MediaTypeError(f"invalid media type: {mimetype!r}")
    return f"{main_type}/{subtype}"
