"""Parse and build HTTP media type and Content-Type headers with correct parameter quoting."""

from __future__ import annotations

from ._build import build
from ._errors import MediaTypeError
from ._normalize import matches, normalize
from ._parse import parse

__version__ = "0.1.0"

__all__ = [
    "MediaTypeError",
    "build",
    "matches",
    "normalize",
    "parse",
]
