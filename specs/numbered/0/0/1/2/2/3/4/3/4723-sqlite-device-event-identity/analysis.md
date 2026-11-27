# Specification Analysis Report: SQLite Device Event Identity

## Findings

| ID | Severity | Location | Finding | Action |
| - | - | - | - | - |
| A-1 | High | `src/foundation/support/refactors/sqlite_database_writer.py` lines 362 to 368 | The writer uses INSERT OR REPLACE for composite keys. A replacing insert counts as a success (R10, R11). | The identity branch for this endpoint replaces the path (T007). Other endpoints keep the path. |
| A-2 | High | `src/foundation/support/refactors/sqlite_database_writer.py` lines 459 to 475 | The batch returns True after one successful insert (R12). | The identity branch returns True only after the presence check (T005, T007). |
| A-3 | Medium | `src/foundation/support/refactors/sqlite_database_writer.py` lines 489 to 521 | The count check logs the table total, not the batch proof (R13). | The identity branch uses a batch presence check. The shared check stays for other endpoints. |
| A-4 | High | `src/operations/exporting/export/org_alarm_event_exporter.py` lines 140 to 146 | Menu 21 ignores the writer result and prints a completion line (R26). | Add the result check (T008, T009). |
| A-5 | High | `src/mist/access/api/api_data_fetcher.py` lines 411 to 417 | The shared fetcher logs success after the export, whether or not the write succeeded (R32). | Follow-up issue. Decision D-9. |
| A-6 | Medium | `src/operations/exporting/export/data_exporter.py` lines 182 to 198 | The loss warning covers only the polyglot write (R18). No SQLite loss warning exists. | Follow-up issue. The identity branch logs its own error. |
| A-7 | Medium | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 265 to 271 | The description says "composite key for uniqueness" (R5). The claim is false when a key field is absent. | Keep the entry for Redis and ArangoDB (D-3). Correct the text with issues #4724 and #4725. |
| A-8 | Medium | `documentation/diagrams/core/database-strategy.md` line 137 and `.github/copilot-instructions.md` lines 208 and 209 | Both documents name the old composite key for this endpoint (R41, R43). | Update in T014 and T015. |
| A-9 | Low | `src/operations/exporting/export/device_events_52w_exporter.py` line 345 | The docstring says SQLite stays idempotent (R24). The claim is true for the identity key after this change. | No edit. |
| A-10 | Medium | Issue #4723 body | The issue states that the exporter matched the reproduction commit. The exporter changed through merged pull request #4834 (R25). | The spec uses main evidence for guard claims. The reproduction claim for the writer still holds (R6, R10). |
| A-11 | Medium | `tests/unit/db/test_database_schema_utils.py` lines 190 to 200 | Tests encode the partial composite key behavior (R35). | Keep the shared builder unchanged. Other endpoints depend on it. |
| A-12 | High | `src/foundation/support/refactors/sqlite_database_writer.py` lines 369 to 372 | The auto-increment fallback runs `DELETE FROM` before the insert (R15). An endpoint with a non-keyed strategy would clear its table. | Not changed. The identity branch never reaches this path. Follow-up issue. |
| A-13 | Medium | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 513 to 519, 527 to 533, and 1540 to 1546 | Other device event endpoints use the same composite key shape. | The defect class is not verified for them (U-5). Follow-up issue. |
| A-14 | Medium | `src/operations/wan/org_data_collector.py` line 312 and `src/mist/access/api/api_data_fetcher.py` line 411 | Menu 153 writes SQLite rows under the same endpoint and ignores the result (R30, R32). | Decision D-9. Follow-up issue. |
| A-15 | Medium | `src/foundation/persistence/db/writers/arango_writer.py` lines 1487 to 1489 | The Arango graph map keys on field `id` (R33). | Issue #4725 owns the change. |
| A-16 | Low | `scripts/migrate_sqlite_to_polyglot.py` lines 1 to 12 | The script exports SQLite tables by strategy type (R76). Compatibility with an identity table is not verified (U-7). | Follow-up issue. The migration keeps the table name. |
| A-17 | Medium | Open pull request #4813 | The pull request edits `data_exporter.py` and one test file (S-3). | This change does not edit either file. |
| A-18 | High | `.specify/memory/constitution.md` line 322 | The natural key rule conflicts with the fingerprint key (R50). | Decision D-12. Complexity Tracking records the exception. |
| A-19 | Low | `tests/unit/export/test_org_alarm_event_exporter.py` lines 148 to 220 | Existing menu 21 tests use a mock writer that returns a truthy value (R38). | The new tests set the return value explicitly. The existing tests keep passing. |

