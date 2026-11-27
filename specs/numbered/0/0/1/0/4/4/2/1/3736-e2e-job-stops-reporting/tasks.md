# Tasks: E2E stall diagnostics

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/contracts/e2e-diagnostic-files.md`, and `design/data-model.md`.

**Status values**: `verified-present` means the evidence is in place now. `partial` means part of the change exists. `absent` means the change does not exist yet.

**Format**: Each task names its requirement IDs, exact paths, acceptance statement, verification command, and status.

## Phase 1: Coordination and evidence

### T001 Confirm that no open pull request overlaps this change

- **Parallel**: no. This task gates the branch.
- **Requirements**: FR-010.
- **Files**: none. The check is read-only.
- **Acceptance**: No open pull request changes the five files that this plan changes, except the web-portal test files of #4208.
- **Verification**: `gh pr list -R jmorrison-juniper/MistHelper --state open --limit 200 --json number,headRefName,files`
- **Status**: verified-present. The scan on 2026-11-26 found that #4208 changes only `tests/e2e/web_portal/` files.

### T002 Confirm the shard layout and the job limits on main

- **Parallel**: no.
- **Requirements**: FR-009.
- **Files**: `.github/workflows/ci.yml` lines 782, 793, 795, 797, 909, 955, and 962.
- **Acceptance**: The shard job keeps 20 minutes. The three shard rows exist. The aggregator keeps 5 minutes. The pytest command keeps `--timeout=180`.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py tests/guardrails/test_ci_runtime_budgets.py -q`
- **Status**: verified-present. Research rows RC-04 to RC-10.

### T011 Keep the budgets unchanged

- **Parallel**: no.
- **Requirements**: FR-009.
- **Files**: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` line 43, `tests/guardrails/test_ci_runtime_budgets.py` line 33, `tests/guardrails/test_e2e_shard_partition.py` line 27, and `tests/e2e/conftest.py` line 33.
- **Acceptance**: `E2E_TIMEOUT_SECONDS` is 120. The pinned guard values match the current workflow values.
- **Verification**: `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_ci_runtime_budgets.py tests/guardrails/test_e2e_shard_partition.py -q`
- **Status**: verified-present. Research rows RC-17, RC-29, RC-30, and RC-31.

## Phase 2: Harness changes

### T003 Add the stack dump watch to the E2E harness

- **Parallel**: no. This task and T004 change the same file.
- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-009.
- **Files**: `tests/e2e/conftest.py`.
- **Acceptance**: A class named `StackDumpWatch` arms a `faulthandler.dump_traceback_later` watch at the protocol start of each item. The threshold is 100 seconds by default, read from `MISTHELPER_E2E_STACK_DUMP_SECONDS`, and it must be a positive finite number below 120. The watch cancels when the protocol ends. The file `test-artifacts/e2e-stack-dumps.txt` opens once at session start. Each function has at most 25 lines. Each new line has an inline comment.
- **Verification**: `python -m mypy tests/e2e/conftest.py --config-file pyproject.toml`
- **Status**: absent.

### T004 Add the protocol boundary records to the phase trail

- **Parallel**: no. This task follows T003 in the same file.
- **Requirements**: FR-005.
- **Files**: `tests/e2e/conftest.py`.
- **Acceptance**: `PhaseTrailWriter` writes one `protocol_start` record before the first phase of each item and one `protocol_end` record after the last phase. Boundary records set `duration_seconds` to null. The records use the field set in `design/contracts/e2e-diagnostic-files.md`.
- **Verification**: `python -m pytest tests/guardrails/e2e_timeout_budget/test_timeout_budget.py -q` after T008.
- **Status**: absent.

## Phase 3: Workflow changes

### T005 Add the stack dump path to the shard diagnostics upload

- **Parallel**: yes, with T003 and T004. These tasks change different files.
- **Requirements**: FR-006.
- **Files**: `.github/workflows/ci.yml` lines 943 to 946.
- **Acceptance**: The diagnostics path list contains `test-artifacts/e2e-stack-dumps.txt`. The upload condition at line 939 stays `failure() || cancelled()`.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py -q` after T007.
- **Status**: partial. The upload exists with the trail path. The dump path is absent.

### T006 Reword the cancel message

- **Parallel**: no. This task and T005 change the same file.
- **Requirements**: FR-007.
- **Files**: `.github/workflows/ci.yml` lines 948 to 952.
- **Acceptance**: The message names the 20-minute job limit, the concurrency cancel, and the artifact `e2e-diagnostics-<shard>`. The condition stays `if: cancelled()`.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py -q` after T007.
- **Status**: partial. The step exists. Its text names only the 20-minute limit.

## Phase 4: Guard tests and documentation

### T007 Add workflow contract tests

- **Parallel**: yes, with T003 to T006. The test file is separate.
- **Requirements**: FR-008.
- **Files**: `tests/guardrails/test_e2e_shard_partition.py`.
- **Acceptance**: Three tests fail for three mutations: a removed dump path, a changed upload condition, and a cancel message that names only the job limit. Each test reads the parsed workflow, not a copy.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py -q`
- **Status**: absent. This task adds 3 planned tests.

