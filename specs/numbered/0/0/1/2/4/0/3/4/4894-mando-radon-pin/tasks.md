# Tasks: Keep mando inside the radon requirement

**Input**: Numeric record `specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin/`.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/quickstart.md.

**Tests**: Required. The constitution and AGENTS.md require a test for each change. The test IDs TC-001 to TC-012 appear in this file.

**Organization**: Tasks follow the three user stories. Each task names its requirement IDs and its test IDs.

## Format

- `[P]`: Safe in parallel. The task edits different files and has no dependency.
- `FR-###`: Requirement IDs from spec.md.
- Verification: one command from the local gates table in `.github/copilot-instructions.md`. A GitHub read or a CI check follows where needed.
- Status: open, verified-present, partial, or absent.

## Test IDs

| ID | Requirement | Test | Command or check |
| - | - | - | - |
| TC-001 | FR-001 | Existing export guard | `python -m pytest tests/guardrails/test_dependency_export.py::TestDependencyExport::test_requirements_exports_match_the_lock` |
| TC-002 | FR-003, FR-004 | The pip block ignores mando | `python -m pytest tests/guardrails/test_dependency_export.py::TestDependabotPipIgnore::test_pip_block_ignores_mando` |
| TC-003 | FR-003, FR-004 | The ignore entry blocks every version | `python -m pytest tests/guardrails/test_dependency_export.py::TestDependabotPipIgnore::test_mando_ignore_blocks_every_version` |
| TC-004 | FR-009 | Pull request title and body | GitHub read: `gh pr view --json title,body` on the fix branch |
| TC-005 | FR-008 | The record names the check and the rule | PowerShell `Select-String` for `pytest (coverage gate)` and `ResolutionImpossible` in the record folder |
| TC-006 | FR-006 | One fragment and an STE score of 80 or above | `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4894-mando-radon-pin.md` |
| TC-007 | FR-007 | Only change-map paths changed | `git diff --name-only origin/main` |
| TC-008 | FR-005 | Pull request #4888 is closed | GitHub read: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt` |
| TC-009 | FR-001, FR-002 | Dependency lock and exports check | CI check: `Dependency lock and exports` on the fix branch |
| TC-010 | FR-002 | Pytest gate and shards | CI checks: `pytest (coverage gate)` and the four `pytest coverage shard` checks |
| TC-011 | FR-002 | Required contexts | CI checks: the 15 required contexts of branch protection on main |
| TC-012 | FR-010 | Two separate issues exist | GitHub read: `gh issue list -R jmorrison-juniper/MistHelper --search "changelog in:title" --json number,title,labels` |

## Phase 1: Claim, evidence, and edits

- [ ] T001 [FR-009] Claim the issue and create the branch.
  - Paths: none changed. Create the worktree at `..\MistHelper-4894-fix`. Label GitHub issue #4894.
  - Acceptance: Issue #4894 carries `in-progress`. Branch `fix/4894-mando-radon-pin` starts from `origin/main` in a new worktree.
  - Warning: removing a worktree deletes its uncommitted files. Create a new worktree for each branch.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py::TestDependencyExport::test_requirements_exports_match_the_lock` (TC-001).
  - Status: open.

- [x] T002 [P] [FR-001] Verify the main pins.
  - Paths: `requirements-dev.txt` (lines 179, 356, and 365), `uv.lock` (lines 1301 and 2432), `pyproject.toml` (line 118).
  - Acceptance: Line 179 reads `mando==0.7.1`. Line 365 reads `radon==6.0.1`. Line 1301 of uv.lock reads `version = "0.7.1"`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py::TestDependencyExport::test_requirements_exports_match_the_lock` (TC-001).
  - Status: verified-present (research rows RC-04, RC-06, RC-07, RC-08).

- [ ] T003 [FR-003, FR-004] Write two guard tests that fail before the change.
  - Paths: `tests/guardrails/test_dependency_export.py`.
  - Acceptance: Class `TestDependabotPipIgnore` holds `test_pip_block_ignores_mando` and `test_mando_ignore_blocks_every_version`. Both fail on main. Each executable line has an inline comment.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py::TestDependabotPipIgnore` (TC-002, TC-003). Expected before T004: both tests fail.
  - Status: open. Depends on T001.

- [ ] T004 [FR-003] Add the mando ignore entry to the pip update block.
  - Paths: `.github/dependabot.yml` (pip update block, lines 3 to 11 on main).
  - Acceptance: The pip block holds `ignore:` with `- dependency-name: "mando"` and no other key. The comment names issue #4894, radon 6.0.1, `mando<0.8`, and the removal condition. The npm block stays unchanged.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py::TestDependabotPipIgnore` (TC-002, TC-003). Expected after this task: both tests pass.
  - Status: open. Depends on T003.

- [ ] T005 [P] [FR-006] Add the changelog fragment.
  - Paths: `changelog.d/issue-4894-mando-radon-pin.md`.
  - Acceptance: One `###` heading. One `- **Fixed**:` bullet that names issue #4894. No version number.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4894-mando-radon-pin.md` (TC-006).
  - Status: open. Depends on T001.

