# Analysis: Upgrade Portal Session Recovery

This review checks the spec, the plan, the tasks, and the remote code against each other. It also lists defects in existing work and the open items that need an owner.

## Consistency Review

| ID | Check | Result |
| - | - | - |
| C-01 | The spec lists 24 functional requirements (FR-001 to FR-024). The coverage table in tasks.md lists the same 24. | Consistent |
| C-02 | tasks.md lists 21 tasks: T001 to T017 and four delivery tasks. STATUS.json reports 21. | Consistent |
| C-03 | tasks.md lists 28 planned tests (TP-01 to TP-28). STATUS.json reports 28. | Consistent |
| C-04 | Decisions D-1 to D-20 appear in the research record. The plan and the tasks cite them by the same IDs. STATUS.json lists the same 20. | Consistent |
| C-05 | The remote table in research.md has 78 rows. The database table holds 78 rows. STATUS.json reports 78 `remote_checks` objects with 70 present and 8 absent. | Consistent |
| C-06 | The protected-handler counts total 51: capture 6, org_controls 4, org_precheck 1, org_upgrade 7, review 6, select 12, upgrade 15 (RC-23 to RC-29). | Consistent |
| C-07 | The file change map in plan.md equals the file lists in tasks.md. Test files are the four existing contract and unit modules, and no new test module appears. | Consistent |
| C-08 | The new module path `persistence/session_store.py` matches the placement decision (D-14) and the child counts (RC-21). | Consistent |
| C-09 | The mistapi calls in the spec (constructor, `login`, `getSelf`) match D-20 and the mapping in RC-55 and RC-56. | Consistent |
| C-10 | Every requirement and success criterion has at least one task and one test. The coverage tables in tasks.md show the mapping. | Consistent |
| C-11 | The spec states the organization pick survives replacement. The code stores it in the signed session (RC-28, `select.py:621` and `select.py:1875`). | Consistent |
| C-12 | The spec states that site selections do not survive replacement. The site list lives in the registry record (`identity.py:491`). | Consistent |

## Defects in Existing Work