## Coverage Summary

- All 23 requirements map to at least one task and one check in `tasks.md`.
- The 20 tasks cover 16 implementation and documentation items and 4 process gates.
- The plan lists 23 new tests in 3 files. The compatibility task runs 5 existing modules without edits.
- No task lacks a verification command from the local gates table.

## Constrained-Field Coverage

| Field | Constraint | Covered by |
| - | - | - |
| `org_id` | Part of the primary key. Stored as an empty string when absent. | Contract `sqlite-identity-table.md`, FR-003, test in T006 |
| `misthelper_row_fingerprint` | Part of the primary key. 64 hexadecimal characters. | Contract `sqlite-identity-table.md`, FR-023, fixed digest test in T006 |
| `timestamp` | An index field. The legacy primary key when the first batch holds no other key field. | Data model, legacy table state, FR-008 |
| `type` | An index field. Part of the identity content. | Data model, FR-002 |
| `device_id` | An index field when present. The catalog key lists it. | Contract index list (R5), R80 |
| Table names | SQLite identifiers are case-insensitive (S-6). `OrgDeviceEvents` and `OrgDeviceevents` name one table. | D-2, migration table list |

## Constitution Alignment

- Principle I is recorded with a debt entry in the plan. The new package adds one child to a folder that has room.
- Principle II has no wrapper function. The module guard constructs the class directly.
- Principle III has a typed confirmation and a refusal path.
- Principle V and Principle VII are covered by the logging tests in T006 and T012.
- The Database Keys rule fails with a recorded justification (D-12). Review must accept or reject it before merge.

## Unmapped Tasks

None. Each task maps to a requirement or to a process gate.

## Unresolved Items

- U-1: Live Mist responses may contain `id` or `device_id`. This record did not call the API.
- U-2: The production database state is unknown. This record opened no production data.
- U-3: Other tools that read `OrgDeviceEvents` were not searched outside this repository.
- U-4: Runtime SQLite behavior was not tested. The SQLite documents were read instead.
- U-5: Row loss in the other composite endpoints was not tested.
- U-6: The SQLite ALTER TABLE page was not fetched.
- U-7: Compatibility of `scripts/migrate_sqlite_to_polyglot.py` with the identity table is not verified.
- U-8: The menu 153 success message after a failed write was not tested at runtime.
- H-1 (decision D-10): Deletion of legacy tables and backups needs a human decision.
- H-2 (decision D-11): The production migration run needs a human decision.

## Metrics

- Functional requirements: 23.
- Tasks: 20.
- New tests: 23 in three modules. The menu 21 tests add to an existing module.
- Decisions: 15. Human decisions: 2 (D-10 and D-11).
- Remote checks: 84 rows in `design/research.md`. The status file repeats the same count.
- Unverified items: 8 (U-1 to U-8).

## Convergence After Implementation

- Recheck main. The head must match the record, or the record must state the new head.
- Recheck R5, R8, and R10 after any change to main. The writer and catalog facts drive the design.
- Recheck R25. The reproduction blob stays stale after the merge.
- Rerun the compatibility tests in T010 after the final rebase.
- Recheck the STE score of each changed Markdown file after the final edit.
