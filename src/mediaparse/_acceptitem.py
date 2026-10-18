"""One media range of an Accept header with its weight."""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import MediaTypeError, show
from ._mediatype import MediaType
from ._tokens import ascii_lower


@dataclass(frozen=True)
class AcceptItem:
    """One media range of an Accept header and its weight ``q`` (0 to 1, default 1).

    The range is a :class:`MediaType` whose type or subtype may be ``*``; ``*/subtype``
    is not a range and raises :class:`MediaTypeError`, and so does a ``q`` parameter
    inside the range, since the weight is ``q``. A ``q`` outside 0 to 1 (or NaN) raises
    :class:`MediaTypeError`, one that is not a number :class:`TypeError`. Integers are
    stored as floats.

    >>> from mediaparse import AcceptItem, MediaType
    >>> item = AcceptItem(MediaType("text", "*"), 0.5)
    >>> item.q, item.specificity(), item.matches(MediaType("text", "html"))
    (0.5, (True, False, 0), True)
    """

    media_range: MediaType
    q: float = 1.0

    def __post_init__(self) -> None:
        rng = self.media_range
        if not isinstance(rng, MediaType):
            raise TypeError(f"media_range must be a MediaType, got {type(rng).__name__}")
        if rng.type == "*" and rng.subtype != "*":
            raise MediaTypeError(f"invalid media range: {show(rng.essence)}")
        if rng.get("q") is not None:
            raise MediaTypeError("the weight goes in q, not in the media range parameters")
        if isinstance(self.q, bool) or not isinstance(self.q, (int, float)):
            raise TypeError(f"q must be a number, got {type(self.q).__name__}")
        try:
            q = float(self.q) + 0.0  # a plain float, and -0.0 becomes 0.0
        except OverflowError:
            q = float("inf")
        if not 0 <= q <= 1:
            raise MediaTypeError(f"q must be between 0 and 1, got {show(self.q)}")
        object.__setattr__(self, "q", q)

    def specificity(self) -> tuple[bool, bool, int]:
        """Precedence of the range: concrete type, concrete subtype, parameter count.

        A larger tuple is a more specific range (RFC 9110 section 12.5.1).

        >>> from mediaparse import parse_accept
        >>> [item.specificity() for item in parse_accept("*/*, text/*, text/plain;a=1")]
        [(False, False, 0), (True, False, 0), (True, True, 1)]
        """
        rng = self.media_range
        return (rng.type != "*", rng.subtype != "*", len(rng.params))

    def matches(self, media: MediaType) -> bool:
        """Return whether the range covers ``media``, parameters included.

        Every parameter of the range must be present in ``media`` with the same value
        (``charset`` compared without case). A ``media`` that is not a :class:`MediaType`
        raises :class:`TypeError`.

        >>> from mediaparse import parse_accept, parse_media_type
        >>> item = parse_accept("text/plain;format=flowed")[0]
        >>> item.matches(parse_media_type("text/plain; format=flowed; charset=utf-8"))
        True
        >>> item.matches(parse_media_type("text/plain"))
        False
        """
        if not isinstance(media, MediaType):
            raise TypeError(f"media must be a MediaType, got {type(media).__name__}")
        rng = self.media_range
        if rng.type not in ("*", media.type) or rng.subtype not in ("*", media.subtype):
            return False
        given = dict(media.params)
        return all(_same(name, value, given.get(name)) for name, value in rng.params)


def _same(name: str, wanted: str, actual: str | None) -> bool:
    if actual is None:
        return False
    if name == "charset":
        return ascii_lower(wanted) == ascii_lower(actual)
    return wanted == actual
