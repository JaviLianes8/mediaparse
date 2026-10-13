"""Read an Accept header and pick a representation (RFC 9110 sections 12.4.2 and 12.5.1)."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from ._errors import MediaTypeError, show
from ._lenient import collect_quoted, parse_lenient
from ._mediatype import MediaType
from ._parse import parse_media_type
from ._strict import parse_strict
from ._tokens import HTTP_WHITESPACE, OWS, ascii_lower

# qvalue = ( "0" [ "." 0*3DIGIT ] ) / ( "1" [ "." 0*3("0") ] )
_QVALUE = re.compile(r"0(?:\.[0-9]{0,3})?|1(?:\.0{0,3})?")


@dataclass(frozen=True)
class AcceptItem:
    """One media range of an Accept header and its weight ``q`` (0 to 1, default 1)."""

    media_range: MediaType
    q: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.media_range, MediaType):
            raise TypeError(
                f"media_range must be a MediaType, got {type(self.media_range).__name__}"
            )
        if isinstance(self.q, bool) or not isinstance(self.q, (int, float)):
            raise TypeError(f"q must be a number, got {type(self.q).__name__}")
        if not 0 <= self.q <= 1:
            raise MediaTypeError(f"q must be between 0 and 1, got {show(self.q)}")
        object.__setattr__(self, "q", float(self.q))

    def specificity(self) -> tuple[bool, bool, int]:
        """Precedence of the range: concrete type, concrete subtype, parameter count."""
        rng = self.media_range
        return (rng.type != "*", rng.subtype != "*", len(rng.params))

    def matches(self, media: MediaType) -> bool:
        """Return whether the range covers ``media``, parameters included."""
        rng = self.media_range
        if rng.type not in ("*", media.type) or rng.subtype not in ("*", media.subtype):
            return False
        return all(_same(name, value, media.get(name)) for name, value in rng.params)


def parse_accept(header: str, *, strict: bool = False) -> list[AcceptItem]:
    """Read an Accept header into its media ranges, in header order.

    Elements are split on commas outside quoted strings and empty elements are ignored.
    The ``q`` parameter is the weight wherever it appears and is removed from the range.
    By default an element that is not a valid media range, or whose ``q`` breaks the
    ``qvalue`` grammar, is skipped; with ``strict=True`` it raises :class:`MediaTypeError`
    and each range must match the RFC 9110 grammar exactly.
    """
    if not isinstance(header, str):
        raise TypeError(f"expected str, got {type(header).__name__}")
    items: list[AcceptItem] = []
    for start, element in _elements(header):
        if not element.strip(OWS if strict else HTTP_WHITESPACE):
            continue
        try:
            items.append(_item(element, strict))
        except MediaTypeError as error:
            if strict:
                where = None if error.position is None else start + error.position
                raise MediaTypeError(str(error), position=where) from None
    return items


def quality(accept: str | None, offer: str) -> float:
    """Return the weight ``accept`` gives ``offer``: the ``q`` of the most specific range
    that covers it (the earliest such range on a tie), 0 if none does. ``None`` means the
    request had no Accept field, which accepts everything with weight 1.
    """
    media = _offer(offer)
    if accept is None:
        return 1.0
    return _quality(parse_accept(accept), media)


def negotiate(accept: str | None, offers: Iterable[str]) -> str | None:
    """Return the offer with the highest non-zero weight, or ``None`` if none is acceptable.

    Offers are concrete media types in the server's order of preference, which breaks ties.
    The chosen offer is returned exactly as given.
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


def _item(element: str, strict: bool) -> AcceptItem:
    quoted: set[str] = set()
    media = parse_strict(element, quoted) if strict else parse_lenient(element)
    if media.type == "*" and media.subtype != "*":
        raise MediaTypeError(f"invalid media range: {media.essence!r}")
    weight = media.get("q")
    if weight is None and not strict and "q" in _raw_names(element):
        # The browser algorithm dropped a malformed q (q =0, q=, a control character);
        # reading it as the default weight 1 would turn "not acceptable" into "best".
        raise MediaTypeError("invalid weight")
    q = 1.0
    if weight is not None:
        if _QVALUE.fullmatch(weight) is None or "q" in quoted:
            raise MediaTypeError(f"invalid weight q={show(weight)}")
        q = float(weight)
    rest = tuple(pair for pair in media.params if pair[0] != "q")
    return AcceptItem(MediaType(media.type, media.subtype, rest), q)


def _elements(header: str) -> Iterator[tuple[int, str]]:
    start = index = 0
    while index < len(header):
        char = header[index]
        if char == '"':
            _, index = collect_quoted(header, index)
            continue
        if char == ",":
            yield start, header[start:index]
            start = index + 1
        index += 1
    yield start, header[start:]


def _raw_names(element: str) -> set[str]:
    """Parameter names as written, trimmed and lower-cased, even where the value is broken."""
    names: set[str] = set()
    index, length = element.find(";"), len(element)
    while 0 <= index < length:
        index += 1
        start = index
        while index < length and element[index] not in ";=":
            index += 1
        names.add(ascii_lower(element[start:index].strip(HTTP_WHITESPACE)))
        while index < length and element[index] != ";":
            if element[index] == '"':
                _, index = collect_quoted(element, index)
            else:
                index += 1
    return names


def _offer(offer: str) -> MediaType:
    media = parse_media_type(offer)
    if "*" in (media.type, media.subtype):
        raise MediaTypeError(f"an offer must be a concrete media type, not {show(offer)}")
    return media


def _same(name: str, wanted: str, actual: str | None) -> bool:
    if actual is None:
        return False
    if name == "charset":
        return ascii_lower(wanted) == ascii_lower(actual)
    return wanted == actual
