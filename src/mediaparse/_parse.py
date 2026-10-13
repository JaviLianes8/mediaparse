"""Parse a Content-Type style header into a media type and its parameters."""

from __future__ import annotations

from ._lenient import parse_lenient
from ._mediatype import MediaType
from ._strict import parse_strict


def parse_media_type(text: str, *, strict: bool = False) -> MediaType:
    """Parse a media type header value into a :class:`MediaType`.

    By default the WHATWG MIME Sniffing algorithm is used, so the result is what a browser
    would read: whitespace is trimmed, parameters a browser would ignore are skipped and
    the first of a repeated parameter wins. With ``strict=True`` the text must match the
    RFC 9110 grammar exactly and a repeated parameter is an error. Either way a value with
    no valid ``type/subtype`` raises :class:`MediaTypeError`.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    return parse_strict(text) if strict else parse_lenient(text)


def parse(header: str, *, strict: bool = False) -> tuple[str, dict[str, str]]:
    """Split a media type header into ``(essence, params)``, see :func:`parse_media_type`."""
    media = parse_media_type(header, strict=strict)
    return media.essence, media.parameters
