"""The parsed media type value."""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import MediaTypeError
from ._tokens import ascii_lower, is_quotable, is_token, quote


@dataclass(frozen=True)
class MediaType:
    """A media type: ``type``, ``subtype`` and ordered ``params`` as ``(name, value)`` pairs.

    Construction checks the parts: type, subtype and parameter names must be tokens and
    are stored in lower case, names must be unique, and values must fit a quoted string.
    ``str()`` serializes it the way the WHATWG MIME Sniffing standard does, which is the
    form browsers expose, for example ``text/html;charset=utf-8``.
    """

    type: str
    subtype: str
    params: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for label, part in (("type", self.type), ("subtype", self.subtype)):
            if not isinstance(part, str) or not is_token(part):
                raise MediaTypeError(f"invalid media {label}: {part!r}")
        names: list[str] = []
        pairs = tuple(self.params)
        for pair in pairs:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise MediaTypeError(f"parameters must be (name, value) pairs, got {pair!r}")
            name, value = pair
            if not isinstance(name, str) or not is_token(name):
                raise MediaTypeError(f"invalid parameter name: {name!r}")
            if not isinstance(value, str) or not all(is_quotable(char) for char in value):
                raise MediaTypeError(f"parameter {name!r} has a value no header can carry")
            names.append(ascii_lower(name))
        if len(set(names)) != len(names):
            raise MediaTypeError("a parameter is given more than once")
        object.__setattr__(self, "type", ascii_lower(self.type))
        object.__setattr__(self, "subtype", ascii_lower(self.subtype))
        lowered = tuple((name, value) for name, (_, value) in zip(names, pairs, strict=True))
        object.__setattr__(self, "params", lowered)

    @property
    def essence(self) -> str:
        """``type/subtype`` without parameters."""
        return f"{self.type}/{self.subtype}"

    @property
    def suffix(self) -> str | None:
        """The structured syntax suffix of RFC 6838 section 4.2.8 (``json`` for ``+json``)."""
        _, plus, tail = self.subtype.rpartition("+")
        return tail if plus and tail else None

    @property
    def parameters(self) -> dict[str, str]:
        """The parameters as a new ordered dict."""
        return dict(self.params)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Return a parameter value by case-insensitive name, or ``default``."""
        wanted = ascii_lower(name)
        for key, value in self.params:
            if key == wanted:
                return value
        return default

    def __str__(self) -> str:
        parts = [self.essence]
        parts.extend(f"{name}={quote(value)}" for name, value in self.params)
        return ";".join(parts)
