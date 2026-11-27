# Analysis: Menu 243 Result File Not Found

## 1. Consistency review

| Check | Result | Note |
| --- | --- | --- |
| Requirement to task mapping | Pass | FR-001 to FR-010 each map to at least one task. |
| Requirement to test mapping | Pass | Each requirement maps to an existing test or to T005. |
| Task paths | Pass | Existing paths carry remote rows. New paths are the fragment and the record folder. |
| Task verification commands | Pass | Each task names one command from the local gates table or a test module command. |
| Plan to remote code | Pass | Each code claim in the plan cites a row in `design/research.md`. |
| Spec to issue facts | Pass | The expected behavior in the issue maps to FR-001. The issue allows a statement that JSON preview is unsupported. This record keeps JSON preview. |
| Legacy record claims | Fail, recorded | Section 2 lists the claims and their results. |
| Constitution rules | Pass with recorded failures | Principles VI and VII fail for commit `18ce4c8` as committed. T005 corrects both. |
| Folder placement | Pass | The test joins an existing file. The record adds no direct child under `specs/`. |

## 2. Legacy claim map

The legacy record is `specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview`. Each row maps one legacy claim to remote rows in `design/research.md`. Counts: verified 17, stale 4, absent 2.

| LC | Legacy claim | Rows | Result |
| --- | --- | --- | --- |
| LC-01 | The legacy folder holds the spec, plan, tasks, and design files | RC-58 | verified |
| LC-02 | The legacy design folder holds five children | RC-59 | verified |
| LC-03 | The table route captured nested paths on the pre-fix layout | RC-17 | verified |
| LC-04 | Main selects nested files by complete path | RC-14, RC-18 | verified |
| LC-05 | Main keeps SQLite table selection separate | RC-19 | verified |
| LC-06 | JSON read errors return fixed text and log details | RC-24, RC-25 | verified |
| LC-07 | Pending previews clear rows and page controls | RC-30 | verified |
| LC-08 | Route tests cover nested JSON for both menu 243 paths | RC-45 | verified |
| LC-09 | Route tests cover nested malformed and missing files | RC-46 | verified |
| LC-10 | Route tests cover SQLite tables and denied paths | RC-48, RC-49 | verified |
| LC-11 | A browser test renders a nested JSON result | RC-51 | verified |
| LC-12 | A changelog fragment has a Fixed heading | RC-55 | verified |
| LC-13 | The streaming preview test module exists | RC-50 | verified |
| LC-14 | The discovery test lives at `tests/unit/test_operation_output_file_discovery.py` | RC-61 | absent |
| LC-15 | The path guard test lives at `tests/unit/test_data_browser_path_guard.py` | RC-62 | absent |
| LC-16 | The validated fix must include `Closes #4036` | RC-65 | stale |
| LC-17 | The feature selector names feature 4258 | RC-63 | stale |
| LC-18 | The plan states Python 3.13 | RC-64 | stale |
| LC-19 | `changelog.d` holds 272 direct children | RC-56 | stale |
| LC-20 | The legacy HEAD `fb7a7d10` is on main history | RC-72 | verified |
| LC-21 | Run `42339040613` exists and failed in Quality Gates | RC-74 | verified |
| LC-22 | `specs` holds 795 direct children | RC-57 | verified |
| LC-23 | PR #4081 merged on 2026-10-09 | RC-66 | verified |

## 3. Defects in existing work

- DF-01 The legacy validation list names two test paths. One path is absent [LC-14, LC-15]. Action: none in this record [D-09].
- DF-02 The legacy spec requires `Closes #4036`. PR #4615 used `Relates to #4036` [RC-67]. Action: decision D-04.
- DF-03 The legacy record reports acceptance on synthetic fixtures. The live symptom stays unverified [UR-01]. Action: T-MERGE.
- DF-04 The legacy plan states Python 3.13. The project floor is 3.15 [RC-08]. Action: none in this record [D-09].
- DF-05 The legacy plan counts 272 `changelog.d` children. The count on main is 335 [RC-56]. Action: separate remediation action in `plan.md`.
- DF-06 The legacy evidence cites feature 4258 as the selector. The selector names feature 4785 [RC-13]. Action: none. Read-only work must not change the selector.
- DF-07 Commit `18ce4c8` lacks inline comments on most lines and lacks action logs [research F-13]. Action: T005.
- DF-08 Commit `18ce4c8` defines `READY_TIMEOUT_MS`, which the target module already defines [test module line 36]. Action: T005 reuses the module constant.
- DF-09 `documentation/container-deployment.md` line 156 names a test profile in the command `podman compose --profile test up -d`. `compose.yml` defines only the `monitoring` profile [RC-11, RC-12]. Action: separate issue. This change does not own the document.
- DF-10 The PR #4081 body names the old discovery test path [RC-61]. Action: none. The path moved.

## 4. Open items

- OI-01 The live check on the deployed container. It runs at T-MERGE. Status: open [UR-01].
- OI-02 Pass or fail results for the new test and the red proof. They run at T005 and T007. Status: open [UR-05].
- OI-03 Whether the reporter data volume maps to `/app/data` [UR-09]. The live check records the observed path.
- OI-04 Removal of the scratch worktree after T007. Status: open.
- OI-05 A separate remediation issue for `changelog.d` direct children and for the container guide command in DF-09. Status: open. Open that issue under the repository issue rules.
