# Tasks: Validate menu 309 with an MSP login

**Input**: Numeric record at `specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/`, and `design/checklists/requirements.md`.

**Tests**: Each task names one automated test or one gate command. The live check is a human-only step. The implementer runs no part of it.

## Format

- `[P]` means the task is safe in parallel.
- `[FR-###]` lists the requirements that the task covers.
- Each path is an exact repository path.
- Each verification command comes from the local gates table, or it names an existing test.
- Status is one of: open, verified-present, partial, or absent.

## Phase 1: Agent checks (no credential, no live request)

- [ ] **T001** [P] [FR-012, FR-013, FR-014] Verify the remote table and the checkout SHA.
  - Paths: each path in the remote table of `design/research.md` (rows R-01 to R-93). The MSP scope test is `tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py`.
  - Acceptance: each row keeps its blob SHA and its line on `main`. The checkout SHA equals the SHA of `main`. A changed row updates `design/research.md`.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py`
  - Status: verified-present. The author checked each row on 2026-11-26 at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The implementer repeats the check before the owner starts.

- [ ] **T002** [P] [FR-003, FR-016] Check the step 1 console lines.
  - Paths: `tests/unit/ex_hardware_inventory/test_hardware_operation.py` (line 329) and `src/operations/exporting/ex_hardware_inventory/console.py` (lines 38 to 48).
  - Acceptance: the test passes. Its expected credential line matches `console.py`.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - Status: verified-present.

- [ ] **T003** [P] [FR-013, FR-016] Check the two-factor prompt text.
  - Paths: `tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py` (lines 113 to 118) and `src/mist/access/auth/interactive/credential_prompter.py` (line 57).
  - Acceptance: the test passes. It asserts the prompt `  Enter 2FA code: `.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py`
  - Status: verified-present.

- [ ] **T004** [P] [FR-013, FR-016] Check the two-factor replay and the success message.
  - Paths: `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` (lines 463 and 546) and `src/mist/access/auth/interactive/login_orchestrator.py` (lines 199, 202, and 230).
  - Acceptance: the test passes. The replay sends the code as `two_factor`. The success line is `  + Login successful!`.
  - Verification: `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py`
  - Status: verified-present.

- [ ] **T005** [P] [FR-013] Check that a password login sends its cookies.
  - Paths: `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py` (line 79).
  - Acceptance: the test passes. A password login sends its cookies and no token header.
  - Verification: `python -m pytest tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`
  - Status: verified-present.

- [ ] **T006** [P] [FR-005, FR-013] Check the outcome row of an unread organization in the CSV report.
  - Paths: `tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py` (line 108) and `src/operations/exporting/ex_hardware_inventory/operation.py` (line 130).
  - Acceptance: the test passes. One unread organization gives one outcome row.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py`
  - Status: verified-present.

- [ ] **T007** [P] [FR-005, FR-013] Check the element of an unread organization in the master XML file.
  - Paths: `tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py` (line 439) and `src/operations/exporting/ex_hardware_inventory/run/master_xml.py` (lines 414 and 416).
  - Acceptance: the test passes. One unread organization gives one element with `status="failed"` and no site.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py`
  - Status: verified-present.

- [ ] **T008** [P] [FR-004, FR-005, FR-013] Check the MSP integration run.
  - Paths: `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` (line 400).
  - Acceptance: the test passes. Each organization of the MSP run is listed. The unread organization has no site.
  - Verification: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`
  - Status: verified-present.

## Phase 2: Record and documentation changes (implementer)

- [ ] **T009** [P] [FR-013, FR-017] Remove the unverified refusal sentence from the operator guide.
  - Paths: `documentation/operator-guide.md` (lines 620 to 623, the Caution about the login session).
  - Acceptance: the Caution keeps the sentence "The profile field `session_expiry` gives that lifetime in minutes." It removes the sentence that starts "After that time, Mist refuses the requests of the session." It keeps the advice "Use a token for a long run."
  - Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
  - Status: partial. The lifetime sentence is verified (R-62, R-87). The refusal sentence is unverified (U-02).

- [ ] **T010** [P] [FR-018] Add one changelog fragment.
  - Paths: `changelog.d/issue-4925-menu-309-msp-validation.md` (new file).
  - Acceptance: the file has one `### Changed` heading and one bullet. The bullet names issue #4925 and states the operator guide change in one sentence.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open.

## Phase 3: Live check (human-only)

- [ ] **T011** [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-015] Human-only: run the CLI live check.
  - Paths: `src/operations/exporting/ex_hardware_inventory/console.py` (lines 38 to 48, 62, 81, and 90), `design/contracts/msp-console-lines.md`, and `design/contracts/live-msp-evidence.md`.
  - Acceptance: the owner completes the steps in `design/quickstart.md`, section 3. The owner posts counts only on issue #4925, in the form of `design/contracts/live-msp-evidence.md`. A failed check opens a new issue that names the cause.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py` must pass first (task T002).
  - Status: open. Human-only. The implementer uses no credential.

