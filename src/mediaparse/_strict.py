"""The RFC 9110 ``media-type`` grammar, exactly, with the position of the first error.

    media-type = type "/" subtype parameters               ; section 8.3.1
    parameters = *( OWS ";" OWS [ parameter ] )            ; section 5.6.6
    parameter  = token "=" ( token / quoted-string )       ; no whitespace around "="

Leading and trailing OWS is skipped, since a field parser removes it before the value is
read (section 5.5). A parameter given twice is an error, as RFC 6838 section 4.3 says.
"""

from __future__ import annotations

from ._errors import MediaTypeError
from ._mediatype import MediaType
from ._tokens import OWS, TOKEN_CHARS, ascii_lower


def parse_strict(text: str, quoted: set[str] | None = None) -> MediaType:
    """Parse ``text`` against the RFC 9110 grammar, raising on the first deviation.

    The names of parameters written as quoted strings are added to ``quoted`` if given.
    """
    reader = _Reader(text)
    reader.skip_ows()
    main = reader.token("media type")
    reader.expect("/")
    subtype = reader.token("media subtype")
    params: dict[str, str] = {}
    while True:
        reader.skip_ows()
        if reader.done():
            break
        reader.expect(";")
        reader.skip_ows()
        if reader.done() or reader.peek() == ";":
            continue
        start = reader.position
        name = ascii_lower(reader.token("parameter name"))
        if name in params:
            raise MediaTypeError(f"parameter {name!r} is given more than once", position=start)
        reader.expect("=")
        if reader.peek() == '"':
            params[name] = reader.quoted()
            if quoted is not None:
                quoted.add(name)
        else:
            params[name] = reader.token("value")
    return MediaType(main, subtype, tuple(params.items()))


class _Reader:
    def __init__(self, text: str) -> None:
        self.text = text
        self.position = 0

    def done(self) -> bool:
        return self.position >= len(self.text)

    def peek(self) -> str:
        return self.text[self.position : self.position + 1]

    def fail(self, message: str) -> MediaTypeError:
        found = self.peek()
        where = f"found {found!r}" if found else "found the end"
        return MediaTypeError(
            f"{message} at position {self.position}, {where}: {self.text!r}",
            position=self.position,
        )

    def skip_ows(self) -> None:
        while self.peek() and self.peek() in OWS:
            self.position += 1

    def expect(self, char: str) -> None:
        if self.peek() != char:
            raise self.fail(f"expected {char!r}")
        self.position += 1

    def token(self, label: str) -> str:
        start = self.position
        while self.peek() and self.peek() in TOKEN_CHARS:
            self.position += 1
        if self.position == start:
            raise self.fail(f"expected a token for the {label}")
        return self.text[start : self.position]

    def quoted(self) -> str:
        self.position += 1  # the opening quote
        chars: list[str] = []
        while True:
            char = self.peek()
            if not char:
                raise self.fail("unterminated quoted string")
            if char == '"':
                self.position += 1
                return "".join(chars)
            if char == "\\":
                self.position += 1
                char = self.peek()
                if not (char and _quoted_pair(char)):
                    raise self.fail("invalid escape in quoted string")
            elif not _qdtext(char):
                raise self.fail("character not allowed in a quoted string")
            chars.append(char)
            self.position += 1


def _qdtext(char: str) -> bool:
    # HTAB / SP / %x21 / %x23-5B / %x5D-7E / obs-text
    return char in "\t !" or "#" <= char <= "[" or "]" <= char <= "~" or "\x80" <= char <= "\xff"


def _quoted_pair(char: str) -> bool:
    # "\" ( HTAB / SP / VCHAR / obs-text )
    return char in "\t " or "!" <= char <= "~" or "\x80" <= char <= "\xff"
