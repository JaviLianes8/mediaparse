"""Build a Content-Type style header from a media type and parameters."""

from __future__ import annotations

from collections.abc import Mapping

from ._errors import MediaTypeError
from ._extended import encode_extended
from ._tokens import OWS, ascii_lower, is_quotable, is_token, quote


def build(mimetype: str, params: Mapping[str, str] | None = None, *, extended: bool = False) -> str:
    """Render ``mimetype`` and ``params`` as a header value such as ``text/html; charset=utf-8``.

    The media type and parameter names are lower-cased. Each value is written as a bare
    token when it can be and as a quoted string otherwise. A value that no header can carry
    raises :class:`MediaTypeError`: control characters (other than tab) would split or
    corrupt the header, and characters outside ASCII have no agreed byte form. With
    ``extended=True`` such a value is written instead as ``name*=UTF-8''...``, the
    percent-encoded form of RFC 8187 and RFC 2231.
    """
    parts = [essence(mimetype)]
    seen: set[str] = set()
    for name, value in (params or {}).items():
        key = _name(name)
        if key in seen:
            raise MediaTypeError(f"parameter {key!r} is given more than once")
        seen.add(key)
        if not isinstance(value, str):
            raise TypeError(f"parameter {key!r} must be a str, got {type(value).__name__}")
        if value.isascii() and all(map(is_quotable, value)):
            parts.append(f"{key}={quote(value)}")
        elif extended:
            if key.endswith("*"):
                raise MediaTypeError(f"parameter {key!r} already names an extended value")
            parts.append(f"{key}*={encode_extended(value)}")
        else:
            raise MediaTypeError(
                f"parameter {key!r} holds a control or non-ASCII character; "
                "pass extended=True to percent-encode it"
            )
    return "; ".join(parts)


def essence(mimetype: str) -> str:
    """Return the lower-cased ``type/subtype``, or raise if it is not two tokens."""
    if not isinstance(mimetype, str):
        raise TypeError(f"mimetype must be a str, got {type(mimetype).__name__}")
    cleaned = mimetype.strip(OWS)
    main, slash, subtype = cleaned.partition("/")
    if not slash:
        raise MediaTypeError(f"media type has no subtype: {mimetype!r}")
    if not is_token(main) or not is_token(subtype):
        raise MediaTypeError(f"invalid media type: {mimetype!r}")
    return ascii_lower(cleaned)


def _name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError(f"parameter names must be str, got {type(name).__name__}")
    key = ascii_lower(name.strip(OWS))
    if not is_token(key):
        raise MediaTypeError(f"invalid parameter name: {name!r}")
    return key
