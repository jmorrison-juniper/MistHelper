# Tasks: Gated Converter Administration and Unassignment

**Input**: [Specification](spec.md), [plan](plan.md), and supporting artifacts under `design/`.

**Prerequisites**: This record authorizes offline design and synthetic tests only. No task starts a live Mist write.

**Tests**: Unit and integration tests are mandatory for each refusal and each outcome. Use synthetic objects and simulated SDK responses. Do not use a live credential.

**Organization**: Tasks follow the four user stories in `spec.md`. The dependency table controls the run order.

## Format and File Ownership

Each task has an ID, requirement IDs, explicit paths, an acceptance statement, a verification command, and a status.
Status values are `open`, `verified-present`, `partial`, or `absent`.
Add `(delivered: path)` only after the file exists and the verification command passes.
Each Python and JavaScript line that the task adds carries an inline comment.

Warning: Do not run a live Mist delete or unassign command. This record authorizes none.

## Phase 1: Prerequisites and Gates

- [ ] T001 Confirm the prerequisites and the owner decisions. Requirements: FR-003, FR-015, FR-023, FR-025. Paths: none. Acceptance: Issues 4634, 4636, and 4643 show the evidence this record needs. Owners record decisions D-1, D-2, and D-3 in issue 4645. Verification: `gh issue view 4645 -R jmorrison-juniper/MistHelper --json comments`. Status: open.
- [ ] T002 Reserve one converter root slot. Requirements: FR-025. Paths: `src/interfaces/portals/cisco_config_converter/conversion.py` (move to `engine/conversion.py`), `src/interfaces/portals/cisco_config_converter/routes.py`, and each test module that imports the moved module. Acceptance: The converter root holds five children. The `engine/` folder holds `__init__.py` and `conversion.py`. No shim remains. Verification: `python -m pytest tests/guardrails/test_move_module_guidance.py`. Status: absent.
- [ ] T003 Verify the Mist contract for each write, read, reference, and read-back in scope. Requirements: FR-013, FR-014, FR-015, FR-026. Paths: `design/contracts/mist-administration.md` and the issue 4634 evidence file. Acceptance: Each row in the contract shows `verified`. The unknowns UV-01 to UV-06 close. Verification: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`. Status: open.

## Phase 2: Tests First

- [ ] T004 [P] Create the test package. Requirements: FR-024. Paths: `tests/integration/web_portal/cisco_config_converter/administration/__init__.py`. Acceptance: The package holds a module docstring. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration -q`. Status: absent.
- [ ] T005 [P] Write the permission and refusal tests. Requirements: FR-001, FR-002, FR-003, FR-004, FR-024. Paths: `tests/integration/web_portal/cisco_config_converter/administration/test_permission.py`. Acceptance: The five tests fail before T010 and pass after it. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_permission.py -q`. Status: absent. Depends on T004.
- [ ] T006 [P] Write the scope and backup tests. Requirements: FR-005, FR-006, FR-007, FR-008, FR-012, FR-024. Paths: `tests/integration/web_portal/cisco_config_converter/administration/test_scope.py`. Acceptance: The seven tests cover explicit IDs, invalid input, digest changes, outside references, backup defects, and store failure. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_scope.py -q`. Status: absent. Depends on T004.
- [ ] T007 [P] Write the execution tests. Requirements: FR-009 to FR-020, FR-024. Paths: `tests/integration/web_portal/cisco_config_converter/administration/test_execute.py`. Acceptance: The eleven tests cover confirmations, approval expiry, reuse, changed state, unknown results, the stop rule, unrelated fields, and outcomes for each object. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_execute.py -q`. Status: absent. Depends on T004.
- [ ] T008 [P] Write the page tests. Requirements: FR-021, FR-022. Paths: `tests/integration/web_portal/cisco_config_converter/administration/test_administration_page.py`. Acceptance: The three tests cover the hidden page, the visible scope and backup status, and the disabled run control after a change. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_administration_page.py -q`. Status: absent. Depends on T004.

## Phase 3: Implementation

