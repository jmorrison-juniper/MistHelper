# Tasks: Editor Import Diagnostics

**Input**: Numeric record at `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/editor-evidence.md`.

**Tests**: The acceptance checks AT-01 to AT-11 are listed below. They replace automated tests because this change adds no code (decision D-5).

## Format

- `[P]` marks a task that can run in parallel. It touches different files and has no dependency.
- `[FR-###]` names the requirements that the task satisfies.
- Status values are `open`, `verified-present`, `partial`, or `absent`.
- A verification that no table gate covers names a supporting command. Analysis finding A-03 explains each one.

## Acceptance Checks

- **AT-01** (FR-002, FR-003, FR-004, FR-005, FR-015): The live editor check records one evidence row for each current path. Each row holds every field of the contract. Each row shows zero E0401 and zero E0611.
- **AT-02** (FR-004, FR-011): Each current path exits with code 0 and no output from the terminal Pylint command.
- **AT-03** (FR-001, FR-002, FR-003): The root and interpreter command prints paths that sit inside the worktree.
- **AT-04** (FR-006): The remote tree filter returns the 27 current paths with blob SHAs, and it returns no path under the listed old prefix.
- **AT-05** (FR-007): The remote line check returns the current content of each of the 8 cited lines.
- **AT-06** (FR-008): The `init-hook` line and the setup section match the repository evidence.
- **AT-07** (FR-014): A text search finds no user-profile path segment and no credential name in the record or the pull request body.
- **AT-08** (FR-010, FR-017): The issue state is OPEN, the pull request body holds `Refs #4126`, and the issue labels match decision D-9.
- **AT-09** (FR-009): The changed file list holds only the record files and the changelog fragment.
- **AT-10** (FR-013): The changelog fragment holds one `###` heading and one bullet, and its name is unique.
- **AT-11** (FR-016): The route equals the required path. Each directory on the route holds five children or fewer.

## Phase 1: Confirm the Evidence on Main

- [x] T001 [P] [FR-008] Confirm the editor setup section on main.
  - Files: `documentation/development-setup.md` (lines 197 to 260).
  - Acceptance: The heading sits at line 197. The settings block sits at lines 216 to 222. The command sits at line 236. Rows R47 to R49 record these lines.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`
  - Status: verified-present

- [x] T002 [P] [FR-006] Confirm the 27 current paths and the listed old prefix.
  - Files: the 27 current paths in `design/data-model.md`. Rows R01 to R28 record them.
  - Acceptance: 27 paths exist on `main` with a blob SHA. Ten paths moved. The listed old prefix has no entry.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md` in the record folder
  - Status: verified-present

- [x] T003 [P] [FR-007] Confirm the status of the 8 cited lines.
  - Files: `MistHelper.py` lines 474, 480, 543, 699, 779, 3384, 3426, and 3678. Rows R29 to R36 record them.
  - Acceptance: Eight rows exist. Each row states the current content or the absence of the cited text.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md` in the record folder
  - Status: verified-present

- [x] T004 [P] [FR-008] Confirm the Pylint claims in the repository.
  - Files: `pyproject.toml` (line 566), `requirements-dev.txt` (line 313), `.gitignore` (line 248). Rows R51 to R53 record them.
  - Acceptance: The `init-hook` adds the working directory. The pin is `pylint==4.1.4`. Git ignores `.vscode/`.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 analysis.md` in the record folder
  - Status: verified-present

- [x] T005 [P] [FR-013] Confirm the changelog fragment from pull request #4322.
  - Files: `changelog.d/issue-4126-editor-import-worktree.md`. Row R50 records it.
  - Acceptance: The fragment exists on `main`. The new fragment name differs from this name (decision D-10).
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4126-editor-import-worktree.md`
  - Status: verified-present

## Phase 2: Author This Change

- [ ] T006 [P] [FR-016] Write the ten record files.
  - Files: `specs/numbered/0/0/1/1/3/0/0/1/4126-editor-import-diagnostics/spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/editor-evidence.md`, `design/checklists/requirements.md`, and `design/checklists/live-check.md`.
  - Acceptance: Each file exists at the route path. AT-11 passes.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80` with the ten record file paths
  - Status: open

