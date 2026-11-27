# Implementation Plan: SQLite schema context errors

**Branch**: `fix/4712-schema-context-errors` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\2\3\2\2\4712-schema-context-errors\spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/3/2/2/4712-schema-context-errors/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The detector returns `unknown` after a local failure. The default strategy then applies to a table that has a configured endpoint strategy. The change removes the broad handler, so a local failure propagates. The exporter dispatch boundary then stops the write and logs the table and the format.

## Technical Context

| Item | Value | Source |
|---|---|---|
| Language | Python 3.15.2 or newer | `pyproject.toml` line 23 (row 25) |
| Typing | mypy strict for `src/` | `pyproject.toml` line 279 (row 26) |
| Lint and format | ruff and black, line length 120 | `pyproject.toml` line 202 (row 27) |
| Testing | pytest. Tests sit outside the mypy path list | `.github/workflows/ci.yml` line 93 (row 28) |
| Storage | SQLite file `data/mist_data.db`. No schema change | `documentation/operator-guide.md` line 752 (row 53) |
| Dependencies | None added. mistapi is not called by this change | row 62 |
| Scale | Two code files, one new test file, one updated test, two documents, one fragment, one record | spec.md |

## Constitution Check

Each rule has a result and a reason. Pass means the plan satisfies the rule. Fail means an existing violation remains. This change adds no violation.

| Rule | Result | Reason |
|---|---|---|
| I. Five-Item Rule, classes and methods | Fail (existing debt) | `DatabaseSchemaUtils` holds 14 methods (row 72). This change adds no method. A separate follow-up action splits the class. This plan does not create that issue. |
| I. Five-Item Rule, specs taxonomy | Pass | The record uses the managed root `specs/numbered/`. The route folder holds one child. The parent folder `0\0\1\2\2\3\2` holds three children after the change (row 36). |
| II. Class-based architecture | Pass | The change edits an existing method. It adds no wrapper function. |
| III. Safety-first | Pass | A local failure stops the write. No unvalidated name reaches the strategy step. No keyboard input changes. |
| IV. Full deployment pipeline | Pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 follow the merge in T-MERGE. |
| V. Observability | Pass | The new message uses ASCII text. The detector logs at debug level. The boundary logs at error level. |
| VI. Inline comments | Pass (planned) | Each changed line and each adjacent line in a changed block carries an inline comment. |
| VII. Action logging | Pass | The detector keeps its debug line after a match. The boundary logs the failure with the table and the format. |
| Technology: mistapi | Pass | No REST call changes (row 62). |
| Technology: packages | Pass | `requirements.txt` and `requirements-dev.txt` do not change. |
| Technology: containers | Not applicable | No container, port, or image changes. |
| Technology: file paths | Pass | Tests use `tmp_path`. The change joins no path string. |
| Technology: output backends | Pass | `DataExporter.write_with_format_selection` and its outputs do not change. |
| Technology: database keys | Pass | No key or strategy changes (row 15 stays as it is). |
| Technology: data directory | Pass | No output path changes. |
| Documentation: README | Pass (planned) | Task T009 adds two sentences (row 49). |
| Documentation: release note | Pass (planned) | Task T011 adds one fragment (row 50). |
| Workflow: issue first | Pass | Issue #4712 exists with the `bug`, `MistHelper.py`, and `in-progress` labels. |
| Workflow: branch | Pass (planned) | `fix/4712-schema-context-errors` from current `main` (D-10). |
| Workflow: file overlap | Pass | Open pull request #4813 changes `data_exporter.py` only. This plan does not touch that file. |
| Test rules | Pass | The change has a unit test (TST-4), an edge-case test (TST-2), and an integration test (TST-3). No production credential appears in a test. |
| Security findings | Pass | The blind handler ratchet stays clean (rows 16 and 17). No suppression comment is added. |
| Spec escalation | Pass | Three or more files and an unclear failure boundary require a specification. |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| `DatabaseSchemaUtils` exceeds five methods (existing) | The class predates this change. | Splitting the class changes many call sites and needs its own ownership reservation (analysis A-11). |

## Architecture

```text
Menu operation
  -> DataExporter.write_with_format_selection
     -> DataExporter._dispatch_format_write                 boundary: catches, logs, returns False (row 10)
        -> DataExporter._write_sqlite_format                writer call at line 386 (row 12)
           -> SQLiteDatabaseWriter.write                    calls the resolver at line 93 (row 6)
              -> SQLiteDatabaseWriter._resolve_api_function_name   detector runs only when unset, line 145 (row 7)
                 -> DatabaseSchemaUtils.determine_api_function_name_from_context   changed by this plan
              -> DatabaseSchemaUtils.get_endpoint_strategy   line 221 (row 9)
```

Failure path after the change: a local failure raises inside the detector. `SQLiteDatabaseWriter.write` does not catch it, so no directory, connection, or table work starts. `_dispatch_format_write` catches the error. It logs `Failed to write data to <table> in <format> format: <error>` and returns `False`.

## File Change Map