- [ ] T009 [P] Add the two variables to the environment template. Requirements: FR-001, FR-002, FR-027. Paths: `deploy/.env.example`. Acceptance: Variable `CISCO_CONVERTER_ADMIN_MODE` defaults to `disabled`. Variable `CISCO_CONVERTER_ADMIN_FAMILIES` defaults to an empty value. Each variable has a comment. Verification: `Select-String -LiteralPath deploy\.env.example -Pattern 'CISCO_CONVERTER_ADMIN_'`. Status: absent.
- [ ] T010 Create the administration package. Requirements: FR-001 to FR-020, FR-025, FR-026. Paths: `src/interfaces/portals/cisco_config_converter/engine/administration/__init__.py`, `permission.py`, `scope.py`, `executor.py`, and `outcome.py`. Acceptance: Each class holds five members or fewer. Each function holds 25 lines or fewer. The tests from T005 to T007 pass. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration -q`. Status: absent. Depends on T001, T002, T003, T005, T006, and T007.
- [ ] T011 Register the administrative routes. Requirements: FR-001 to FR-004, FR-009, FR-023. Paths: `src/interfaces/portals/cisco_config_converter/routes.py`. Acceptance: `ConverterRoutes.blueprint` registers `/admin`, `/admin/scope`, `/admin/approve`, and `/admin/execute`. Class `AdministrationRoutes` holds four members. The module holds five top-level names. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter -q`. Status: absent. Depends on T010.
- [ ] T012 Add the page template and script. Requirements: FR-021, FR-022. Paths: `src/interfaces/portals/cisco_config_converter/presentation/administration.html` and `src/interfaces/portals/cisco_config_converter/presentation/administration.js`. Acceptance: Each control has a `data-testid` value. The script writes output with `textContent`. The run control stays disabled until the review is current. Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_administration_page.py -q`. Status: absent. Depends on T011.
- [ ] T013 [P] Add the changelog fragment. Requirements: FR-028. Paths: `changelog.d/issue-4645-converter-administration.md`. Acceptance: The fragment holds one `###` heading and one bullet. The bullet names issue 4645. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: absent.

## Phase 4: Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies. Requirements: FR-024, FR-025, FR-026. Paths: each changed file in `plan.md`. Acceptance: Each gate reports its expected result. Each skipped gate has a stated reason. Verification: the commands in `design/quickstart.md`, Scenario 6. Status: open. Depends on T010, T011, T012, and T013.
- [ ] T-PR Commit, push, and open the pull request. Requirements: FR-028. Paths: the changed files and this record. Acceptance: The commit and the pull request title use Conventional Commits, for example `feat(web-portal): add gated converter administration`. The body holds `Closes #4645`, the gate results, and the count of removed non-comment lines. Verification: `gh pr view -R jmorrison-juniper/MistHelper --json title,body` run on the pull request branch. Status: open. Depends on T-LOCAL-GATES.
- [ ] T-REMOTE-CI Watch the remote checks. Requirements: FR-024. Paths: none. Acceptance: Each required check and the CodeQL check report success. Verification: `gh pr checks -R jmorrison-juniper/MistHelper --watch` run on the pull request branch. Status: open. Depends on T-PR.
- [ ] T-MERGE Obtain human review and squash merge. Requirements: FR-003, FR-023. Paths: none. Acceptance: A human reviews the destructive-operation change (decision D-14). The pull request carries no `auto-merge` label. After the merge, the main build of `container-build.yml` completes. Verification: `gh run list -R jmorrison-juniper/MistHelper --workflow container-build.yml --branch main --limit 1`. Status: open. Depends on T-REMOTE-CI.

## Dependencies and Execution Order

| Task | Prerequisites |
| --- | --- |
| T001 | None |
| T002 | T001 |
| T003 | T001 |
| T004 | None |
| T005 | T004 |
| T006 | T004 |
| T007 | T004 |
| T008 | T004 |
| T009 | T001 |
| T010 | T001, T002, T003, T005, T006, T007 |
| T011 | T010 |
| T012 | T011 |
| T013 | None |
| T-LOCAL-GATES | T010, T011, T012, T013 |
| T-PR | T-LOCAL-GATES |
| T-REMOTE-CI | T-PR |
| T-MERGE | T-REMOTE-CI |

### Parallel Work

- After T004, tasks T005, T006, T007, and T008 use separate test files. Each file can proceed in parallel.
- Task T009 and task T013 touch files that no other task edits. Each can proceed in parallel with the test tasks.
- Do not edit `routes.py` in parallel with T011. Tasks T010 and T011 share the import path that T002 changes.

## Implementation Strategy

Start with T001 and T002. Do not add source code before the owners answer the three decisions. Write the tests before the code. Stop the run at the first failed gate. Do not deploy from this record.
