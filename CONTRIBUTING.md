# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/mediaparse/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `python scripts/fetch_upstream.py` once: it downloads the web-platform-tests MIME
  type files listed in `tests/upstream/MANIFEST.json`, which are not committed. Their
  tests skip without them.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes. Set
  `MEDIAPARSE_E2E=1` to also build the wheel and test the installed package.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
