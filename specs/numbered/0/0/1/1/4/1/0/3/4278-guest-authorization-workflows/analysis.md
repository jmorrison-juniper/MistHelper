# Specification Analysis Report: Guest authorization workflows

## 1. Scope of This Review

This review checks the spec, the plan, the tasks, the design files, and the remote evidence in `design/research.md`. It lists each defect in existing work, and each item that stays unresolved.

## 2. Coverage Counts

| Artifact | Count | Source of the count |
| --- | --- | --- |
| Functional requirements | 32 (FR-001 to FR-032) | `spec.md` |
| User stories | 6 (P1 to P3) | `spec.md` |
| Success criteria | 7 (SC-001 to SC-007) | `spec.md` |
| Tasks | 20 (T001 to T016, plus 4 final tasks) | `tasks.md` |
| Planned tests | 37 (TEST-001 to TEST-037) | `tasks.md` |
| Decisions | 21 (D-1 to D-21) | `design/research.md` Section 6 |
| Human decisions | 1 (D-4) | `design/research.md` D-4 |
| Remote checks | 112 (R001 to R112) | `design/research.md` Section 7 |

Each count matches its entry in `4278-STATUS.json` and in `4278-summary.md`.

## 3. Requirement Coverage

Each requirement maps to at least one task and at least one test. The test IDs refer to `tasks.md`.

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 Navigation entry and page | T001, T009, T010, T011 | TEST-024, TEST-029 |
| FR-002 Binding to organization, site, and WLAN | T004, T009 | TEST-002, TEST-027 |
| FR-003 Site and WLAN from discovery | T004, T005 | TEST-002, TEST-005 |
| FR-004 Trusted identity | T002, T004, T009 | TEST-004, TEST-026 |
| FR-005 CSRF and server-side word check | T004, T007, T009 | TEST-003, TEST-024 |
| FR-006 Review through the list call | T005, T009 | TEST-005 |
| FR-007 Missing values stay unknown | T003, T009 | TEST-001 |
| FR-008 Client search through statistics | T005, T009 | TEST-009 |
| FR-009 Grant with minutes 1 to 259200 | T007 | TEST-010 |
| FR-010 Writable fields only | T005, T007 | TEST-006 |
| FR-011 Extension gated by G5 | T007 | TEST-011 |
| FR-012 Revoke with read-back | T005, T007 | TEST-007, TEST-012 |
| FR-013 No delete call | T005 | TEST-008 |
| FR-014 Exact review before confirmation | T004, T009 | TEST-025 |
| FR-015 Zero writes on cancel, wrong word, stale, or denied | T007, T009 | TEST-025 |
| FR-016 Unknown outcome, no retry | T007 | TEST-013 |
| FR-017 Intent and outcome rows | T006, T007 | TEST-015, TEST-016 |
| FR-018 Intent failure stops dispatch | T006 | TEST-015 |
| FR-019 Outcome failure reported separately | T006 | TEST-016 |
| FR-020 CSV bounds and headers | T008 | TEST-019, TEST-020 |
| FR-021 Preview sends no write | T008 | TEST-022 |
| FR-022 Digest-bound IMPORT confirmation | T004, T008 | TEST-003, TEST-022 |
| FR-023 Sequential row outcomes | T008 | TEST-023 |
| FR-024 Stop on rate limit, unknown, or audit failure | T007, T008 | TEST-014, TEST-023 |
| FR-025 Masking in logs, audit, and responses | T003, T006, T009 | TEST-001, TEST-017, TEST-028 |
| FR-026 data-testid and failure evidence | T009, T011, T012 | TEST-029, TEST-032 |
| FR-027 No new application, port, service, or variable | T001, T010, T015 | TEST-035, TEST-036 |
| FR-028 mistapi methods only | T005 | TEST-005, TEST-006, TEST-007, TEST-008 |
| FR-029 Site scope only | T005 | TEST-008 |
| FR-030 Offline tests only | T012, T-REMOTE-CI | TEST-030, TEST-031 |
| FR-031 Operator guide and changelog | T013, T014, T-PR, T-MERGE | TEST-033 |
| FR-032 Package move | T003, T016 | TEST-001, TEST-037 |

## 4. Test Coverage Map

| Test range | Task | Subject |
| --- | --- | --- |
| TEST-001 | T003 | Projection cases, moved to `test_domain.py` |
| TEST-002 to TEST-004 | T004 | Scope, confirmation, and identity |
| TEST-005 to TEST-009 | T005 | Mist client contract |
| TEST-010 to TEST-014 | T007 | Write service |
| TEST-015 to TEST-018 | T006 | Audit store |
| TEST-019 to TEST-023 | T008 | CSV import |
| TEST-024 to TEST-028 | T009 | Routes, identity, privacy |
| TEST-029 to TEST-032 | T012 | Browser flows |
| TEST-033 | T014 | Changelog guard |
| TEST-034 to TEST-036 | T015 | Structure and container guards |
| TEST-037 | T016 | Module-move guidance |

