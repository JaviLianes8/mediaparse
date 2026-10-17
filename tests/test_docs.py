"""The README examples run and print what their comments say; docs and versions agree."""

from __future__ import annotations

import contextlib
import io
import itertools
import re
from pathlib import Path

import mediaparse

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
GUIDE = (ROOT / "GUIDE.md").read_text(encoding="utf-8")


def _python_blocks(text: str = README) -> list[str]:
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


def _expected_output(block: str) -> list[str]:
    """Each print line is followed by a comment line that holds what it prints."""
    lines = block.splitlines()
    return [
        following.strip()[2:]
        for line, following in itertools.pairwise(lines)
        if line.strip().startswith("print(") and following.strip().startswith("# ")
    ]


def _run_blocks(text: str) -> int:
    checked = 0
    for block in _python_blocks(text):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "docs", "exec"), {"__name__": "docs"})
        expected = _expected_output(block)
        assert expected, block
        assert out.getvalue().splitlines() == expected
        checked += len(expected)
    return checked


def test_every_readme_example_runs_and_prints_its_comment() -> None:
    assert len(_python_blocks()) == 5
    assert _run_blocks(README) == 15


def test_every_guide_example_runs_and_prints_its_comment() -> None:
    assert len(_python_blocks(GUIDE)) == 4
    assert _run_blocks(GUIDE) == 8


def test_the_readme_links_are_absolute() -> None:
    for target in re.findall(r"\]\(([^)]+)\)", README):
        assert target.startswith("https://"), target
    assert "GUIDE.md" in README and "CHANGELOG.md" in README


def test_every_print_in_the_readme_shows_its_output() -> None:
    for block in _python_blocks() + _python_blocks(GUIDE):
        prints = [line for line in block.splitlines() if line.strip().startswith("print(")]
        assert len(prints) == len(_expected_output(block))


def test_the_api_table_lists_every_public_name() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in mediaparse.__all__:
        assert f"`{name}" in table, name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == mediaparse.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{mediaparse.__version__}]" in text


def test_no_em_dash_anywhere_in_the_tree() -> None:
    suffixes = {".py", ".md", ".toml", ".ps1", ".txt", ".json"}
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if parts[:2] == ("tests", "upstream") and path.name != "MANIFEST.json":
            continue
        if any(part.startswith(".") or part in ("__pycache__", "build", "dist") for part in parts):
            continue
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*(ROOT / "src").rglob("*.py"), *(ROOT / "tests").glob("*.py")]:
        lines = path.read_text(encoding="utf-8").count("\n")
        assert lines <= 200, path
