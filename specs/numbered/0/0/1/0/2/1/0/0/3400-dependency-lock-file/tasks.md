# Tasks: Tracked Dependency Lock File

Each task gives its status, requirements, parallel flag, exact repository paths, acceptance statement, and one verification command from the Local gates table. Four final tasks close each slice.

Status values are `open`, `verified-present`, `partial`, and `absent`. A `verified-present` task needs no edit. Its verification command still runs before a slice closes.

The `[P]` flag marks a task that edits different files from other `[P]` tasks in the same slice.

The slices follow plan.md. The order is R, then 1 to 5.

## Slice R: Record

### T001 Replace the legacy record and remove the legacy comparison file

- Status: absent
- Requirements: none. Record only (decision D-9).
- Parallel: no
- Files: `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md` (modify), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/plan.md` (modify), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/tasks.md` (modify), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/analysis.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/research.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/data-model.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/quickstart.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/contracts/lock-install-contract.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/checklists/requirements.md` (add), `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/lock-comparison.md` (delete)
- Acceptance: The record folder holds these files only. The `design` folder holds five children or fewer. Each Markdown file passes the STE command in T-LOCAL-GATES.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`

## Slice 0: Verified tasks

### T002 Confirm the declarations

- Status: verified-present
- Requirements: FR-001, FR-017
- Parallel: [P]
- Files: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `tests/guardrails/test_dependency_declaration_parity.py`
- Acceptance: The mistapi floor, the devtools pin, and the uv pin are declared (RC-11, RC-13, RC-14, RC-53). The declaration test and the Python floor test pass.
- Verification: `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`

### T003 Confirm the lock is tracked and current

- Status: verified-present
- Requirements: FR-002
- Parallel: [P]
- Files: `uv.lock`, `pyproject.toml`, `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: `uv.lock` is tracked (RC-01) and requires Python 3.15 (RC-02). The currency test passes (RC-58).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T004 Confirm the exports equal the lock

- Status: verified-present
- Requirements: FR-004
- Parallel: [P]
- Files: `requirements.txt`, `requirements-dev.txt`, `uv.lock`, `tests/guardrails/test_dependency_export.py`
- Acceptance: Both exports carry the uv export header (RC-16, RC-18). The export match test passes (RC-54).
- Verification: `python -m pytest tests/guardrails/test_dependency_export.py`

### T005 Confirm the bootstrap syncs from the lock

- Status: verified-present
- Requirements: FR-005
- Parallel: [P]
- Files: `scripts/bootstrap_worktree.py`, `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
- Acceptance: The bootstrap runs `uv sync --locked --extra dev` (RC-30). The bootstrap sync test passes (RC-55).
- Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`

### T006 Confirm the CI lock gate

- Status: verified-present
- Requirements: FR-006
- Parallel: [P]
- Files: `.github/workflows/ci.yml`, `tests/guardrails/test_dependency_lock_workflow.py`
- Acceptance: The `dependency_lock` job runs `uv lock --check` (RC-20) and the export guard (RC-21). The workflow guard passes (RC-56).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`

### T007 Confirm the container unit tests use the lock

- Status: verified-present
- Requirements: FR-009
- Parallel: [P]
- Files: `.github/workflows/container-build.yml`, `tests/guardrails/test_container_build_trigger.py`
- Acceptance: The unit test step runs `uv sync --locked` (RC-26). The trigger includes `uv.lock` (RC-25). The locked test environment test passes (RC-57).
- Verification: `python -m pytest tests/guardrails/test_container_build_trigger.py`

### T008 Keep the audit on the runtime export

- Status: verified-present
- Requirements: FR-008
- Parallel: [P]
- Files: `.github/workflows/ci.yml`, `documentation/quality-gates.md`
- Acceptance: The `pip_audit` job runs `pip-audit -r requirements.txt` (RC-23). The quality gates document keeps the command (RC-45). Case c6 in T013 guards the command.
- Verification: `pip-audit -r requirements.txt`

## Slice 1: Guards and pins

### T009 Guard the `.gitignore` rule

- Status: partial
- Requirements: FR-003
- Parallel: no
- Files: `tests/guardrails/test_dependency_lock_file.py`, `.gitignore` (read only)
- Acceptance: The `.gitignore` file holds no uv ignore rule today (RC-08). No guard checks it (RC-41). Case c1 fails when a `uv.lock` ignore rule appears.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T010 Declare the uv range in `pyproject.toml`

- Status: absent
- Requirements: FR-015
- Parallel: no
- Files: `pyproject.toml`, `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: A `[tool.uv]` table holds `required-version = ">=0.13.9,<0.14"`. RC-15 is absent today. The pin stays at line 101 (RC-14). Case c2 passes. `uv lock --check` still passes.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T011 Pin the bootstrap uv install

- Status: absent
- Requirements: FR-015
- Parallel: no
- Files: `scripts/bootstrap_worktree.py` (function `install_uv`, lines 449 to 460), `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`, `changelog.d/issue-3400-uv-pin.md` (add)
- Acceptance: The install command uses `uv==0.13.9` (RC-29 is absent today). The log lines before and after the install stay in place. Each changed line carries an inline comment. Case c3 passes. The fragment names issue 3400.
- Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`

