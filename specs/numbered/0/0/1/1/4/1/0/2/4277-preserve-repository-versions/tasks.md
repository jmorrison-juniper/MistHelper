# Tasks: Preserve Repository Versions and Update the Local Main Checkout

**Input**: Design documents in `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\`

**Prerequisites**: `plan.md`, `spec.md`, `design\research.md`, `design\data-model.md`, `design\contracts\`, and `design\quickstart.md`

**Tests**: Each requirement maps to one verification test (V-01 to V-15). The verification tests are listed in `design\quickstart.md` and recorded in `design\contracts\validation-report.md`.

**Ownership**: The primary checkout stays unchanged. All writes go to the record path, `test-artifacts\4277\`, and two sibling worktrees.

**Environment**: Run Python with the repository virtual environment inside each worktree. Each new worktree needs the bootstrap first.

**Record path**: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions`

## Format: `[ID] [P?] [Requirement] Description`

- **[P]**: The task can run in parallel with other [P] tasks in its phase. It reads only or writes a separate file.
- **[Requirement]**: The functional requirement that the task serves.
- **Status**: `verified-present`, `partial`, `absent`, or `open`. A checkbox `[X]` marks `verified-present` only.

## Phase 1: Evidence (read-only)

- [X] T001 [P] [FR-001] Verify GitHub main head and baseline ancestry. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` (rows R-01 and R-02). Acceptance: The record states the main head, its read time, and the baseline ancestry count. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md`. Status: verified-present.

- [X] T002 [P] [FR-002] Verify the primary checkout equals `origin/main`. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` (rows L-01 and L-02). Acceptance: HEAD equals `origin/main`, and both commit counts equal zero. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md`. Status: verified-present.

- [X] T003 [P] [FR-003] Verify the PR 4404 merge and the issue 4280 closure. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` (rows R-03, R-04, and L-19), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\analysis.md` (finding A-005). Acceptance: The record states the pull request state, the merge time, and the issue state with dates. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\analysis.md`. Status: verified-present.

- [ ] T004 [P] [FR-004] Verify each cited commit on GitHub and in the object store. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` (rows R-05 to R-10 and L-06), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md` (item U-001). Acceptance: Each commit has a present or absent result and a source. The three absent commits appear as item U-001. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md`. Status: partial. The check is complete. The owner must locate the three absent commits.

- [ ] T005 [P] [FR-005] Record the owner-reported backup evidence. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md` (rows UV-01 and UV-02), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\data-model.md` (entity BackupEvidence). Acceptance: The record states the same-disk storage, the 24-hour window, and the comment IDs. Each figure is marked owner-reported. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\research.md specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\data-model.md`. Status: partial. The bundle is absent, so `git bundle verify` cannot run.

## Phase 2: Register and preservation

- [ ] T006 [FR-006] Build the branch disposition register. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\branch-disposition-register.md` (contract), `test-artifacts\4277\branch-register.tsv` (git-ignored output). Acceptance: The output holds one row for each local head counted at run time. Each row holds one disposition from the contract. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\branch-disposition-register.md`. Status: partial. Counts are measured in research L-04, but the register file is not built. Depends on T002.

- [ ] T007 [FR-007] Preserve the five modified entries. Paths: `test-artifacts\4277\preserved-files\` (five copies with relative paths), `test-artifacts\4277\modified-files.patch`, `test-artifacts\4277\modified-files.sha256`, `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md` (item U-003). Acceptance: Each copy keeps its relative path. The SHA-256 manifest lists each copy. The primary checkout keeps every file unchanged. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md`. Status: open. Depends on T006.

- [ ] T008 [FR-008] Verify zero deletions by comparing counts. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (row V-08). Acceptance: Each count equals its count before the work. The counts cover heads, tags, stash refs, preserved refs, copilot refs, agents refs, and worktree admin entries (research L-04, L-05, L-08). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md`. Status: open. Depends on T006 and T007.

## Phase 3: Baseline validation

- [ ] T009 [FR-009] Create the detached baseline worktree and bootstrap it. Paths: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline` (sibling worktree), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (setup row). Acceptance: The worktree HEAD equals `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` in detached state. The bootstrap exits with code 0. Verification: `.venv\Scripts\python.exe -m py_compile MistHelper.py`, run inside the baseline worktree (Compile gate, research R-18). Status: open. Depends on T002.

- [ ] T010 [FR-009] Run the static baseline gates. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (rows V-09). Acceptance: The compile, lint, format, and type gates each exit with code 0. Verification: `.venv\Scripts\python.exe -m ruff check .` (Lint gate, copilot-instructions line 58). The format and type commands appear in quickstart scenario 8. The mypy paths are listed in `.github\workflows\ci.yml` line 93. Status: open. Depends on T009.

