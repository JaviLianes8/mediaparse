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
assert mediaparse.__version__ == "1.0.0"
public = sorted(name for name in dir(mediaparse) if not name.startswith("_"))
assert sorted(mediaparse.__all__) == public, public
try:
    MediaType("a", "b").get(1)
except TypeError:
    pass
else:
    raise AssertionError("get accepted a non-str name")
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


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    built = _run(sys.executable, "-m", "build", "--outdir", out, ROOT)
    assert built.returncode == 0, built.stderr
    return out


def _venv(folder: Path) -> Path:
    venv.create(folder, with_pip=True)
    return folder / ("Scripts" if sys.platform == "win32" else "bin") / "python"


def _check(python: Path, work: Path) -> None:
    # Run from an empty folder so the source tree cannot shadow the install.
    work.mkdir(exist_ok=True)
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == "e2e ok"


def test_wheel_and_sdist_contents(dist: Path) -> None:
    (wheel,) = dist.glob("mediaparse-*.whl")
    (sdist,) = dist.glob("mediaparse-*.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    assert "mediaparse/py.typed" in names
    assert any(name.endswith("licenses/LICENSE") for name in names)
    assert not any(name.startswith("tests/") for name in names)
    assert not any(name.endswith((".json", ".js", ".md")) for name in names)
    listing = _run(sys.executable, "-m", "tarfile", "-l", sdist).stdout.decode()
    for absent in ("IMPROVEMENTS-round", "CERT-1.0-REPORT", ".txt", ".xml", ".html", "wpt-"):
        assert absent not in listing.replace("requirements-dev.txt", ""), absent
    assert "node_modules" not in listing
    for present in ("tests/upstream/MANIFEST.json", "tests/test_wpt.py", "GUIDE.md", "LICENSE"):
        assert present in listing, present


def test_installed_wheel_end_to_end(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("mediaparse-*.whl")
    python = _venv(tmp_path / "venv")
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr
    _check(python, tmp_path / "work")


@pytest.mark.skipif(
    os.environ.get("MEDIAPARSE_E2E_PYPI") != "1", reason="set MEDIAPARSE_E2E_PYPI=1 to use PyPI"
)
def test_upgrade_in_place_from_the_pypi_release(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("mediaparse-*.whl")
    python = _venv(tmp_path / "venv")
    old = _run(python, "-m", "pip", "install", "-q", "mediaparse==0.2.0")
    assert old.returncode == 0, old.stderr
    probe = "import mediaparse; print(mediaparse.__version__, mediaparse.parse('a/b;c=1'))"
    before = _run(python, "-I", "-c", probe, cwd=tmp_path)
    assert before.stdout.decode().split()[0] == "0.2.0"
    upgraded = _run(python, "-m", "pip", "install", "-q", "--upgrade", wheel)
    assert upgraded.returncode == 0, upgraded.stderr
    after = _run(python, "-I", "-c", probe, cwd=tmp_path)
    assert after.stdout.decode().split()[0] == "1.0.0"
    assert after.stdout.decode().split(None, 1)[1] == before.stdout.decode().split(None, 1)[1]
    _check(python, tmp_path / "work")