| ID | Defect | Evidence | Handling |
| - | - | - | - |
| A-1 | The issue body names `src/upgrade_portal/runtime/identity.py`. That path does not exist on main. | RC-39 absent, RC-01 present | Corrected in spec.md Clarifications |
| A-2 | The issue body names a proof test that does not exist on main. Its "3 passed" result cannot be reproduced. | RC-38 absent, U-1 | T013 creates the restart contract in an existing module |
| A-3 | The assessment comments cite capture Gunicorn lines 312 to 321 and 315 to 318. Main places the capture command at lines 321 to 327. | RC-10 | Cited from main in this record |
| A-4 | The assessment says that no credential redaction filter protects the portal logger. The factory installs `SensitiveFilter`. The filter is pattern based. | RC-05, RC-16 | D-13 keeps the filter and adds TP-22 |
| A-5 | The legacy draft and the assessment state "51 handlers across 13 route files". Seven route files hold the 51 handlers. | LC-05, RC-23 to RC-29 | Corrected in research.md |
| A-6 | Base revisions in the legacy record: efd0828 (issue comment 2), d82f715 (comments 4 and 5 and the legacy spec), and f1505203 (the legacy plan). Main is f03c6c9. | RC-49 to RC-52 | This record uses f03c6c9 |
| A-7 | The legacy plan passes the five-item rule for a new module in `runtime/`. The folder holds ten children. | LC-12, RC-20 | D-14 places the module in `persistence/` |
| A-8 | The legacy plan adds seven batches with 51 route edits. One guard covers every route. | LC-16, RC-23 to RC-29 | D-18 replaces the batches |
| A-9 | The legacy success criterion SC-005 asks to preserve live sessions through the migration. The old process holds sessions in memory, so a new process cannot read them. | `identity.py:516` | D-19 accepts one planned sign-in |
| A-10 | The compose file defines a literal default for `REDIS_PASSWORD`, and the Redis service applies it as `requirepass`. | RC-12 | D-2 requires a change before activation |
| A-11 | The local checkout differs from remote main for `src/foundation/support/utils/logger_utils.py`. The local blob is `b47036046770f9a36aaecaff1e2821f165ed66df`. The remote blob is `6cb99dc0e3e0a4808391e6953560071b69e36683`. | Local hash, RC-16 | The branch starts from remote main. The local change stays out of the commit. |
| A-12 | Issue #2708 reserves `tests/contract/upgrade_portal/test_no_credential_leak.py`. The issue was updated on 2026-11-17. | RC-32 | FR-023 and T002 |
| A-13 | Draft PR #4208 changes `deploy/.env.example`. | Open PR list | T003 coordinates the edit |
| A-14 | Issue #3714 carries the `in-progress` label. The issue body asks to keep the issue unclaimed until approval. | Issue labels | STATUS.json recommends removing the label |
| A-15 | Five-item debt: `runtime/` holds 10 children, `app/` holds 10, `app/routes/` holds 13, `upgrade_portal/` holds 12, `upgrade/` holds 22, `tests/unit/upgrade_portal/` holds 168, and `tests/contract/upgrade_portal/` holds 66. | RC-20, RC-72 to RC-76, RC-78 | D-17. OI-3 covers the remediation issue. |
| A-16 | The module `auth/session.py` defines a JWT session manager. The sign-in path does not import it. Its only other users are a unit test and a file under `junk/`. | RC-19 | The spec does not use it. OI-4 covers cleanup. |
| A-17 | The run driver keeps its threads in a class dictionary. Its daemon threads stop at a worker replacement. | RC-17 | D-12. OI-1 covers the separate issue. |
| A-18 | Existing tests register records in the registry directly. GitHub code search returned at least 30 files for `SESSION_REGISTRY`, and the search stopped at its limit. | GitHub code search, limit 30 reached | The registry-hit path keeps those tests valid. OI-2 covers the enumeration before T012 and T013. |
| A-19 | The portal writes `_MAX_429_RETRIES` on the SDK object at `auth.py:364` and `auth.py:378`. | Local file hash equals RC-07 blob | Out of scope. The new code does not write private attributes. |
| A-20 | The test at `test_identity.py:1647` asserts that sign-out after a worker replacement returns False. The new design changes that result. | RC-31 | T012 replaces the assertion |
| A-21 | The operator guide states that the portal does not store the token (`upgrade_capture_portal.md:192`). The statement holds only under D-1 option (a). | RC-69 | D-1 is HUMAN-DECISION-REQUIRED |
| A-22 | The README holds no sign-in behavior text. It links the operator guide at line 42. | RC-70 | D-16 changes the guide only |
| A-23 | The legacy draft pull request closed without merge. Its check rollup shows failures in the coverage shards and the coverage gate. | PR 4018 status rollup | The legacy draft is not reused as a file set |
| A-24 | The mistapi private state includes `_apitoken`, `_apitoken_index`, `_csrftoken`, and `_session`. The constitution requires a contract test that pins these names when an owned transport exists. The feature owns no transport. | RC-55 | No pin is needed. The feature reads no private attribute. |

## Open Items

| ID | Item | Owner | Blocks |
| - | - | - | - |
| OI-1 | File a separate issue for run driver recovery (A-17). | Orchestrator | No task. The issue must exist before the release. |
| OI-2 | Enumerate every direct `SESSION_REGISTRY` reference in committed files, then list the test files that call the sign-in path. | Implementer | T012 and T013 |
| OI-3 | File a remediation issue for the five-item debt (A-15). | Orchestrator | No task. The issue must exist before the next new module in those parents. |
| OI-4 | Decide the fate of `auth/session.py` (A-16). | Owner | No task |
| OI-5 | Approve D-1 and D-2 (HUMAN-DECISION-REQUIRED). | Owner | T005, T006, T016 |
| OI-6 | Obtain the handoff of `test_no_credential_leak.py` from issue #2708 (A-12). | Issue #2708 owner | T-PR |
| OI-7 | Coordinate `deploy/.env.example` with draft PR #4208 (A-13). | PR #4208 owner | T008 |
| OI-8 | Remove the `in-progress` label from issue #3714 (A-14). | Orchestrator | None |
| OI-9 | Announce the one planned sign-in at deployment (D-19 and A-9). | Operations owner | Deployment |
| OI-10 | Replace the compose default Redis password before activation (A-10). | Operations owner | Activation, after D-2 |

## Coverage Summary

- Requirements: 24. Every requirement maps to at least one task and one test (tasks.md, Requirement Coverage).
- Success criteria: 8. Every criterion maps to a test or to a gate (tasks.md, Success Criteria table).
- Planned tests: 28. Each test names one file and one requirement.
- Legacy draft claims: 19. The verdicts are 10 verified, 7 stale, and 2 absent (research.md).
