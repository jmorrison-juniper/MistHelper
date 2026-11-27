# Specification Analysis Report: Redis device event identity

This report checks `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. The remote code is the authority. Row citations (RC-nn) refer to `design/research.md`, section R14.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A1 | Defect | HIGH | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` line 267 (RC-01) | The device event key uses `id` and `device_id`. The documented schema defines neither field (RC-24). | Resolved by T004 with decisions D-1 and D-2. |
| A2 | Defect | MEDIUM | Same file, line 268 (RC-02) | The index list names `device_id`, which device events never carry. | Resolved by T004. The index uses `mac`. |
| A3 | Defect | HIGH | `src/foundation/persistence/db/writers/redis_writer.py` line 632 (RC-04) | A missing key field becomes `unknown`. Events that share a timestamp collide. | Resolved by T006 and decision D-3. |
| A4 | Defect | HIGH | Same file, lines 603 and 618 (RC-05, RC-06) | `JSON.SET` replaces a whole document. A replacement counts as a success. | Resolved by unique keys (T004, T005) and decision D-4. |
| A5 | Defect | MEDIUM | `src/foundation/persistence/db/writers/arango_writer.py` lines 1489 to 1501 and 4109 (RC-14, RC-15, RC-16) | Device events without `id` skip their vertex and their site edge. No error is logged. | Resolved by T007 and decision D-6. |
| A6 | Defect | MEDIUM | Same file, line 4067 (RC-13) | ArangoDB uses a UUID when the first key field is absent. Repeat writes duplicate events. | Resolved for device events by T004, because `record_id` is the first key field. The general UUID rule stays with issue #4725. |
| A7 | Documentation drift | MEDIUM | `documentation/diagrams/core/database-strategy.md` lines 43 and 137 (RC-28, RC-29). `.github/copilot-instructions.md` line 205 (RC-30) | Three documents show the defective key. | Resolved by T010 and T011. |
| A8 | Script drift | LOW | `scripts/pk_strategy_suggestions.py` line 2115 (RC-35) | The generator proposes `mac` and `timestamp`. Two events with one MAC and one timestamp still collide. | Unresolved. The generator stays unchanged. A follow-up issue is recommended. |
| A9 | Same pattern | MEDIUM | `endpoint_primary_key_strategies.py` line 2643 (RC-03) | `searchOrgTunnelsStats` uses `id` and `device_id`. | Unresolved. Out of scope under decision D-9. A follow-up issue must check its schema first (research U-8). |
| A10 | Test gap | MEDIUM | `tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py` line 72 (RC-37) | No test covers a collision. The existing test checks only the success result and the count. | Resolved by T001. |
| A11 | Constitution tension | MEDIUM | `.specify/memory/constitution.md` line 322 (RC-66) | The rule requires Mist natural keys. Device events have no unique Mist key. | Resolved by a recorded exception. The rogue DHCP `record_id` is the precedent (RC-44, RC-45). |
| A12 | Environment mismatch | LOW | Issue #4724 environment section (R1) | The reproduction ran on Python 3.13.13. The repository requires Python 3.15 (RC-31). | No change. The fix runs on the repository version. The reproduction shows the defect, not a version claim. |
| A13 | Shared files | MEDIUM | Issues #4721, #4722, #4723, #4725, and #4726 (R2) | The issues share identity files and writers. | Resolved by gate D-12. The snapshot on 2026-11-26 shows zero overlaps. |
| A14 | Dependency order | LOW | Decision D-2 | The ArangoDB UUID rule from issue #4725 could block this change. | No block. `record_id` is the first key field, so the rule works unchanged. |
| A15 | Route allocation | LOW | `spec-route.ps1` line 76 (RC-65) and main tree (RC-60) | The route for 4724 needs one new folder under an existing parent. | No action. The parent check passes (research R4). |
| A16 | Test expectation drift | MEDIUM | `tests/contract/test_arango_declared_indexes.py` line 154 (RC-40) and `test_preservation.py` line 36 (RC-41) | Two existing tests assume the original rows and the `id` key. Each one fails after the change. | Resolved by T008 and T009. |
| A17 | Structure risk | MEDIUM | `tests/guardrails/test_persistence_package_structure.py` lines 88 and 89 (RC-36, RC-37) | A new module breaks the pinned child counts. | Resolved by decision D-8. No new module is planned. |

## Coverage Summary

| Requirement | Tasks | Notes |
| - | - | - |
| FR-001 | T001, T002, T005 | The router stamps `record_id` before both writes. |
| FR-002 | T002, T005 | The digest reuses `_hash_payload` (RC-11). |
| FR-003 | T002, T005, T009 | The router copies rows. The contract test checks the copies. |
| FR-004 | T004, T008 | The strategy changes. The preservation test checks `_key`. |
| FR-005 | T001, T006 | The Redis writer rejects rows with missing fields. |
| FR-006 | T001, T006 | A rejected row or a failed SET reports failure. |
| FR-007 | T003, T007 | The graph map uses `record_id`. |
| FR-008 | T-LOCAL-GATES | The diff check confirms that no delete, purge, or remove call exists. |
| FR-009 | Format section and T005 to T007 | Each task requires comments and logs. |
| FR-010 | T010, T011, T012 | The design guide, contributor guide, and changelog change. |
| SC-001 | T001 | The regression test keeps two documents. |
| SC-002 | T002 | Two organizations produce two digests. |
| SC-003 | T002, T008 | A repeat write keeps one key. |
| SC-004 | T001, T006 | No device event key contains `unknown`. |
| SC-005 | T013 | The structure guard passes unchanged. |
| SC-006 | T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE | Local gates, remote checks, and merge steps. |

Every requirement maps to at least one task. Every task names exact paths and one verification command.

## Defects in Existing Work

The previous draft work for this issue does not exist. No legacy record was found (RC-58). The defects above describe the current code on `main` (commit `f03c6c9`, RC-57).

## Unresolved Items

- Decision D-7 needs human approval for any purge of existing Redis keys. The recommended option is no purge.
- Live row shape is unverified (research U-1). Duplicate frequency is unverified (research U-2).
- Graph volume, hashing cost, and rejection counts are unverified (research U-6, U-7, U-9).
- External readers of the old key format are unverified (research U-5).
- The tunnel statistics schema and the `device_type` default effect are unverified (research U-8, U-10).
- Other direct callers of the endpoint are unverified. Their write paths need a trace before the merge (research U-11).

## Consistency Checks

- Functional requirements: 10 (FR-001 to FR-010).
- Success criteria: 6 (SC-001 to SC-006).
- Tasks: 13 numbered tasks and 4 release tasks, for a total of 17.
- Test functions planned: 8.
- Decisions: 12. Decisions that need human approval: 1 (D-7).
- Remote checks: 66 rows (RC-01 to RC-66). The `STATUS.json` array and the summary report the same count.
- The route for 4724 matches the orchestrator route (research R4).
