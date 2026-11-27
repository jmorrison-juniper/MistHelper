# Specification Analysis Report: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/`, and the remote evidence in `design/research.md` (RC-01 to RC-124). The check runs on remote main f03c6c9b. The pinned commit 3964d21d is used for count drift only.

## Findings

Severity values: High means data loss or wrong identity. Medium means wrong data shape or a missing test. Low means documentation or text drift. Info means a verified fact that limits the change.

| ID | Severity | Finding | Evidence | Disposition |
| - | - | - | - | - |
| A-1 | High | The writer assigns the document key from the first declared key field. Two records that differ only in later key fields replace each other. The writer then counts two successful writes. | `arango_writer.py` lines 4067 to 4068 (RC-57). Effective affected entries: 121 (RC-76). Example: `searchSiteBgpStats` (RC-64). | Fixed by this change (FR-001 to FR-003). |
| A-2 | High | The strategy dictionary holds 612 entries for 595 unique names. Python keeps the last definition of a repeated key. At main, 11 composite definitions are shadowed by later UUID entries (137 raw and 126 effective composite entries). Example: `listSiteSleImpactedChassis` at lines 2599 and 4443 (RC-70, RC-76). | RC-70, RC-76. Ruff status for this pattern is unverified (U-3). | Out of scope. Follow-up issue (T018 a). These endpoints get UUID keys. The result is duplicate rows, not overwrites. |
| A-3 | Medium | The issue counts 136 `composite_pk` entries at the pinned commit. That is the raw count. The effective count is 125 at the pinned commit and 126 at main. The main table adds `ExHardwareInventory` (line 3506), the only composite name not in the pinned table. | RC-75, RC-76, RC-71. The effective affected count is 120 at the pinned commit and 121 at main. | This record uses effective counts. Scope and SC-005 use 121. |
| A-4 | High | The BGP graph mapping keys vertices by `id` (line 2199). The `bgp_stats` schema declares no `id` property. The vertex builder skips records without the key field. No BGP vertex comes from documented fields. | RC-59, RC-60, RC-48, RC-44 (items reference `bgp_stats`). | Out of scope. Follow-up issue (T018 b). Runtime effect unverified (U-5). |
| A-5 | Medium | The preservation test pins the key `record-1` for `searchOrgDeviceEvents`. The `device_event` schema documents no `id` property. The rule changes the key for records that carry an `id`. | RC-95, RC-94, RC-49, RC-50, RC-51. | Changed in T010, under D-10. The changelog fragment names the contract change. |
| A-6 | Medium | Three composite entries use one timestamp as the whole key: `listSiteAnomalyEvents` (line 562), `searchSiteDeviceConfigHistory` (line 570), and `searchSiteDeviceLastConfigs` (line 577). Records from different devices that share a timestamp can collide. The writer cannot fix an identity that the table does not declare. | RC-74. | Out of scope. Follow-up issue (T018 c). |
| A-7 | Medium | The SQLite composite primary key includes only the strategy fields that the response contains. A missing field narrows the key. | `database_schema_utils.py` lines 171 to 172 (RC-84). | Out of scope. Tracked by #4723. |
| A-8 | Low | The Redis JSON key joins values with `:`. A missing field becomes the sentinel `unknown`. A value that contains `:` can make two keys match, for example an IPv6 neighbor. | `redis_writer.py` lines 630 to 633 (RC-83). | Out of scope. Tracked by #4724. |
| A-9 | Medium | `_sanitize_key` maps `/` and `:` to `_`. Vertex keys that differ only by those characters can collide. | `arango_writer.py` line 4293 (def) and line 4295 (RC-61). | Not repaired here. Included in the follow-up for A-4. |
| A-10 | Info | `mark_absent_as_deleted` has no production caller. Changing the key does not trigger the soft-delete pass. | RC-62 (repository-wide Python search, excluding `.venv`). Tests call it at `test_arango_writer.py` lines 224, 655, 675, and 695. | No action. |
| A-11 | Low | Version text drifts. Instructions say `mistapi>=0.64.0,<0.65` (RC-05). The constitution says `0.59+` (RC-13). `pyproject.toml` says `>=0.64.1,<0.65` (RC-28). `requirements.txt` pins 0.64.1 (RC-31). | RC-05, RC-13, RC-28, RC-31. | Recorded only. The installed SDK is 0.64.1 (RC-116). |
| A-12 | Low | The quality-gates page lists a mypy path set that differs from CI (RC-33). CI `MYPY_PATHS` adds two script packages (RC-23). | RC-33, RC-23. | This record uses `ci.yml`, as the page instructs. |
| A-13 | Medium | No test calls `_compute_key` or `_prepare_document` (RC-63). The first-field defect has no direct test on main. | RC-63. | Closed by tests 1 to 9 (T006 and T007). |
| A-14 | Medium | `_batch_import` counts `created` and `updated` as successful writes (RC-54). A replacement inside one batch counts twice. | RC-54, RC-53. | Kept by D-12. Logs record the counts (FR-014). |
| A-15 | Low | The probe heuristic classifies `id` plus `timestamp` as `composite_pk` (RC-112, lines 21 to 23). The heuristic does not prove an identity. | RC-112. | Not an authority for keys. The identity audit (T002) decides each verdict. |
| A-16 | High | Ownership is unresolved. The open pull request check (7 open pull requests) finds no pull request that changes `arango_writer.py` or the strategy table. The issue reports writer changes on three refs, strategy changes on six refs, and a preserved local branch that the issue does not name. Those refs and the branch are not verified here (U-1). | `gh pr list --state open` check at record time. Issue comment 6753824761. | Blocker for T004 and T005. T001 must finish first. |
| A-17 | Info | The BGP example response in the OpenAPI file has `mac`, `neighbor`, and `timestamp`, and no `id` (RC-45, RC-46, RC-47, RC-48). | RC-45 to RC-48. | Supports the declared identity. Supports A-4. |

