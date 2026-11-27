# Implementation Plan: Menu 97 SQLite Write Status

**Branch**: `fix/4722-sqlite-partial-batch` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/2/3/4/2/4722-menu-97-sqlite-write-status/spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/3/4/2/4722-menu-97-sqlite-write-status/spec.md`. The route is the base-5 encoding of issue 4722, padded to eight digits.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Menu 97 treats a partial SQLite batch as a success. The SQLite writer returns True when at least one row inserts. This plan adds an opt-in full-batch flag to SQLite writes. With the flag, the writer discards any batch that has a rejected row and returns False. The 52-week exporter sets the flag on every SQLite write. Remote main already stops on a False result, and this plan keeps that behavior.

## Technical Context

**Language/Version**: Python 3.15 or newer. `.github/copilot-instructions.md` line 20 names this version.

**Primary Dependencies**: mistapi 0.64.1, pinned as `>=0.64.0,<0.65`. The Python standard library `sqlite3` module provides the storage driver.

**Storage**: The SQLite file `data/mist_data.db`, written by `SQLiteDatabaseWriter`. The checkpoint file `data/OrgDeviceEvents_52w.<org_id>.checkpoint` holds the continuation token.

**Testing**: pytest with `tmp_path` and `monkeypatch`. The gates include Ruff, Black, mypy, pylint, vulture, pydocstyle, interrogate, radon, and bandit.

**Target Platform**: Windows 11 for local runs. macOS and Linux also run the code. The product ships as a Podman container.

**Project Type**: Command-line and web tool. The entry point is `MistHelper.py`.

**Performance Goals**: No change. The flag adds no API request and no extra table query.

**Constraints**: The five-item rule. Simplified Technical English for prose and log messages. ASCII-only log output. No secret in a log. An inline comment on each new line. An action log before and after each new action.

**Scale/Scope**: One batch for each API page. The exporter requests pages of 1000 events, set by `_DEFAULT_LIMIT` at `src/operations/exporting/export/device_events_52w_exporter.py` line 24. The OpenAPI file lists a default of 100 and no maximum. See Unverified item U-3 in `design/research.md`.

## Constitution Check

The check uses the principles in `.specify/memory/constitution.md`. Line numbers refer to the remote file.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (line 38) | Pass with recorded debt | No direct child is added to a noncompliant directory. Two classes gain one method each. Both already exceed five methods. See touched violations below. |
| II. Class-based architecture (line 91) | Pass | Every change stays in an existing class. Helpers are methods of the owning class. |
| III. Safety-first (line 113) | Pass | The change adds no external input and no confirmation prompt. It logs no credential. |
| IV. Full deployment pipeline (line 143) | Pass with owner step | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 through 9. Steps 10 through 12 need the owner. The agent does not deploy. |
| V. Observability and logging (line 182) | Pass | New log lines use ASCII. They carry the table name and row counts only. |
| VI. Inline comments (line 204) | Pass | Each new executable line carries a same-line comment that gives its purpose. |
| VII. Action logging (line 235) | Pass | The new rejection path logs an info line before the rollback and a debug line after it. |
| Technology: mistapi (Technology section) | Pass | The REST call stays `searchOrgDeviceEvents` in mistapi. No direct HTTP request is added. |
| Technology: output backends (line 312) | Pass | Full-batch writes still pass through `DataExporter.write_with_format_selection`. |
| Technology: operational store (line 315) | Not applicable | The export stores API data, not internal coordination records. |
| Technology: export boundary (line 320) | Pass | The flag is opt-in. The backend path stays the same. |
| Technology: database keys (line 322) | Pass | No key changes. The key collapse belongs to issue 4723. |
| Technology: data directory | Pass | Tests use `tmp_path`. Product output stays under `data/`. |
| Technology: container security | Not applicable | The change edits no container file. |
| Development: adding menu operations | Not applicable | The change adds no menu and no registry row. |
| Development: testing (line 361) | Pass with gates | Every applicable local gate runs in T-LOCAL-GATES. |
| Development: documentation (line 398) | Pass with reason | The README and the operator guide hold no text about menu 97 write results. The release fragment records the change. |
| Audience standard | Pass | The new log message uses plain words for a junior engineer. |

### Touched Existing Violations

- `DataExporter` in `src/operations/exporting/export/data_exporter.py` has more than five methods. This plan adds one static method.
- `SQLiteDatabaseWriter` in `src/foundation/support/refactors/sqlite_database_writer.py` has more than five methods. This plan adds one method.
- `DataExporter.write_with_format_selection` spans 28 lines. The limit is 25 lines. This plan adds lines to it.
- The directories `tests/unit/export` (55 children) and `tests/integration` (26 children) are noncompliant. This plan adds no file to either directory.

### Separate Remediation Actions

These actions are incremental. This record does not file them. The orchestrator decides when to file them.

- R-1: Split `write_with_format_selection` into smaller helpers.
- R-2: Move the SQLite full-batch dispatch into a compliant module.
- R-3: Split the methods of `SQLiteDatabaseWriter` into compliant helper modules.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/4/2/4722-menu-97-sqlite-write-status/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
    checklists/
```

### Source Code (repository root)

```text
src/foundation/models/dataclasses/export_backend_options.py
src/foundation/support/refactors/sqlite_database_writer.py
src/operations/exporting/export/data_exporter.py
src/operations/exporting/export/device_events_52w_exporter.py
tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py
tests/unit/export/test_data_exporter.py
tests/unit/test_device_events_52w_exporter_extended.py
changelog.d/issue-4722-partial-batch.md
```

**Structure Decision**: The change edits four existing source modules and three existing test modules. It adds one changelog fragment. No new source module and no new test module is added.