- [ ] T011 [FR-010] Run both full test shards on the baseline. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (rows V-10), `test-artifacts\4277\baseline-logs\` (shard output). Acceptance: Each shard prints one summary line with zero failures. A failed chunk reruns alone, and the record keeps both results. Verification: the Full tests gate (copilot-instructions line 62). Its two `pytest-chunks.exe` commands appear in quickstart scenario 9. Status: open. Depends on T010.

- [ ] T012 [FR-011] Run the safe sweep on the baseline. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (row V-11), `test-artifacts\4277\baseline-logs\` (sweep output). Acceptance: The sweep exits with code 0. The baseline holds no `.env` file, so each Mist check skips with a credential reason. The record names each relevant variable without its value. Verification: `.venv\Scripts\python.exe MistHelper.py --test` (Safe sweep gate, copilot-instructions line 63). Status: open. Depends on T010.

- [ ] T013 [FR-013] Finalize the recovery register. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md` (rows U-001 to U-009), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\analysis.md` (section Unresolved Items). Acceptance: Each row has a severity, an owner, a close condition, and a status from the contract. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\recovery-register.md specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\analysis.md`. Status: partial. Rows exist. Owner confirmations remain open. Depends on T004, T005, and T007.

- [ ] T014 [FR-014] Remove the baseline worktree. Paths: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md` (row V-14), folder `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-baseline`. Acceptance: `git worktree remove` exits with code 0, and the folder is absent. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\design\contracts\validation-report.md`. Status: open. Depends on T011 and T012.

- [ ] T015 [FR-012] Create the record branch worktree and copy the record. Paths: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4277-record` (new worktree on branch `chore/4277-preserve-repository-versions` from GitHub main), `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions` (copied folder with twelve files). Acceptance: The bootstrap runs first. The copied folder holds the twelve record files. The folder counts stay within five children. Verification: `.venv\Scripts\python.exe -m pytest tests\guardrails\test_process_folder_structure.py`, run in the record worktree (process folder guard, research R-45). Status: open. Depends on T008, T013, and T014.

## Phase 4: Delivery

- [ ] T-LOCAL-GATES [FR-012] Run the local gates for each changed file. Paths: the twelve files under `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions`. Acceptance: Each Markdown file scores 80 or above. The guard test passes. Its output names the count of examined directories. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80` for each Markdown file in the record, and `.venv\Scripts\python.exe -m pytest tests\guardrails\test_process_folder_structure.py`. Status: open. Depends on T015.

- [ ] T-PR [FR-015] Commit, push, and open the pull request. Paths: the twelve files under `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions`, and the pull request body file `test-artifacts\4277\pr-body.md`. Acceptance: One commit uses the subject `chore(specs): add repository preservation record for issue 4277`. The body holds `Refs #4277`, and it states that no changelog fragment applies (research D-8). The pull request labels are `chore`, `docs`, and `in-progress`. Verification: `.venv\Scripts\python.exe -m pytest tests\guardrails\test_process_folder_structure.py` on the pushed head. Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI [FR-015] Watch the required checks on the pull request head. Paths: the pull request head, which holds the twelve record files. Acceptance: Every required check reports success, including CodeQL. No check is canceled, stale, or skipped without a stated cause. Verification: `gh pr checks --watch` in the record worktree (AGENTS.md line 229 rule). Status: open. Depends on T-PR.

- [ ] T-MERGE [FR-015] Add the auto-merge label after authorization. Paths: the pull request labels. Acceptance: The label `auto-merge` is added only after every check is green and the orchestrator authorizes the merge. The change touches no destructive operation, so no human hold applies (AGENTS.md line 230). Verification: `gh pr view --json labels --jq .labels[].name` lists `auto-merge`. Status: open. Depends on T-REMOTE-CI.

## Dependencies and Execution Order

### Task dependencies

- T006 depends on T002.
- T007 depends on T006.
- T008 depends on T006 and T007.
- T009 depends on T002.
- T010 depends on T009.
- T011 depends on T010.
- T012 depends on T010.
- T013 depends on T004, T005, and T007.
- T014 depends on T011 and T012.
- T015 depends on T008, T013, and T014.
- T-LOCAL-GATES depends on T015.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI.

### Parallel opportunities

- Tasks T001 to T005 run in parallel. They read evidence only.
- Task T009 runs in parallel with tasks T006 to T008. Both depend only on T002.

## Notes

- Warning: a write to the primary checkout can change the preservation evidence. Keep the primary checkout unchanged.
- Caution: a baseline worktree that fails to bootstrap leaves a partial environment. Record the cause before any retry.
- Verification commands use the repository virtual environment in each worktree.
