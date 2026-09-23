# Implementation Plan: Prune test output from the portal output scan

**Branch**: `fix/3201-scan-prune-test-artifacts` | **Date**: 2026-09-23 | **Spec**: [spec.md](./spec.md)

## Summary

After every operation, `OperationExecutor._capture_and_run` asks `OutputFileScanner.changed_files()` which files the run wrote. The scanner walks the data folder with `os.walk` and prunes the folder names in `EXCLUDED_DIR_NAMES`. That list prunes `portal-test-artifacts` but not `test-artifacts`. The upgrade portal suites write `data/test-artifacts/upgrade-portal/`, which grew to 1,520 folders, so each walk lists every one of them.

## Root cause

| Fact | Evidence |
| - | - |
| The walk skips only the names in `EXCLUDED_DIR_NAMES` | `web_portal/services/output_scan.py`, `_walk()` |
| `test-artifacts` is absent from that list | `EXCLUDED_DIR_NAMES` before this change |
| Three test modules write under `data/test-artifacts` | `tests/e2e/upgrade_portal/conftest.py:91`, `tests/unit/upgrade_portal/test_runs/test_isolation.py:142`, `tests/unit/benchmarks/test_capture_concurrency_benchmark.py:17` |
| A fourth module writes `data/test-control-byte-guard` | `tests/unit/test_markdown_control_bytes.py:16` |
| The cost is the folder listings, not the files | 129 files but 1,522 folders. The walk of that tree alone took 67.2 seconds. |

## Design

1. Add `test-artifacts` and `test-control-byte-guard` to `EXCLUDED_DIR_NAMES`, each with its reason.
2. Publish `last_walk_directories`, the count of folders that the most recent walk listed. A test that reads only the result panel cannot tell a real prune from a filter after the descent. The count can.
3. Add a drift guard that reads every test module and requires the prune for each `data/` folder whose name carries the word part `test`.

## Technical context

- Python 3.13. Standard library only. No new dependency.
- The existing test module `tests/unit/web_portal/test_output_scan_runtime_files.py` already holds the prune tests of issue #3140. The new tests join it.

## Risks

| Risk | Control |
| - | - |
| A real report lands in a pruned folder | No operation writes into a test output folder. The drift guard applies only to names that mark themselves as test output. |
| The drift guard regex stops matching | The guard fails if it reads fewer than 500 modules or finds fewer than 3 folders. |
| The count attribute changes the public surface | It is a read-only integer with a default of zero. No caller depends on its absence. |

## Constitution check

- Explicit over implicit: each pruned name carries its reason and its issue.
- Safe over fast: the prune list still omits `per-host-logs`, and an existing test enforces that.