### T008 Add behavior tests for the watch and the boundary records

- **Parallel**: no. The tests need T003 and T004.
- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005.
- **Files**: `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py`.
- **Acceptance**: Four tests exist. A synthetic item that runs 1.5 times the threshold leaves a `Timeout (` line. A synthetic item that finishes early leaves no dump text. An invalid threshold fails with the variable name in the message. The trail holds one `protocol_start` and one `protocol_end` record for each item, in order. The tests reuse the existing subprocess harness.
- **Verification**: `python -m pytest tests/guardrails/e2e_timeout_budget/test_timeout_budget.py -q`
- **Status**: absent. This task adds 4 planned tests.

### T009 Update the quality-gate document

- **Parallel**: yes. The document is a separate file.
- **Requirements**: FR-009.
- **Files**: `documentation/quality-gates.md` lines 6 to 10, 53, and 68.
- **Acceptance**: The job list names `playwright_shards`. The shard row states the 20-minute job limit. The effective per-test budget of 120 seconds applies to E2E items, and the CLI value of 180 seconds does not apply to them. The row names the diagnostics artifact. Each sentence follows the writing rules.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
- **Status**: partial. The document lists `playwright` only, and it gives the 120-second value for coverage shards only (RC-33, RC-34).

### T010 Add the changelog fragment

- **Parallel**: yes. The fragment is a separate file.
- **Requirements**: FR-011.
- **Files**: `changelog.d/issue-3736-e2e-stall-diagnostics.md`.
- **Acceptance**: The fragment has one `###` heading. It has one `Changed` bullet that names issue #3736. The name follows the issue form in `changelog.d/README.md`.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: absent.

### T012 Track the changelog debt

- **Parallel**: yes. This task opens a separate issue and changes no file.
- **Requirements**: FR-011.
- **Files**: none.
- **Acceptance**: A separate issue exists that consolidates the `changelog.d/` fragments. The issue names the 335 children and links to this record.
- **Verification**: `gh issue view <number> -R jmorrison-juniper/MistHelper --json title,labels`
- **Status**: absent. The action runs in the implementation phase.

## Phase 5: Final tasks

### T-LOCAL-GATES Run the local gates

- **Parallel**: no.
- **Requirements**: FR-009, FR-010.
- **Files**: each changed file.
- **Acceptance**: Each gate from the Local gates table that applies to the changed files passes. The changed-file list has no path under `src/`, `web_portal/`, or `container/`, and it does not name `Containerfile` or `compose.yml`. The gate commands are these:
  - `python -m py_compile tests/e2e/conftest.py`
  - `python -m ruff check tests/e2e/conftest.py tests/guardrails`
  - `python -m black --check tests/e2e/conftest.py tests/guardrails`
  - `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, with `MYPY_PATHS` read from `ci.yml`
  - `radon cc tests/e2e/conftest.py -j | complexity-gate --max 10`
  - `bandit -c pyproject.toml -r tests/e2e -q`
  - `pydocstyle tests/e2e/conftest.py`
  - `interrogate tests/e2e/conftest.py --fail-under 90`
  - `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file
  - `markdown-link-check` on each changed Markdown file
- **Verification**: The commands above. Record each result in the pull request body.
- **Status**: absent.

### T-PR Commit, push, and open the pull request

- **Parallel**: no.
- **Requirements**: FR-011, FR-012.
- **Files**: the changed files from T003 to T012, and the specification record.
- **Acceptance**: The commit subject is `fix(ci): record E2E stall evidence`, and the commit trailer names Copilot. The branch is `fix/3736-e2e-stall-diagnostics`. The pull request title is Conventional. The body contains `Refs #3736` and does not contain a closing keyword for #3736. The body lists the local gate results.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body --jq '.body'` shows `Refs #3736`.
- **Status**: absent.

### T-REMOTE-CI Watch the required checks

- **Parallel**: no.
- **Requirements**: FR-009.
- **Files**: none.
- **Acceptance**: All 15 required checks pass on the pull request head. The shard jobs keep 20 minutes. A cancelled shard, if any, uploads the diagnostics artifact.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --required --watch`
- **Status**: absent.

### T-MERGE Merge after authorization

- **Parallel**: no.
- **Requirements**: FR-012.
- **Files**: none.
- **Acceptance**: Auto-merge starts only after T-REMOTE-CI passes and the orchestrator authorizes the merge. The merge is a squash. The issue stays open after the merge.
- **Verification**: `gh issue view 3736 -R jmorrison-juniper/MistHelper --json state --jq '.state'` returns `OPEN` after the merge.
- **Status**: absent.
