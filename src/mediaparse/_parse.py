"""Parse a Content-Type style header into a media type and its parameters."""

from __future__ import annotations

from collections.abc import Iterator

from ._tokens import normalize_mimetype


def parse(header: str) -> tuple[str, dict[str, str]]:
    """Split a media type header into ``(mimetype, params)``.

    The media type and parameter names are lower-cased, quoted values are
    unescaped, and whitespace around separators is ignored. A header with no
    valid ``type/subtype`` raises :class:`MediaTypeError`; stray parameters
    without a value are tolerated and dropped.
    """
    main, _, rest = header.partition(";")
    mimetype = normalize_mimetype(main)
    params: dict[str, str] = {}
    for key, value in _iter_params(rest):
        params[key] = value
    return mimetype, params


def _iter_params(text: str) -> Iterator[tuple[str, str]]:
    index, length = 0, len(text)
    while index < length:
        while index < length and text[index] in "; \t":
            index += 1
        if index >= length:
            break
        start = index
        while index < length and text[index] not in "=;":
            index += 1
        key = text[start:index].strip().lower()
        if index < length and text[index] == "=":
            index += 1
            value, index = _read_value(text, index)
            if key:
                yield key, value
        else:
            # A parameter with no value is not useful to preserve; skip it.
            index += 1


def _read_value(text: str, index: int) -> tuple[str, int]:
    if index < len(text) and text[index] == '"':
        return _read_quoted(text, index)
    start = index
    while index < len(text) and text[index] != ";":
        index += 1
    return text[start:index].strip(), index


def _read_quoted(text: str, index: int) -> tuple[str, int]:
    length = len(text)
    index += 1  # skip the opening quote
    chars: list[str] = []
    while index < length:
        char = text[index]
        if char == "\\" and index + 1 < length:
            chars.append(text[index + 1])
            index += 2
            continue
        if char == '"':
            index += 1
            break
        chars.append(char)
        index += 1
    return "".join(chars), index
