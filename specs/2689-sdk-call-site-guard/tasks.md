# Tasks: mistapi SDK call-site guard

**Input**: Design documents from `specs/2689-sdk-call-site-guard/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required because issue #2689 asks for negative proof.

## Phase 1: Setup

**Purpose**: Establish the isolated worktree and the preserved prior work.

- [x] T001 Create the issue branch from current `origin/main` in `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-2689b-sdk-guard`. (delivered: worktree)
- [x] T002 Bootstrap the worktree virtual environment and confirm `mistapi` 0.64.0. (delivered: `.venv`)
- [x] T003 Restore only `tests/integration/test_mistapi_sdk_compatibility.py` from `origin/recovery/2689-sdk-guard-wip`. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)

## Phase 2: Guard implementation

**Purpose**: Replace the unmeasured skip with a measured SDK call-site guard.

- [x] T004 [US1] Add AST collection for SDK functions defined by the installed `mistapi` package. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T005 [US1] Add AST collection for direct, aliased, and registry-based `mistapi` call sites in source. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T006 [US1] Fail on missing SDK functions with caller file, caller line, and missing function. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T007 [US2] Fail when the guard resolves zero call sites. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T008 [US3] Report unresolved dynamic SDK module references and fail when the count grows beyond 10. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)

## Phase 3: Defect found by the guard

**Purpose**: Keep the guard green after it found one real call-site typo on current main.

- [x] T009 [US1] Report the new `getSiteSettings` defect on issue #2689 before repair. (delivered: issue comment)
- [x] T010 [US1] Change `getSiteSettings` to `getSiteSetting` in the site auto-upgrade reader. (delivered: `src/firmware/site_auto_upgrade.py`)
- [x] T011 [US1] Update site auto-upgrade unit mocks to match the installed SDK function name. (delivered: `tests/unit/test_site_auto_upgrade.py`)

## Phase 4: Negative proof tests

**Purpose**: Prove the guard fails when it must fail.

- [x] T012 [US1] Add a deliberately missing SDK function fixture and assert the failure names the file and line. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T013 [US2] Add a zero-call-site fixture and assert the guard fails. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T014 [US3] Add a dynamic module fixture and assert unresolved growth can fail against a lower baseline. (delivered: `tests/integration/test_mistapi_sdk_compatibility.py`)
- [x] T015 [US2] Remove issue #2689 from the known unmeasured guard baseline. (delivered: `tools/guard_proof_audit.py`)
- [x] T016 [US2] Update the guard proof test to assert the SDK guard is no longer known debt. (delivered: `tests/guardrails/test_guard_proof_audit.py`)

## Phase 5: Documentation and release note

**Purpose**: Record the design and the user-visible repair.

- [x] T017 Create `spec.md`, `plan.md`, and `tasks.md` from the SpecKit templates. (delivered: `specs/2689-sdk-call-site-guard/`)
- [x] T018 Add one release-note fragment for issue #2689. (delivered: `changelog.d/issue-2689-sdk-guard.md`)

## Phase 6: Validation and pull request

**Purpose**: Prove the change locally and in CI.

- [x] T019 Run ruff, black, mypy, radon, the compatibility test, `tools.guard_proof_audit`, and collection. (delivered: local gate output)
- [ ] T020 Commit, push, open the pull request, wait for checks, merge, and verify issue #2689 closure.

## Dependencies & Execution Order

- Phase 1 must complete before Phase 2.
- Phase 2 must complete before Phase 3 can identify real missing functions.
- Phase 3 must complete before the installed SDK guard can pass.
- Phase 4 proves the guard fails independently of the installed SDK scan.
- Phase 5 can run after Phase 2 decisions are known.
- Phase 6 runs after all file changes are complete.
