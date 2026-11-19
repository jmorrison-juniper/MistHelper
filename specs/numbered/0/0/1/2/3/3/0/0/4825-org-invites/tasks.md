# Tasks: Organization Invites Export Reports Missing SDK Call

**Input**: Numeric record `/specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/` with `spec.md` and `plan.md`.

**Note**: The code, test, and documentation tasks were delivered in commit b2249e25. The changelog fragment and this record were delivered in the follow-up commit. The publication tasks stay open until the coordinator gives a publication instruction.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies).
- **[Story]**: The user story that the task serves.

## Phase 1: Investigation

- [X] T001 [US1] Introspect `mistapi.api.v1.orgs.invites` and search the installed mistapi package for invite list functions. (delivered: specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/spec.md)
- [X] T002 [US1] Compare the Mist OpenAPI definitions for the org invites and SDK invites endpoints. (delivered: documentation/mist-api-openapi31json.json)

## Phase 2: Tests

- [X] T003 [US2] Replace the test that injected a fake `listOrgInvites` with a supported-path test. (delivered: tests/unit/export/test_org_export_utils.py)
- [X] T004 [US1] Add the absent-path regression test. It fails before the fix with `AttributeError`. (delivered: tests/unit/export/test_org_export_utils.py)

## Phase 3: Implementation

- [X] T005 [US1] Guard the SDK lookup in `OrgExportUtils._invites`. Log one error and return when the call is absent. (delivered: src/operations/exporting/export/org_export_utils.py)
- [X] T006 [US2] Keep the supported path unchanged. Pass the SDK callable to `export_data` with `data_type="invites"` and `sort_key="email"`. (delivered: src/operations/exporting/export/org_export_utils.py)

## Phase 4: Documentation and Changelog

- [X] T007 [P] Correct the stale MistHelper note on the invite delete page. (delivered: documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md)
- [X] T008 [P] Add the changelog fragment for the fix. (delivered: changelog.d/issue-4825-org-invites.md)

## Phase 5: Validation

- [X] T009 [US1] Run the focused test file. The result is 96 passed. (evidence: tests/unit/export/test_org_export_utils.py)
- [X] T010 Run ruff, black, py_compile, mypy, pylint, bandit, radon, and symbol-diff on the changed Python files. (evidence: src/operations/exporting/export/org_export_utils.py)
- [X] T011 Run the export test folder, the SDK signature guard, and the markdown link guard. The result is 2490 passed and 4 skipped. (evidence: tests/integration/test_mistapi_sdk_compatibility.py)
- [X] T012 Run the test-quality gate on the changed test file. The result is 0 new findings. (evidence: .github/test-quality-baseline.json)
- [X] T013 Run `ste-linter` with `--min-score 80` on the new markdown files. (evidence: .ste-linter.toml)
- [X] T014 Run the process folder guard for the new record. (evidence: tests/guardrails/test_process_folder_structure.py)

## Phase 6: Publication (waits for a coordinator instruction)

- [ ] T015 Push branch `fix/4825-org-invites` and open a pull request that closes #4825. Condition: a publication instruction from the coordinator is required first.
- [ ] T016 Confirm that the required pull request checks pass on the latest commit. Condition: T015 must complete first.