### T012 Guard the uv pins

- Status: absent
- Requirements: FR-015
- Parallel: no
- Files: `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: Case c4 reads the uv pin in `pyproject.toml` (line 101), in `requirements-dev.txt` (line 470), in `.github/workflows/container-build.yml` (line 92), and in the bootstrap install literal. It fails when any value differs from `0.13.9`.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

## Slice 2: CI installs

### T013 Write the CI contract cases

- Status: absent
- Requirements: FR-007, FR-008
- Parallel: no
- Files: `tests/guardrails/test_dependency_lock_workflow.py`
- Acceptance: Case c5 requires each install step to run the pin command, the locked sync command, and the `GITHUB_PATH` step. Case c6 requires the `pip_audit` command to read `requirements.txt`. Case c5 fails on today's file (RC-22).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`

### T014 Switch the CI installs to a locked uv sync

- Status: absent
- Requirements: FR-007
- Parallel: no
- Files: `.github/workflows/ci.yml`, `changelog.d/issue-3400-ci-locked-sync.md` (add)
- Acceptance: Each job that installs packages runs `python -m pip install uv==0.13.9`. The job then runs `uv sync --locked --extra dev --no-install-project`. It then appends the `.venv/bin` path to `GITHUB_PATH`. Jobs that import the project omit `--no-install-project`. The `dependency_lock` job keeps its export guard. Caution: a wrong PATH step fails each job that uses it.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`

## Slice 3: Images

### T015 Write the image contract cases

- Status: absent
- Requirements: FR-010, FR-011
- Parallel: no
- Files: `tests/guardrails/test_container_build_trigger.py`
- Acceptance: Case c7 requires the Dockerfile to run a locked uv sync into `/opt/misthelper-venv` and to drop `pip install -r requirements.txt` (RC-31). Case c8 requires the same for `Containerfile` (RC-32). Case c9 requires `.dockerignore` to admit `uv.lock` after line 121 (RC-09). All three cases fail on today's files.
- Verification: `python -m pytest tests/guardrails/test_container_build_trigger.py`

### T016 Switch the image installs and the build context

- Status: absent
- Requirements: FR-010, FR-011
- Parallel: no
- Files: `Dockerfile`, `Containerfile`, `.dockerignore`, `changelog.d/issue-3400-image-locked-sync.md` (add)
- Acceptance: The image copies `pyproject.toml` and `uv.lock` before the source. It installs uv 0.13.9 with pip, runs `UV_PROJECT_ENVIRONMENT=/opt/misthelper-venv uv sync --locked --no-install-project`, and uninstalls uv in the same `RUN` step. `PATH` points to the venv. `.dockerignore` gets `!uv.lock` after line 121. The `misthelper` user (UID 1000) must read the venv (U-K). This task checks whether the sync needs `README.md` (U-C). Warning: a pushed image tag can reach users before anyone checks its package set.
- Verification: `python -m pytest tests/guardrails/test_container_build_trigger.py`

### T017 Add the image freeze comparison

- Status: absent
- Requirements: FR-012
- Parallel: no
- Files: `.github/workflows/container-build.yml`, `tests/guardrails/test_container_build_trigger.py`
- Acceptance: Case c10 requires a step after the image build. The step runs `python -m pip freeze` inside the built image and compares the output with the runtime export. RC-28 shows no freeze step today.
- Verification: `python -m pytest tests/guardrails/test_container_build_trigger.py`

## Slice 4: Ops lock

### T018 Add the ops lock

- Status: absent
- Requirements: FR-014
- Parallel: no
- Files: `mist-ops-platform/uv.lock` (add), `mist-ops-platform/pyproject.toml` (modify only if the lock check reports drift), `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: `uv lock --check` passes in `mist-ops-platform/`. Case c11 runs that check. RC-36 is absent today. Complexity Tracking applies (Principle I).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T019 Switch the ops containers and the ops CI job to the ops lock

- Status: absent
- Requirements: FR-014
- Parallel: no
- Files: `mist-ops-platform/deploy/Containerfile.api`, `mist-ops-platform/deploy/Containerfile.worker`, `.github/workflows/ci.yml` (ops install lines), `tests/guardrails/test_dependency_lock_file.py`, `changelog.d/issue-3400-ops-lock.md` (add)
- Acceptance: Case c12 requires both Containerfiles to install from `mist-ops-platform/uv.lock`. RC-37 and RC-38 are absent today. The ops CI job uses the same lock. Confirm the exact uv flags from the ops project layout before the change (U-D).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T020 Replace the ops export