- [ ] **T012** [FR-011, FR-015] Human-only: run the portal check.
  - Paths: `src/mist/realtime/websocket_streams/web/static/websockets.js` (lines 784 and 785) and `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` (line 194).
  - Acceptance: the preview scope line starts with `Scope: MSP,`. The output choice `One combined CSV report (.csv)` exists. The owner posts a counts-only result.
  - Verification: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` must pass first (task T008).
  - Status: open. Human-only.

## Phase 4: Delivery (final tasks)

- [ ] **T-LOCAL-GATES** [FR-013, FR-017, FR-018, FR-019] Run each local gate that applies to the changed files.
  - Paths: every Markdown file of the record, `documentation/operator-guide.md`, and `changelog.d/issue-4925-menu-309-msp-validation.md`.
  - Gates that apply, with commands:
    - STE: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/spec.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/plan.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/tasks.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/analysis.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/research.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/data-model.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/quickstart.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/contracts/msp-console-lines.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/contracts/live-msp-evidence.md specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/checklists/requirements.md`
    - Tests: `python -m pytest tests/guardrails/test_process_folder_structure.py`, `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`, and `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.
    - Not applicable: compile, lint, format, types, full tests, safe sweep, coverage, test quality, complexity, security lint, dependency audit, code quality, dead code, docstrings, menu reference, symbols, ops portal, and ops platform. This change has no Python file, no menu text, no npm file, and no changed symbol.
  - Acceptance: each file scores 80 or above. Each guard passes. The gate output is part of the pull request body.
  - Verification: the STE command above.
  - Status: open.

- [ ] **T-PR** [FR-014, FR-019] Commit, push, and open the pull request.
  - Paths: the record folder `specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/`, `documentation/operator-guide.md`, and `changelog.d/issue-4925-menu-309-msp-validation.md`.
  - Acceptance: add the label `in-progress` to issue #4925 before the branch exists. Create the branch `chore/4925-menu-309-msp-validation` from `main`. The commit subject is `docs(specs): record the menu 309 MSP validation`, with the Co-authored-by trailer. The pull request title uses the same subject. The body contains `Refs #4925` and does not contain `Closes #4925`, under decision D-3. Set the labels `chore` and `docs`. Check the open pull requests for a file overlap before the push.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: open.

- [ ] **T-REMOTE-CI** [FR-013] Wait for the remote checks.
  - Acceptance: every required check passes on the pull request head, including CodeQL. Add the `auto-merge` label only after each check is green.
  - Verification: `gh pr checks --watch` run on the record branch.
  - Status: open.

- [ ] **T-MERGE** [FR-019] Merge after the orchestrator authorizes the merge.
  - Acceptance: the orchestrator authorizes the merge. The squash merge removes the branch. Issue #4925 stays open after the merge, because task 5 is open.
  - Verification: `gh pr view --json state,mergedAt` run on the record branch shows the state `MERGED` after the merge.
  - Status: open.

## Dependencies and Execution Order

- Tasks T001 to T010 are parallel. Each touches a different file or only reads one.
- Task T011 needs tasks T001 to T008. Task T012 needs task T011.
- Task T-LOCAL-GATES needs tasks T009 and T010.
- Task T-PR needs task T-LOCAL-GATES. Task T-REMOTE-CI needs task T-PR. Task T-MERGE needs task T-REMOTE-CI and the orchestrator authorization.
- The live check (tasks T011 and T012) does not block the record pull request.

## Traceability

Tests:

| ID | Test or gate | Task |
| - | - | - |
| TST-01 | `tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py` | T001 |
| TST-02 | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | T002 |
| TST-03 | `tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py` | T003 |
| TST-04 | `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` | T004 |
| TST-05 | `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py` | T005 |
| TST-06 | `tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py` | T006 |
| TST-07 | `tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py` | T007 |
| TST-08 | `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` | T008 |
| TST-09 | `tests/guardrails/test_hardware_shell_lock_docs.py` | T009 |
| TST-10 | `tests/guardrails/test_changelog_fragment_policy.py` | T010 |
| TST-11 | `tests/guardrails/test_process_folder_structure.py` | T-PR |
| TST-12 | STE gate on the record files and the operator guide | T-LOCAL-GATES |
| TST-13 | Human-only CLI live check | T011 |
| TST-14 | Human-only portal check | T012 |

Requirements:

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T011, T012 | TST-13, TST-14 |
| FR-002 | T011 | TST-13 |
| FR-003 | T002, T011 | TST-02, TST-13 |
| FR-004 | T008, T011 | TST-08, TST-13 |
| FR-005 | T006, T007, T008, T011 | TST-06, TST-07, TST-08, TST-13 |
| FR-006 | T011 | TST-13 |
| FR-007 | T011 | TST-13 |
| FR-008 | T011 | TST-13 |
| FR-009 | T011, T012 | TST-13, TST-14 |
| FR-010 | T011 | TST-13 |
| FR-011 | T012 | TST-14 |
| FR-012 | T001 | TST-01 |
| FR-013 | T001 to T010, T-LOCAL-GATES | TST-01 to TST-12 |
| FR-014 | T001, T-PR | TST-01, TST-11 |
| FR-015 | T011, T012 | TST-13, TST-14 |
| FR-016 | T002, T003, T004 | TST-02, TST-03, TST-04 |
| FR-017 | T009, T-LOCAL-GATES | TST-09, TST-12 |
| FR-018 | T010, T-LOCAL-GATES | TST-10, TST-12 |
| FR-019 | T-PR, T-MERGE | TST-11 |
