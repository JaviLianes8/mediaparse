"""Read an Accept header into media ranges and weights (RFC 9110 sections 12.4.2, 12.5.1)."""

from __future__ import annotations

import re
from collections.abc import Iterator

from ._acceptitem import AcceptItem
from ._errors import MediaTypeError, show
from ._lenient import collect_quoted, parse_lenient
from ._mediatype import MediaType
from ._strict import parse_strict
from ._tokens import HTTP_WHITESPACE, OWS, ascii_lower

# qvalue = ( "0" [ "." 0*3DIGIT ] ) / ( "1" [ "." 0*3("0") ] )
_QVALUE = re.compile(r"0(?:\.[0-9]{0,3})?|1(?:\.0{0,3})?")


def parse_accept(header: str, *, strict: bool = False) -> list[AcceptItem]:
    """Read an Accept header into its media ranges, in header order.

    Elements are split on commas outside quoted strings and empty elements are ignored.
    The ``q`` parameter is the weight wherever it appears and is removed from the range.
    By default each element is read like :func:`parse_media_type`, and one that is not a
    valid media range, or whose ``q`` breaks the ``qvalue`` grammar, is skipped; with
    ``strict=True`` it raises :class:`MediaTypeError` and each range must match the
    RFC 9110 grammar exactly. A ``header`` that is not a ``str`` raises :class:`TypeError`.

    >>> from mediaparse import parse_accept
    >>> [(str(i.media_range), i.q) for i in parse_accept("text/html, */*;q=0.1, a/b;q=2")]
    [('text/html', 1.0), ('*/*', 0.1)]
    """
    if not isinstance(header, str):
        raise TypeError(f"expected str, got {type(header).__name__}")
    items: list[AcceptItem] = []
    for start, element in _elements(header):
        if not element.strip(OWS if strict else HTTP_WHITESPACE):
            continue
        try:
            items.append(_strict_item(element, start) if strict else _lenient_item(element))
        except MediaTypeError:
            if strict:
                raise
    return items


def _strict_item(element: str, start: int) -> AcceptItem:
    values: dict[str, tuple[int, bool]] = {}
    media = parse_strict(element, values, start)
    if media.type == "*" and media.subtype != "*":
        where = start + len(element) - len(element.lstrip(OWS))
        raise MediaTypeError(f"invalid media range: {show(media.essence)}", position=where)
    weight = media.get("q")
    if weight is not None and (values["q"][1] or _QVALUE.fullmatch(weight) is None):
        raise MediaTypeError(f"invalid weight q={show(weight)}", position=values["q"][0])
    return _with_weight(media, weight)


def _lenient_item(element: str) -> AcceptItem:
    media = parse_lenient(element)
    # The browser algorithm drops a malformed q (q =0, q=, q="1", a control character);
    # reading it as the default weight 1, or letting another q win, would turn a weight
    # the sender wrote into a different one. Every q must be well formed.
    weight = media.get("q")
    if not all(_raw_weights(element)) or (weight and _QVALUE.fullmatch(weight) is None):
        raise MediaTypeError("invalid weight")
    return _with_weight(media, weight)


def _with_weight(media: MediaType, weight: str | None) -> AcceptItem:
    rest = tuple(pair for pair in media.params if pair[0] != "q")
    return AcceptItem(
        MediaType(media.type, media.subtype, rest), 1.0 if weight is None else float(weight)
    )


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


def _raw_weights(element: str) -> list[bool]:
    """For each parameter named ``q`` (any case, trimmed), whether it is written exactly
    ``q=qvalue``: no space before ``=``, an unquoted value of the qvalue grammar."""
    found: list[bool] = []
    index, length = element.find(";"), len(element)
    while 0 <= index < length:
        index += 1
        start = index
        while index < length and element[index] not in ";=":
            index += 1
        name = element[start:index].lstrip(HTTP_WHITESPACE)
        value_start = index + 1
        while index < length and element[index] != ";":
            if element[index] == '"':
                _, index = collect_quoted(element, index)
            else:
                index += 1
        if ascii_lower(name.rstrip(HTTP_WHITESPACE)) == "q":
            value = element[value_start:index].rstrip(HTTP_WHITESPACE)
            found.append(name in ("q", "Q") and _QVALUE.fullmatch(value) is not None)
    return found
