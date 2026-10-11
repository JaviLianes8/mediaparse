"""Canonicalize and compare media type headers."""

from __future__ import annotations

from ._build import build
from ._parse import parse


def normalize(header: str) -> str:
    """Return a canonical form of the header for display or comparison.

    The media type and parameter names are lower-cased, parameters are sorted by
    name, and the ``charset`` value is lower-cased (it is case insensitive).
    Other values keep their case, since a filename or boundary is significant.
    """
    mimetype, params = parse(header)
    canonical = {
        key: params[key].lower() if key == "charset" else params[key] for key in sorted(params)
    }
    return build(mimetype, canonical)


def matches(first: str, second: str) -> bool:
    """Return whether two headers denote the same media type and parameters."""
    return normalize(first) == normalize(second)
