# Implementation Plan: Preserve CSV Carriage Returns

**Branch**: `fix/4776-csv-carriage-returns` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The shared normalizer removes carriage returns from text values. This plan keeps them in the normalizer. A new CSV presenter shows each carriage return as a backslash and the letter `r`, and only CSV writers use it. Every CSV writer that receives normalized rows uses the presenter. SQLite and polyglot outputs keep raw carriage returns.

## Technical Context

- **Language and Version**: Python 3.15 or newer (RC-71).
- **Primary Dependencies**: Standard library `csv`. Existing `DataProcessingUtils` and `DataExporter`. No new dependency.
- **Storage**: CSV files under `data/`, and SQLite file `data/mist_data.db`.
- **Testing**: pytest with `tmp_path`. Local gates from the table at RC-38.
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Python operations tool with numbered menu operations.
- **Performance Goals**: None. The change copies each CSV row once.
- **Constraints**: Five-item rule (RC-40). Functions at 25 lines or fewer. ASCII log text. No new child in a noncompliant parent (RC-03, RC-09, RC-15, RC-64, RC-66).
- **Scale and Scope**: Five source files, two of them new. Six test files, one of them new. One changelog fragment.

## Constitution Check

*GATE: Passed before Phase 0 research. Passed again after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. New folder children at five or fewer | PASS | `src/foundation/models` holds four children (RC-63). The new package adds one child, which makes five. The new package holds two children. |
| I. No new child in a noncompliant parent | PASS | No method is added to `DataProcessingUtils` (RC-03), `DataExporter` (RC-09), or `DeviceEvents52wExporter` (RC-15). No file is added to `src/foundation/models/data` (RC-64) or `tests/unit/export` (RC-66). |
| I. Function limits | PASS | `write_to_csv` stays at 25 lines because one line changes (RC-04). New methods hold at most two parameters and at most 25 lines. |
| I. Existing violations touched | PASS with debt | Three classes and two folders already exceed the limit. Each one is listed in Complexity Tracking with remediation R-1 and R-2. |
| I. Spec route | PASS | The route base is 5 with eight segments (RC-51). Route parent `3/1/0` holds one child, so the new child makes two (RC-52). The leaf is absent (RC-53). |
| I. Required process records | PASS | One changelog fragment joins `changelog.d/`, which the constitution permits as a required unique record. |
| II. Class-based architecture | PASS | The new presenter is a class. No wrapper function is added. |
| III. Safety-first input | PASS | No keyboard read or destructive operation is added. |
| IV. Full deployment pipeline, steps 1 to 9 | PASS | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. |
| IV. Full deployment pipeline, steps 10 to 12 | PASS with owner | The orchestrator owns the main build, the revision check, and the deployment after T-MERGE (D-13, U-1). |
| V. ASCII log text | PASS | The presenter log text uses ASCII only. T015 checks this rule. |
| VI. Inline comments | PASS by task | Each new executable line carries a same-line comment. T015 checks this rule. |
| VII. Action logging | PASS by task | `prepare_rows` writes an info log before the copy and a debug log after it. T015 checks this rule. |
| Technology. Mist REST calls | PASS | No Mist request changes. Neither changed module references mistapi (RC-61, RC-62). |
| Technology. Output backends | PASS | The write path still starts at `DataExporter.write_with_format_selection` (RC-49). |
| Technology. Database keys | PASS with risk | Key fields are not changed by the presentation. Key strategy fields are not read in this record (R-10, U-6). |
| Technology. Data directory | PASS | Tests use `tmp_path`. Product outputs stay under `data/`. |
| Technology. Containers | PASS, not applicable | No container starts in this change. If a test container starts, the policy at RC-50 applies. |
| Technology. File paths | PASS | The change adds no path join by hand. |
| Development workflow. Release note | PASS | The fragment follows D-9 and FR-009. |
| Development workflow. README | PASS with decision | No README change is made. Decision D-10 gives the reason. |
| Escalation | PASS | This record exists because the change touches more than three files and two classes. |
| Multi-agent. Labels and claim | PASS | The issue already carries `bug`, `MistHelper.py`, and `in-progress` (D-14). |
| Multi-agent. File overlap | PASS with action | T-PR checks open pull requests for overlap on the changed files before the push. |
| Multi-agent. Hot file | PASS | `MistHelper.py` is not changed. |
| Multi-agent. Branch name | PASS | The branch is `fix/4776-csv-carriage-returns` (RC-43, RC-44). |
| AGENTS.md. Writing style | PASS | This record follows the writing rules. The validator checks forbidden tokens and semicolons. |

## Architecture

```text
Exporter -> DataExporter.write_with_format_selection -> write_to_csv
  -> CsvCellPresenter.prepare_rows (copy, escape_multiline, present carriage returns)
  -> csv.DictWriter

Exporter -> SQLiteDatabaseWriter -> escape_multiline (carriage returns kept) -> SQLite row

DeviceEvents52wExporter CSV branch -> escape_multiline (kept) -> CsvCellPresenter.present_carriage_returns -> csv.DictWriter
DeviceEvents52wExporter SQLite branch -> escape_multiline (kept) -> SQLite batch
```

## Change Map

