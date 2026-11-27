# Tasks: Migrate Mist Guest Authorizations

**Input**: spec.md, plan.md, design/research.md, design/data-model.md, design/quickstart.md, and the four contracts under design/contracts/.

**Format**: Each row gives the task ID, the parallel marker, requirement IDs, exact paths, acceptance, one verification command, and status. The parallel marker is `[P]` when safe in parallel and `seq` otherwise. Status values are open, verified-present, partial, and absent.

**Prerequisites**: Phase 0 closes before any write route. Writes also need gate G5.

## Phase 0: Gates and Decisions

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | seq | FR-005 | design/research.md (D-11) | Maintainers record the operator identity method with a dated decision. | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |
| T002 | seq | FR-028 | design/research.md (D-13) | Maintainers record the licensing path for any reuse of source expression. | `python -m pytest tests/guardrails/test_guest_access_topology.py` | open |
| T003 | seq | FR-012, FR-013, FR-016 | design/contracts/mist-api.md | Gate G5 closes for WLAN binding, revoke semantics, and list shape. | `python -m pytest tests/contract/guests/test_guest_gateway.py` | open |
| T004 | [P] | FR-027 | tests/guardrails/nested_package_baseline.json, tests/guardrails/test_nested_package_structure.py | The guard and baseline exist, and `src/interfaces/portals` holds five children. | `python -m pytest tests/guardrails/test_nested_package_structure.py` | verified-present |
| T005 | seq | FR-001 | web_portal/app.py, web_portal/templates/base.html | PR #4208 hands over both files in writing before any edit. | `python -m pytest tests/guardrails/test_nested_package_structure.py` | open |

## Phase 1: Foundation

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T006 | [P] | FR-007, FR-008, FR-027 | src/interfaces/portals/guest_authorizations.py (delete), src/interfaces/portals/guest_authorizations/__init__.py, src/interfaces/portals/guest_authorizations/read_model.py, tests/unit/web_portal/test_guest_authorization_read_model.py | The projection moves into the package with unchanged output fields. The test imports the new module path. | `python -m pytest tests/unit/web_portal/test_guest_authorization_read_model.py` | open |
| T007 | [P] | FR-016, FR-017, FR-018, FR-021, FR-028 | src/mist/access/guests/__init__.py, src/mist/access/guests/gateway.py, src/mist/access/guests/responses.py | The gateway calls only allowlisted mistapi functions with keyword arguments. It classifies responses as the contract states. | `python -m pytest tests/contract/guests/test_guest_gateway.py` | open |
| T008 | seq | FR-016, FR-017, FR-018, FR-021, FR-028 | tests/contract/guests/test_guest_gateway.py | TC-022 to TC-026 pass offline with zero live calls. | `python -m pytest tests/contract/guests/test_guest_gateway.py` | open |
| T009 | [P] | FR-009, FR-011, FR-014, FR-015 | src/interfaces/portals/guest_authorizations/workflows/domain.py, tests/unit/web_portal/test_guest_authorization_domain.py | Validation, typed words, and hashes pass TC-001 to TC-008. | `python -m pytest tests/unit/web_portal/test_guest_authorization_domain.py` | open |
| T010 | [P] | FR-003, FR-019, FR-020 | src/interfaces/portals/guest_authorizations/workflows/journal.py, tests/unit/web_portal/test_guest_authorization_journal.py | Journal read-back, unknown states, and scope locks pass TC-011 to TC-013. | `python -m pytest tests/unit/web_portal/test_guest_authorization_journal.py` | open |
| T011 | [P] | FR-026, FR-030 | src/interfaces/portals/guest_authorizations/workflows/audit.py, tests/unit/web_portal/test_guest_authorization_audit.py | Audit events mask MAC addresses, and captured logs hold no secrets (TC-014 and TC-015). | `python -m pytest tests/unit/web_portal/test_guest_authorization_audit.py` | open |
| T012 | seq | FR-012, FR-013, FR-015, FR-016, FR-018, FR-019, FR-020 | src/interfaces/portals/guest_authorizations/workflows/changes.py, tests/integration/web_portal/test_guest_authorizations.py | Change orchestration passes TC-031 to TC-037 with zero-write checks. | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |
| T013 | seq | FR-001, FR-002 | web_portal/app.py, web_portal/templates/base.html | After the T005 handover, the blueprint registers. The tab shows only when `GUEST_ACCESS_ENABLED` is true (TC-045). | `python -m pytest tests/e2e/web_portal/test_guest_authorizations.py` | open |

