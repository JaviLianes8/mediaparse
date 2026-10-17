"""The PyPI release 0.2.0 as an oracle: 1.0.0 answers the same, except where documented.

Set MEDIAPARSE_V02 to a folder holding the 0.2.0 package (for example the unpacked
wheel: `pip download mediaparse==0.2.0 --no-deps` and unzip it); the test skips otherwise.
"""

from __future__ import annotations

import importlib.util
import os
import random
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from generators import media_params, noise, unicode_text

import mediaparse


@pytest.fixture(scope="module")
def old() -> ModuleType:
    folder = os.environ.get("MEDIAPARSE_V02")
    if not folder:
        pytest.skip("set MEDIAPARSE_V02 to the unpacked 0.2.0 release")
    init = Path(folder) / "mediaparse" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "mediaparse_v02", init, submodule_search_locations=[str(init.parent)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mediaparse_v02"] = module
    spec.loader.exec_module(module)
    assert module.__version__ == "0.2.0"
    return module


def _outcome(module: ModuleType, name: str, *args: Any, **kwargs: Any) -> object:
    try:
        result = getattr(module, name)(*args, **kwargs)
    except (TypeError, ValueError) as error:
        family = "MediaTypeError" if type(error).__name__ == "MediaTypeError" else "other"
        return (family, type(error).__mro__[1].__name__ if family == "other" else None)
    if isinstance(result, list):
        return [(str(item.media_range), item.q) for item in result]
    return str(result) if type(result).__name__ == "MediaType" else result


def _same(old: ModuleType, calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]]) -> int:
    for name, args, kwargs in calls:
        assert _outcome(old, name, *args, **kwargs) == _outcome(
            mediaparse, name, *args, **kwargs
        ), (
            name,
            args,
            kwargs,
        )
    return len(calls)


def test_parsers_agree_with_0_2_0(old: ModuleType) -> None:
    rng = random.Random(21)
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    for _ in range(4000):
        text = noise(rng)
        for strict in (False, True):
            for name in ("parse", "parse_media_type", "normalize", "parse_accept"):
                calls.append((name, (text,), {"strict": strict}))
        calls.append(("matches", (text, text.upper()), {}))
    assert _same(old, calls) == 4000 * 9


def test_builders_and_negotiation_agree_with_0_2_0(old: ModuleType) -> None:
    rng = random.Random(22)
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    offers = ["text/html", "text/plain;format=flowed", "image/png"]
    for _ in range(3000):
        essence, params = media_params(rng, latin1=True)
        extended = rng.random() < 0.5
        values = {"t": unicode_text(rng)}
        calls.append(("build", (essence, params), {"extended": extended}))
        calls.append(("build", ("a/b", values), {"extended": extended}))
        header = ",".join(noise(rng, 12) for _ in range(3))
        calls.append(("negotiate", (header, offers), {}))
        calls.extend(("quality", (header, offer), {}) for offer in offers)
        extended_header = mediaparse.build("a/b", values, extended=True)
        calls.append(("decode_extended", (mediaparse.parse(extended_header)[1],), {}))
    assert _same(old, calls) == 3000 * 7


def test_the_documented_changes_and_nothing_else(old: ModuleType) -> None:
    media = mediaparse.MediaType("a", "b")
    changes: list[tuple[Callable[[ModuleType], object], type[Exception], type[Exception]]] = [
        (lambda m: m.MediaType("a", "b").get(1), AttributeError, TypeError),
        (lambda m: m.AcceptItem(m.MediaType("a", "b")).matches("a/b"), AttributeError, TypeError),
        (lambda m: m.AcceptItem(m.MediaType("a", "b"), 10**5000), ValueError, Exception),
    ]
    for call, before, after in changes:
        with pytest.raises(before):
            call(old)
        with pytest.raises(after):
            call(mediaparse)
    assert old.AcceptItem(old.MediaType("*", "b")).q == 1.0
    assert old.decode_extended({"a*": "charmap''%41"}) == {"a": "A"}
    for refused in (
        lambda: mediaparse.AcceptItem(mediaparse.MediaType("*", "b")),
        lambda: mediaparse.decode_extended({"a*": "charmap''%41"}),
        lambda: mediaparse.AcceptItem(media, 10**5000),
    ):
        with pytest.raises(mediaparse.MediaTypeError):
            refused()
