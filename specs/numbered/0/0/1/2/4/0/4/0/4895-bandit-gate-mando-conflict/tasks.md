# Tasks: Bandit Gate Dependency Conflict

**Input**: Design documents in `specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Tests**: Each guard case is written first. Its acceptance names the failure that proves the case can fail.

**Ownership**: Edit only the three files in the change map of `plan.md`. Do not edit `requirements-dev.txt`, `uv.lock`, `ci.yml`, or `pyproject.toml`.

**Environment**: Create a worktree and run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py` before any gate. Run each gate from the worktree root.

## Format: `[ID] [P?] Description`

- **[P]**: The task edits a different file from its neighbors and can run in parallel.
- **Status** values: `open`, `verified-present`, `partial`, or `absent`. Each status states the current repository state.
- Each task names exact paths, its requirement IDs, its acceptance, one verification command, and its status.

## Phase 1: Current State

**Purpose**: Confirm what `main` already contains.

- [ ] T001 [FR-001] Keep the `mando` pin at 0.7.1. Paths: `requirements-dev.txt` (line 179) and `uv.lock` (line 1301). Acceptance: the pin stays `mando==0.7.1`, and the export guard passes. Verification: `python -m pytest tests/guardrails/test_dependency_export.py`. Status: verified-present (main blob `9a528bfe03a10f7bc903f5768ef26de765bbff43`).

## Phase 2: Guard Cases (write first)

**Purpose**: Add the guard cases before the policy change. Each case must fail first.

- [ ] T002 [FR-002, FR-003, FR-007] Add class `RadonPinBoundary` and two test functions to `tests/guardrails/test_dependency_declaration_parity.py`. Acceptance: the synthetic function fails for `mando==0.8.2`. The real-file function fails on the PR #4888 head content and passes on `main`. Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`. Status: absent.
- [ ] T003 [FR-005] Add the `mando` ignore entry to the pip stream of `POLICY_SNAPSHOTS["dependabot"]` in `tests/guardrails/test_pr_title_workflow.py` (lines 23 to 30). Acceptance: the snapshot test fails until T004 adds the same entry to the YAML file. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`. Status: absent.

## Phase 3: Policy Change

**Purpose**: Add the Dependabot rule that matches the guard snapshot.

- [ ] T004 [FR-004] Add the `ignore` block to the pip stream of `.github/dependabot.yml` (lines 3 to 11). Acceptance: the pip stream ignores `mando` major and minor updates. Every other field keeps its value. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`. Status: absent. Depends on T003.
- [ ] T005 [FR-006, FR-008] Confirm that the change adds no file under `tests/guardrails` and removes no gate. Paths: `tests/guardrails` and `.github/workflows/ci.yml`. Acceptance: the guardrail suite passes, and the folder still holds 77 files. Verification: `python -m pytest tests/guardrails`. Status: open. Depends on T002 and T004.

## Phase 4: Record

**Purpose**: Commit the record with the change.

- [ ] T006 [P] [SC-005] Add the record files from this draft to `specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/`. Acceptance: the folder holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. Every Markdown file scores 80 or above. Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/spec.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/plan.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/tasks.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/analysis.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/design/research.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/design/data-model.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/design/quickstart.md specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/design/checklists/requirements.md`. Status: absent.

## Final Tasks

- [ ] T-LOCAL-GATES Run each gate that applies to the changed files. Acceptance: each applicable gate exits 0 and reports zero new findings. Verification: `python -m pytest tests/guardrails`. Status: open. Depends on T002, T003, T004, T005, and T006.
  - Lint: `python -m ruff check .`
  - Format: `python -m black --check .`
  - Tests: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py` and `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Guardrails: `python -m pytest tests/guardrails`
  - Security lint: `bandit -c pyproject.toml -r . -q`
  - Test quality, after the local commit: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - STE, for the record files: the command in T006.
  - Not applicable: Compile, Coverage, Code quality, Dependency audit, Menu reference, Safe sweep, Ops portal, Ops platform, and Full tests. Each of these gates covers files that this change does not touch.
  - Complexity, Dead code, and Docstrings do not include the guard tests. Their scopes sit at `ci.yml` lines 93 to 107.
  - Symbols does not apply. The copilot instructions reserve that gate for scripted sweeps.
- [ ] T-PR Commit with the Conventional Commits title `fix(ci): block mando releases that radon rejects`. Push branch `fix/4895-bandit-gate-mando-conflict` and open a pull request against `main`. Acceptance: the pull request body contains `Closes #4895`, and the title passes the Conventional Commits PR title check. Verification: `python -m pytest tests/guardrails`. Status: open. Depends on T-LOCAL-GATES.
- [ ] T-REMOTE-CI Watch the CI run on the pull request head with `gh pr checks --watch`. Acceptance: job `Bandit (security)` shows step `Run Bandit` as `success`, and each required check passes. Verification: `bandit -c pyproject.toml -r . -q` on the same head as a local preflight, which matches the CI command at `ci.yml` line 451. Status: open. Depends on T-PR.
- [ ] T-MERGE After remote CI passes and the orchestrator authorizes the merge, add the `auto-merge` label, squash merge, and delete the fix branch. Then close PR #4888 with a closing comment. The comment names the merged fix commit and the surviving branch `dependabot/pip/mando-0.8.2` at `e86098cdc2b189d217805b3b4060ef609cbc37af`. Acceptance: the `main` run of `Quality Gates` shows `success`. PR #4888 shows state `CLOSED`. The 15 gate issues close after the next `main` run. The record notes that the container build did not start. Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py` on the merged `main`. Status: open. Depends on T-REMOTE-CI.

## Traceability

| Requirement | Task | Test |
| - | - | - |
| FR-001 | T001 | `tests/guardrails/test_dependency_export.py` |
| FR-002 | T002 | `test_pinned_mando_satisfies_installed_radon` |
| FR-003 | T002 | `test_radon_boundary_rejects_mando_0_8_2` |
| FR-004 | T004 | `tests/guardrails/test_pr_title_workflow.py` |
| FR-005 | T003 | `tests/guardrails/test_pr_title_workflow.py` |
| FR-006 | T005 | `python -m pytest tests/guardrails` |
| FR-007 | T002 and T-MERGE | `test_pinned_mando_satisfies_installed_radon` on the PR #4888 head content |
| FR-008 | T005 and T-LOCAL-GATES | `python -m pytest tests/guardrails` |
| FR-009 | T-LOCAL-GATES | `bandit -c pyproject.toml -r . -q` |

## Dependencies and Execution Order

- T001 has no prerequisite.
- T002 and T003 run before T004. T003 must precede T004, because the snapshot fails first.
- T005 runs after T002, T003, T004, and T006.
- T-LOCAL-GATES runs after T002 to T006. T-PR, T-REMOTE-CI, and T-MERGE run in that order.
- T006 can run in parallel with T002 to T004, because it edits a different folder.
