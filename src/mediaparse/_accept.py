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
            items.append(_item(element, strict))
        except MediaTypeError as error:
            if strict:
                where = None if error.position is None else start + error.position
                raise MediaTypeError(str(error), position=where) from None
    return items


def _item(element: str, strict: bool) -> AcceptItem:
    quoted: set[str] = set()
    media = parse_strict(element, quoted) if strict else parse_lenient(element)
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
