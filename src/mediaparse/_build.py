"""Build a Content-Type style header from a media type and parameters."""

from __future__ import annotations

from collections.abc import Mapping

from ._errors import MediaTypeError
from ._tokens import is_token, normalize_mimetype


def build(mimetype: str, params: Mapping[str, str] | None = None) -> str:
    """Render ``mimetype`` and ``params`` as a header value.

    The media type and parameter names are lower-cased. Each value is emitted
    as a bare token when it can be, and quoted (with backslash escaping) when it
    contains anything a token may not. An invalid media type or parameter name
    raises :class:`MediaTypeError`.
    """
    parts = [normalize_mimetype(mimetype)]
    for name, value in (params or {}).items():
        key = name.strip().lower()
        if not is_token(key):
            raise MediaTypeError(f"invalid parameter name: {name!r}")
        parts.append(f"{key}={_encode_value(value)}")
    return "; ".join(parts)


def _encode_value(value: str) -> str:
    if is_token(value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
