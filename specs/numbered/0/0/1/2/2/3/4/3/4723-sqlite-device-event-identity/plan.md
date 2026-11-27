# Implementation Plan: SQLite Device Event Identity

**Branch**: `fix/4723-sqlite-device-event-identity` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/3/4/3/4723-sqlite-device-event-identity/spec.md`.

Feature root children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. The `design/` folder holds the research, data model, quickstart, contracts, and checklists.

## Summary

The SQLite writer keeps one row for each distinct device event that uses the endpoint `searchOrgDeviceEvents`. The current composite key reduces to `timestamp` for the documented event shape, so distinct events replace each other (evidence R5, R8, R10). The fix keys each row on `org_id` and a SHA-256 fingerprint of its stored values. A dry-run-first migration rebuilds each legacy table, keeps the legacy table, and checks a backup first. Redis and ArangoDB keys do not change.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml` requires `>=3.15`). Evidence R44 names the language rule.

**Primary Dependencies**: Standard library `sqlite3`, `hashlib`, `json`, `shutil`, and `pathlib`. The existing `structlog` package is used by `database_schema_utils.py` (evidence R8). No new package.

**Storage**: SQLite file `data/mist_data.db` (evidence R75). Tables `OrgDeviceEvents` (menus 21 and 153) and `OrgDeviceEvents_52w` (menu 97).

**Testing**: pytest with `tmp_path` fixtures. No network, no Mist credential, and no production file.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container (evidence R44).

**Project Type**: Menu-driven command-line tool with SQLite output.

**Performance Goals**: The migration copies rows in batches of 5,000. The writer verifies keys in chunks of 500.

**Constraints**: ASCII logs. No new direct child in a folder that already holds more than five children. No change to Redis, ArangoDB, or the strategy catalog.

**Scale/Scope**: One endpoint, three menus, two tables, one migration module, and seven changed or added files plus tests and docs.

## Constitution Check

*Gate: must pass before research. Re-check after design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | The new package `src/foundation/persistence/device_events/` adds one child to `src/foundation/persistence/` (3 to 4). The package holds four children. The change adds no child to `src/foundation/persistence/db/` (6 children, R67), to `scripts/` (53, R69), or to `src/foundation/support/refactors/` (33, R68). Debt is listed in the five-item section below. |
| II. Class-Based Architecture | Pass | Logic sits in `DeviceEventIdentity`, `DeviceEventIdentityStore`, and `LegacyDeviceEventMigration`. The module guard constructs the migration class directly, with no wrapper function. |
| III. Safety-First | Pass | The migration requires the typed word `MIGRATE` through `InputUtils.safe_input` (R34). The migration is dry-run by default and keeps the legacy table. The writer refuses legacy tables. |
| IV. Full Deployment Pipeline | Pass | `tasks.md` lists local gates, a pull request, remote CI, and a merge step in order. |
| V. Observability and Logging | Pass | The new modules use `structlog`, as `database_schema_utils.py` does (R8). Messages use ASCII. |
| VI. Inline Comments | Pass | Each executable line in the changed and new code gets a same-line comment that explains intent. |
| VII. Action Logging | Pass | Each action logs info before and debug after. Errors log full context. |
| Mist SDK only | Pass | No new REST request. The existing SDK method is unchanged (R74). |
| Package Manager | Pass | No dependency changes. `requirements.txt` stays unchanged. |
| Podman Runtime | Pass | No test starts a container. |
| File Paths | Pass | Paths use `pathlib.Path` and `Path.as_uri()` for the read-only URI. |
| Output Backends | Pass | CSV, Redis, and ArangoDB paths keep their behavior. Only the SQLite path for `searchOrgDeviceEvents` changes. |
| Operational Store | Not applicable | The feature stores no coordination record. |
| Export Boundary | Pass | The multi-backend export rule is unchanged (R16 and R19). |
| Database Keys | Fail, justified | The constitution requires natural business keys (R50). No documented field identifies a device event (R72, R73). The chosen key uses `org_id` plus a fingerprint of source fields. Decision D-12 and Complexity Tracking record the exception. Review must accept the exception before merge. |
| Development Workflow, new menus | Not applicable | No menu is added or renumbered. |
| Testing | Pass | 23 new tests and 4 existing test modules run (`tasks.md`). |
| Security Findings | Pass | No suppression comment. The SQL identifiers pass a fixed pattern before any statement. Bandit findings are fixed or justified in code review. |
| Documentation | Pass | The README, operator guide, strategy diagram, and instruction file change (FR-021). |
| Release Notes | Pass | One fragment `changelog.d/issue-4723-sqlite-device-event-identity.md` (R46). |
| Audience Standard | Pass | Messages use plain words for a junior operator. |
| SpecKit Escalation | Pass | The change touches more than three files and changes a database schema. The record is required (R53). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/4/3/4723-sqlite-device-event-identity/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      migration-cli.md
      sqlite-identity-table.md
      writer-result.md
    checklists/
      requirements.md
      data-safety.md
      process.md
