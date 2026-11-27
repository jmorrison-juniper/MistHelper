# Tasks: Ops platform dateutil pin (issue #4908)

**Input**: Numeric record `specs\numbered\0\0\1\2\4\1\1\3\4908-ops-platform-dateutil-pin\`. Supporting files are in `design\`: `research.md`, `data-model.md`, `quickstart.md`, `contracts\ci-dependency-contract.md`, and `checklists\`.

**Format**: `Txxx [P] [FR-###] Description`. `[P]` marks a task that can run in parallel. Each task names its paths, its acceptance statement, one verification command from the local gates table, and its status.

**Status values**: `open`, `verified-present`, `partial`, or `absent`.

**Verification commands**: Each command comes from the Local gates table in `.github/copilot-instructions.md` (RC-32). Run each command from the repository root of the fix worktree, not from the read-only checkout.

## Phase 1: Evidence and Pin Checks

- [ ] T001 [P] [FR-002] Confirm the ops pin on `main`.
  - Paths: `mist-ops-platform/requirements.txt`
  - Acceptance: Line 157 reads `python-dateutil==2.9.0.post0` on `main` (RC-16). The task makes no edit.
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: verified-present

- [ ] T002 [P] [FR-001] Confirm the install step and the celery pin.
  - Paths: `.github/workflows/ci.yml`, `mist-ops-platform/requirements.txt`
  - Acceptance: `ci.yml` line 1162 keeps the pip command (RC-02). Requirements line 27 keeps `celery==5.7.0` (RC-15). The task makes no edit.
  - Verification: `pytest --cov=src --cov-fail-under=56` in `mist-ops-platform/`
  - Status: verified-present

- [ ] T003 [P] [FR-008] Confirm the root pins.
  - Paths: `requirements.txt`, `requirements-dev.txt`
  - Acceptance: `requirements.txt` line 201 and `requirements-dev.txt` line 341 keep `python-dateutil==4.0.0` (RC-26, RC-27). The task makes no edit.
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: verified-present

## Phase 2: Policy and Guard

- [ ] T004 [P] [FR-003, FR-004] Add the Dependabot rule.
  - Paths: `.github/dependabot.yml`
  - Acceptance: The pip entry, which starts at line 3 (RC-23), gains an `ignore` block after line 11. The block names `python-dateutil` with `update-types: ["version-update:semver-major"]` (contract `ci-dependency-contract.md`). The block carries a reason comment. The npm and github-actions entries stay unchanged.
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: open. RC-25 records the absent rule on `main`.

- [ ] T005 [P] [FR-005, FR-006, FR-007] Add the guard cases.
  - Paths: `tests/guardrails/test_dependency_declaration_parity.py`
  - Acceptance: The module gains `import yaml`, two path constants, one pin constant of `2.9.0.post0`, class `OpsPlatformPins`, and four test functions. The functions hold nine cases in total. The positive cases succeed on the fix branch. The drift cases fail with a defect message that names the file and the rule.
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: open. The module has no ops pin check on `main` (RC-29).

- [ ] T006 [P] [FR-009] Document the ops pin.
  - Paths: `documentation/quality-gates.md`
  - Acceptance: A section named `Ops platform dependency pins` appears before the heading `## Exclusion drift report`, which follows the gate issue rule (RC-37). The section states the pin, the reason, and the condition for removing the Dependabot rule. Each sentence has 25 words or fewer and no semicolon.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
  - Status: open

- [ ] T007 [P] [FR-010] Add the changelog fragment.
  - Paths: `changelog.d/issue-4908-ops-platform-dateutil-pin.md` (new file)
  - Acceptance: The file has one `###` heading and one `- **Fixed**:` bullet. The bullet names issue #4908 at its end (RC-43). The file keeps this name after the pull request opens (RC-42).
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4908-ops-platform-dateutil-pin.md`
  - Status: open

- [ ] T008 [P] [FR-011] Name the failure evidence in the record.
  - Paths: `spec.md`, `analysis.md` in the record folder
  - Acceptance: The spec names check `pytest (ops platform)`, job `ops_platform_pytest`, step `Install dependencies`, rule `ResolutionImpossible`, run 45064318582, and job 137336951691. The spec also states that no test ran.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 spec.md`
  - Status: verified-present

## Phase 3: Final Tasks

- [ ] T-LOCAL-GATES [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, FR-010]
  - Paths: `tests/guardrails/test_dependency_declaration_parity.py`, `.github/dependabot.yml`, `documentation/quality-gates.md`, `changelog.d/issue-4908-ops-platform-dateutil-pin.md`, and the Markdown files of the record.
  - Acceptance: Each applicable row of the Local gates table prints its expected result. The applicable rows are:
    - Compile: `python -m py_compile tests/guardrails/test_dependency_declaration_parity.py` prints no output.
    - Lint: `python -m ruff check .` prints `All checks passed`.
    - Format: `python -m black --check .` reports no file that needs a change.
    - Tests: the guard module passes all nine cases.
    - Symbols: `symbol-diff --base origin/main tests/guardrails/test_dependency_declaration_parity.py` prints `no module-level name changed`.
    - Security lint: `bandit -c pyproject.toml -r tests/guardrails/test_dependency_declaration_parity.py -q` reports no finding.
    - Complexity: `radon cc tests/guardrails/test_dependency_declaration_parity.py -j | complexity-gate --max 10` reports no block above 10.
    - Citations: `check-citations src tests` reports no unresolved citation.
    - Test quality: the preflight and the analyzer command in the Test quality ratchet section report `gate: 0 new findings vs baseline`.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` grades each changed and new Markdown file at 80 or above.
    - Not applicable: Types, Dead code, Docstrings, and Code quality. Their paths exclude `tests/` (RC-10 to RC-14).
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: open

- [ ] T-PR [FR-010, FR-011]
  - Paths: All changed paths in `plan.md`, and the record folder at `specs\numbered\0\0\1\2\4\1\1\3\4908-ops-platform-dateutil-pin\`.
  - Acceptance:
    - The branch `fix/4908-ops-platform-dateutil-pin` starts from `main`.
    - The commit subject is `fix(ci): keep ops platform python-dateutil at the celery pin`. The commit body contains `Closes #4908` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
    - The pull request title matches the commit subject. The pull request body contains `Closes #4908`, the local gate results, the changed-file summary, and the revert steps.
    - Before the push, `gh pr list --json number,headRefName,files` shows no other open pull request that touches the same paths.
    - The pull request does not touch PR #4890 or its branch.
    - Warning: a commit pushed after a squash merge becomes an orphan. File a new issue, then branch again from `main`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: open

- [ ] T-REMOTE-CI [FR-001]
  - Paths: The pull request checks. The job is `ops_platform_pytest`.
  - Acceptance: The check `pytest (ops platform)` reports success on the pull request merge commit. The checks `Ruff (ops platform)`, `pytest coverage shard`, and `Dependency lock and exports` also report success.
  - Verification: `pytest --cov=src --cov-fail-under=56` in `mist-ops-platform/`
  - Status: open

- [ ] T-MERGE [FR-003, FR-004]
  - Paths: `.github/dependabot.yml`, and the pull request labels.
  - Acceptance:
    - The `auto-merge` label is added only after every check is green and the orchestrator authorizes the merge.
    - After the merge, the next weekly pip run from Dependabot opens no python-dateutil major update. This check verifies U-1.
    - No agent closes PR #4890 or pushes to its branch (D-4).
  - Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`
  - Status: open

## Dependencies & Execution Order

- T001, T002, and T003 are evidence checks. They run first and in parallel.
- T004 and T005 depend on T001 and T002. The guard reads the rule that T004 adds.
- T006 and T007 run in parallel with T004 and T005.
- T008 runs in parallel with the other edits.
- T-LOCAL-GATES depends on T004 to T008.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the orchestrator authorization.

## Notes

- A task changes only the paths that it names.
- Each guard case runs as a separate pytest case.
- A task that finds a conflicting file stops and reports the conflict.
