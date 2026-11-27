# Specification Analysis Report: OSPF Peer Identity Keys

This report checks the consistency of `spec.md`, `plan.md`, `tasks.md`, and the remote evidence in `design/research.md`. It records each defect in the existing work and each open item.

## Findings

| ID | Category | Severity | Location | Finding | Recommendation |
| - | - | - | - | - | - |
| A-01 | Defect | Critical | `src/foundation/persistence/db/database_schema_utils.py` lines 166 to 173 (RV-05) | The composite DDL keeps only primary key columns present in the batch. A batch without `peer_ip` creates a primary key of `mac` and `timestamp`. | Fixed for OSPF endpoints by D-6 and D-7. The generic function keeps its behavior for other endpoints (D-1). |
| A-02 | Defect | High | `src/foundation/persistence/db/writers/redis_writer.py` lines 624 to 633 (RV-15, RV-16) | The Redis key builder substitutes `unknown` and joins values with colons. Two different records can produce one key. | Fixed for OSPF endpoints by D-3, D-6, and D-12. |
| A-03 | Defect | High | `src/foundation/persistence/db/writers/arango_writer.py` line 4067 (RV-19) | The ArangoDB `_key` uses only the first primary key field. For site records that field is `mac`. | Fixed for OSPF endpoints by D-8 and D-12. The generic fallback stays unchanged, because issue #4725 owns it. |
| A-04 | Defect | High | `src/foundation/support/refactors/sqlite_database_writer.py` line 319 (RV-11) | An ALTER adds columns and keeps the primary key. An existing table keeps its old key after a later write. | Fixed by writing to a `_v2` table with a new key (D-7). The legacy table stays unchanged (D-9). |
| A-05 | Defect | Medium | `src/foundation/persistence/db/writers/arango_writer.py` lines 2218 and 2905 (RV-20, RV-21) | The OSPF graph mappings use `id` as the key field. Records without `id` produce no OSPF graph vertices. | Out of scope. A follow-up issue owns it (D-15). |
| A-06 | Defect | Medium | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` line 1563 (RV-02) | The org strategy uses `device_id`. The item schema declares no such property (RV-48 forbids additional properties, and RV-49 lists no required field). | Replaced by the identity key (D-12). |
| A-07 | Defect | Low | `scripts/pk_strategy_suggestions.py` line 2486 (RV-79) | The generated suggestion says "no stable key" for `searchSiteOspfStats`. The current catalog differs. | Stale output. A follow-up issue owns it (D-15). |
| A-08 | Documentation drift | Low | `src/operations/exporting/export/site_export_utils.py` (RV-36, RV-38) | Menu 70 writes `Site<Type>_<site>.csv` (RV-38). Its function docstring names a single `SiteOspfStats.csv` file. | Recorded only. This record does not edit the file. |
| A-09 | Coverage gap | Medium | `documentation/operator-guide.md` (RV-62) | The operator guide has no statement about OSPF tables. | Task T009 adds the statement. |
| A-10 | Coverage method | Low | `spec.md` FR-016 and FR-017 | Two requirements use documentation checks instead of unit tests. The brief rule (a) asks for a test. | Documented in `design/checklists/requirements.md`. The STE and guardrail runs are the checks. |
| A-11 | Scope boundary | Info | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` line 2415 (RV-03) | `searchOrgBgpStats` uses the same key tuple as the org OSPF strategy. | Out of scope (D-1). Test 15 pins the boundary. |
| A-12 | Coordination | Medium | `plan.md` Preconditions | The issue comments cite 27 open pull requests. The check on 2026-11-26 found seven open pull requests, none of which touches the change map. | Repeat the Preconditions check in T-PR. Record a handoff on #4726 before the branch exists. |
| A-13 | Unverified fact | Medium | `design/research.md` U-01 | Live records may omit `neighbor`. | The batch fails with the component name (D-3). The risk is recorded. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 to FR-005 | T001, T004 | Tests 1 to 10, 16 |
| FR-006 to FR-008 | T002, T006 | Tests 17, 18, 19 |
| FR-009 to FR-011 | T003, T005, T007 | Tests 21, 22 |
| FR-012 | T008 | Existing export tests (RV-57 to RV-59) |
| FR-013 and FR-014 | T001, T005 | Tests 14, 15 |
| FR-015 | T001, T004, T006 | Test 16 |
| FR-016 | T009 | STE check (documentation) |
| FR-017 | T009 | STE check and guardrail run |
| FR-018 | T002, T006 | Test 18 |
| SC-001 to SC-006 | T002, T003, T008, T-LOCAL-GATES | Tests 17, 21, 18, export tests, gates |

## Constrained-Field Coverage

| Field | Constraint | Enforced by |
| - | - | - |
| `mac` | Required, non-empty string | Test 8 (missing) and the validation order in the contract |
| `neighbor` | Required, non-empty string, or `peer_ip` fallback | Tests 7 and 8 |
| `timestamp` | Required, finite, zero or greater, decimal text without exponent | Tests 9 and 10 |
| `vrf_name` | Optional scope, empty or absent becomes null | Tests 5 and 6 |
| `port_id` | Optional scope, empty or absent becomes null | Test 4 and tests 5 and 6 |
| `misthelper_ospf_peer_key` | `TEXT NOT NULL`, primary key, format `ospf_` plus 64 hexadecimal characters | Tests 17, 19, and the storage contract |

## Constitution Alignment

The Constitution Check table in the plan holds each rule and its result. Every rule passes. Principle I records the existing violations in two noncompliant classes and adds no method to either class.

## Unmapped Tasks

None. Each task maps to at least one requirement and one verification command.

## Metrics

- Requirements: 18 (FR-001 to FR-018).
- Success criteria: 6 (SC-001 to SC-006).
- Tasks: 13 (T001 to T009 and four final tasks).
- New or modified test functions: 22.
- Remote checks: 102.
- Decisions: 16. Human decisions: 1 (D-9).
- Changed files: 10. Added files: 4. Modified files: 6.

## Convergence After Implementation

1. Tests 1 to 22 pass.
2. The export tests in T008 pass without edits.
3. `symbol-diff` reports no removed module-level name in the three edited modules.
4. The guardrails pass with the new package under `persistence`.
5. The changelog fragment and the operator guide name the `_v2` tables.

## Unresolved Items

- D-9, HUMAN-DECISION-REQUIRED: a purge or a copy of legacy OSPF rows.
- U-01 to U-06 in `design/research.md`.
- Follow-up issues for the graph mapping (A-05) and the suggestion script (A-07). The orchestrator files them.
- The handoff on #4726 before the branch exists (A-12).
