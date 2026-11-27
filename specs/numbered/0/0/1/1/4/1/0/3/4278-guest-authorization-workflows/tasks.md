# Tasks: Guest authorization workflows

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/contracts/`, and `design/data-model.md` in this record.

**Record path**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Format**: `[ID] [P?] Title`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task lists its requirements, tests, paths, acceptance, one verification command, and status.

**Status values**: `open` means no delivered artifact exists. `partial` means some artifact exists and the change completes it. `verified-present` means the artifact exists and passes its check. `absent` means the evidence shows no artifact.

**Gate rule**: No task that changes a Mist write path starts before decision D-4 passes. No task that changes `web_portal/app.py` or `web_portal/templates/base.html` starts before T001 passes.

**Totals**: 16 implementation and verification tasks, 4 final tasks, 37 planned tests (TEST-001 to TEST-037).

## Phase 1: Gates and Decisions

### T001 Confirm the PR 4208 handover

- **Requirements**: FR-001, FR-027.
- **Tests**: none. Existing guard `tests/guardrails/test_src_public_symbol_preservation.py` verifies symbols.
- **Paths**: `web_portal/app.py`, `web_portal/templates/base.html`.
- **Acceptance**: PR 4208 is closed, or the owner records the handover on issue 4278. Only then do T010 and T011 start.
- **Verification**: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`
- **Status**: open
- **Depends on**: none

### T002 Record the access decision and approvals

- **Requirements**: FR-004.
- **Tests**: none.
- **Paths**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows\spec.md`.
- **Acceptance**: The spec Clarifications record the outcome of D-4. The record names each approver and the date. The owner records the CSV and audit approvals on issue 4278.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows\spec.md`
- **Status**: open
- **Depends on**: none

## Phase 2: Domain Foundation

### T003 [P] Move the projection into a package

- **Requirements**: FR-007, FR-025, FR-032.
- **Tests**: TEST-001 (22 cases from the existing projection test, moved to `test_domain.py`).
- **Paths**: Delete `src/interfaces/portals/guest_authorizations.py` and `tests/unit/web_portal/test_guest_authorization_read_model.py`. Add `src/interfaces/portals/guest_authorizations/__init__.py`, `src/interfaces/portals/guest_authorizations/domain/__init__.py`, `src/interfaces/portals/guest_authorizations/domain/read_model.py`, `tests/unit/web_portal/guest_authorizations/__init__.py`, and `tests/unit/web_portal/guest_authorizations/test_domain.py`.
- **Acceptance**: The 22 projection cases pass unchanged. The test imports the new module path. The package `__init__.py` exports no alias for the old path.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/test_domain.py`
- **Status**: partial (module and test exist at the old paths, R063 and R066)
- **Depends on**: T002

### T004 Add scope, confirmation, and identity rules

- **Requirements**: FR-002, FR-003, FR-004, FR-005, FR-014, FR-022.
- **Tests**:
  - TEST-002: An unknown site or WLAN rejects.
  - TEST-003: The exact word, cancel, wrong word, and digest mismatch behave as specified.
  - TEST-004: Identity is accepted only from a trusted peer. A spoofed header rejects.
  - The tests append to `test_domain.py`.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/domain/scope.py`, `src/interfaces/portals/guest_authorizations/domain/confirmation.py`, and `src/interfaces/portals/guest_authorizations/domain/identity.py`.
- **Acceptance**: Each rule returns an explicit reason and sends no call. Identity follows the trusted peer rule in `web_portal/services/config.py` line 9 (R054).
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/test_domain.py`
- **Status**: open
- **Depends on**: T003

## Phase 3: Mist and Audit Services

### T005 [P] Add the Mist client and contract tests

- **Requirements**: FR-003, FR-006, FR-008, FR-012, FR-013, FR-028, FR-029.
- **Tests**:
  - TEST-005: The list call uses the site ID and the WLAN ID.
  - TEST-006: The update body allowlist rejects read-only fields.
  - TEST-007: The unauthorize call runs once with the client MAC.
  - TEST-008: No delete call and no organization guest call run.
  - TEST-009: Client search filters MAC, hostname, and IP locally. It returns at most 200 rows.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/services/__init__.py`, `src/interfaces/portals/guest_authorizations/services/mist_client.py`, and `tests/unit/web_portal/guest_authorizations/test_contract.py`.
- **Acceptance**: Each mistapi call uses explicit named arguments (R098 to R108). The class never sends a direct HTTP request. The client reads the SDK retry limit of three (R109) and counts calls.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/test_contract.py`
- **Status**: open
- **Depends on**: T004

### T006 [P] Add the audit store

- **Requirements**: FR-017, FR-018, FR-019, FR-025.
- **Tests**:
  - TEST-015: An intent write failure prevents dispatch.
  - TEST-016: An outcome write failure reports the audit failure and stops later writes.
  - TEST-017: Rows survive a restart. No automatic deletion runs.
  - TEST-018: A second in-flight write for one masked target blocks.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/services/audit_store.py` and `tests/unit/web_portal/guest_authorizations/services/__init__.py` and `tests/unit/web_portal/guest_authorizations/services/test_audit_store.py`.
