# Specification Analysis Report: Mist Identity Object Sign-In

This report checks the spec, the plan, the tasks, and the remote code. Row numbers name the remote verification rows in design/research.md.

## Findings

| ID | Severity | Finding | Evidence | Action |
|----|----------|---------|----------|--------|
| A-01 | High | Pull request #1896 changed the list layer that holds the drop rule. The diff was not read. Caution: a valid identity object never reaches sign-in, and each valid token fails. | R01 (endpoints.py line 316), R09 (auth.py line 123), R78 (merge commit on main), R19 (test pins the drop) | Repair in this change (D-1, D-3). |
| A-02 | High | Warning: derived from source reading. When both `MIST_HOST` and `MIST_APITOKEN` are set, the SDK installs the environment token during construction. A rejected supplied token leaves that token active, so the identity read then belongs to the environment token. The dictionary drop masks this path today. Fixing A-01 alone exposes it. | R81, R84 (SDK environment reads), R82, R83 (token installation), R06, R07 (`_fetch_self` call and session) | Repair in this change with the active-token check (D-4, D-5). Runtime behavior is unverified (see research Unverified list). |
| A-03 | Medium | The middleware stores returned privileges on the session record before the 401 check. The record then reuses them for 300 seconds, so Caution: an empty result persists for the window. | R12 (store call), R13 (freshness constant), R11 (401 check) | Follow-up issue (D-8). |
| A-04 | Medium | Sign-in caches the supplied token for workers after a successful login. The active-token check prevents a wrong token from reaching that cache. | R16 (cache call), R15 (login rejection) | No further action. The check covers the path. |
| A-05 | Medium | One environment-token call remains for each validation when both variables are set. The check discards that identity. | R81, R84 | Follow-up issue for environment isolation (D-8). |
| A-06 | High | `auth.py` is reserved for the local repair of issue #4748. Issue #4748 also changes `_fetch_self`. | Issue comment IC_kwDOQltU8c8AAAABk_UEwg, R06 | Task T001 checks the release. Sequence per D-6. |
| A-07 | Low | Folder debt: `src/shared/services` (7), `tests/unit/mist` (17), `tests/unit/api` (11), `changelog.d` (335). | R27, R29, R30, R28 | Separate remediation issues. The change adds no child to these folders except the fragment. |
| A-08 | Low | Documentation drift. The constitution states mistapi 0.59 or later. The brief pins 0.64.x. | R57 and R87 | Separate documentation issue. |
| A-09 | Info | Issue #1884 describes `_extract_list` as wrapping a dictionary into a one-element list. The current code drops it (R01). The issue text describes the code before pull request #1896. | Issue #1884 body, R01, R78 | No code action. This record uses the current code as the baseline. |
| A-10 | Info | `test_consumer_registry_usage.py` calls `_fetch_self` on a 200 path with a mocked SDK. The test asserts only the call. The active-token check returns empty privileges in that case. | R20 | Expected to pass. Not executed in this record. |
| A-11 | Info | Issue comment IC_kwDOQltU8c8AAAABk_ehTA reports that a mocked 401 blocked a valid supplied-token sign-in. This record cannot reproduce that control. The mechanism in A-02 gives a different account. | Issue comment IC_kwDOQltU8c8AAAABk_ehTA, R81 to R85 | Task T006 tests the mechanism with mocks. |
| A-12 | Medium | The record names the environment-token path at source level. Security wording in a shared record needs review. | research Decision D-9 and checklist security.md | Review the security checklist before the record is committed. |

## Coverage Summary

| Requirement | Tasks | Tests or gate |
|-------------|-------|---------------|
| FR-001 | T003, T004, T007, T008 | TC-01, TC-03 |
| FR-002 | T007, T008 | TC-04, TC-05 |
| FR-003 | T007 | TC-02 |
| FR-004 | T003, T008 | TC-07 and the existing test at R19 |
| FR-005 | T008 | TC-06 |
| FR-006 | T009 | TG-01 |
| FR-007 | T009 | TG-02, TG-03, TG-04 |
| FR-008 | T009, T012 | TG-05, TG-06, existing tests at R21 and R22 |
| FR-009 | T007, T008, T009, T011 | TG-01 asserts the info and debug lines |
| FR-010 | T011 | TG-02 asserts that no token value appears in the log text |
| FR-011 | T004, T013 | TC-01 patches the SDK method and asserts one call |
| FR-012 | T010 | STE gate in T010. The record has no pytest case for documentation. |

Every requirement maps to at least one task and at least one test or gate. The mapping covers spec.md section Requirements.

## Consistency Review

- The spec names thirteen new contract tests. The plan and tasks name the same thirteen (TC-01 to TC-07 and TG-01 to TG-06).
- The spec, plan, and tasks name the same four existing test modules. Each module is listed at research rows R19, R20, R21, R22, and R23.
- The plan names the same six paths as the tasks. The tasks name the same change set.
- The research table lists ninety-one remote checks. The STATUS file and the summary report the same count.
- No task contradicts the sequencing rule. T009 follows T001, and T001 checks the reserved file.

## Constitution Alignment

- Principle I (five-item rule): Pass. No new child in a noncompliant folder. Existing debt is recorded.
- Principle II (class-based design): Pass. New methods sit in existing classes.
- Principle III (safety first): Pass. The token check fails closed.
- Principle IV (full pipeline): Pass with tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- Principle V (observability): Pass. ASCII logs. No token values.
- Principles VI and VII (inline comments and action logging): Pass when T011 completes.

No constitution principle fails.

## Unmapped Tasks

None. Each task maps to a requirement, a success criterion, or a final gate.

## Metrics

- Requirements: 12 (FR-001 to FR-012).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 17 (T001 to T013 and four final tasks).
- New tests: 13 (seven contract cases and six guard cases).
- Remote verification rows: 91.
- Decisions: 10 (D-1 to D-10). Human decisions: 0.

## Convergence After Implementation

The change is complete when each condition holds.

1. The 13 new tests pass.
2. The four existing modules pass with no edit.
3. The Ops platform gate reports at least 390 collected tests and coverage of at least 56 percent.
4. The changed file list equals the six paths in plan.md.
5. The symbol gate reports no module-level name changed.
6. The lint gate reports no finding on the changed files.

## Unresolved Items

1. Environment isolation for the SDK session (A-05). Open a follow-up issue with the security label.
2. Negative caching of empty privileges on the session record (A-03). Open a follow-up issue.
3. Folder splits (A-07). Open follow-up issues for the services folder and the two test folders.
4. The constitution mistapi bullet (A-08). Open a documentation issue.
5. Coordination with issue #4748 (A-06). The reservation holder releases `auth.py`.
6. The live shape of the `/self` response is not observed. This record relies on the OpenAPI contract only.
7. The Ops platform test baseline (T002) is not measured in this record.
