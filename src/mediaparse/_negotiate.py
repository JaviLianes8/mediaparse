"""Pick a representation from an Accept header (RFC 9110 section 12.5.1)."""

from __future__ import annotations

from collections.abc import Iterable

from ._accept import parse_accept
from ._acceptitem import AcceptItem
from ._errors import MediaTypeError, show
from ._mediatype import MediaType
from ._parse import parse_media_type


def quality(accept: str | None, offer: str) -> float:
    """Return the weight ``accept`` gives ``offer``: the ``q`` of the most specific range
    that covers it (the earliest such range on a tie), 0 if none does. ``None`` means the
    request had no Accept field, which accepts everything with weight 1.

    The header is read like :func:`parse_accept` in its default mode. The offer is a
    concrete media type; a wildcard or invalid offer raises :class:`MediaTypeError`.

    >>> from mediaparse import quality
    >>> accept = "text/*;q=0.3, text/plain;q=0.7, */*;q=0.5"
    >>> quality(accept, "text/plain"), quality(accept, "text/html"), quality(accept, "a/b")
    (0.7, 0.3, 0.5)
    >>> quality(None, "image/png"), quality("", "image/png")
    (1.0, 0.0)
    """
    media = _offer(offer)
    if accept is None:
        return 1.0
    return _quality(parse_accept(accept), media)


def negotiate(accept: str | None, offers: Iterable[str]) -> str | None:
    """Return the offer with the highest non-zero weight, or ``None`` if none is acceptable.

    Offers are concrete media types in the server's order of preference, which breaks ties.
    The chosen offer is returned exactly as given. A single ``str`` instead of an iterable
    raises :class:`TypeError`; an invalid offer raises :class:`MediaTypeError`.

    >>> from mediaparse import negotiate
    >>> negotiate("text/html;q=0.8, application/json", ["text/html", "application/json"])
    'application/json'
    >>> negotiate("image/*", ["text/html"]) is None
    True
    """
    if isinstance(offers, str):
        raise TypeError("offers must be an iterable of media types, not a single str")
    items = None if accept is None else parse_accept(accept)
    best, best_q = None, 0.0
    for offer in offers:
        media = _offer(offer)
        weight = 1.0 if items is None else _quality(items, media)
        if weight > best_q:
            best, best_q = offer, weight
    return best


def _quality(items: list[AcceptItem], media: MediaType) -> float:
    covering = [item for item in items if item.matches(media)]
    if not covering:
        return 0.0
    top = max(item.specificity() for item in covering)
    return next(item.q for item in covering if item.specificity() == top)


def _offer(offer: str) -> MediaType:
    media = parse_media_type(offer)
    if "*" in (media.type, media.subtype):
        raise MediaTypeError(f"an offer must be a concrete media type, not {show(offer)}")
    return media