- [ ] T007 [P] [FR-013] Add the changelog fragment.
  - Files: `changelog.d/issue-4126-editor-import-spec.md`.
  - Acceptance: The file holds one `### Changed` heading and one bullet. The bullet names issue #4126. AT-10 passes.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4126-editor-import-spec.md`
  - Status: open

## Phase 3: Live Verification (Owner-Run, Not Part of This Change)

- [ ] T008 [FR-001, FR-002, FR-003] Run the root and interpreter check in the worktree.
  - Files: the worktree root and its `.venv`. The check reads no repository file.
  - Acceptance: The command prints a root, an interpreter, and an environment inside the worktree (AT-03). If the worktree still uses `src/org/juniper_rma/`, rebase onto `main` first (decision D-8).
  - Verification: Supporting command in `design/quickstart.md`, step 3. No table gate covers this check.
  - Status: open

- [ ] T009 [FR-011] Run the terminal Pylint check for each current path.
  - Files: the 27 current paths in `design/data-model.md`.
  - Acceptance: Each path exits with code 0 and no output (AT-02). This result does not count as live evidence (FR-011).
  - Verification: Supporting command in `design/quickstart.md`, step 4. No table gate covers this check.
  - Status: open

- [ ] T010 [FR-004, FR-005, FR-015] Run the live editor check for each current path.
  - Files: the 27 current paths and the editor window. The check writes no repository file.
  - Acceptance: One evidence row exists for each path, with zero E0401 and zero E0611 (AT-01). If a native permission is missing, record each path as unverified with the cause (FR-015).
  - Verification: Live editor check in `design/checklists/live-check.md`. No table gate covers this check.
  - Status: open. Blocked by the missing Screen Recording permission reported on 2026-10-31.

- [ ] T011 [FR-010, FR-017] Post the evidence rows to issue #4126 and keep the issue open.
  - Files: the issue #4126 comments. The owner posts the evidence rows after T010.
  - Acceptance: The issue remains OPEN until all 27 paths pass (AT-08).
  - Verification: `gh issue view 4126 -R jmorrison-juniper/MistHelper --json state --jq .state` returns OPEN. No table gate covers this check.
  - Status: open

## Phase 4: Gate and Ship

- [ ] T-LOCAL-GATES [FR-009, FR-012, FR-013] Run the local gates on the changed files.
  - Files: the eleven changed Markdown files from T006 and T007.
  - Acceptance: Each file scores 80 or above. The changed file list holds only the eleven files (AT-09).
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80` with the eleven file paths.
  - Status: open

- [ ] T-PR [FR-010, FR-014] Commit, push, and open the pull request.
  - Files: the eleven changed files.
  - Acceptance: The branch is `chore/4126-editor-import-diagnostics`. The commit subject is `docs(spec): record editor import diagnostics for issue 4126`. The commit message ends with the Co-authored-by trailer. The pull request title uses the same subject. The body holds `Refs #4126`, the changed-file summary, the gate result, and the rollback note. AT-07 and AT-08 pass.
  - Verification: The STE result from T-LOCAL-GATES.
  - Status: open

- [ ] T-REMOTE-CI [FR-010] Watch the remote checks for the pull request.
  - Files: the pull request checks. The check reads no repository file.
  - Acceptance: `gh pr checks` with the pull request number ends with every required check green.
  - Verification: The STE result from T-LOCAL-GATES, and the check list from `gh pr checks`.
  - Status: open

- [ ] T-MERGE [FR-010, FR-017] Squash-merge the pull request after the orchestrator authorizes it.
  - Files: none.
  - Acceptance: The merge uses one squash commit. The issue remains OPEN after the merge (AT-08). The branch is deleted after the merge.
  - Verification: `gh issue view 4126 -R jmorrison-juniper/MistHelper --json state --jq .state` returns OPEN.
  - Status: open

## Dependencies

- T006 and T007 come before T-LOCAL-GATES.
- T-LOCAL-GATES comes before T-PR.
- T-PR comes before T-REMOTE-CI and T-MERGE.
- T008, T009, and T010 run in order on the owner machine. They do not block T-PR.
- T011 comes after T010. The issue stays open until the evidence passes.
