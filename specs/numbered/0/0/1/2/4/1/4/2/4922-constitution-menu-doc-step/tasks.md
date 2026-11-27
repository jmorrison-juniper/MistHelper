# Tasks: Menu step names the generated pages

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/4/2/4922-constitution-menu-doc-step/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, and `design/quickstart.md`

**Tests**: The five guard cases in `tests/guardrails/test_changelog_fragment_policy.py` come first. Each case fails on the unchanged text before the amendment tasks run.

**Environment**: Activate the worktree environment with `.venv\Scripts\Activate.ps1`, as `.github/copilot-instructions.md` describes. Run each command from the worktree root.

## Format

- **[P]**: The task edits a different file from the other tasks in its phase, so it can run in parallel.
- **Requirements**: The FR IDs in `spec.md` that the task serves.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Baseline

- [ ] T001 [P] Confirm that the generated menu pages and the generator exist on `main`.
  - Paths: `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `scripts/generate_menu_wiki.py`.
  - Requirements: FR-001.
  - Acceptance: The three paths match RC-12, RC-14, and RC-15 in `design/research.md`.
  - Verification: `python scripts/generate_menu_wiki.py`, then `python -m scripts.menu_api_map`. No changed file appears after the run (Menu reference row).
  - Status: verified-present.

## Phase 2: Tests first

- [ ] T002 Add the five guard cases to `tests/guardrails/test_changelog_fragment_policy.py`.
  - Paths: `tests/guardrails/test_changelog_fragment_policy.py`, at the end of `TestPolicyStaysStated`.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006.
  - Acceptance: The method `test_menu_step_and_version_record_stay_stated` exists with the five cases in `plan.md`. All five cases fail on the unchanged text.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -k menu_step_and_version_record`.
  - Status: open.

## Phase 3: Amend the guidance text

- [ ] T003 Replace step 5 in `.specify/memory/constitution.md` (lines 352 and 353) with the text in `plan.md`.
  - Requirements: FR-001, FR-002.
  - Acceptance: Case `menu-step` passes. The phrases "menu table" and "Update README" no longer appear in step 5.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -k menu_step_and_version_record`.
  - Status: open. Depends on T002.

- [ ] T004 Replace the README bullet in `.specify/memory/constitution.md` (lines 400 and 401).
  - Requirements: FR-003.
  - Acceptance: Case `readme-bullet` passes.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -k menu_step_and_version_record`.
  - Status: open. Depends on T003, because both edits change the same file.

- [ ] T005 Replace the Sync Impact Report fields (lines 4 to 24) and the footer (line 562) in `.specify/memory/constitution.md`.
  - Requirements: FR-005, FR-006.
  - Acceptance: Cases `footer-version` and `sync-report` pass.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -k menu_step_and_version_record`.
  - Status: open. Depends on T004, because both edits change the same file.

- [ ] T006 [P] Replace step 1 of "Add a menu operation" in `.github/copilot-instructions.md` (line 242).
  - Requirements: FR-004, FR-009.
  - Acceptance: Case `rule-file-step` passes. The STE gate scores the file at 80 or above.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` (STE row).
  - Status: open. Depends on T002.

- [ ] T007 [P] Add the fragment `changelog.d/issue-4922-constitution-menu-doc-step.md`.
  - Requirements: FR-008.
  - Acceptance: The fragment holds one `###` heading and one `Changed` bullet that names issue 4922. The file name follows the issue form in `changelog.d/README.md`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row).
  - Status: open.

## Phase 4: Gates and delivery

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - Paths: the four changed files and the record folder.
  - Requirements: FR-007, FR-009, FR-010.
  - Acceptance: Each applicable command below passes. Run the commands in this order.
    1. Test quality preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`.
    2. Lint: `python -m ruff check .` prints `All checks passed`.
    3. Format: `python -m black --check .` reports no file that needs a change.
    4. Tests: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` and `python -m pytest tests/guardrails/test_websocket_transport_constitution.py`.
    5. Full tests shard: the second `pytest-chunks` command of the Full tests row. It covers `tests\guardrails`.
    6. Symbols: `symbol-diff --base origin/main tests/guardrails/test_changelog_fragment_policy.py` prints `no module-level name changed`.
    7. STE: the STE row command, then the measurement `ste-linter --config .ste-linter.toml --min-score 80 .specify/memory/constitution.md`.
  - Not applicable: Compile, Types, Safe sweep, Coverage, Complexity, Security lint, Dependency audit, Code quality, Dead code, Docstrings, Menu reference, Ops portal, and Ops platform. The reasons are in `design/quickstart.md`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row).
  - Status: open. Depends on T003, T004, T005, T006, and T007.
  - If a Lint or Format failure exists on `main` before this change, record it. Do not fix it in this pull request.

- [ ] T-PR Commit, push, and open the pull request.
  - Paths: the four changed files and `specs/numbered/0/0/1/2/4/1/4/2/4922-constitution-menu-doc-step/`.
  - Requirements: SC-006.
  - Steps:
    1. Stage each file by explicit path. Do not run `git add -A` or `git add .`.
    2. Commit with the subject `docs(constitution): name generated menu pages, not the README table`. The body holds `Closes #4922` and this trailer: `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
    3. Run the required Test quality check after the commit and before the push. The command is in `design/quickstart.md`.
    4. Push the branch `docs/4922-constitution-menu-doc-step`.
    5. Open the pull request. Use the same title as the commit. The body holds `Closes #4922` and the changed-file summary. It also holds the local gate results, the measured STE score of the constitution, and the reason for the PATCH class (D-5).
  - Verification: the required Test quality command in `design/quickstart.md`, section 5. Its output line is `gate: 0 new findings vs baseline`.
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: SC-004, SC-007.
  - Steps: Set `PR_NUMBER` to the number that `gh pr create` returns. Run `gh pr checks $PR_NUMBER -R jmorrison-juniper/MistHelper --watch`.
  - Acceptance: Each required check passes. The Conventional Commits title check and the STE compliance check pass.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md` (STE row, the local form of the `ste-lint.yml` check).
  - Status: open. Depends on T-PR.

- [ ] T-MERGE Enable the merge after the orchestrator authorizes it.
  - Requirements: SC-007.
  - Steps: Add the `auto-merge` label only after each check shows green. Wait for the orchestrator authorization. The `auto-merge` workflow then squash-merges the pull request.
  - Acceptance: The pull request state is MERGED, and the issue closes through `Closes #4922`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` on `main` after the merge (Tests row).
  - Status: open. Depends on T-REMOTE-CI.
  - Warning: do not push to the branch after the squash merge. A later commit leaves the pull request orphaned, and no one merges it.

## Dependencies

- T002 comes before T003 and T006.
- T003 comes before T004, and T004 comes before T005. These tasks change the same file.
- T001 and T007 do not depend on other tasks. T006 runs in parallel with T003 to T005.
- T-LOCAL-GATES runs after T003 to T007.
- T-PR runs after T-LOCAL-GATES. T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI.
