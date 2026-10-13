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

    def __reduce__(self) -> tuple[object, ...]:
        # Keep ``position`` across pickling, which only replays ``args`` by default.
        return (_rebuild, (str(self), self.position))


def _rebuild(message: str, position: int | None) -> MediaTypeError:
    return MediaTypeError(message, position=position)
