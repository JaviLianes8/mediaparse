# mediaparse 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to mediaparse. PyPI has 0.2.0, which is
byte for byte the `main` branch at c692de6 (the wheel's modules compared with the tree), so
every change listed here is a change against the PyPI release.

Progress:
- [x] Branch `release/1.0.0` created from `main` (c692de6, same code as PyPI 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: specifications and registries fetched live, reference parsers (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e and upgrade from PyPI 0.2.0, every Python (items 8, 10, 13, 14)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [ ] Gates (item 15), final run
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

Fresh clone of `release/1.0.0` at c692de6 on the laptop, CPython 3.14: `ruff format --check .`,
`ruff check .` and `mypy --strict src tests` exit 0; `pytest` 282 passed, 1 skipped (the
installed-wheel test, which needs `MEDIAPARSE_E2E=1`); no doctests existed.

Defects found in 0.2.0 by reading and then reproducing:

- `MediaType.get(1)` and `AcceptItem.matches("text/html")` raised `AttributeError`.
- `AcceptItem(MediaType("*", "plain"))` was accepted, although no Accept header can
  hold that range, and so was a `q` parameter inside a hand-built range.
- `AcceptItem(range, 10**5000)` raised `ValueError` from `repr` instead of
  `MediaTypeError`.
- Two error messages quoted the whole input: `build(..., extended=True)` with a
  600 KB message for a 100,000 lone surrogate value, and a strict Accept header with a
  100 KB `*/subtype` element.
- `decode_extended` accepted the `charmap` codec name as a charset.
- No public docstring had a runnable example; the README linked LICENSE relatively,
  which breaks on PyPI; there was no GUIDE.
