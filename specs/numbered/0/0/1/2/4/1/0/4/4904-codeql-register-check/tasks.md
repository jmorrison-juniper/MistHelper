# Tasks: CodeQL register check fails on pull request 4888

**Input**: `plan.md`, `spec.md`, `design/research.md`, and `design/quickstart.md`.

**Tests**: The change adds three test cases. The negative case proves that the guard can fail.

**Ownership**: Edit only the paths that each task names. Do not edit `requirements-dev.txt` or `uv.lock`.

## Format: `[ID] [P?] [Story] [FR] Description`

- **[P]**: The task edits a different file from the other [P] tasks of its phase.
- **[Story]**: The user story that the task serves.
- **Status**: Each task starts as `open`.

## Phase 1: Implementation

- [ ] T001 [P] [US2] [FR-003] Add the `mando` ignore entry to the pip stream.
  - Files: `.github/dependabot.yml`
  - Acceptance: The pip stream ignores `mando` for `version-update:semver-minor` and `version-update:semver-major`. A comment names radon 6.0.1 and issue 4904.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Status: open

- [ ] T002 [US2] [FR-003] Update the pip snapshot and add the policy test.
  - Depends on: T001
  - Files: `tests/guardrails/test_pr_title_workflow.py`
  - Acceptance: `POLICY_SNAPSHOTS["dependabot"]` holds the same pip ignore entry. Class `TestDependabotPolicy` gains `test_pip_stream_ignores_mando_minor_and_major`. Each new line has an inline comment.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Status: open

- [ ] T003 [P] [US3] [FR-001] [FR-002] [FR-005] Add the radon ceiling check and its tests.
  - Files: `tests/guardrails/test_dependency_lock_file.py`
  - Acceptance: Class `RadonRequirementCheck` reads the installed radon requirement with `importlib.metadata`. The pinned case passes and prints the examined count. The negative case reports `mando==0.8.2` as a defect. Each read logs before and after.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`
  - Status: open

- [ ] T004 [P] [US1] [FR-007] Add a note below the job table of the quality-gates document.
  - Files: `documentation/quality-gates.md`
  - Acceptance: The note names the `mando` ceiling, the ignore entry, and issue 4904. Each sentence has 25 words or fewer.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
  - Status: open

- [ ] T005 [P] [US1] [FR-006] Add the release-note fragment.
  - Files: `changelog.d/issue-4904-codeql-register-check.md`
  - Acceptance: One `###` heading and one `**Fixed**` bullet name issue 4904. The file follows `changelog.d/README.md`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open

- [ ] T006 [US1] [FR-004] Confirm that the gate files stay unchanged.
  - Files: `.github/workflows/ci.yml`, `tests/guardrails/test_codeql_register_gate.py`
  - Acceptance: `git status` lists neither file as changed. The gate guard passes with the exact commands.
  - Verification: `python -m pytest tests/guardrails/test_codeql_register_gate.py`
  - Status: open

## Phase 2: Gates, Pull Request, and Merge

- [ ] T-LOCAL-GATES [US1] [US2] [US3] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-007] Run the applicable local gates.
  - Depends on: T001 through T006
  - Files: The paths of the change map in `plan.md`.
  - Acceptance: Commit the intended tests first. Run the test quality analyzer after that commit. Run each applicable gate in `plan.md`. Each gate exits 0.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_pr_title_workflow.py tests/guardrails/test_codeql_register_gate.py tests/guardrails/test_dependency_export.py tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open

- [ ] T-PR [US1] [US2] [US3] [FR-001] [FR-003] Open the pull request.
  - Depends on: T-LOCAL-GATES
  - Files: Branch `fix/4904-codeql-register-check` from `main`.
  - Acceptance: The commit subject is `fix(ci): keep mando below the radon ceiling`. The commit body holds `Closes #4904`. The pull request title matches the subject. The body lists each gate result and the files changed.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open

- [ ] T-REMOTE-CI [US1] [FR-001] Watch the pull request run.
  - Depends on: T-PR
  - Files: None. The check reads the remote run.
  - Acceptance: The check CodeQL verdict register check reports success. The run has zero failed jobs and zero `ResolutionImpossible` lines. Use `gh pr checks <number> --watch`, which only reads.
  - Verification: `python -m pytest tests/guardrails/test_codeql_register_gate.py`
  - Status: open

- [ ] T-MERGE [US2] [FR-003] Merge the fix and close pull request #4888.
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Files: None.
  - Acceptance: Add the `auto-merge` label only after each check passes. Squash merge after authorization. Then close pull request #4888 unmerged, with a comment that names issue 4904.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`
  - Status: open

## Dependencies

- T002 depends on T001.
- T-LOCAL-GATES depends on T001 through T006.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on orchestrator authorization.