- [ ] T006 [P] [FR-008] Copy the reviewed record into the repository.
  - Paths: `specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin/` (the eight files listed in plan.md).
  - Acceptance: Each file matches the draft. Each folder holds five children or fewer. TC-005 passes.
  - Verification: Full tests, the second `pytest-chunks` command in `.github/copilot-instructions.md`. It runs `tests\guardrails`.
  - Status: open. Depends on T001.

- [ ] T007 [P] [FR-010] Open two separate issues.
  - Paths: none changed. The issues cite `changelog.d/README.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`.
  - Acceptance: Issue A states the fragment policy conflict. It cites `changelog.d/README.md` line 58, `.github/copilot-instructions.md` line 451, and `.specify/memory/constitution.md` line 409. It carries `chore` and `docs`. Issue B states the folder debt of 335 files in `changelog.d/`. It carries `refactor` and `docs`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py::TestDependencyExport::test_requirements_exports_match_the_lock` (TC-001). GitHub read: TC-012.
  - Status: open.

## Phase 2: Final tasks

- [ ] T-LOCAL-GATES [FR-002, FR-003, FR-004, FR-006, FR-008] Run each applicable local gate.
  - Paths: the files from T003 to T006.
  - Acceptance: Each gate below exits 0 with the expected result. Record each result in the pull request body.
    - Lint: `python -m ruff check .` prints `All checks passed`.
    - Format: `python -m black --check .` reports no file that needs a change.
    - Tests: `python -m pytest tests/guardrails/test_dependency_export.py` passes every test.
    - Full tests: both `pytest-chunks` commands pass. Each prints one summary line for each shard.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` reports 80 percent or above.
    - Security lint: `bandit -c pyproject.toml -r tests/guardrails/test_dependency_export.py -q` reports no finding.
    - Symbols: `symbol-diff --base origin/main tests/guardrails/test_dependency_export.py` exits 0. Record its output.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` scores each changed Markdown file at 80 or above.
  - Not applicable: Compile, because MistHelper.py does not change. Types, complexity, dead code, docstrings, and Pylint, because their CI path lists exclude `tests/`. Dependency audit, because no requirements file changes. Menu reference, ops portal, and ops platform, because those areas do not change.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py` (TC-002, TC-003).
  - Status: open. Depends on T003, T004, T005, and T006.

- [ ] T-PR [FR-005, FR-007, FR-009] Commit, push, open the pull request, and close pull request #4888.
  - Paths: the change map in plan.md. Add each file by explicit path. Do not run `git add -A`.
  - Acceptance:
    - Commit the change. The subject is `fix(ci): keep mando pinned inside the radon requirement`. The body holds `Closes #4894` and the Co-authored-by trailer.
    - Run the test quality gate after the local commit and before the push. The command is `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. It prints `gate: 0 new findings vs baseline`.
    - `git diff --name-only origin/main` lists only the change-map paths (TC-007).
    - Push `fix/4894-mando-radon-pin`. Open a pull request to `main`. Its title passes the Conventional Commits check. Its body holds `Closes #4894`, the local gate results, the file list, and the changelog reason from D-5 (TC-004).
    - Close pull request #4888 without a merge. The comment names run 45064243269, job 137338442288, and the radon requirement. The comment links the fix pull request (TC-008).
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py` before the push (TC-002, TC-003).
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI [FR-001, FR-002, FR-009] Watch the CI checks on the fix pull request.
  - Paths: none changed. The checks come from `.github/workflows/ci.yml`.
  - Acceptance:
    - The Quality Gates workflow runs on the pull request. Its trigger has no paths filter (research row RC-15).
    - These checks report success: `Dependency lock and exports`, `pytest (coverage gate)`, the four `pytest coverage shard` checks, and `Ruff (ops platform)` (TC-009, TC-010).
    - The 15 required contexts report success (TC-011).
    - The two Native Windows workflows do not run, because their push paths do not match this change (research rows RC-17 and RC-19). Their absence is expected.
    - The branch contains the latest `origin/main`, because branch protection uses strict mode (research row RC-31).
    - If a check fails, record its log lines in analysis.md and stop before the merge.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py` on the rebased branch (TC-002, TC-003). GitHub read: `gh pr checks --watch` on the fix branch.
  - Status: open. Depends on T-PR.

- [ ] T-MERGE [FR-009] Enable auto-merge after authorization.
  - Paths: none changed. The merge carries the change map in plan.md.
  - Acceptance: The orchestrator authorizes the merge. Add the `auto-merge` label only after each required check shows green. The pull request merges as one squash commit. Issue #4894 closes through `Closes #4894`. Remove the branch and the worktree after the merge.
  - Caution: a squash merge cannot be undone by removing the branch. A revert needs a new pull request.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py` on the merged main (TC-002, TC-003). GitHub read: `gh pr view --json state,mergedAt` on the fix branch shows MERGED.
  - Status: open. Depends on T-REMOTE-CI.
