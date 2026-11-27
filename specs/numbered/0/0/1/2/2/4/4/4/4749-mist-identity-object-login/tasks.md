# Tasks: Mist Identity Object Sign-In

**Input**: Numeric record `specs/numbered/0/0/1/2/2/4/4/4/4749-mist-identity-object-login/`.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, design/contracts/.

**Tests**: Required by FR-001 to FR-008 and SC-001. The new test modules run first and fail before the implementation tasks.

**Organization**: Tasks follow the user stories US1, US2, and US3. Setup and final gate tasks bracket the stories.

**Working directory**: Run each command from the `mist-ops-platform` directory unless the task names another directory.

## Format

- `[P]` marks a task that is safe in parallel. Each task names its requirement IDs, its exact paths, an acceptance statement, one verification command, and a status.
- Status values are `open`, `verified-present`, `partial`, and `absent`.
- Leave each checkbox unchecked until the delivered file passes the verification command.

## Phase 1: Setup and Baseline

- [ ] T001 [US2] [FR-006, FR-007]
  - Files: `mist-ops-platform/src/shared/services/auth.py`
  - Acceptance: The file keeps blob `175cb458001750b6af4e02b14072848fca1a19a5` (research row R06). The reservation holder releases `auth.py` before the first edit.
  - Verify: `symbol-diff --base origin/main mist-ops-platform/src/shared/services/auth.py`
  - Status: verified-present

- [ ] T002 [SC-003]
  - Files: none
  - Acceptance: The output records the collected test count and the coverage percentage before any edit. The count must reach 390 after the change (research row R46).
  - Verify: `python -m pytest --cov=src --cov-fail-under=56`
  - Status: open

## Phase 2: Foundational Registry Change

- [ ] T003 [P] [FR-004]
  - Files: `mist-ops-platform/src/shared/mist/types.py`
  - Acceptance: The `MistEndpoint` dataclass gains `object_response: bool = False` after `list_method` (research row R05). Every existing registry entry keeps its values.
  - Verify: `python -m pytest tests/unit/mist/test_consumer_registry_usage.py`
  - Status: absent

- [ ] T004 [FR-001, FR-011]
  - Files: `mist-ops-platform/src/shared/mist/types.py`
  - Acceptance: The `self_identity` entry (research row R04) sets `object_response=True` and keeps `list_method="getSelf"`.
  - Verify: `symbol-diff --base origin/main mist-ops-platform/src/shared/mist/types.py`
  - Status: absent

## Phase 3: Tests First

Test cases in the two new modules. Each case states its purpose and its requirements.

- TC-01 (FR-001, FR-011): A 2xx non-empty identity object becomes one record with status 200. The patched SDK method is the only call.
- TC-02 (FR-003): A 2xx list body keeps its records.
- TC-03 (FR-001): A 2xx empty object yields no record.
- TC-04 (FR-002, FR-008): A 4xx object body yields no record and keeps the 4xx status.
- TC-05 (FR-002, FR-008): A 5xx object body yields no record and keeps the 5xx status.
- TC-06 (FR-005): An object endpoint makes one call even when the response carries a next cursor.
- TC-07 (FR-004): A list endpoint given a dictionary body returns no record.
- TG-01 (FR-006, FR-009): A valid supplied token returns the identity privileges and logs the info and debug lines.
- TG-02 (FR-007, FR-010): An active token that differs from the supplied token returns empty privileges. The warning contains no token value.
- TG-03 (FR-007): No active token, where the index is minus one, returns empty privileges.
- TG-04 (FR-007): Comma-separated supplied tokens match one active token and return its identity.
- TG-05 (FR-008): A 4xx response returns empty privileges and skips the active-token check.
- TG-06 (FR-008): A 5xx response raises MistApiUnavailableError.

- [ ] T005 [P] [US1] [FR-001, FR-002, FR-003, FR-004, FR-005]
  - Files: `mist-ops-platform/tests/contract/test_self_identity_response_contract.py` (new)
  - Acceptance: Cases TC-01 to TC-07 exist. TC-01 and TC-06 fail before T007 and T008. The 4xx and 5xx cases use patched responses. No test calls the network.
  - Verify: `python -m pytest tests/contract/test_self_identity_response_contract.py`
  - Status: absent

- [ ] T006 [P] [US2] [FR-006, FR-007, FR-008]
  - Files: `mist-ops-platform/tests/contract/test_validation_token_guard.py` (new)
  - Acceptance: Cases TG-01 to TG-06 exist. TG-01 and TG-02 fail before T009. The 4xx and 5xx cases assert the status and the exception type.
  - Verify: `python -m pytest tests/contract/test_validation_token_guard.py`
  - Status: absent

## Phase 4: US1 Identity Object

- [ ] T007 [US1] [FR-001, FR-002, FR-003, FR-009, FR-010]
  - Files: `mist-ops-platform/src/shared/mist/endpoints.py`
  - Acceptance: The static method `_extract_object` sits beside `_extract_list` (research row R01). It returns no record for a non-2xx status. It returns the list for a list body. It returns one record for a non-empty dictionary.
  - Verify: `python -m py_compile mist-ops-platform/src/shared/mist/endpoints.py`
  - Status: absent

