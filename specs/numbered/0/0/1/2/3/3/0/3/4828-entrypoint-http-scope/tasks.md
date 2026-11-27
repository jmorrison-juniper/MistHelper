# Tasks: Entry-point test quality for HTTP status scope

Format: `T### [P?] Title`. The `[P]` marker means the task is safe in parallel. Status values are `open`, `verified-present`, `partial`, and `absent`. Requirement IDs refer to `spec.md`. Verification commands come from the local gates table in `.github/copilot-instructions.md` (RC-63) unless the task names another source.

## Phase 1: Verify the present state

### T001 [P] Verify the help tests use the public entry point

- **Requirements**: FR-001, SC-002
- **Files**: `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py`
- **Acceptance**: The file imports `MainEntrypoint` and not `ApplicationBootstrap` (RC-01). All 15 cases pass.
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py`
- **Status**: verified-present (RC-01, RC-04)
- **Depends on**: none

### T002 [P] Verify the reject-flag tests use the public entry point

- **Requirements**: FR-002, SC-002
- **Files**: `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py`
- **Acceptance**: The file imports `MainEntrypoint` and not `ApplicationBootstrap` (RC-05, RC-07). All 3 tests pass.
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py`
- **Status**: verified-present (RC-05, RC-07)
- **Depends on**: none

## Phase 2: Remove the duplicate argument test

### T003 Delete the duplicate argument test

- **Requirements**: FR-003, SC-003
- **Files**: `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` (delete lines 158 to 166)
- **Acceptance**: `test_empty_argument_list_reaches_normal_startup` no longer exists (RC-12). The `ApplicationBootstrap` import stays for the logging tests (RC-11). The module loses one case. The help case `["MistHelper.py"]` remains (help file, lines 51 to 69).
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py`
- **Status**: open
- **Depends on**: T001

## Phase 3: Analyzer fix and pin (external repository)

### T004 Open the misthelper-devtools issue

- **Requirements**: FR-005, FR-009
- **Files**: None in this repository. The issue belongs to `jmorrison-juniper/misthelper-devtools`.
- **Acceptance**: The issue cites `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` at commit `2239e7bd`. It names lines 327 and 328 (RC-32) and lines 370 to 379 (RC-34). The orchestrator opens the issue. This agent does not create issues.
- **Verification**: `gh issue view <number> -R jmorrison-juniper/misthelper-devtools`. This read-only GitHub check is the only check. No local gate covers an external issue.
- **Status**: absent
- **Depends on**: none

### T005 Fix the analyzer scope in misthelper-devtools

- **Requirements**: FR-005
- **Files** (external repository): `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py`. Add a good fixture under `src/misthelper_devtools/test_quality_analyzer/fixtures/good/` (Unverified U-08).
- **Acceptance**: A class import whose unrelated method imports `mistapi.__logger` yields no `missing_fm_http` finding. A test that calls an HTTP client keeps its HTTP finding. The fix merges to the misthelper-devtools `main` branch.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` after T006 (RC-63 Test quality row)
- **Status**: absent
- **Depends on**: T004

### T006 Pin the analyzer fix in three files

- **Requirements**: FR-006, SC-005
- **Files**:
  - `pyproject.toml`: comment on line 122 and pin on line 123 (RC-29).
  - `uv.lock`: regenerated with `uv lock` (RC-30).
  - `requirements-dev.txt`: pin on line 197 (RC-28). Header regenerated from the export command on line 2.
- **Acceptance**: All three files name the same commit. The comment on `pyproject.toml` line 122 names the new commit or its release tag (analysis A-05). `uv lock --check` exits with code 0. `tests/guardrails/test_dependency_export.py` passes (RC-25). Review the `uv.lock` diff. Accept only `misthelper-devtools` changes.
- **Verification**: `uv lock --check`
- **Status**: absent
- **Depends on**: T005

### T007 Refresh the baseline after the pin

