"""Canonicalize and compare media type headers."""

from __future__ import annotations

from ._parse import parse_media_type
from ._tokens import ascii_lower, quote


def normalize(header: str, *, strict: bool = False) -> str:
    """Return a canonical form of the header for display or comparison.

    The header is read like :func:`parse_media_type`. The media type and parameter names
    are lower-cased, parameters are sorted by name and the ``charset`` value is lower-cased
    (it is case insensitive, RFC 2046 section 4.1.2). Other values keep their case, since
    a filename or boundary is significant. The output uses ``"; "`` between parts.
    """
    media = parse_media_type(header, strict=strict)
    parts = [media.essence]
    for name, value in sorted(media.params):
        parts.append(f"{name}={quote(ascii_lower(value) if name == 'charset' else value)}")
    return "; ".join(parts)


def matches(first: str, second: str) -> bool:
    """Return whether two headers denote the same media type and parameters."""
    return normalize(first) == normalize(second)