## Architecture

The full-batch request flows from the exporter to the writer, and the writer decides the result.

```text
DeviceEvents52wExporter._write_sqlite_batch
  -> DataExporter.write_with_format_selection (format_override sqlite, require_full_batch true)
     -> DataExporter._write_full_batch_sqlite (new static method)
        -> DataExporter._write_sqlite_format (new require_full_batch argument)
           -> SQLiteDatabaseWriter.write (require_full_batch)
              -> _execute_database_operations -> _insert_all_rows -> _finish_batch
                 -> commit when every row is stored
                 -> _reject_partial_batch (new method) discards the batch and returns False
```

## File-by-File Change Map

| Path | Action | Change | Requirements | Tasks |
| - | - | - | - | - |
| `src/foundation/models/dataclasses/export_backend_options.py` | modify | Add `require_full_batch: bool = False` and list it in the module docstring. | FR-004, FR-006 | T010 |
| `src/foundation/support/refactors/sqlite_database_writer.py` | modify | Add the `require_full_batch` argument to `write`, `_execute_database_operations`, and `_finish_batch`. Add `_reject_partial_batch`. | FR-004, FR-005, FR-007 | T011 |
| `src/operations/exporting/export/data_exporter.py` | modify | Add the full-batch branch in `write_with_format_selection`. Add `_write_full_batch_sqlite`. Add the `require_full_batch` argument to `_write_sqlite_format`. | FR-004, FR-008 | T012 |
| `src/operations/exporting/export/device_events_52w_exporter.py` | modify | Set `require_full_batch=True` in the options of `_write_sqlite_batch`. | FR-006 | T013 |
| `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` | modify | Add TC-01 through TC-04 after the last test. | FR-004, FR-005 | T006 |
| `tests/unit/export/test_data_exporter.py` | modify | Add TC-05 through TC-07 in a new test class at the end. Start after PR #4813 merges. | FR-008 | T007 |
| `tests/unit/test_device_events_52w_exporter_extended.py` | modify | Add TC-08 through TC-11 at the end of the module. | FR-002, FR-003, FR-004, FR-005, FR-006 | T008, T009 |
| `changelog.d/issue-4722-partial-batch.md` | add | One fragment with a heading and a Fixed bullet that names issue 4722. | FR-010 | T014 |

No documentation file changes. The README and the operator guide hold no text about menu 97 write results. The fragment carries the operator-visible change.

## Dependencies

- No package changes. The mistapi pin stays at 0.64.1 in `requirements.txt`. The change uses only the standard library.
- Sequencing dependency: open PR #4813 changes `src/operations/exporting/export/data_exporter.py` and `tests/unit/export/test_data_exporter.py`. Task T001 checks this overlap before any edit.
- Coordination: issues #4721 and #4723 share the menu 97 exporter file and the key strategy. Keep one owner for each file.

## Design Decisions

The decisions are recorded in `design/research.md` as D-1 through D-10. The main choices are these.

- The writer gets an opt-in flag. The default result for other callers does not change.
- A rejected full-batch write discards the whole batch. It does not keep the rows that did store.
- The DataExporter branch uses a new helper. It does not add a sixth argument to `_dispatch_format_write`.
- The writer receives the flag as a keyword argument on `write`. It does not change `__init__`, which is 24 lines long.

## Contracts

Three contract files under `design/contracts/` define the interfaces:

- `design/contracts/writer-full-batch.md` defines the writer argument and results.
- `design/contracts/export-backend-options.md` defines the new option field.
- `design/contracts/device-events-52w-sqlite-write.md` defines the exporter call, the failure text, and the checkpoint rules.

## Risks and Mitigations

- Caution: PR #4813 changes `data_exporter.py`. Mitigation: task T001 checks the overlap. T-PR starts after #4813 merges, or after the owner gives a handover.
- Caution: the polyglot mirror can store rows from a discarded SQLite batch. Mitigation: the next successful run sends the same rows again. The mirror upsert is unverified (research U-6). Decision D-9 keeps the mirror behavior.
- Caution: a new SQLite caller that omits the flag can reintroduce the partial success. Mitigation: TC-08 checks the exporter calls. Future callers need their own tests.
- Caution: the trigger in TC-10 might not reject a row on every SQLite build. Mitigation: TC-10 asserts the outcome, and a missing rejection fails the test. Do not weaken the assertion.
- Caution: under the current code, a partial batch shows a success message. The lost rows stay missing until the next manual run. The change removes this result.
- Warning: a fresh CSV run replaces the CSV file. Issue #4721 owns the CSV resume path. This record does not change that path.
- Caution: the Mist API `next` value might be a URL, not a cursor. The exporter passes it unchanged. This record does not change the pagination. Analysis item A-8 records the open question.

## Rollback Steps

1. Revert the merge commit on `main` with a new pull request. Do not force-push `main`.
2. Run the existing writer test for the default partial result. It must pass after the revert.
3. The SQLite table needs no migration. The flag never changes the stored table shape.
4. Checkpoint files keep their format. An operator needs no manual step.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `DataExporter` gains one static method in a noncompliant class | The full-batch branch needs the same exception handling as `_dispatch_format_write`. | An inline try block makes `write_with_format_selection` longer. The sixth-argument option on `_dispatch_format_write` breaks the five-argument rule and test line 170. |
| `write_with_format_selection` stays over 25 lines | The branch chooses the full-batch helper. | The existing function already spans 28 lines. Splitting it is remediation R-1, which is outside this change. |
| `SQLiteDatabaseWriter` gains one method in a noncompliant class | The rejection path needs its own method to keep `_finish_batch` under 25 lines. | An inline branch makes `_finish_batch` 26 lines or longer. |