| Path | Action | Change |
| - | - | - |
| `src/foundation/models/data/data_processing_utils.py` | Modify | Keep carriage returns in `escape_multiline`. Update the docstring at lines 157 to 161 and the inline comment at line 167. |
| `src/foundation/models/csv_presentation/__init__.py` | Add | Package marker with a one-line documentation comment. |
| `src/foundation/models/csv_presentation/cell_presenter.py` | Add | Class `CsvCellPresenter` with `prepare_rows` and `present_carriage_returns`. |
| `src/operations/exporting/export/data_exporter.py` | Modify | Import `CsvCellPresenter`. Replace line 408 with `prepare_rows`. Remove the type-ignore comment on that line. |
| `src/operations/exporting/export/device_events_52w_exporter.py` | Modify | Import `CsvCellPresenter`. Present rows in the CSV branch of `_write_initial_batch` (lines 312 to 314) and of `_append_rows` (lines 327 to 328). |
| `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py` | Modify | Replace the removal assertion at lines 262 to 267 with the preservation assertion. |
| `tests/unit/config/foundation/models/dataproc/test_csv_cell_presenter.py` | Add | Presenter tests (T004). |
| `tests/unit/export/test_data_exporter.py` | Modify | Add CSV cell, raw row, list, non-CSV dispatch, and double-presentation tests (T005, T008). |
| `tests/unit/db/sle_window_summary/test_backend_preservation.py` | Modify | Add the SQLite raw carriage return test (T007). |
| `tests/unit/test_device_events_52w_exporter_extended.py` | Modify | Add the 52-week CSV and SQLite tests (T006). |
| `tests/unit/export/test_endpoint_family_exporter.py` | Modify | Keep carriage returns in the expected notes at lines 687 and 692 (T009). |
| `changelog.d/issue-4776-csv-carriage-returns.md` | Add | One heading and one `Fixed` bullet (T014). |
| `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/` | Add | This record. T-PR adds it to the pull request. |

## Implementation Order

1. Write the test tasks T003 to T009. Run them on `main`. Each new carriage return assertion must fail.
2. Implement T010 to T013. Run the focused test files named in `quickstart.md`.
3. Add the changelog fragment (T014). Review comments, logs, and function limits (T015).
4. Run T-LOCAL-GATES. Then T-PR, T-REMOTE-CI, and T-MERGE.

## Complexity Tracking

| Existing violation | Evidence | Why it stays | Simpler alternative rejected | Remediation |
| - | - | - | - | - |
| `DataProcessingUtils` holds 11 methods | RC-03 | The shared normalizer lives in this class | A new method adds a child to a noncompliant class | R-1 |
| `DataExporter` holds 27 methods | RC-09 | The CSV writer lives in this class | A new method adds a child to a noncompliant class | R-1 |
| `DeviceEvents52wExporter` holds 25 methods | RC-15 | The 52-week writer lives in this class | A new method adds a child to a noncompliant class | R-1 |
| `src/operations/exporting/export` holds 49 children | RC-65 | The exporters live in this folder | A new file here adds a child to a noncompliant folder | R-2 |
| `tests/unit/export` holds 55 children | RC-66 | The export tests live in this folder | A new test file here adds a child to a noncompliant folder | R-2 |
| `src/foundation/models` reaches five children | RC-63 | The presenter package needs a compliant parent | A module in `src/foundation/models/data` breaks the limit (RC-64) | R-3 |

Remediation actions:

- R-1: After merge, open one remediation issue. Split the three classes into compliant classes. The orchestrator owns this issue.
- R-2: After merge, open one remediation issue. Split the two folders into nested packages.
- R-3: Before any new package in `src/foundation/models`, choose another compliant parent or split the folder.

## Dependencies

No package is added. The change uses the standard library `csv` module. It uses these internal symbols: `DataProcessingUtils`, `DataExporter`, `DeviceEvents52wExporter`, and `SQLiteDatabaseWriter` (RC-10).

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| R-01 | New database rows keep carriage returns. | Caution: existing rows do not change. T007 tests the SQLite raw value. The release note names the change. |
| R-02 | The 52-week CSV shows raw carriage returns if its branch is skipped. | T006 and T013 cover the branch. |
| R-03 | A caller reads its rows after a write and expects escaped text. | D-4 copies rows. Checked callers escape before writing (RC-17). The full test run covers the rest. |
| R-04 | Existing 52-week tests inject a `MagicMock` for `data_processing_utils` (RC-23). | `CsvCellPresenter` is static and is not injected. The mock does not reach the presenter. |
| R-05 | The symbol gate reports the new import as a changed module-level name. | Record the added names in the pull request body. The gate's purpose is to detect lost names. |
| R-06 | `src/foundation/models` reaches its limit. | R-3 applies before any further package is added. |
| R-07 | Issue #4773 routes EX rows through the shared path later. | U-2 requires an owner review before that change merges. |
| R-08 | The full test run takes a long time on Windows. | Run T-LOCAL-GATES once. Plan the time before the run. |
| R-09 | Two open pull requests confuse reviewers for a short time. | Close PR #4813 after the new branch is pushed, with a preservation proof (D-8). |
| R-10 | A primary key field holds free text, so a carriage return changes a key. | Warning: check each key field before T-PR. Stop the push if a key field holds free text. |

## Rollback Steps

1. Open a revert pull request for the squash commit. Do not push to `main`.
2. Run `python -m pytest tests/unit/export/test_data_exporter.py` after the revert. The old removal behavior returns.
3. Keep the stored rows as they are. Caution: rows written with carriage returns stay raw after the revert.
4. The revert removes `changelog.d/issue-4776-csv-carriage-returns.md` with the other files.
