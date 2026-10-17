"""Parse and build HTTP media types, Content-Type and Accept headers, exactly."""

from ._accept import parse_accept
from ._acceptitem import AcceptItem
from ._build import build
from ._errors import MediaTypeError
from ._mediatype import MediaType
from ._negotiate import negotiate, quality
from ._normalize import matches, normalize
from ._parse import parse, parse_media_type
from ._rfc2231 import decode_extended

__version__ = "1.0.0"

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
