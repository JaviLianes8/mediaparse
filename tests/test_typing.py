"""The public API is typed: mypy infers the documented types and rejects wrong ones."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
from mediaparse import build, decode_extended, negotiate, parse, parse_accept, quality
from mediaparse import parse_media_type
reveal_type(parse("t/s"))
reveal_type(parse_media_type("t/s").params)
reveal_type(parse_media_type("t/s").suffix)
reveal_type(build("t/s", {"a": "b"}, extended=True))
reveal_type(parse_accept("*/*")[0].q)
reveal_type(quality(None, "t/s"))
reveal_type(negotiate("*/*", ["t/s"]))
reveal_type(decode_extended({"a": "b"}))
parse(b"t/s")
build("t/s", {"a": 1})
parse("t/s", True)
negotiate("*/*", "t/s", 1)
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    args = ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    try:
        from mypy import api
    except ImportError:
        # The interpreter running pytest may lack mypy while the one on PATH has it.
        program = shutil.which("mypy")
        if program is None:
            pytest.skip("mypy is not installed")
        result = subprocess.run([program, *args], capture_output=True, text=True, check=False)
        return result.stdout + result.stderr
    out, err, _ = api.run(args)
    return str(out) + str(err)


def test_functions_return_the_documented_types(mypy_output: str) -> None:
    assert [_revealed(mypy_output, line) for line in range(4, 12)] == [
        "tuple[str, dict[str, str]]",
        "tuple[tuple[str, str], ...]",
        "str | None",
        "str",
        "float",
        "float",
        "str | None",
        "dict[str, str]",
    ]


def test_misuse_is_rejected(mypy_output: str) -> None:
    for line, code in ((12, "arg-type"), (13, "dict-item"), (14, "call-arg"), (15, "call-arg")):
        assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix.
    return match.group(1).replace("builtins.", "")