- [ ] T008 [US1] [FR-001, FR-005, FR-009]
  - Files: `mist-ops-platform/src/shared/mist/endpoints.py`
  - Acceptance: `list_all_entities` (research row R02) branches on `endpoint.object_response`. The branch calls `_read_object` once and never calls `_paginate`. `_list_result` keeps the real status.
  - Verify: `python -m pytest tests/contract/test_self_identity_response_contract.py`
  - Status: absent

## Phase 5: US2 Fail-Closed Token Check

- [ ] T009 [US2] [FR-006, FR-007, FR-008, FR-009, FR-010]
  - Files: `mist-ops-platform/src/shared/services/auth.py`
  - Acceptance: The static method `_active_token_is_supplied` returns false for a missing or out-of-range active token. It compares the active token with the comma-split, stripped supplied tokens. The static method `_identity_from_success` runs after the success check (research row R08). `_fetch_self` stays at 25 lines or fewer.
  - Verify: `python -m pytest tests/contract/test_validation_token_guard.py`
  - Status: absent

## Phase 6: US3 Regression, Changelog, and Review

- [ ] T010 [P] [US3] [FR-004, FR-012]
  - Files: `changelog.d/issue-4749-mist-identity-object-login.md` (new)
  - Acceptance: The fragment has one `###` heading and one `Fixed` bullet that names issue #4749. The bullet states no defect detail (decision D-9).
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4749-mist-identity-object-login.md`
  - Status: absent

- [ ] T011 [FR-009, FR-010]
  - Files: `mist-ops-platform/src/shared/mist/endpoints.py`, `mist-ops-platform/src/shared/mist/types.py`, `mist-ops-platform/src/shared/services/auth.py`
  - Acceptance: Each changed line has an inline comment. Each changed action has an info line before and a debug line after. No new log line holds a token or an identity body.
  - Verify: `python -m ruff check .`
  - Status: absent

- [ ] T012 [SC-002] [FR-004, FR-008]
  - Files: none changed. The four existing modules stay as they are.
  - Acceptance: The four modules pass with no edit. Their assertions for the 401 path, the 503 path, the dictionary drop, and the registry call still hold.
  - Verify: `python -m pytest tests/unit/mist/test_list_status.py tests/unit/mist/test_consumer_registry_usage.py tests/unit/api/test_auth.py tests/unit/api/test_session_security.py`
  - Status: open

- [ ] T013 [SC-001] [FR-011]
  - Files: `mist-ops-platform/src/shared/services/auth.py`, `mist-ops-platform/src/shared/mist/endpoints.py`, `mist-ops-platform/src/shared/mist/types.py`
  - Acceptance: The symbol gate reports no module-level name changed. The new methods belong to classes and add no module-level name.
  - Verify: `symbol-diff --base origin/main mist-ops-platform/src/shared/services/auth.py`
  - Status: open

## Final Gate and Delivery Tasks

- [ ] T-LOCAL-GATES [SC-003, SC-004]
  - Files: the six changed or added paths listed in plan.md.
  - Acceptance: Each applicable gate in research.md section Local Gate Plan passes on the changed files. The record lists each gate that does not apply, with the reason.
  - Verify: `python -m pytest --cov=src --cov-fail-under=56`
  - Status: open

- [ ] T-PR [FR-012]
  - Files: branch `fix/4749-mist-identity-object-login`
  - Acceptance: The commit subject reads `fix(ops-platform): accept a valid Mist identity object during login`. The commit body contains `Closes #4749`. The pull request body lists the local gate results and the sequencing note from plan.md.
  - Verify: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open

- [ ] T-REMOTE-CI [SC-005]
  - Files: the pull request for branch `fix/4749-mist-identity-object-login`
  - Acceptance: Every required remote check passes on the latest commit. The `ops_platform_pytest` job (research row R43) reports the same count as the local run.
  - Verify: `python -m pytest --cov=src --cov-fail-under=56` (local mirror), then `gh pr checks <number> --watch` for the remote checks.
  - Status: open

- [ ] T-MERGE [SC-005]
  - Files: the pull request for branch `fix/4749-mist-identity-object-login`
  - Acceptance: The branch is rebased on the current `main`, the gates run again, and the orchestrator authorizes the merge. Add the `auto-merge` label only after every check passes.
  - Verify: `python -m pytest --cov=src --cov-fail-under=56`
  - Status: open

## Dependencies and Execution Order

- T001 comes first. It confirms that the reserved file is free.
- T002 and T003 can run in parallel after T001.
- T004 follows T003 because both edit `types.py`.
- T005 and T006 run in parallel and fail before the implementation.
- T007 and T008 both edit `endpoints.py`, so they run in order. T008 follows T004 and T007.
- T009 follows T001, T005, and T006.
- T010 can run at any time after the record is final.
- T011 to T013 follow the implementation tasks.
- The final tasks follow every earlier task in this list.

## Notes

- Warning: a pull request that ships T007 and T008 without T009 exposes the defect described in decision D-5. Do not split these tasks across pull requests.
- Caution: T001 fails when the reserved file changed on `main`. Stop the work and resolve the conflict with the #4748 owner first.