```

### Source Code (repository root)

```text
src/foundation/persistence/device_events/
  __init__.py
  identity.py
  store.py
  legacy_migration.py
src/foundation/support/refactors/sqlite_database_writer.py   (modify)
src/operations/exporting/export/org_alarm_event_exporter.py  (modify)
tests/unit/db/test_device_event_identity.py                  (add)
tests/unit/db/test_device_event_migration.py                 (add)
tests/unit/export/test_org_alarm_event_exporter.py           (modify)
documentation/operator-guide.md                              (modify)
documentation/diagrams/core/database-strategy.md             (modify)
.github/copilot-instructions.md                              (modify)
README.md                                                    (modify)
changelog.d/issue-4723-sqlite-device-event-identity.md       (add)
```

**Structure Decision**: The new package holds the identity contract, the SQLite store, and the migration. It sits under `src/foundation/persistence/`, because that folder has room for one child (R66). The writer and the menu 21 code stay where they are, because moving them would widen the change and touch more shared files.

## Architecture

```text
Menu 97  -> DeviceEvents52wExporter -> DataExporter.write_with_format_selection -> OrgDeviceEvents_52w
Menu 21  -> OrgAlarmEventExporter.device_events -> DataExporter.write_with_format_selection -> OrgDeviceEvents
Menu 153 -> APIDataFetcher -> DataExporter.export_with_processing -> OrgDeviceevents (same table as menu 21)
                  |
                  v
SQLiteDatabaseWriter.write -> _execute_database_operations
                  |  endpoint is searchOrgDeviceEvents?
                  |  yes: DeviceEventIdentityStore (identity table, INSERT OR IGNORE, presence check)
                  |  no:  existing path (unchanged)

Migration: operator -> LegacyDeviceEventMigration
  dry run (read-only URI) -> typed MIGRATE -> backup copy and check -> BEGIN IMMEDIATE
  -> rename legacy table -> create identity table -> copy rows with fingerprints
  -> count checks -> COMMIT, or discard the transaction
