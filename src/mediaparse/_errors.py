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


def show(value: object, limit: int = 80) -> str:
    """Return ``repr(value)`` cut to ``limit`` characters, so a huge input stays out of messages."""
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."
