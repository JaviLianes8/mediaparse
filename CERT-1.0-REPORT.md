# mediaparse 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to mediaparse. PyPI has 0.2.0, which is
byte for byte the `main` branch at c692de6 (the wheel's modules compared with the tree), so
every change listed here is a change against the PyPI release.

Progress:
- [x] Branch `release/1.0.0` created from `main` (c692de6, same code as PyPI 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: specifications and registries fetched live, reference parsers (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e and upgrade from PyPI 0.2.0, every Python (items 8, 10, 13, 14)
- [x] Five QA lenses report PASS (item 19)
- [x] Independent reviewer reports PASS (item 16)
- [x] Gates (item 15), final run
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 12 names, signatures and parameter names kept from 0.2.0 and pinned; every behaviour change in CHANGELOG and GUIDE |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: 18 doctests; README (15 outputs) and GUIDE (8) examples run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, `get` overloads, typing checked from a consumer |
| 5 | Typed, documented, bounded errors | PASS: `MediaTypeError` (a `ValueError`) with positions, `TypeError` for wrong types, messages quote at most 80 characters |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: 13 fetched sources with a hash manifest, IANA registries, WPT, the Node.js reference, werkzeug, multipart, `email`, PyPI 0.2.0 |
| 8 | Real e2e from the wheel | PASS: installed wheel driven from an empty folder, upgrade in place from PyPI 0.2.0 (no CLI) |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.13t not installed here |
| 11 | README and `twine check` | PASS |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-18 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | PASS (two rounds) |
| 17 | PR and trace guard | see the PR; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 50, lens a 67, b 47, c 78, e 146, reviewer 32 (9 of them author mutants re-run); every non-equivalent survivor killed by a contract |
| 19 | Five independent QA lenses | PASS: a round 4, b round 2, c round 4, d round 2, e round 2 |

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

## API review (item 1)

Kept: the twelve public names of 0.2.0 with their signatures, parameter names and
defaults, now pinned by `tests/test_contract_api.py` (the GUIDE promises the parameter
names too). Changed, all in the CHANGELOG and the GUIDE: `TypeError` from
`MediaType.get` and `AcceptItem.matches` for arguments of the wrong type; `AcceptItem`
refuses `*/subtype` and a `q` inside the range, stores a plain float and checks it after
conversion; `MediaType` stores plain `str` values; `get` overloads; the default Accept
mode skips an element with any `q` not written as `q=qvalue`; error positions point at
the offending character in the text being read; `build(extended=True)` keeps names
unique without case and free of `*`; `decode_extended` accepts only charset names of
Python's standard encodings (at most 40 characters, no `charmap`); bounded messages;
linear `AcceptItem.matches`. Internal: the Accept module split in three (reading, the item,
negotiation) to keep every file under 200 lines with the new examples; the stray
`annotations` name is gone from the package top.

## Ground truth (item 7)

Fetched on 2026-10-17 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence and
the tests check the hash before reading. Nothing fetched is committed or shipped.

- RFC 9110 (`tests/test_spec_rfc9110.py`): the `tchar`, `qdtext`, `quoted-pair` and
  `obs-text` rules are parsed out of the ABNF in the text and compared with the strict
  parser code point by code point (U+0000 to U+02FF, a surrogate, an astral character);
  the `qvalue` rule is read from the text and every weight string of up to six
  characters over `01.25` is checked; the four equivalent forms of section 8.3.1, the
  Accept precedence example, the audio and text examples and Table 5 are cut from the
  text. Table 5 is read with verified erratum 7138 (fetched): only its last row changes.
- RFC 2231 with verified erratum 590, RFC 8187, RFC 2045, RFC 6838
  (`tests/test_spec_mime.py`): every example header is cut from the fetched text; the
  decoded values are checked against Python's own `urllib.parse.unquote`; the RFC 6838
  `restricted-name-chars` rule and its "error for a parameter specified more than once"
  sentence are read from the text.
- WHATWG MIME Sniffing and Fetch (commit snapshots; `tests/test_spec_whatwg.py`): the
  HTTP token, HTTP quoted-string token and HTTP whitespace code points are read from the
  prose and compared with the default parser; each step of the algorithm is located in
  the text and exercised, and its worked example is cut from the page.
- web-platform-tests MIME type corpus (two files, commit ca5384f): every case matches.
- IANA Media Types registry (2,366 templates) and Structured Syntax Suffixes registry
  (`tests/test_iana.py`): every registered name parses in both modes, round trips,
  lower-cases, builds and negotiates; the suffix is checked on every name.
- Reference parsers run live (`tests/test_oracles.py`): the whatwg-mimetype 5.0.0
  reference implementation on 60,000 seeded hostile strings and on the WPT inputs, no
  difference; werkzeug 3.1.9 `parse_options_header` on 3,000 valid headers and 2,000
  RFC 2231 values, no difference; Python's `email` package agrees except where a quoted
  value ends in an escaped backslash (its known misreading, asserted precisely);
  multipart 2.0.1 agrees within the parameter names it accepts.
- PyPI 0.2.0 as an oracle (`tests/test_upgrade.py`, `MEDIAPARSE_V02`): 57,000 calls give
  the same results and the same error families; the documented changes are checked
  case by case.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`: three seeds of 5,000 to 10,000 hostile strings per property
(parsing never raises anything but `MediaTypeError` with a message under 300 characters
and a position inside the input; serialization is stable through both parsers; strict
mode accepts exactly a regular expression written from the RFC 9110 grammar, with
unique names; `build` round trips through both parsers; extended values round trip
through `decode_extended`; Accept weights, `quality` and `negotiate` agree with each
other). `tests/test_hostile.py`: nine input shapes timed at 50,000 and 200,000
characters through both parsers and both Accept modes (linear), 100,000 RFC 2231
sections, 100,000 parameters and ranges, 1 MB values in every error path (messages
under 300 characters), an int past the digit limit as a weight, lone surrogates.

## Author mutation round (item 18)

50 mutants over every module, each applied alone to a fresh clone of the pushed branch on
another machine, the full suite (fetched sources, werkzeug, multipart and the 0.2.0
oracle present) run with `-x` and a 300 s per-test limit. All 50 killed at once.

The table is in [CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/mediaparse/blob/main/CERT-1.0-MUTANTS.md).

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- Full suite on another machine from a fresh clone at e981f60 with `MEDIAPARSE_E2E=1`,
  `MEDIAPARSE_E2E_PYPI=1`, the 0.2.0 oracle, werkzeug and multipart: 434 passed, 4
  skipped (the Node.js reference parser, not present there). The e2e tests build the wheel
  and sdist, inspect both, install the wheel in a fresh venv and drive it from an empty
  folder with `-I`, and install 0.2.0 from PyPI, then upgrade it in place to the built
  wheel and check the same results and the full program again.
- Every interpreter on this PC from `requires-python` up, the wheel installed in a fresh
  venv and the sdist's own suite run with `src` removed (fetched sources, Node.js reference,
  werkzeug, multipart and the 0.2.0 oracle present), at e981f60: CPython 3.10.19,
  3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded, 417 passed and 3 skipped
  each (the three e2e tests, which need the source tree and run separately). 3.8 and 3.9
  are below `requires-python`.

## QA lenses (item 19)

Independent reviews, one at a time, each reading the certification rules, running the
code and reporting only to the maintainer. Later rounds confirm the earlier findings and
sweep at most 40 new mutants on the code changed since the previous round.

| Lens | Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- | --- |
| a. API and docs | 1 | 4dafb9a | FAIL | GUIDE comparison claims (werkzeug, email, multipart) true only on build output; README said email has no builder and werkzeug is a framework; strict Accept message and position disagreed; several errors without position or pointing at the part start; decode_extended position counted after the prefix; quoted q read as a weight in default mode; get had no overloads; parameter names kept (published in 0.2.0, now promised in the GUIDE); fixed in dc951a0 |
| a | 2 | dc951a0 | FAIL | all ten confirmed; 40 mutants on the changed code, 4 survivors (q name trimmed with OWS only, second q not checked, non-ASCII position, get overload type); every q must now be well formed, contracts added in 6f1ca5b |
| a | 3 | 6f1ca5b | FAIL | 4 confirmed killed; 18 new mutants, 3 survivors (whitespace around q name and value), 1 equivalent dead clause removed; two GUIDE lines; fixed in 9c67400 |
| a | 4 | 9c67400 | PASS | 3 survivors killed, 7 new mutants all killed, GUIDE lines confirmed |
| b. Correctness and ground truth | 1 | 9c67400 | FAIL (minor) | 13 sources re-fetched (sha256 match); own WHATWG and RFC 9110 references written from the spec text: 400,000 parse inputs, 150,000 Accept headers, 106,610 quality pairs, 43,000 inputs against the Node.js reference, WPT 955/955, 0 mismatches; RFC examples, IANA names and properties pass; rules 10 and 13 hold. Findings: `build(extended=True)` wrote two fields for names equal without case when one value was encoded; a `*` inside a name could be read back as a section; 40 mutants, 1 survivor (us-ascii default of a plain first section), 1 equivalent; an imprecise test comment; fixed in 44efdc4 to d569d74 |
| b | 2 | d569d74 | PASS | fixes confirmed, property run 0 mismatches, 7 mutants on the changed code all killed |
| c. Adversarial and robustness | 1 | d569d74 | FAIL | 13.9 million fuzz cases on four seeds, 64 shapes at n/4n/16n, 10 MB and 100k inputs, recursion limit pass, free-threaded 3.14.2t with 4 threads (0 mismatches), 40 mutants all killed. Findings: a bare `ValueError` from default-mode Accept for `a/b;x=a"b;q="` (a quote inside an unquoted value hid the weight; introduced earlier in this round, never in 0.2.0); unbounded codec-cache growth from new charset names in `decode_extended`; quadratic `AcceptItem.matches`; an unprintable argument escaping as another exception; `q` subclass and `-0.0`, value subclasses stored as given; fixed in 34c2412 |
| c | 2 | 34c2412 | FAIL (minor) | all five confirmed (2.89 million new fuzz cases, 300,000 elements against an independent walk of the browser algorithm, codec cache growth 0, matching linear to 100k parameters, 20,792 charset names unchanged); 32 mutants, 1 survivor (a quoted value after a bare name), 7 equivalent; a weak charset test; fixed in 99a83ec |
| c | 3 | 99a83ec | FAIL (minor) | both survivors killed; 6 mutants on the changed line, 1 survivor (the name check bypassed for short names); short-name contract added in 0440066 |
| c | 4 | 0440066 | PASS | the last survivor killed by the full suite; no open survivors besides the argued equivalents |
| d. Packaging and real e2e | 1 | 0440066 | PASS (2 minor) | clean-clone wheel and sdist, `twine check --strict`, contents and metadata, consumer script with `mypy --strict` from the installed wheel, live PyPI 0.2.0 upgraded in place with all nine documented changes confirmed, sdist suite against the install (469 passed with fetched files, 435 passed and 37 clean skips without), every CPython here 3.10.19 to 3.14.2t (469 passed each), 3.8/3.9 refused; minor: a CHANGELOG entry described a crash that never shipped, `release.ps1` refused any upload once the name existed; fixed in a1744aa |
| d | 2 | a1744aa | PASS | both confirmed against PyPI 0.2.0; release script check run alone in PowerShell 5.1 and 7; rebuilt wheel byte-identical, `twine check --strict`, sdist suite 469 passed |
| e. Contract strength (blind) | 1 | a1744aa | FAIL | 146 own mutants over all 13 modules, full suite each (fetched sources, werkzeug, multipart, Node.js reference, 0.2.0 oracle): 132 killed, 5 argued equivalent (E1, B2, R2, A3, A17), 9 missing contracts (message cut boundary, vertical tab before the type, CR/LF around a built media type, second hex digit, utf-8 bytes after a plain first section, charset name syntax, which plain duplicate wins, a newline in an encoded value, strict position of an out-of-range weight); contracts added in 689add2, the duplicate rule documented in c3707df |
| e | 2 | c3707df | PASS | all 9 now killed by `tests/test_contract_edges.py`; 141 of 146 killed, the other 5 equivalent |

## Independent review (item 16)

| Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- |
| 1 | fa87e41 | PASS (minor) | 18 items PASS, 17 pending; 9 author mutants re-run and killed; tampered fetched files make the tests fail; minor: report over 200 lines, an `email` wording, public classes reporting private modules (pickles depending on them), the CHANGELOG date, the release script building from a dirty tree; fixed in 0a8358e and 4e23a0f |
| 2 | 4e23a0f | PASS | all five confirmed; 15 mutants on the changed code, 13 killed, 2 harmless (one pinned in a later test) |

## Gates (item 15)

At 0a8358e on the laptop from a fresh clone, each command on its own, with the fetched
sources, werkzeug, multipart, the 0.2.0 oracle, `MEDIAPARSE_E2E=1` and
`MEDIAPARSE_E2E_PYPI=1`: `ruff format --check .`, `ruff check .`, `mypy --strict src`,
`mypy --strict src tests` and `pytest` (512 passed, 4 skipped: the Node.js reference,
not installed there) all exit 0. The reviewer repeated them at 4e23a0f (exit 0). On this
PC with the Node.js reference present the suite has no skips besides the opt-in e2e tests.