| Path | Action | Change |
|---|---|---|
| `src/foundation/persistence/db/database_schema_utils.py` | Modify | Delete lines 62 and 63, the `except` clause and its log call. Update the docstring at line 50. Update the comment on the fallback return at line 66. |
| `tests/unit/db/test_database_schema_utils.py` | Modify | Lines 55 to 67: expect `RuntimeError` with the message `frame introspection failed`. Update the docstring at line 56. Add inline comments to each changed line. |
| `tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py` | Add | Three regression tests, TST-1 to TST-3. |
| `README.md` | Modify | Add two sentences after the sentence at line 30. |
| `documentation/operator-guide.md` | Modify | Add one paragraph after the SQLite row at line 752. |
| `changelog.d/issue-4712-schema-context-errors.md` | Add | One `###` heading and one Fixed bullet that names issue #4712. |
| `specs\numbered\0\0\1\2\2\3\2\2\4712-schema-context-errors\` | Add | The record files from the draft folder: spec, plan, tasks, analysis, and design. |

No change: `src/foundation/support/refactors/sqlite_database_writer.py`, `src/operations/exporting/export/data_exporter.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `MistHelper.py`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.github/blind-exception-handler-baseline.json`, `.github/test-quality-baseline.json`, and `.specify/feature.json`.

## Test Plan

| ID | Test | File | Requirement | Red before the change |
|---|---|---|---|---|
| TST-1 | `test_logging_failure_in_matched_frame_propagates` | new file | FR-002 | Yes. The detector returns `unknown`. |
| TST-2 | `test_mid_walk_inspection_failure_propagates` | new file | FR-001 | Yes. The detector returns `unknown`. |
| TST-3 | `test_exporter_boundary_stops_sqlite_write_on_context_failure` | new file | FR-005 | Yes. The writer reaches the database connection. |
| TST-4 | `test_handles_stack_inspection_error` (updated expectation) | `tests/unit/db/test_database_schema_utils.py` | FR-001, FR-006 | Yes. The detector returns `unknown`. |

Test designs:

- TST-1: Define a function named `getOrgInventory` that returns the detector result. Patch `module.logger.debug` to raise `RuntimeError("synthetic logging defect")`. Assert that the call raises that error.
- TST-2: Patch `inspect.currentframe` to return a first frame named `ordinary`. Its `f_back` property raises `AttributeError("synthetic frame link defect")`. Assert that the call raises that error.
- TST-3: Define a function named `getOrgInventory` that calls `DataExporter._dispatch_format_write` with two rows, the table `widgets`, the format `sqlite`, and no API function name. Patch `module.logger.debug` to raise the synthetic logging error. Patch `sqlite_database_writer._resolve_runtime_dependencies` to return a namespace with the real `DatabaseSchemaUtils`, the real `DataProcessingUtils`, and a `DATABASE_PATH` under `tmp_path`. Patch `sqlite3.connect` with a `Mock`. Assert that the call returns `False`, that the mock records no call, and that caplog contains the ERROR message `Failed to write data to widgets in sqlite format`.
- TST-4: Wrap the call in `pytest.raises(RuntimeError, match="frame introspection failed")`. Update the docstring to say that the failure propagates.

Red check: before the source change, TST-1 to TST-4 fail, so the run shows four failures. After the source change, all four pass.

## Dependencies

- No new package, service, or port.
- Test tools: pytest fixtures `monkeypatch`, `caplog`, and `tmp_path`. Standard library `types.SimpleNamespace` and `unittest.mock.Mock`.
- Module imports for the new tests: `src.foundation.persistence.db.database_schema_utils`, `src.foundation.support.refactors.sqlite_database_writer`, `src.operations.exporting.export.data_exporter`, and `src.foundation.models.data.data_processing_utils` (row 83).

## Risks and Mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| R-1: An unnamed SQLite write stops on a local failure. | One table write is missing for that run. | The boundary logs one error line (row 11). README and operator guide text describe the behavior (D-7 and D-8). |
| R-2: Overlap with open pull request #4813. | A merge conflict in `data_exporter.py`. | This plan does not change that file. Repeat the overlap check in T001 and before push. |
| R-3: The later move of the legacy test drops the updated expectation. | A regression in the test expectation. | Issue #4142 must carry the updated expectation through the move (analysis item A-03). |
| R-4: The patched module logger affects other tests. | Test isolation failure. | `monkeypatch` restores each attribute after its test. Each test patches one attribute. |
| R-5: The publication hold lasts longer than the implementation. | The branch stays local for longer. | D-11. Check the base again before the pull request opens. |
| R-6: The candidate commits enter the branch by mistake. | A stale base and Python 3.14.7 evidence enter the change. | D-10. Create the branch from `main`. Do not cherry-pick `b4b81164`. |
| R-7: The five-item debt grows. | More methods land in `DatabaseSchemaUtils`. | This change adds no method. The follow-up action is recorded in the Constitution Check. |
| R-8: The test quality analyzer reports a finding. | The push gate fails. | The new tests use no bare `assert result`. The analyzer runs before push. |

Warning: do not drop, rewrite, or delete a table in `data/mist_data.db` during a repair or a rollback. Each table keeps the schema that earlier runs created. This change does not repair those tables.

Caution: a stopped write leaves no row for that run. Fix the cause first. Then run the operation again.

## Rollback

1. Revert the implementation commit on a new branch from current `main`. The revert restores the `unknown` fallback and the earlier test expectation.
2. Open a pull request for the revert. It follows the same local gates and the same checks.
3. Warning: do not delete `data/mist_data.db` during a rollback. The file holds the output of every run, and deletion cannot be undone.

No data migration applies. The schema of a table does not change in this feature.

## Project Structure

```text
specs/numbered/0/0/1/2/2/3/2/2/4712-schema-context-errors/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      schema-context-contract.md
    checklists/
      requirements.md
      security.md
```

Structure check: the feature root holds five children. `design/` holds five children. `contracts/` holds one file. `checklists/` holds two files. The route folder `0\0\1\2\2\3\2\2` holds one child.

Contracts: one contract file is included, because the detector return and raise behavior is an internal interface. No menu, CLI, output column, or Mist API request changes.