## Phase 2: Review (User Story 1)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T014 | seq | FR-001, FR-005, FR-006, FR-007, FR-008, FR-029, FR-030 | src/interfaces/portals/guest_authorizations/presentation/routes.py, src/interfaces/portals/guest_authorizations/presentation/templates/guest_access.html, src/interfaces/portals/guest_authorizations/presentation/static/guest_access.js, src/interfaces/portals/guest_authorizations/read_model.py | The review page, selectors, masked table, and unknown states follow the portal contract (TC-031, TC-033, TC-046). | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |
| T015 | [P] | FR-002, FR-004, FR-027, FR-028 | tests/guardrails/test_guest_access_topology.py | TC-028 to TC-030 pass. | `python -m pytest tests/guardrails/test_guest_access_topology.py` | open |
| T016 | [P] | FR-001 | deploy/.env.example, README.md | `GUEST_ACCESS_ENABLED` documents a default of false. No secret value appears. | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` | open |

## Phase 3: Grant (User Story 2)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T017 | seq | FR-009, FR-014, FR-015, FR-016, FR-019, FR-020 | src/interfaces/portals/guest_authorizations/presentation/routes.py, src/interfaces/portals/guest_authorizations/workflows/changes.py, src/mist/access/guests/gateway.py | The grant route sends one PUT and one reconciliation read. It runs only after gate G5 closes (D-16). | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |
| T018 | seq | FR-014, FR-029, FR-030 | tests/e2e/web_portal/test_guest_authorizations.py | TC-047 proves the typed word GRANT and the reviewed summary. | `python -m pytest tests/e2e/web_portal/test_guest_authorizations.py` | open |

## Phase 4: Edit and Extend (User Stories 3 and 4)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T019 | seq | FR-010 | src/interfaces/portals/guest_authorizations/presentation/routes.py, src/interfaces/portals/guest_authorizations/workflows/domain.py, src/mist/access/guests/gateway.py | Edit sends allowlisted fields only. Name input fails before any call (TC-027 and TC-035). | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |
| T020 | seq | FR-011 | src/interfaces/portals/guest_authorizations/workflows/domain.py, src/interfaces/portals/guest_authorizations/presentation/routes.py | Extension applies the duration bounds and shows the UTC expiry before confirmation (TC-004 and TC-041). | `python -m pytest tests/unit/web_portal/test_guest_authorization_domain.py` | open |

## Phase 5: Revoke (User Story 5)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T021 | seq | FR-012, FR-013, FR-018 | src/interfaces/portals/guest_authorizations/workflows/changes.py, src/mist/access/guests/gateway.py, src/interfaces/portals/guest_authorizations/presentation/routes.py | Revoke checks the WLAN, sends minutes 0, reconciles, and never retries (TC-038 to TC-040). | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |

## Phase 6: Client Search (User Story 6)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T022 | seq | FR-021, FR-030 | src/mist/access/guests/gateway.py, src/interfaces/portals/guest_authorizations/presentation/routes.py, src/interfaces/portals/guest_authorizations/presentation/templates/guest_access.html | Client search filters the selected site and masks MAC addresses (TC-044). | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |

## Phase 7: Import (User Story 7)

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T023 | [P] | FR-022, FR-023 | src/interfaces/portals/guest_authorizations/imports.py, tests/unit/web_portal/test_guest_authorization_imports.py | CSV limits, headers, duplicates, and the minutes rule pass TC-016 to TC-020. | `python -m pytest tests/unit/web_portal/test_guest_authorization_imports.py` | open |
| T024 | seq | FR-023, FR-024, FR-025 | src/interfaces/portals/guest_authorizations/presentation/routes.py, src/interfaces/portals/guest_authorizations/workflows/changes.py, tests/integration/web_portal/test_guest_authorizations.py | The preview, typed word IMPORT, sequential run, and stop rules pass TC-021, TC-042, and TC-043. | `python -m pytest tests/integration/web_portal/test_guest_authorizations.py` | open |

## Phase 8: Validation and Documentation

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T025 | seq | FR-029 | tests/e2e/web_portal/test_guest_authorizations.py, src/interfaces/portals/guest_authorizations/presentation/templates/guest_access.html | Stable `data-testid` values, failure artifacts, and strict mode pass TC-045 to TC-049. | `python -m pytest tests/e2e/web_portal/test_guest_authorizations.py` | open |
| T026 | seq | FR-026, FR-027 | src/interfaces/portals/guest_authorizations/, src/mist/access/guests/ | Child counts stay within five, and log output stays redacted (TC-015 and TC-030). | `python -m pytest tests/guardrails/test_nested_package_structure.py` | open |
| T027 | [P] | Documentation (AGENTS.md Documentation section) | documentation/guest-authorizations.md, README.md, changelog.d/issue-4231-guest-authorizations.md | The operator guide, README entry, and release note describe the final behavior. | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` | open |

