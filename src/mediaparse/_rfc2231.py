"""Join RFC 2231 parameter continuations and decode charset-encoded values."""

from __future__ import annotations

import re
from collections.abc import Mapping

from ._errors import MediaTypeError
from ._extended import percent_decode

# attribute, optional section (no leading zeros), optional "*" for an encoded value.
_NAME = re.compile(r"(?P<attr>[^*]+)(?:\*(?P<section>0|[1-9][0-9]*))?(?P<encoded>\*)?")
_INITIAL = re.compile(r"(?P<charset>[^']*)'(?P<language>[^']*)'(?P<rest>.*)", re.DOTALL)


def decode_extended(params: Mapping[str, str]) -> dict[str, str]:
    """Return ``params`` with RFC 2231 continuations joined and encoded values decoded.

    ``title*0*=us-ascii'en'This%20is``, ``title*1=" fun"`` become ``title="This is fun"``.
    When both ``name`` and an extended form are present the extended form wins, as it is
    the one that carries the real value. The language tag is dropped. Gaps or leading
    zeros in the sections, a section given twice, a bad percent escape, an unknown or
    non-text charset and bytes the charset cannot decode raise :class:`MediaTypeError`.
    """
    plain: dict[str, str] = {}
    pieces: dict[str, dict[int, tuple[bool, str]]] = {}
    for name, value in params.items():
        if "*" not in name:
            plain[name] = value
            continue
        match = _NAME.fullmatch(name)
        if match is None:
            raise MediaTypeError(f"invalid extended parameter name: {name!r}")
        attr, section = match["attr"], match["section"]
        index = -1 if section is None else int(section)
        slot = pieces.setdefault(attr, {})
        if index in slot:
            raise MediaTypeError(f"parameter {attr!r} section {section} is given twice")
        slot[index] = (match["encoded"] is not None, value)
    result = dict(plain)
    for attr, slot in pieces.items():
        result[attr] = _join(attr, slot)
    return result


def _join(attr: str, slot: dict[int, tuple[bool, str]]) -> str:
    if -1 in slot:
        if len(slot) > 1:
            raise MediaTypeError(f"parameter {attr!r} mixes {attr}* with numbered sections")
        slot = {0: slot[-1]}
    if sorted(slot) != list(range(len(slot))):
        raise MediaTypeError(f"parameter {attr!r} has missing sections: {sorted(slot)}")
    charset = "us-ascii"
    data = bytearray()
    for index in range(len(slot)):
        encoded, value = slot[index]
        if encoded and index == 0:
            initial = _INITIAL.fullmatch(value)
            if initial is None:
                raise MediaTypeError(f"parameter {attr!r} lacks the charset'language' prefix")
            charset = initial["charset"] or "us-ascii"
            value = initial["rest"]
        if encoded:
            data += percent_decode(value)
        elif value.isascii():
            data += value.encode("ascii")
        else:
            raise MediaTypeError(f"parameter {attr!r} has non-ASCII text in a plain section")
    try:
        return bytes(data).decode(charset)
    except LookupError as error:
        raise MediaTypeError(f"unknown or non-text charset {charset!r}") from error
    except UnicodeDecodeError as error:
        raise MediaTypeError(f"parameter {attr!r} is not valid {charset}") from error