- **Requirements**: FR-004, FR-007, SC-001, SC-004
- **Files**: `.github/test-quality-baseline.json`
- **Acceptance**: Run `test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` on the full suite only. The diff adds zero lines. The two stale reject-flag entries (RC-18, RC-19) disappear. Each other removed entry is listed in the pull request with its file and rule.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` (RC-63 Test quality row). The output prints `gate: 0 new findings vs baseline`.
- **Status**: absent
- **Depends on**: T006

Caution: Do not add `--roots` to a baseline command. The command then drops entries for files that the scan does not reach (RC-40).

## Phase 4: Record placement

### T008 [P] Place the record in the repository

- **Requirements**: FR-009 (process)
- **Files**: `specs/numbered/0/0/1/2/3/3/0/3/4828-entrypoint-http-scope/` (copy `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` from the draft folder)
- **Acceptance**: The repository record holds the same feature-root children and design children as the draft folder. The record adds no other file. The record folder sits under the numbered route (RC-45).
- **Verification**: `python -m pytest tests/guardrails` (guardrail command in RC-65, section "Move a module")
- **Status**: open
- **Depends on**: none

## Phase 5: Final tasks

### T-LOCAL-GATES Run the applicable local gates

- **Requirements**: FR-004, FR-008, SC-001
- **Files**: Each changed file: the test module, the three pin files, the baseline, and the record folder.
- **Acceptance**: Each applicable gate passes. Each gate that does not apply carries a reason in the pull request body. The applicable gates are these.
  - Compile: `python -m py_compile MistHelper.py` prints no output (RC-60).
  - Lint: `python -m ruff check .` prints `All checks passed` (RC-53).
  - Format: `python -m black --check .` reports that no file needs a change.
  - Tests: The entry-point test folder passes.
  - Preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` passes (RC-46).
  - Test quality: The changed-file gate and the full gate print `gate: 0 new findings vs baseline`.
  - Symbols: `symbol-diff --base origin/main tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` prints `no module-level name changed`.
  - Security lint: `bandit -c pyproject.toml -r . -q` reports no finding.
  - Dependency lock: `uv lock --check` exits with code 0.
  - Not applicable: mypy (RC-24 excludes tests), vulture, pydocstyle, interrogate, pylint, radon, safe sweep, menu reference, coverage (no `src/` change), and STE (no listed Markdown file changes).
- **Verification**: `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint`
- **Status**: open
- **Depends on**: T003, T007

### T-PR Open the pull request

- **Requirements**: FR-009, SC-006
- **Files**: Branch `fix/4828-entrypoint-http-scope` from `main`. The branch holds four commits. The commits add the record, change the test module, change the pin files, and change the baseline.
- **Acceptance**:
  - Add the `in-progress` label to issue #4828 before you create the branch (RC-54).
  - Create the branch in a worktree from `main` (RC-55).
  - Check open pull requests for file overlap before the pin commit. Use the Edge Cases rule for pull request 4888 (RC-49).
  - Write each commit subject in Conventional Commits form (RC-56). Each commit body ends with the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
  - Title the pull request `test(entrypoint): drop duplicate argument test and pin analyzer fix`.
  - Fill the sections of `.github/PULL_REQUEST_TEMPLATE.md` (RC-48). Name all three bootstrap modules in the body (analysis A-01).
  - The body contains `Closes #4828` (RC-57).
- Warning: Do not force-push a shared branch. Push this branch with `--force-with-lease` only (RC-55).
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json body --jq .body` prints a body that contains `Closes #4828`.
- **Status**: open
- **Depends on**: T-LOCAL-GATES, T003, T005, T006, T007, T008

### T-REMOTE-CI Watch the remote checks

- **Requirements**: FR-008, SC-001
- **Files**: None. The check runs belong to GitHub.
- **Acceptance**: These checks report success on the latest commit. Their names come from the check rollup of pull request 4833 and from RC-26: `Test quality ratchet (gate)`, `Ruff (lint)`, `Black (format check)`, `mypy (strict)`, the four pytest coverage shards, `Dependency lock and exports`, `Bandit (security)`, `Conventional Commits PR title`, `ste-lint / STE compliance`, and `CodeQL`. Wait for CodeQL before you add the auto-merge label (RC-57).
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
- **Status**: open
- **Depends on**: T-PR

### T-MERGE Merge and verify the build

- **Requirements**: FR-009, SC-006
- **Files**: The pull request branch, which the merge removes. The workflow `.github/workflows/container-build.yml` runs on `main` (RC-41).
- **Acceptance**:
  - The orchestrator authorizes the merge.
  - Add the `auto-merge` label only after each check shows success (RC-57).
  - Squash merge the pull request (RC-58). The linked-issue workflow closes #4828.
  - Wait for `container-build.yml` on the merged commit. Principle IV steps 10 to 12 apply (RC-59). The image revision label must equal the merged commit SHA.
  - Remove the branch and the worktree after the merge (RC-58).
- Warning: Do not push to the branch after the squash merge. The pull request becomes an orphan that nobody merges (RC-58).
- **Verification**: `gh run list -R jmorrison-juniper/MistHelper --workflow container-build.yml --branch main --limit 1 --json conclusion,headSha` shows `success` and the merged commit SHA.
- **Status**: open
- **Depends on**: T-REMOTE-CI

## Task summary

- Verified present: T001, T002.
- Open in this repository: T003, T008, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE.
- Absent, waiting on the external analyzer fix: T004, T005, T006, T007.
