"""Error type raised when a media type, parameter or Accept header is invalid."""

from __future__ import annotations


class MediaTypeError(ValueError):
    """Raised when a media type, a parameter or an Accept header is invalid.

    ``position`` is the index in the input of the first offending character when the
    error comes from parsing text, and ``None`` otherwise.
    """

    def __init__(self, message: str, *, position: int | None = None) -> None:
        super().__init__(message)
        self.position = position
