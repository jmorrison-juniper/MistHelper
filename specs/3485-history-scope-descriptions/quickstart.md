# Validation: History scope descriptions

## Prerequisites

Use Python 3.13 or newer in this worktree's own `.venv`.
Install the current requirement files only when tools are missing.
Use the existing bootstrap and Chromium download.
Do not use production credentials or start a container.

## Focused checks

Run the dedicated scope cases.

```bash
rtk proxy .venv/bin/python -m pytest -q \
  tests/unit/upgrade_portal/test_history_card_scope.py \
  tests/contract/upgrade_portal/test_history_card_scope_routes.py
```

Run the real browser journey.

```bash
rtk proxy .venv/bin/python -m pytest -q --browser chromium \
  tests/e2e/upgrade_portal/test_history_card_scope_journey.py
```

The first command must verify all nine descriptions for both scopes.
The browser command must verify site and organization history without a required skip.

## Existing behavior

Repeat the existing history, organization isolation, pagination, attribution, and authentication cases.
Inspect exact record identifiers and totals, not only page status.
Compare every reader and query body with the starting revision.

## Local gates

Run the configured full Ruff and Black checks.
Read the exact mypy scope from `.github/workflows/ci.yml`.
Run configured Bandit and the unchanged test-quality ratchet.
Run the configured link and STE checks on the owned documentation and changed prose.
Record exact commands and results before the local commit.

If STE reports `dictionary_unavailable`, record partial word grading.
Do not replace its dictionary or change its configuration.

## Publication

Commit only the reserved files.
Report the commit SHA and local evidence to the parent.
Do not push or create a pull request before the explicit publication grant.

## Recorded local results

The original rendered route failed all 27 cases across the nine descriptions.
The repaired focused matrix passed 970 cases with no failures or skips.
The Chromium history matrix passed 35 cases with no failures or skips.
All 33 statements of the new view model have coverage.
Both added executable lines of the history context wiring have coverage.
The complete `review.py` coverage is 96.25 percent.
The complete audit reader coverage is 100 percent.
Combined coverage is 96.86 percent.

The full Ruff gate passed.
The full Black gate checked 2,004 Python files.
The exact CI mypy scope checked 664 files.
Full Bandit checked 787 files and 214,004 lines with no findings or scan errors.
The unchanged test-quality ratchet checked 995 files and found no new finding.
All three new test modules have no finding.
The link check scanned nine Markdown files and found no broken local link.
The configured STE heuristics passed for 14 files.
Word grading remains partial because `data/ste_dictionary.json` is unavailable.
No dictionary, configuration, baseline, or exclusion changed.

The normal requirements audit aborted during macOS temporary-environment `ensurepip`.
The complete hashed Linux graph contains 107 runtime pins and 2,087 artifact hashes.
Its strict audit found no known vulnerability.

```bash
rtk proxy uv pip compile requirements.txt --python .venv/bin/python \
  --python-platform linux --generate-hashes --quiet --output-file <session-runtime-requirements>
rtk proxy .venv/bin/python -m pip_audit -r <session-runtime-requirements> \
  --require-hashes --no-deps --disable-pip --strict --progress-spinner off --timeout 30
```

The installed-package strict audit cannot measure the Git-only `misthelper-devtools` package through PyPI.
It reports that version 0.6.0 is unavailable there.
This limitation does not reduce the complete runtime graph audit.

AST comparisons confirm that 66 other route and reader bodies remain unchanged.
Only the history page context wiring changes.
The complete existing scope class remains unchanged.
All 36 new test methods obey the 25-line and five-parameter limits.
The symbol comparison reports no lost module-level name.
It reports the genuine `HistoryCardDescription` and `HistoryCardScope` additions.
The new module also imports `annotations` and `dataclass`.
The route imports `HistoryCardScope`.
The CLI cannot read a new file from the older base tree.
The comparator API checks the new file after Git confirms its absence from that tree.
Its verdict is 1 for the intentional additions, not an unchanged-name result.

The parent authorized a dedicated semantic module to resolve structural finding C1.
The repeated checks above apply to that completed extraction.
No push or pull request occurred.
