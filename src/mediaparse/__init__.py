"""Parse and build HTTP media types, Content-Type and Accept headers, exactly."""

from __future__ import annotations

from ._accept import AcceptItem, negotiate, parse_accept, quality
from ._build import build
from ._errors import MediaTypeError
from ._mediatype import MediaType
from ._normalize import matches, normalize
from ._parse import parse, parse_media_type
from ._rfc2231 import decode_extended

__version__ = "0.2.0"

__all__ = [
    "AcceptItem",
    "MediaType",
    "MediaTypeError",
    "build",
    "decode_extended",
    "matches",
    "negotiate",
    "normalize",
    "parse",
    "parse_accept",
    "parse_media_type",
    "quality",
]
