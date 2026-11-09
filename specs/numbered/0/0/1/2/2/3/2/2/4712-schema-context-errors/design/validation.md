# Validation: Schema context errors

## Environment and Isolation

The base commit is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
The local `origin/main` reference resolves to that commit.
The interpreter is Python 3.14.7.
The locked environment restoration used `uv run --offline --locked --extra dev python -c 'import pytest; print(pytest.__version__)'`.
It reported pytest `9.2.0`.
No bootstrap, credential change, or Git configuration change occurred.

A session-owned `run_offline_tests.py` blocks socket creation, DNS, socket connections, and SQLite connections before repository imports.
It uses `--noconftest -p no:cacheprovider -q`.
This prevents the root fixture from importing the MistHelper entry point.
It leaves test assertions unchanged.

## Regression Evidence

The new test file contains 19 parameterized cases.
Against the original committed source, it reports `8 failed, 11 passed, 1 warning`.
The failures cover logging in a real inventory context, six injected frame or logging failures, and cleanup during an exception.
The original source loads from its Git object without modifying the working source.

The corrected source and five complete test files report `104 passed, 1 warning in 0.53s` in the final run.
The files are:

- `tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py`
- `tests/unit/db/test_database_schema_utils.py`
- `tests/unit/db/test_retention_redis_scan.py`
- `tests/unit/db/test_sqlite_database_writer_logging.py`
- `tests/unit/db/sle_window_summary/test_export_identity.py`

No test skipped.
The warning concerns the existing Dash pytest plugin and its deprecated hook declaration.
The schema cases cover normal detection, all six patterns, nearest matching frames, legitimate unknown results, unchanged inventory strategy, exception identity, and cleanup.

## Static Checks

The Python checks apply to the source file, the new test file, and the handed-off legacy test where applicable.

| Command | Result |
| - | - |
| `python -m py_compile` with all three Python paths | Passed with no output |
| `python -m ruff check` with all three Python paths | `All checks passed!` |
| `python -m black --check` with all three Python paths | Three files unchanged |
| `python -m mypy src/foundation/persistence/db/database_schema_utils.py --config-file pyproject.toml` | No issues in one source file |
| `bandit -c pyproject.toml src/foundation/persistence/db/database_schema_utils.py -q` | Passed with no findings |
| `radon cc src/foundation/persistence/db/database_schema_utils.py -j` through `complexity-gate --max 10` | All functions within the threshold |
| `pydocstyle src/foundation/persistence/db/database_schema_utils.py` | Passed with no output |
| `interrogate src/foundation/persistence/db/database_schema_utils.py --fail-under 90` | 100 percent |
| `pylint src/foundation/persistence/db/database_schema_utils.py --fail-under=9.5 --score=y` | 10.00/10 |
| `symbol-diff --base HEAD src/foundation/persistence/db/database_schema_utils.py` before commit | No module-level name changed |
| `git diff --check` | Passed with no output |

The isolated `TestLiveGuides` preflight reports `1 passed, 1 warning`.
The initial test-quality check examined one new test file and reported no new findings.
The five initial Markdown records passed STE with scores of 86 through 98.
The route check examined 12 directories and found no directory above five children.

## Limitations

An exploratory recursive database unit run reports `8 failed, 104 passed, 5 warnings`.
Eight backend-preservation cases require temporary SQLite access or DNS.
The guards blocked those operations.
The failures do not establish a defect in this repair.
Do not report that broader run as passed.

No live Mist, SSH, firmware, TUI, or production database operation ran.
The full repository suite did not run.
PowerShell was unavailable, so the route calculation used the documented base-5 algorithm locally.
The source repair removes two executable lines and no production declaration.
The legacy test update follows the exclusive handoff from the owner of draft #4358.
Its later authorized rename must retain the repaired assertion.

## Artifact Consistency

All five functional requirements map to T004 through T006.
T001 through T003 establish ownership and isolation.
T007 and T008 document and preserve the result.
T009 updates the handed-off test.
The analysis found no unresolved behavior conflict.
