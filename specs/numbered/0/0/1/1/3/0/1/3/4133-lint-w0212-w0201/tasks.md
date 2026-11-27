# Tasks: Lint repair for W0212 and W0201 findings

**Input**: Design documents in `specs/numbered/0/0/1/1/3/0/1/3/4133-lint-w0212-w0201/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`.

**Tests**: The test module already exists. This change keeps its 35 cases and changes two of them. The change adds no new test function.

**Organization**: Tasks run in the order below. Each task names exact repository paths and one verification command from the local gates table in `.github/copilot-instructions.md`.

## Format

- `[P]` marks a task that can run in parallel with another `[P]` task. Parallel tasks edit different files.
- Requirement IDs refer to `spec.md`.
- Status values: `open` means the task has not started. `absent` means the required change is not on `main` yet. `verified-present` means `main` already holds the requirement. `partial` means some parts hold.

## Phase 1: Baseline and Change

### T001 Verify the baseline of the test file

- Requirements: FR-001, FR-010.
- Files: `tests/unit/test_menu_entry_metadata.py` (read only).
- Acceptance: The pylint command in `design/quickstart.md` reports exactly two W0212 messages, at lines 84 and 93. The pytest run collects 35 cases before the change.
- Verification command: `python -m pytest tests/unit/test_menu_entry_metadata.py`
- Status: open

### T002 Replace the protected handler calls in the test file

- Requirements: FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-010.
- Depends on: T001.
- Files: `tests/unit/test_menu_entry_metadata.py` (modify).
- Acceptance: The file holds no call to a name that starts with an underscore on the `MistHelper` module. The two test names and the parameter lists stay unchanged. Each new line carries a `# WHY:` comment. The four replacements use monkeypatch.
- Verification command: `python -m pytest tests/unit/test_menu_entry_metadata.py`
- Status: absent

### T003 Add the changelog fragment

- Requirements: FR-008.
- Depends on: none. This task runs in parallel with T002.
- Files: `changelog.d/issue-4133-lint-w0212-w0201.md` (add).
- Acceptance: The file holds one `###` heading. It holds one `- **Changed**:` bullet that names issue 4133. It holds no other text.
- Verification command: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- Status: absent

## Phase 2: Local Gates and Publication

### T-LOCAL-GATES Run each applicable local gate

- Requirements: FR-001 to FR-010.
- Depends on: T002, T003.
- Files: `tests/unit/test_menu_entry_metadata.py`, `changelog.d/issue-4133-lint-w0212-w0201.md`, and the record files copied into the worktree.
- Acceptance: Each gate below prints its expected result. A failed gate stops the task.
  - Compile: `python -m py_compile tests/unit/test_menu_entry_metadata.py` prints no output.
  - Lint: `python -m ruff check .` prints `All checks passed`.
  - Format: `python -m black --check .` reports that no file needs a change.
  - Tests: `python -m pytest tests/unit/test_menu_entry_metadata.py` passes all 35 cases.
  - Security lint: `bandit -c pyproject.toml -r tests/unit/test_menu_entry_metadata.py -q` reports no finding.
  - Complexity: `radon cc tests/unit/test_menu_entry_metadata.py -j` piped to `complexity-gate --max 10` reports no block above 10.
  - Test quality: the command in `design/quickstart.md` prints `gate: 0 new findings vs baseline`.
  - Symbols: `symbol-diff --base origin/main tests/unit/test_menu_entry_metadata.py` prints `no module-level name changed` and exits with code 0.
  - STE: `ste-linter --config .ste-linter.toml --min-score 80` applied to each record Markdown file scores 80 or above.
  - Pylint evidence: the quickstart pylint command prints `[]` for both files. This command is the issue acceptance check. The table does not include it.
  - Not applicable to the changed files: Full tests run in T-REMOTE-CI. Coverage, Safe sweep, Menu reference, and Dependency audit do not apply to this change.
  - Types, Dead code, and Docstrings: `ci.yml` omits the tests tree from these gates (rows RC-19 to RC-21 and RC-37).
- Verification command: `python -m ruff check .`
- Status: open

### T-PR Commit, push, and open the pull request

- Requirements: FR-008, FR-009.
- Depends on: T-LOCAL-GATES. The orchestrator authorization must exist (decision D-5).
- Files: `tests/unit/test_menu_entry_metadata.py`, `changelog.d/issue-4133-lint-w0212-w0201.md`, and the record folder `specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\`. No other file.
- Acceptance:
  - Issue 4133 carries the labels `lint`, `tests`, and `in-progress` before the branch exists.
  - The branch `chore/4133-lint-w0212-w0201` starts from `origin/main`.
  - The commit subject is `test(lint): call the public menu dispatch in the menu metadata test`.
  - The commit body holds `Closes #4133` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
  - The pull request title equals the commit subject. The pull request body holds `Closes #4133`, the list of changed files, and the local gate results.
- Verification command: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- Status: open

### T-REMOTE-CI Watch the remote checks

- Requirements: FR-009.
- Depends on: T-PR.
- Files: none changed.
- Acceptance: `gh pr checks --watch` on the pull request that T-PR opened reports every required check as passed. The test-quality gate, CodeQL, and the test shards pass. The advisory jobs `speckit_task_audit` and `exclusion_drift` are read and recorded in the pull request. A failed required check stops the task.
- Verification command: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open

### T-MERGE Enable auto-merge after authorization

- Requirements: FR-009.
- Depends on: T-REMOTE-CI and the orchestrator authorization.
- Files: none changed.
- Acceptance: The `auto-merge` label is added only after every required check passes. The squash merge closes issue 4133 through the pull request body. The branch and the worktree are removed after the merge.
- Verification command: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open

## Dependencies and Execution Order

### Task dependencies

- T001 comes first. T002 depends on T001.
- T003 runs in parallel with T002.
- T-LOCAL-GATES depends on T002 and T003.
- T-PR depends on T-LOCAL-GATES and on the orchestrator authorization.
- T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI and on the orchestrator authorization.

### Phase notes

- The orchestrator decides when T-PR starts. The publication hold in the issue comments applies until then.
- Each task stops at its first failed acceptance check. The next task does not start until the failure is repaired.
