"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with MEDIAPARSE_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("MEDIAPARSE_E2E") != "1", reason="set MEDIAPARSE_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pickle
import mediaparse
from mediaparse import (
    AcceptItem, MediaType, MediaTypeError, build, decode_extended, matches, negotiate,
    normalize, parse, parse_accept, parse_media_type, quality,
)

assert "site-packages" in mediaparse.__file__, mediaparse.__file__
assert importlib.metadata.version("mediaparse") == mediaparse.__version__
assert importlib.resources.files("mediaparse").joinpath("py.typed").is_file()
media = parse_media_type('TEXT/HTML;charset="shift_jis"iso-2022-jp;charset=x')
assert str(media) == "text/html;charset=shift_jis", media
assert pickle.loads(pickle.dumps(media)) == media
assert parse("text/plain;a=1;A=2") == ("text/plain", {"a": "1"})
try:
    parse("text/plain;a=1;A=2", strict=True)
except MediaTypeError as error:
    assert error.position == 15 and pickle.loads(pickle.dumps(error)).position == 15
else:
    raise AssertionError("strict accepted a duplicate")
try:
    build("text/plain", {"x": "a\r\nb"})
except MediaTypeError:
    pass
else:
    raise AssertionError("build wrote a CRLF")
built = build("text/plain", {"title": "caf\xe9"}, extended=True)
assert built == "text/plain; title*=UTF-8''caf%C3%A9", built
assert decode_extended(parse(built)[1]) == {"title": "caf\xe9"}
accept = "text/*;q=0.3, text/plain;q=0.7, */*;q=0.5"
assert quality(accept, "text/html;level=3") == 0.3
assert negotiate(accept, ["text/html", "image/png"]) == "image/png"
assert parse_accept("a/b;q=0.5")[0] == AcceptItem(MediaType("a", "b"), 0.5)
assert matches("Text/HTML;Charset=UTF-8", normalize("text/html; charset=utf-8"))
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, check=False)


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("mediaparse-*.whl")
    (sdist,) = dist.glob("mediaparse-*.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    assert "mediaparse/py.typed" in names
    assert not any(name.startswith("tests/") for name in names)
    assert not any(name.endswith(".json") for name in names)
    listing = _run(sys.executable, "-m", "tarfile", "-l", sdist).stdout.decode()
    assert "IMPROVEMENTS-round" not in listing
    assert "tests/upstream/MANIFEST.json" in listing
    assert "wpt-mime-types.json" not in listing
    assert "wpt-generated-mime-types.json" not in listing
    assert "tests/test_wpt.py" in listing

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == "e2e ok"
