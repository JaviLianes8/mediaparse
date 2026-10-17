"""Build a Content-Type style header from a media type and parameters."""

from __future__ import annotations

from collections.abc import Mapping

from ._errors import MediaTypeError, show
from ._extended import encode_extended
from ._tokens import OWS, ascii_lower, is_quotable, is_token, quote


def build(mimetype: str, params: Mapping[str, str] | None = None, *, extended: bool = False) -> str:
    """Render ``mimetype`` and ``params`` as a header value such as ``text/html; charset=utf-8``.

    The media type and parameter names are lower-cased. Each value is written as a bare
    token when it can be and as a quoted string otherwise. A value that no header can carry
    raises :class:`MediaTypeError`: control characters (other than tab) would split or
    corrupt the header, and characters outside ASCII have no agreed byte form. With
    ``extended=True`` such a value is written instead as ``name*=UTF-8''...``, the
    percent-encoded form of RFC 8187 and RFC 2231, and names may not hold ``*``. Two
    parameters that would be written under the same name raise :class:`MediaTypeError`.
    Spaces and tabs around the media type and the names are dropped. A part of the wrong
    type raises :class:`TypeError`.

    >>> from mediaparse import build
    >>> build("Text/Plain", {"charset": "utf-8", "title": "a; b"})
    'text/plain; charset=utf-8; title="a; b"'
    >>> build("text/plain", {"title": "caf\\xe9"}, extended=True)
    "text/plain; title*=UTF-8''caf%C3%A9"
    """
    parts = [essence(mimetype)]
    if params is not None and not isinstance(params, Mapping):
        raise TypeError(f"params must be a mapping, got {type(params).__name__}")
    seen: set[str] = set()
    for name, value in (params or {}).items():
        key = _name(name)
        if not isinstance(value, str):
            raise TypeError(f"parameter {show(key)} must be a str, got {type(value).__name__}")
        if extended and "*" in key:
            raise MediaTypeError(f"parameter {show(key)} holds '*', which extended=True reserves")
        if key in seen:
            raise MediaTypeError(f"parameter {show(key)} is given more than once")
        seen.add(key)
        if value.isascii() and all(map(is_quotable, value)):
            field = f"{key}={quote(value)}"
        elif extended:
            field = f"{key}*={encode_extended(value)}"
        else:
            raise MediaTypeError(
                f"parameter {show(key)} holds a control or non-ASCII character; "
                "pass extended=True to percent-encode it"
            )
        parts.append(field)
    return "; ".join(parts)


def essence(mimetype: str) -> str:
    """Return the lower-cased ``type/subtype``, or raise if it is not two tokens."""
    if not isinstance(mimetype, str):
        raise TypeError(f"mimetype must be a str, got {type(mimetype).__name__}")
    cleaned = mimetype.strip(OWS)
    main, slash, subtype = cleaned.partition("/")
    if not slash:
        raise MediaTypeError(f"media type has no subtype: {show(mimetype)}")
    if not is_token(main) or not is_token(subtype):
        raise MediaTypeError(f"invalid media type: {show(mimetype)}")
    return ascii_lower(cleaned)


def _name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError(f"parameter names must be str, got {type(name).__name__}")
    key = ascii_lower(name.strip(OWS))
    if not is_token(key):
        raise MediaTypeError(f"invalid parameter name: {show(name)}")
    return key