## 5. Consistency Checks

| Check | Result | Evidence |
| --- | --- | --- |
| The route folder equals 4278 in base 5 | Consistent | `plan.md` Summary and `spec.md` header |
| The spec, plan, and tasks name the same record path | Consistent | `spec.md`, `plan.md`, `tasks.md` headers |
| The CSV limits match in the spec, research, and tasks | Consistent | FR-020, D-13, T008 |
| The minutes range matches in the spec, research, and tasks | Consistent | FR-009, D-8, T007 |
| The revocation sequence matches in the spec, research, and tasks | Consistent | User Story 4, D-10, T007 |
| The file ownership gate matches in the plan and tasks | Consistent | `plan.md` constitution check, D-18, T001, T010, T011 |
| The line numbers match remote evidence | Consistent | R045, R046, R058, R059, R060, R061, R062, R026, R027 |
| The route for each FR exists in the contracts | Consistent after writing `design/contracts/portal.md` | FR-001 to FR-008, D-12 |
| Each task names one verification command from the local gates table | Consistent | `tasks.md` Verification lines |
| The remote count matches in the research table and the STATUS file | Consistent | Section 2 and Section 7 |

## 6. Defects in Existing Work

1. **Location of `wsgi.py`.** The repository instructions state that `web_portal/` serves through `wsgi.py` (R011). The file is at the root (R045). `web_portal/wsgi.py` is absent (R005). Action: correct the instruction in a separate documentation change.
2. **mistapi floor in the constitution.** The constitution names a floor of 0.59 (R016). The pin is at least 0.64.1 (R047, R049). Action: update the constitution in a separate amendment.
3. **mistapi floor in the instructions and pyproject.** The repository instructions name at least 0.64.0 (R008). The pyproject names at least 0.64.1 (R047). Action: align both files in a separate change. Until then, T-LOCAL-GATES records the installed version (R112).
4. **Issue state in the 4588 draft.** The draft states that issue 4278 is closed (draft R11). GitHub reports it open (R094). Action: the owner corrects the draft or closes the issue.
5. **Unauthorize omission in the 4588 draft.** The draft decision D-8 lists four revocation options and omits the unauthorize call. Menu 286 already calls that operation (R072, R073, R075). Action: this record adds the option (D-10).
6. **Test folders above five children.** `tests/unit/web_portal` and `tests/e2e/web_portal` exceed five children. The constitution treats this state as grandfathered debt (R014). Action: remediation R-1 and R-2 below.
7. **CSV limit in the 4588 draft.** The draft selects 1 MiB and 1000 rows (draft D-11). This record selects 262144 bytes and 200 rows (D-13). The owner can change the value with new evidence.

## 7. Unresolved Items

| ID | Item | Owner | Blocks |
| --- | --- | --- | --- |
| UR-1 | Access and write authority under D-4 | Maintainers | All reads and writes (FR-004) |
| UR-2 | Grant semantics: creation of a missing record and extension behavior (U01, U02) | Implementer, with owner-approved live evidence | FR-009, FR-011 |
| UR-3 | Revocation read-back (U04) | Implementer, with owner-approved live evidence | FR-012 |
| UR-4 | Client search fields (U05) and derived WLAN shape (U06) | Implementer, with contract evidence | FR-008, D-5 |
| UR-5 | Maintainer approval of CSV limits and audit-failure handling, as the issue requires | Maintainers | FR-020, FR-024 |
| UR-6 | Handover of `web_portal/app.py` and `base.html` from PR 4208 | Owner | T010, T011 |
| UR-7 | Record of the clean-room decision on issue 4278 (issue acceptance criterion 1) | Owner | T002 |
| UR-8 | SQLite behavior under the threaded worker (U08) | Implementer | FR-017, D-16 |
| UR-9 | Live verification approval for each run (owner comment of 2026-11-08) | Owner | UR-2, UR-3 |

## 8. Remediation Actions Outside This Change

- **R-1**: Split `tests/unit/web_portal` into area folders. Track it in a separate issue.
- **R-2**: Split `tests/e2e/web_portal` into area folders. Track it in a separate issue. The e2e guard must change with the split.
- **R-3**: Correct the wsgi location, the mistapi floors, and the state of issue 4278 in the documents named in Section 6.
