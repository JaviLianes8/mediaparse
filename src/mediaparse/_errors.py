"""Error type raised when a media type, parameter or Accept header is invalid."""

from __future__ import annotations


class MediaTypeError(ValueError):
    """Raised when a media type, a parameter or an Accept header is invalid.

    ``position`` is the index of the first offending character in the text being parsed
    (the whole header for :func:`parse_accept`, the parameter value for
    :func:`decode_extended`), and ``None`` for errors that do not come from reading text,
    such as a bad charset name or a value given to :func:`build`. Messages quote at most
    80 characters of the input.

    >>> from mediaparse import MediaTypeError, parse
    >>> try:
    ...     parse("text/plain; a =1", strict=True)
    ... except MediaTypeError as error:
    ...     print(error.position, isinstance(error, ValueError))
    13 True
    """

    def __init__(self, message: str, *, position: int | None = None) -> None:
        super().__init__(message)
        self.position = position


def show(value: object, limit: int = 80) -> str:
    """Return ``repr(value)`` cut to ``limit`` characters, so a huge input stays out of messages."""
    try:
        text = repr(value)
    except Exception:
        # An int past the digit limit, a structure too deep or a broken __repr__.
        return f"<{type(value).__name__}>"
    return text if len(text) <= limit else text[: limit - 3] + "..."
