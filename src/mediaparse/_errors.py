"""Error type raised when a media type cannot be parsed or built."""

from __future__ import annotations


class MediaTypeError(ValueError):
    """Raised when a media type is structurally invalid."""