## Coverage Summary

Each FR maps to at least one task and at least one test or guard.

| Requirement | Tasks | Tests or guards |
| - | - | - |
| FR-001 | T003, T004 | Tests 1, 2 |
| FR-002 | T003, T004 | Tests 1, 2, 3 |
| FR-003 | T003 | Test 4 |
| FR-004 | T003 | Tests 6, 7 |
| FR-005 | T003 | Test 5 |
| FR-006 | T003, T005 | Tests 8, 9, 17 |
| FR-007 | T004 | Test 10 |
| FR-008 | T004, T012 | Test 11, and existing SLE tests (RC-97, RC-98, RC-99) |
| FR-009 | T002, T003 | Tests 12, 15 |
| FR-010 | T004, T009 | Test 13 |
| FR-011 | T004, T010 | Test 14, and existing `test_preservation.py` (RC-96) |
| FR-012 | T009, T015, T016, T017 | Test 13 (no delete or update call on the handle) |
| FR-013 | T001, T011, T-MERGE | Test 15 reads the table, and the Symbols gate applies |
| FR-014 | T005 | Test 17 |
| FR-015 | T002, T011 | Tests 15, 16 |
| FR-016 | T013, T014 | Changelog guard (RC-122), and documentation review in T013 |

## Constrained-Field Coverage

| Constraint | Source | Covered by |
| - | - | - |
| An ArangoDB key is 1 to 254 bytes (RC-121). | ArangoDB documents page. | FR-005, and test 5. |
| An ArangoDB key allows letters, digits, and a fixed set of punctuation marks that includes the underscore, colon, and percent sign (RC-121). | ArangoDB documents page. | FR-005. The identity key uses letters, digits, and the underscore only, which is a subset. |
| An ArangoDB key is unique within its collection (RC-121). | ArangoDB documents page. | FR-002 and FR-003. |
| Keys are strings (RC-121). | ArangoDB documents page. | FR-004 normalizes values to typed text. |

## Constitution Alignment

Each principle in `plan.md` has a result and a reason. No principle fails. Three rows are pass (planned) because the implementation is not written yet: Principles IV, VI, and VII.

## Unmapped Tasks

These tasks have no test because they are process steps or operator steps: T001, T015, T016, T017, T018, T-PR, T-REMOTE-CI, and T-MERGE. Each task names its nearest command or states that no local gate applies.

## Unresolved Items

- A-16 ownership and handoff (T001).
- D-7 legacy-document policy (T017). This is the only human decision.
- The identity audit rows for 121 entries (T002).
- A-4 BGP graph mapping. A new issue is needed (T018 b).
- A-2 duplicate strategy names. A new issue is needed (T018 a).
- A-6 timestamp-only identities. A new issue is needed (T018 c).
- A-7 and A-8 SQLite and Redis behavior. Tracked by #4723 and #4724.
- The structural split R-1 for `arango_writer.py` (T018 d).
- Live verification. This record runs no live ArangoDB or live Mist check (A-4 of `spec.md`).

## Metrics

| Metric | Value |
| - | - |
| Functional requirements | 16 |
| Success criteria | 6 |
| Tests planned | 17 |
| Tasks | 22 (T001 to T018, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE) |
| Decisions | 13 (1 human decision: D-7) |
| Remote checks | 124 (117 present, 7 absent) |
| Affected effective entries at main | 121 |
| Raw composite lines at main | 137 |
| Effective composite entries at main | 126 |
| Duplicate strategy names at main | 17 |

## Convergence After Implementation

After T004 and the tests pass, the expected state is:

- Tests 1 to 3 pass. Before T004, they fail. That proves each test can fail.
- Test 13 passes. The writer path performs no delete or update call.
- The SLE tests in RC-97, RC-98, and RC-99 pass with no edit.
- The changed `test_preservation.py` expectation passes under D-10.
- The identity audit reports 121 examined entries and zero unclassified entries (SC-005).