- **Acceptance**: The table `guest_authorization_audit` in `data/mist_data.db` matches `design/contracts/audit.md`. The store holds masked values only. The store uses structlog for each action.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_audit_store.py`
- **Status**: open
- **Depends on**: T004

## Phase 4: Write and Import Services

### T007 Add the mutation service

- **Requirements**: FR-005, FR-007, FR-009, FR-010, FR-011, FR-012, FR-015, FR-016.
- **Tests**:
  - TEST-010: A grant sends one update. Minutes 1 to 259200 pass. Zero and 259201 reject.
  - TEST-011: Extension stays disabled without G5 evidence.
  - TEST-012: Revoke reports accepted but not verified without a read-back.
  - TEST-013: A timeout, a 5xx response, or a missing response reports unknown with no retry.
  - TEST-014: HTTP 429 after SDK retries reports rate limited and stops.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/services/mutations.py` and `tests/unit/web_portal/guest_authorizations/services/test_mutations.py`.
- **Acceptance**: Each write follows the sequence in `design/contracts/mist-api.md`. The service writes the intent row before the call and one outcome row after it.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_mutations.py`
- **Status**: open
- **Depends on**: T005, T006

### T008 Add the CSV import service

- **Requirements**: FR-020, FR-021, FR-022, FR-023, FR-024.
- **Tests**:
  - TEST-019: The byte limit is 262144 and the row limit is 200.
  - TEST-020: Exact headers pass. An unknown header rejects. BOM and CRLF pass.
  - TEST-021: A duplicate MAC rejects. An ambiguous name rejects. Identifiers are required.
  - TEST-022: Preview sends zero writes. A digest mismatch sends zero writes.
  - TEST-023: Outcomes run in sequence. A stop leaves later rows not attempted.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/services/csv_import.py` and `tests/unit/web_portal/guest_authorizations/services/test_csv_import.py`.
- **Acceptance**: The header list and limits match `design/contracts/csv-import.md`. The service rejects an oversized file before parsing.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/services/test_csv_import.py`
- **Status**: open
- **Depends on**: T007

## Phase 5: Web Surface

### T009 Add the blueprint, template, and route tests

- **Requirements**: FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-014, FR-015, FR-025, FR-026.
- **Tests**:
  - TEST-024: A POST without a CSRF token rejects.
  - TEST-025: A wrong or canceled confirmation sends zero writes. The review shows scope and change.
  - TEST-026: A missing or untrusted identity disables actions.
  - TEST-027: A denied scope discloses no record.
  - TEST-028: Responses and logs hold no private value.
- **Paths**: Add `src/interfaces/portals/guest_authorizations/web/__init__.py`, `src/interfaces/portals/guest_authorizations/web/routes.py`, `src/interfaces/portals/guest_authorizations/web/templates/guest_authorizations.html`, and `tests/unit/web_portal/guest_authorizations/test_routes.py`.
- **Acceptance**: Routes match `design/contracts/portal.md`. Each interactive element carries a stable data-testid. The route reads the Mist session from `app.config["APISESSION"]` (`web_portal/app.py` line 155, R059).
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/test_routes.py`
- **Status**: open
- **Depends on**: T004, T005, T006, T007, T008

### T010 Register the blueprint

- **Requirements**: FR-001, FR-027.
- **Tests**: none new. TEST-024 from T009 runs against the registered blueprint.
- **Paths**: `web_portal/app.py` (modify `_register_blueprints`, line 182. Insert after the WAN dashboard registration, line 207).
- **Acceptance**: The blueprint registers once. The change adds no port, service, or environment variable. T001 has passed.
- **Verification**: `python -m pytest tests/unit/web_portal/guest_authorizations/test_routes.py`
- **Status**: open
- **Depends on**: T001, T009

### T011 Add the navigation link

- **Requirements**: FR-001, FR-026.
- **Tests**: none new. TEST-029 from T012 checks that the link is visible.
- **Paths**: `web_portal/templates/base.html` (modify after the Operations link, line 60).
- **Acceptance**: The link follows the markup of the other links (R061, R062). T001 has passed.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_guest_authorization_portal.py`
- **Status**: open
- **Depends on**: T001

## Phase 6: Browser, Documentation, and Guards

### T012 Add the browser tests

- **Requirements**: FR-026, FR-030.
- **Tests**:
  - TEST-029: The page loads from the navigation link.
  - TEST-030: The grant flow runs with GRANT and a mocked update.
  - TEST-031: A canceled confirmation sends zero writes.
  - TEST-032: A failed flow keeps a trace or a screenshot.
- **Paths**: Add `tests/e2e/web_portal/test_guest_authorization_portal.py`.
- **Acceptance**: The tests use fictional data and mocked responses. Each failed flow keeps a trace or screenshot in the CI artifacts.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_guest_authorization_portal.py`
- **Status**: open
- **Depends on**: T010, T011

### T013 [P] Update the operator guide

