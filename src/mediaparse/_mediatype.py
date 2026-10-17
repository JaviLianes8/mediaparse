"""The parsed media type value."""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import MediaTypeError, show
from ._tokens import ascii_lower, is_quotable, is_token, quote


@dataclass(frozen=True)
class MediaType:
    """A media type: ``type``, ``subtype`` and ordered ``params`` as ``(name, value)`` pairs.

    Construction checks the parts: type, subtype and parameter names must be tokens and
    are stored in lower case, names must be unique, and values must fit a quoted string.
    ``str()`` serializes it the way the WHATWG MIME Sniffing standard does, which is the
    form browsers expose, for example ``text/html;charset=utf-8``. Equality compares the
    parameters in order; use :func:`matches` to ignore order and ``charset`` case. A part
    of the wrong type raises :class:`TypeError`, an invalid one :class:`MediaTypeError`.

    >>> from mediaparse import MediaType
    >>> media = MediaType("Text", "HTML", (("Charset", "UTF-8"), ("title", "a b")))
    >>> media.type, media.subtype, media.params
    ('text', 'html', (('charset', 'UTF-8'), ('title', 'a b')))
    >>> print(media)
    text/html;charset=UTF-8;title="a b"
    """

    type: str
    subtype: str
    params: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for label, part in (("type", self.type), ("subtype", self.subtype)):
            _require_str(label, part)
            if not is_token(part):
                raise MediaTypeError(f"invalid media {label}: {show(part)}")
        if not isinstance(self.params, (tuple, list)):
            raise TypeError(f"params must be a tuple of pairs, got {type(self.params).__name__}")
        names: list[str] = []
        pairs = tuple(self.params)
        for pair in pairs:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise TypeError(f"parameters must be (name, value) tuples, got {show(pair)}")
            name, value = pair
            _require_str("parameter name", name)
            _require_str("parameter value", value)
            if not is_token(name):
                raise MediaTypeError(f"invalid parameter name: {show(name)}")
            if not all(is_quotable(char) for char in value):
                raise MediaTypeError(f"parameter {show(name)} has a value no header can carry")
            names.append(ascii_lower(name))
        if len(set(names)) != len(names):
            raise MediaTypeError("a parameter is given more than once")
        object.__setattr__(self, "type", ascii_lower(self.type))
        object.__setattr__(self, "subtype", ascii_lower(self.subtype))
        lowered = tuple((name, value) for name, (_, value) in zip(names, pairs, strict=True))
        object.__setattr__(self, "params", lowered)

    @property
    def essence(self) -> str:
        """``type/subtype`` without parameters.

        >>> from mediaparse import parse_media_type
        >>> parse_media_type("Text/HTML; charset=utf-8").essence
        'text/html'
        """
        return f"{self.type}/{self.subtype}"

    @property
    def suffix(self) -> str | None:
        """The structured syntax suffix of RFC 6838 section 4.2.8 (``json`` for ``+json``).

        >>> from mediaparse import parse_media_type
        >>> parse_media_type("application/vnd.api+json").suffix
        'json'
        >>> parse_media_type("application/json").suffix is None
        True
        """
        _, plus, tail = self.subtype.rpartition("+")
        return tail if plus and tail else None

    @property
    def parameters(self) -> dict[str, str]:
        """The parameters as a new ordered dict.

        >>> from mediaparse import parse_media_type
        >>> parse_media_type("text/plain; b=2; a=1").parameters
        {'b': '2', 'a': '1'}
        """
        return dict(self.params)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Return a parameter value by case-insensitive name, or ``default``.

        A name that is not a ``str`` raises :class:`TypeError`.

        >>> from mediaparse import parse_media_type
        >>> media = parse_media_type("text/plain; charset=utf-8")
        >>> media.get("CHARSET"), media.get("format"), media.get("format", "fixed")
        ('utf-8', None, 'fixed')
        """
        _require_str("name", name)
        wanted = ascii_lower(name)
        for key, value in self.params:
            if key == wanted:
                return value
        return default

    def __str__(self) -> str:
        parts = [self.essence]
        parts.extend(f"{name}={quote(value)}" for name, value in self.params)
        return ";".join(parts)


def _require_str(label: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a str, got {type(value).__name__}")
