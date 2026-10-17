"""Seeded generators of header text shared by the oracle and property tests (hand-written)."""

from __future__ import annotations

import random

TCHAR = "!#$%&'*+-.^_`|~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Characters that stress the parsers: separators, quotes, escapes, whitespace of every
# kind, controls, Latin-1, a character past U+00FF, a lone surrogate and an astral one.
HOSTILE = [
    "a", "B", "/", ";", "=", '"', "\\", " ", "\t", "\r", "\n", ",", "x", "*", "+", "\x00",
    "\x7f", "\xe9", "\u0100", "\U0001f600", "\ud800", "q", "0", ".", "(", ")", "\x0b",
    "\x0c", "\xa0", "%", "'",
]  # fmt: skip


def token(rng: random.Random, alphabet: str = TCHAR, longest: int = 6) -> str:
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, longest)))


def quotable(rng: random.Random, longest: int = 8, latin1: bool = False) -> str:
    """Text a quoted string can carry: tab, printable ASCII and, if asked, 0x80-0xFF."""
    pool = ["\t", *map(chr, range(0x20, 0x7F))]
    if latin1:
        pool += list(map(chr, range(0x80, 0x100)))
    return "".join(rng.choice(pool) for _ in range(rng.randint(0, longest)))


def unicode_text(rng: random.Random, longest: int = 8) -> str:
    """Any text that UTF-8 can encode, from all planes."""
    pool = "aZ ;\"\\'%*\t\r\n\x00\xe9\u20ac\u4e2d\U0001f600"
    return "".join(rng.choice(pool) for _ in range(rng.randint(0, longest)))


def media_params(
    rng: random.Random, names: str = TCHAR, latin1: bool = False
) -> tuple[str, dict[str, str]]:
    """A random essence and parameters with unique case-insensitive names."""
    essence = f"{token(rng)}/{token(rng)}"
    params: dict[str, str] = {}
    for _ in range(rng.randint(0, 4)):
        name = token(rng, names, 5)
        if "*" in name or name.lower() in {key.lower() for key in params}:
            continue
        params[name] = token(rng) if rng.random() < 0.4 else quotable(rng, latin1=latin1)
    return essence, params


def noise(rng: random.Random, longest: int = 25) -> str:
    """Hostile text, half of it after a valid looking start."""
    text = "".join(rng.choice(HOSTILE) for _ in range(rng.randint(0, longest)))
    if rng.random() < 0.5:
        text = rng.choice(["text/plain", "a/b", " TEXT/Html ", "x/y;", "*/*;q=0.5,"]) + text
    return text