- **Requirements**: FR-031.
- **Tests**: none. The STE command checks the prose.
- **Paths**: `documentation/operator-guide.md` (add a section under `### Open a portal`, line 211).
- **Acceptance**: The section explains the identity requirement, the typed words, the CSV limits, and the audit file. It uses the Simplified Technical English rules.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
- **Status**: open
- **Depends on**: T009

### T014 [P] Add the changelog fragment

- **Requirements**: FR-031.
- **Tests**: TEST-033 (the changelog fragment guard).
- **Paths**: Add `changelog.d/issue-4278-guest-authorization-workflows.md`.
- **Acceptance**: The fragment has one `###` heading and one bullet that names issue 4278. Rename the file to `pr-<number>.md` after the pull request exists.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open
- **Depends on**: T009

### T015 [P] Run the structure and container guards

- **Requirements**: FR-027.
- **Tests**: TEST-034 (nested package guard keeps five children under `src`), TEST-035 (e2e root guard keeps five entries), TEST-036 (container policy document stays true).
- **Paths**: No file changes. The guards read `src/interfaces/portals/guest_authorizations/` and `tests/e2e/`.
- **Acceptance**: Each guard passes. The output prints the count it examined.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_package_structure.py`
- **Status**: open
- **Depends on**: T010, T011, T012

### T016 Run the module-move gates

- **Requirements**: FR-032.
- **Tests**: TEST-037 (module-move guidance matches the live quality workflow).
- **Paths**: `src/interfaces/portals/guest_authorizations.py` (deleted), `src/interfaces/portals/guest_authorizations/`.
- **Acceptance**: The import smoke test passes for the new path. The old path fails to import. `git grep` finds no reference to the old path. The symbol gate reports no changed module-level name.
- **Verification**: `python -m pytest tests/guardrails/test_move_module_guidance.py`
- **Status**: open
- **Depends on**: T003

## Final Tasks

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: all FR.
- **Tests**: all planned tests (TEST-001 to TEST-037).
- **Paths**:
  - `src/interfaces/portals/guest_authorizations.py` (delete)
  - `src/interfaces/portals/guest_authorizations/__init__.py`, `domain/__init__.py`, `domain/read_model.py`, `domain/scope.py`, `domain/confirmation.py`, `domain/identity.py`
  - `src/interfaces/portals/guest_authorizations/services/__init__.py`, `services/mist_client.py`, `services/mutations.py`, `services/csv_import.py`, `services/audit_store.py`
  - `src/interfaces/portals/guest_authorizations/web/__init__.py`, `web/routes.py`, `web/templates/guest_authorizations.html`
  - `web_portal/app.py`, `web_portal/templates/base.html`
  - `tests/unit/web_portal/test_guest_authorization_read_model.py` (delete)
  - `tests/unit/web_portal/guest_authorizations/__init__.py`, `test_domain.py`, `test_contract.py`, `test_routes.py`
  - `tests/unit/web_portal/guest_authorizations/services/__init__.py`, `test_mutations.py`, `test_audit_store.py`, `test_csv_import.py`
  - `tests/e2e/web_portal/test_guest_authorization_portal.py`
  - `documentation/operator-guide.md`, `changelog.d/issue-4278-guest-authorization-workflows.md`
- **Acceptance**: Each applicable gate from the local gates table passes. The required gates are compile, lint, format, types, tests, and coverage. The other applicable gates are test quality, complexity, security lint, code quality, dead code, docstrings, symbols, and STE. Menu reference and safe sweep do not apply, because no menu changes. Record each command and its result.
- **Verification**: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
- **Status**: open
- **Depends on**: T013, T014, T015, T016

### T-PR Open the pull request

- **Requirements**: FR-031.
- **Tests**: none.
- **Paths**: The branch `feat/4278-guest-authorization-workflows`, with the paths listed in T-LOCAL-GATES.
- **Acceptance**: The Conventional Commits title uses the form `feat(web-portal): <short description>`. The body contains `Closes #4278`. The body lists the local gate results and the files changed. The change adds the `in-progress` label and the scope label `web-portal`.
- **Verification**: `python -m pytest tests/guardrails/test_ci_gate_triggers.py`
- **Status**: open
- **Depends on**: T-LOCAL-GATES

### T-REMOTE-CI Watch the CI run

- **Requirements**: FR-027, FR-030.
- **Tests**: all required CI checks.
- **Paths**: The pull request from T-PR, with the paths listed in T-LOCAL-GATES.
- **Acceptance**: Every required check passes on the latest commit. CodeQL passes before the auto-merge label is added. A failed check creates one issue before any fix.
- **Verification**: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
- **Status**: open
- **Depends on**: T-PR

### T-MERGE Enable auto-merge

- **Requirements**: FR-031.
- **Tests**: none.
- **Paths**: The pull request from T-PR, with the paths listed in T-LOCAL-GATES. The orchestrator authorizes the merge.
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is added only after T-REMOTE-CI passes. The branch is deleted after the squash merge.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open
- **Depends on**: T-REMOTE-CI
