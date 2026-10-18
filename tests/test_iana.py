"""Every media type in the IANA registry, and every registered structured syntax suffix.

The registries are fetched by scripts/fetch_upstream.py (URLs and sha256 in
tests/upstream/MANIFEST.json, CC0) and never committed; these tests skip without them.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest
from conftest import upstream_bytes

from mediaparse import MediaType, build, normalize, parse_accept, parse_media_type, quality

NS = "{http://www.iana.org/assignments}"


@pytest.fixture(scope="module")
def registered() -> list[str]:
    root = ET.fromstring(upstream_bytes("iana-media-types.xml"))
    names = [f.text or "" for f in root.iter(f"{NS}file") if f.get("type") == "template"]
    assert len(names) > 2000
    return names


@pytest.fixture(scope="module")
def suffixes() -> list[str]:
    root = ET.fromstring(upstream_bytes("iana-structured-suffix.xml"))
    found = [s.text or "" for s in root.iter(f"{NS}suffix")]
    assert {"+json", "+xml", "+cbor", "+zip"} <= set(found)
    return found


def test_every_registered_name_parses_both_ways_and_round_trips(registered: list[str]) -> None:
    for name in registered:
        for strict in (False, True):
            media = parse_media_type(name, strict=strict)
            assert media.essence == name.lower(), name
            assert media.params == ()
        upper = parse_media_type(name.upper())
        assert str(upper) == name.lower()
        assert normalize(name.upper()) == name.lower()
        assert build(name) == name.lower()


def test_the_suffix_is_what_follows_the_last_plus(registered: list[str]) -> None:
    with_plus = [name for name in registered if "+" in name.split("/")[1]]
    assert len(with_plus) > 500
    for name in registered:
        subtype = name.split("/")[1].lower()
        expected = subtype.rsplit("+", 1)[1] if "+" in subtype else None
        assert parse_media_type(name).suffix == (expected or None), name


def test_registered_suffixes_are_recognised(registered: list[str], suffixes: list[str]) -> None:
    for suffix in suffixes:
        assert suffix.startswith("+")
        media = parse_media_type(f"application/example{suffix}")
        assert media.suffix == suffix[1:]
    known = {suffix[1:] for suffix in suffixes}
    used = {parse_media_type(name).suffix for name in registered} - {None}
    assert {"json", "xml"} <= used & known


def test_a_registered_type_is_negotiated_by_its_own_range(registered: list[str]) -> None:
    for name in registered[::17]:
        main = name.split("/")[0]
        accept = f"{main}/*;q=0.5, {name};q=0.9, */*;q=0.1"
        assert quality(accept, name) == 0.9
        assert quality(accept, f"{main}/zz-unregistered") == 0.5
        main_type, subtype = name.lower().split("/")
        assert parse_accept(accept)[1].media_range == MediaType(main_type, subtype)