```

## File-by-File Change Map

| Action | Path | Purpose | Requirements |
| - | - | - | - |
| Add | `src/foundation/persistence/device_events/__init__.py` | Package marker with a module docstring | FR-022 |
| Add | `src/foundation/persistence/device_events/identity.py` | `DeviceEventIdentity`: endpoint check, fingerprint, fixed identity key columns | FR-001, FR-002, FR-003, FR-023 |
| Add | `src/foundation/persistence/device_events/store.py` | `DeviceEventIdentityStore` and `LegacyDeviceEventKeyError`: table state, DDL, insert, presence check, transaction control | FR-004 to FR-008 |
| Add | `src/foundation/persistence/device_events/legacy_migration.py` | `LegacyDeviceEventMigration`: dry run, backup, typed confirmation, one-transaction rebuild | FR-009 to FR-015 |
| Modify | `src/foundation/support/refactors/sqlite_database_writer.py` | Branch in `_execute_database_operations` (lines 246 to 262) for the endpoint. Refuse legacy tables. Return the store result | FR-004, FR-005, FR-008, FR-019 |
| Modify | `src/operations/exporting/export/org_alarm_event_exporter.py` | `device_events()` checks the write result for non-empty batches through a helper | FR-016 |
| Modify | `tests/unit/export/test_org_alarm_event_exporter.py` | Two tests in `TestDeviceEvents` (lines 148 to 220) | FR-016 |
| Add | `tests/unit/db/test_device_event_identity.py` | Thirteen unit tests for identity and writer behavior | FR-001 to FR-008, FR-018, FR-019, FR-020, FR-023 |
| Add | `tests/unit/db/test_device_event_migration.py` | Eight unit tests for the migration | FR-009 to FR-015 |
| Modify | `documentation/operator-guide.md` | Subsection after line 754 that explains the migration | FR-021 |
| Modify | `documentation/diagrams/core/database-strategy.md` | Row at line 137 and a note under the table | FR-021 |
| Modify | `.github/copilot-instructions.md` | Sentence at lines 208 and 209 about the device event identity | FR-021 |
| Modify | `README.md` | One paragraph after line 18 that names the migration | FR-021 |
| Add | `changelog.d/issue-4723-sqlite-device-event-identity.md` | One `Fixed` bullet for issue #4723 | FR-021 |

**Unchanged by design**:

- `src/operations/exporting/export/device_events_52w_exporter.py`. The exporter guard from merged pull request #4834 stays. Issues #4721 and #4722 keep ownership of that file (R21 to R23).
- `src/operations/exporting/export/data_exporter.py`. Open pull request #4813 changes this file (source S-3).
- `src/foundation/persistence/db/database_schema_utils.py`. Its partial-key behavior stays for the other endpoints (R8 and R35).
- `src/foundation/support/utils/operation_registry.py` and `MistHelper.py`. Menu numbers, categories, and wiring stay unchanged (R27 to R29).
- `src/mist/access/api/api_data_fetcher.py`. Menu 153 result handling moves to a follow-up issue (decision D-9).
- `src/foundation/persistence/db/writers/arango_writer.py` and the Redis writer. Keys stay with issues #4724 and #4725 (R33).
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. The catalog entry stays unchanged (R5 and R6).

## Dependencies

No new dependency. The change uses the standard library and the existing `structlog` package.

## Implementation Outline

1. Confirm the reproduction facts and the file blobs in `tasks.md` T001.
2. Build the identity contract and its tests first. The tests must fail before the writer branch exists.
3. Add the writer branch and the refusal path.
4. Add the menu 21 result check and its two tests.
5. Build the migration with its dry run, backup, confirmation, and transaction. Add its eight tests.
6. Update the documentation and the fragment.
7. Run the local gates, the pull request steps, remote CI, and the merge gate.

## Five-Item Rule Check

| Folder | Children before | Children after | Status |
| - | - | - | - |
| `src/foundation/persistence/` | 3 (R66) | 4 | Compliant. One package added. |
| `src/foundation/persistence/device_events/` | none | 4 | Compliant. Four children. |
| `src/foundation/persistence/db/` | 6 (R67) | 6 | Noncompliant before this change. Not changed. |
| `src/foundation/support/refactors/` | 33 (R68) | 33 | Noncompliant before this change. One file edited, no child added. |
| `scripts/` | 53 (R69) | 53 | Noncompliant before this change. No script added, so the migration is a module. |
| `tests/unit/db/` | 2 (R70) | 4 | Compliant. Two test files added. |
| `changelog.d/` | process folder | +1 | Allowed. The fragment is a unique process record. |

**Remediation**: Open a separate issue to bring `src/foundation/persistence/db/`, `src/foundation/support/refactors/`, and `scripts/` within five children. This change does not do that work.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| Database Keys rule, fingerprint key (R50) | No documented field identifies an event (R72, R73). | A key of all documented fields fails when a live field is absent or unexpected. Decision D-12. |
| Edit inside a noncompliant folder (`src/foundation/support/refactors/`, 33 children) | The writer owns the SQLite path, and the branch must sit inside it. | A copy of the writer in the new package would fork the SQLite pipeline. |
| New package under a folder with three children (`src/foundation/persistence/`) | The identity logic needs a home that accepts a new child (R66). | `src/foundation/persistence/db/` is noncompliant (R67). `scripts/` is noncompliant (R69). |
| Legacy table and backup kept after migration | Keeps the original data available for review. | Warning: deleting the legacy table destroys data. Decision D-10 keeps it, and a human decides deletion. |

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: the migration can fail in the middle of the copy. | One transaction, a checked backup, and a legacy table that stays in place. |
| Caution: the disk can fill during the backup or the copy. | The migration checks free space before the backup starts. The backup is a separate file. Keep it until a reviewer approves deletion (D-10). |
| Caution: operators can skip the migration. | The writer refuses legacy tables and logs the command (FR-008). |
| Caution: menu 153 logs success after a failed write. | Follow-up issue. Decision D-9 records the choice. |
| Caution: two different events with the same stored values merge into one row. | The log reports each merged row. |
| Caution: Mist can add a field to events. | One rerun can then add a row for an older event. |
| The SQLite key differs from the Redis and ArangoDB keys. | Issues #4724 and #4725 decide those keys. Decision D-3 records the split. |
| Pull request #4813 edits `data_exporter.py`. | This change does not edit `data_exporter.py`. |
| A reviewer rejects the Database Keys exception. | Decision D-12 records the alternatives. The reviewer chooses before merge. |

## Rollback Steps

1. Stop every export and the migration.
2. Revert the squash commit on `main` with a new pull request. Do not force-push `main`.
3. If the migration ran, stop the application. Copy the backup file over `data/mist_data.db`. The backup holds the state before the migration.
4. Keep the backup file until the restored database passes `PRAGMA integrity_check`.
5. Start the application from the reverted code.
