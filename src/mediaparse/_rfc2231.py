"""Join RFC 2231 parameter continuations and decode charset-encoded values."""

from __future__ import annotations

import codecs
import re
from collections.abc import Mapping

from ._errors import MediaTypeError, show
from ._extended import percent_decode
from ._tokens import ascii_lower

# attribute, optional section (no leading zeros, at most nine digits), optional "*" for an
# encoded value.
_NAME = re.compile(r"(?P<attr>[^*]+)(?:\*(?P<section>0|[1-9][0-9]{0,8}))?(?P<encoded>\*)?")
_INITIAL = re.compile(r"(?P<charset>[^']*)'(?P<language>[^']*)'(?P<rest>.*)", re.DOTALL)
# mime-charset characters from RFC 8187 section 3.2.1.
_CHARSET = re.compile(r"[A-Za-z0-9!#$%&+\-^_`{}~]+")
# Python text codecs that are not character sets: escape decoders, host code pages and
# transforms. A header must not decide to run them.
_NOT_CHARSETS = frozenset({"mbcs", "oem", "idna", "punycode", "undefined", "charmap"})


def decode_extended(params: Mapping[str, str]) -> dict[str, str]:
    """Return ``params`` with RFC 2231 continuations joined and encoded values decoded.

    ``title*0*=us-ascii'en'This%20is``, ``title*1=" fun"`` become ``title="This is fun"``.
    Names are compared in ASCII lower case and results keep the order in which each name
    first appears. When both ``name`` and an extended form are present the extended form
    wins, as it is the one that carries the real value. The language tag is dropped.
    Gaps or leading zeros in the sections, a section given twice, a bad percent escape, a
    charset that is not a character set Python can decode, and bytes it cannot decode
    raise :class:`MediaTypeError`; a name or value that is not a ``str`` raises :class:`TypeError`.

    >>> from mediaparse import decode_extended
    >>> decode_extended({"title*0*": "us-ascii'en'This%20is", "title*1": " fun", "a": "1"})
    {'title': 'This is fun', 'a': '1'}
    """
    if not isinstance(params, Mapping):
        raise TypeError(f"params must be a mapping, got {type(params).__name__}")
    order: dict[str, None] = {}
    plain: dict[str, str] = {}
    pieces: dict[str, dict[int, tuple[bool, str]]] = {}
    for raw, value in params.items():
        if not isinstance(raw, str) or not isinstance(value, str):
            raise TypeError("parameter names and values must be str")
        name = ascii_lower(raw)
        if "*" not in name:
            order.setdefault(name)
            plain[name] = value
            continue
        match = _NAME.fullmatch(name)
        if match is None:
            raise MediaTypeError(f"invalid extended parameter name: {show(raw)}")
        attr, section = match["attr"], match["section"]
        order.setdefault(attr)
        index = -1 if section is None else int(section)
        slot = pieces.setdefault(attr, {})
        if index in slot:
            raise MediaTypeError(f"parameter {show(attr)} section {section} is given twice")
        slot[index] = (match["encoded"] is not None, value)
    return {attr: _join(attr, pieces[attr]) if attr in pieces else plain[attr] for attr in order}


def _join(attr: str, slot: dict[int, tuple[bool, str]]) -> str:
    label = show(attr)
    if -1 in slot:
        if len(slot) > 1:
            raise MediaTypeError(f"parameter {label} mixes the unnumbered and numbered forms")
        slot = {0: slot[-1]}
    if sorted(slot) != list(range(len(slot))):
        raise MediaTypeError(f"parameter {label} has missing sections")
    charset = "us-ascii"
    data = bytearray()
    for index in range(len(slot)):
        encoded, value = slot[index]
        if encoded and index == 0:
            initial = _INITIAL.fullmatch(value)
            if initial is None:
                raise MediaTypeError(f"parameter {label} lacks the charset'language' prefix")
            charset = initial["charset"] or "us-ascii"
            value = initial["rest"]
        if encoded:
            data += percent_decode(value)
        elif value.isascii():
            data += value.encode("ascii")
        else:
            raise MediaTypeError(f"parameter {label} has non-ASCII text in a plain section")
    return _decode(bytes(data), charset, label)


def _decode(data: bytes, charset: str, label: str) -> str:
    if _CHARSET.fullmatch(charset) is None:
        raise MediaTypeError(f"invalid charset name {show(charset)}")
    try:
        name = codecs.lookup(charset).name
    except LookupError as error:
        raise MediaTypeError(f"unknown charset {show(charset)}") from error
    if name in _NOT_CHARSETS or "escape" in name:
        raise MediaTypeError(f"{show(charset)} is not a character set")
    try:
        return data.decode(charset)
    except LookupError as error:
        raise MediaTypeError(f"{show(charset)} is not a text encoding") from error
    except (UnicodeError, ValueError) as error:
        raise MediaTypeError(f"parameter {label} is not valid {show(charset)}") from error
