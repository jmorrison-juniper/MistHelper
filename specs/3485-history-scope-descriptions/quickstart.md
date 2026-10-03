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
rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -m pytest -q --browser chromium \
  --tracing off --screenshot off --video off \
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
Use only the parent's explicit granted base before publication.
The current grant names `92dc5d3ebf5fa6d2b9ddba536b5c3bc6cd4ca232`.
Do not publish if live main changes without a new grant.

## Recorded local results

The exact granted-base archive fails all 27 original cases across the nine rendered descriptions.
The repaired focused matrix passed 970 cases with no failures or skips.
The Chromium history matrix passed 35 cases with no failures or skips.
All 33 statements and both branches of the new view model have coverage.
Both added executable lines of the history context wiring have coverage.
The complete `review.py` coverage is 96.25 percent.
The complete audit reader coverage is 100 percent.
Combined statement coverage is 96.86 percent.
Combined statement and branch coverage is 96.09 percent.
The review reader covers 89 of 100 branches.
The audit reader covers all 24 branches.

The full Ruff gate passed.
The full Black gate checks 2,034 Python files.
The exact CI mypy scope checks 666 files.
Full Bandit checks 789 files and 215,196 lines with no findings or scan errors.
The unchanged default test-quality ratchet checks 1,014 files and finds no new finding.
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
All 35 new test methods obey the 25-line and five-parameter limits.
The symbol comparison reports no lost module-level name.
It reports the genuine `HistoryCardDescription` and `HistoryCardScope` additions.
The new module also imports `annotations` and `dataclass`.
The route imports `HistoryCardScope`.
The CLI cannot read a new file from the older base tree.
The comparator API checks the new file after Git confirms its absence from that tree.
Its verdict is 1 for the intentional additions, not an unchanged-name result.

The parent authorized a dedicated semantic module to resolve structural finding C1.
The repeated checks above apply to the exact granted-base branch.
Strict collection measures all 603 CI browser cases with zero import skips.
It preserves all 600 accepted cases and adds only the three required history cases.
The 37 current strict-package, owner-header, and process-owner checks pass.

The native browser receipt measures three required cases, one real fixture identity, and one owned server.
It confirms the actual `magenta` and `default` theme choices.
Trace, screenshot, and video options remain off for the required journey.
The owned journey adds no direct conftest import or unconditional screenshot write.
The existing shared journeys still save their documented manual screenshots.
Those screenshots do not determine the required journey's correctness.

The receipt confirms that the server process stopped, its port closed, and its owner record was removed.
The checkout audit trail remains empty.
The live-run guard reports no leaked run.

Run the six-input and three-guide preflight before both test-quality commands.
Run the changed-scope command on clean committed content against the intended current base.
Its current local equivalent uses the granted immutable SHA and both configured full-gate paths.
Use the default command, without scope controls, for the complete suite.
No guide, baseline, exclusion, dictionary, or dependency change is necessary.