## Closing Tasks

| ID | Parallel | Requirements | Paths | Acceptance | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T-LOCAL-GATES | seq | SC-006, SC-007 | Every changed file in the change set | Run each applicable gate in the local gates table: compile, ruff, black, mypy, changed-file pytest, coverage, complexity, bandit, pylint, vulture, pydocstyle, interrogate, symbol-diff, and STE. | `python -m ruff check .` | open |
| T-PR | seq | SC-007 | Branch docs/4231-mist-guest-authorizations and the changed record files | Commit with the subject `docs(spec): refresh guest authorization migration record`. Push the branch and open a pull request with `Closes #4231` (D-17). | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` | open |
| T-REMOTE-CI | seq | SC-006 | The planning pull request | Each required check reports success, including the STE compliance check that `ste-lint.yml` runs. | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` | open |
| T-MERGE | seq | SC-007 | The planning pull request | Enable auto-merge only after CI passes and the orchestrator authorizes the merge. | `python -m pytest tests/guardrails/test_nested_package_structure.py` | open |

## Requirement Coverage Matrix

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 | T013, T014, T016 | TC-031, TC-045 |
| FR-002 | T013, T015 | TC-028 |
| FR-003 | T010 | TC-011 |
| FR-004 | T015 | TC-029 |
| FR-005 | T001, T014 | TC-032 |
| FR-006 | T014 | TC-033 |
| FR-007 | T006, T014 | TC-009, TC-046 |
| FR-008 | T006, T014 | TC-010 |
| FR-009 | T009, T017, T023 | TC-001 to TC-005, TC-008, TC-020 |
| FR-010 | T019 | TC-027, TC-035 |
| FR-011 | T020 | TC-004, TC-041 |
| FR-012 | T021 | TC-038, TC-040 |
| FR-013 | T021 | TC-039 |
| FR-014 | T009, T017, T018 | TC-006, TC-007, TC-035, TC-047 |
| FR-015 | T012, T017 | TC-007, TC-034, TC-035 |
| FR-016 | T007, T012 | TC-012, TC-023 |
| FR-017 | T007 | TC-024 |
| FR-018 | T007, T021 | TC-012, TC-025 |
| FR-019 | T010, T012 | TC-011, TC-036 |
| FR-020 | T010, T012 | TC-013, TC-037 |
| FR-021 | T007, T022 | TC-026, TC-044 |
| FR-022 | T023 | TC-016, TC-017, TC-018, TC-020 |
| FR-023 | T023, T024 | TC-019, TC-021, TC-048 |
| FR-024 | T024 | TC-021, TC-042 |
| FR-025 | T024 | TC-043 |
| FR-026 | T011, T026 | TC-014, TC-015 |
| FR-027 | T004, T006, T026 | TC-030 |
| FR-028 | T002, T007, T015 | TC-022, TC-029 |
| FR-029 | T014, T018, T025 | TC-045, TC-047, TC-049 |
| FR-030 | T011, T014, T022 | TC-014, TC-044, TC-046 |

Every requirement maps to at least one task and at least one planned test. Test identifiers are defined in design/quickstart.md.