- Status: absent
- Requirements: FR-014
- Parallel: no
- Files: `mist-ops-platform/requirements.txt`, `tests/guardrails/test_dependency_export.py`
- Acceptance: `mist-ops-platform/requirements.txt` becomes an export of the ops lock with the uv export header. RC-39 is absent today. Case c13 fails on drift. Start this task only after pull requests #4889 and #4890 merge or close (R2). Check the Linux resolution against the export (U-I).
- Verification: `python -m pytest tests/guardrails/test_dependency_export.py`

## Slice 5: Dependabot and documentation

### T021 Document the export regeneration command

- Status: partial
- Requirements: FR-016
- Parallel: no
- Files: `documentation/development-setup.md`, `documentation/quality-gates.md`, `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: The header of `requirements.txt` names the command (RC-16). The development setup document does not name it yet (RC-40). Case c14 requires both documents to name `uv export --locked --no-hashes --no-emit-project`. The quality gates document states that the audit reads `requirements.txt` (RC-45).
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T022 Correct the stale document lines

- Status: absent
- Requirements: FR-016, FR-017
- Parallel: no
- Files: `documentation/development-setup.md` (lines 28 and 29, RC-43), `documentation/container-deployment.md` (lines 291 and 292, RC-44), `.github/copilot-instructions.md` (line 21, RC-42), `tests/guardrails/test_dependency_lock_file.py`
- Acceptance: The development setup document describes the locked bootstrap. The container deployment document lists `uv.lock` and `pyproject.toml` among the trigger files. The instruction file states the mistapi floor `>=0.64.1,<0.65`. Case c15 asserts each line.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T023 Move Dependabot to the uv ecosystem

- Status: absent
- Requirements: FR-013
- Parallel: no
- Files: `.github/dependabot.yml`, `tests/guardrails/test_dependency_lock_workflow.py`, `tests/guardrails/test_dependency_export.py`, `changelog.d/issue-3400-dependabot-uv.md` (add)
- Acceptance: The root `pip` entry at line 3 becomes a `uv` entry for `/`. A `uv` entry for `/mist-ops-platform` exists after T018. Case c16 asserts both entries and no `pip` entry for `/`. Case c17 requires the export guard failure text to name the regeneration command. Case c17 runs in `tests/guardrails/test_dependency_export.py`. Confirm the Dependabot uv behavior (U-N) when the first update opens.
- Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`

## Final gates for each slice

### T-LOCAL-GATES

- Status: open
- Requirements: every FR of the slice
- Parallel: no
- Files: `.github/copilot-instructions.md` (gates table, read only), and the paths in the Files line of each task in the slice
- Acceptance: Run each applicable row of the Local gates table in `.github/copilot-instructions.md` (lines 57 to 76). For Markdown files, run the STE row. Run the same `ste-linter` options on each changed record or document file. For Python files, run the Lint row (`python -m ruff check .`) and the Format row (`python -m black --check .`). Run the Tests row for each changed test file. Run the Symbols row, `symbol-diff --base origin/main <file>`, for each changed Python file. Record each result in the pull request.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`

### T-PR

- Status: open
- Requirements: every FR of the slice
- Parallel: no
- Files: `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/` (record slice), and the paths in the Files line of each task in a later slice
- Acceptance: Create the branch `docs/3400-dependency-lock-file` for the record slice. Name later slice branches with the type and the issue number, for example `chore/3400-ci-locked-sync`. Commit with a Conventional Commits subject, such as `docs(spec): record the tracked dependency lock decision`. The commit message carries the Co-authored-by trailer that the session requires. The record pull request body names `Refs #3400` (D-10). Only the final slice body names `Closes #3400`. The body holds the changed-file summary and the local gate results. The orchestrator authorizes the record slice. Slices 2 to 5 need user approval before push or pull request creation (U-G).
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`

### T-REMOTE-CI

- Status: open
- Requirements: every FR of the slice
- Parallel: no
- Files: `.github/workflows/ci.yml` (required checks), `.github/workflows/container-build.yml` (dispatch only)
- Acceptance: Run `gh pr checks --watch` on the branch. Each required check reports success. The required checks include `Conventional Commits PR title` and `ste-lint / STE compliance`. Pull request checks do not run the container build. That workflow starts on a push to `main` or on a manual dispatch (`.github/workflows/container-build.yml` lines 3 to 5). The image freeze check needs a dispatch after user approval.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`

### T-MERGE

- Status: open
- Requirements: every FR of the slice
- Parallel: no
- Files: `.github/workflows/ci.yml` (defines the required checks, read only)
- Acceptance: Enable auto-merge only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Slice R and slice 1 may use auto-merge. Slices 2 to 5 stay open for human review, with no auto-merge, and need user approval (U-G). Use squash merge. Caution: a bad merge needs a new revert pull request.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`
