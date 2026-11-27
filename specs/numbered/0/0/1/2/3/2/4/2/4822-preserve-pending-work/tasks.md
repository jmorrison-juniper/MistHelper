# Tasks: Preserve Pending Work Before Branch Cleanup

**Input**: Record folder `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/`.

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Status values**: `verified-present` means this record verified the result. `partial` means some results are verified. `absent` means the result does not exist. `open` means this record did not verify the result.

**Gate rule**: Record and test tasks name a row of the local gates table. Git and GitHub evidence tasks have no such row, so they name a test case. See `analysis.md` F-17.

## Format

- **[P]**: The task can run in parallel with other [P] tasks in its phase.
- **(FR-nnn)**: The requirements that the task serves.
- **Paths**: The exact repository paths or Git refs that the task reads or changes.
- **Depends on**: The tasks that must finish first.

## Phase 1: Evidence (read-only)

- **T001** [P] (FR-001). Inventory the nine snapshot tags.
  - Paths: Git refs under `refs/tags/recovery/4822/`. No repository file changes.
  - Acceptance: Nine rows in `design/research.md` show commit, parent, and file count.
  - Check: TST-001. Gate: no row in the local gates table applies.
  - Depends on: none. Status: verified-present.

- **T002** [P] (FR-001). Inventory the four recovery branches and their commits.
  - Paths: `refs/heads/chore/2746-recovered-specification`, `refs/heads/fix/2977-recovered-content-dedup`, `refs/heads/feat/4631-recovered-offline-preview`, and `refs/heads/docs/4822-recovered-vmm-export`.
  - Acceptance: Four rows in `design/research.md` show tip, base, and commit count.
  - Check: TST-002. Gate: no row in the local gates table applies.
  - Depends on: none. Status: verified-present.

- **T003** [P] (FR-002). Classify each snapshot file against main.
  - Paths: The nine snapshot tags, compared with `refs/heads/main`.
  - Acceptance: Counts match the snapshot table in `design/research.md`.
  - Check: TST-003. Gate: no row in the local gates table applies.
  - Depends on: T001. Status: verified-present.

- **T004** (FR-005). Compare the two Labs snapshots by blob.
  - Paths: `refs/tags/recovery/4822/labs-original` and `refs/tags/recovery/4822/labs-preview`.
  - Acceptance: Twenty-nine shared paths are identical. Two extra paths are named.
  - Check: TST-004. Gate: no row in the local gates table applies.
  - Depends on: T001. Status: verified-present.

- **T005** (FR-005). Compare the two private Labs folders by SHA-256.
  - Paths: The private recovery store, outside Git.
  - Acceptance: Twenty-nine shared files are identical. The result is a count only.
  - Check: TST-005. Gate: no row in the local gates table applies.
  - Depends on: none. Status: open.

- **T006** (FR-003). Verify the nine private archives.
  - Paths: The private recovery store, outside Git.
  - Acceptance: Nine hash matches. The ZIP entry total matches the owner count.
  - Check: TST-006 and TST-007. Gate: no row in the local gates table applies.
  - Depends on: none. Status: open.

- **T007** [P] (FR-004). Archive the ignored output of each worktree before removal.
  - Paths: The private recovery store, and the worktree folders named in the registrations.
  - Acceptance: Each ignored path appears in an archive manifest.
  - Check: TST-008. Gate: no row in the local gates table applies.
  - Depends on: T006. Status: open.

- **T008** (FR-006). Verify the Git bundle and restore its references.
  - Paths: The bundle file in the private recovery store.
  - Acceptance: Bundle verification passes. The restore holds thirteen references.
  - Check: TST-009 and TST-010. Gate: no row in the local gates table applies.
  - Depends on: none. Status: open.

- **T009** (FR-007). Verify that each removed branch has a recovery copy or a merge proof.
  - Paths: `refs/tags/recovery/4822/http-tests`, `refs/tags/recovery/4822/pdf-dedup`, `refs/tags/recovery/4822/requirements`, and `refs/tags/recovery/4822/release`.
  - Acceptance: Four recovery tags exist. Each original branch name is recorded, or the record marks it unknown.
  - Check: TST-012. Gate: no row in the local gates table applies.
  - Depends on: T001. Status: partial. The tags exist. The original branch names are unknown. See U-04.

## Phase 2: Removal (destructive)

Warning: Deleting a worktree folder removes files that Git does not track. Archive the ignored output first.

Warning: Deleting a local branch removes the only Git reference to its commits. Delete only merged branches.

- **T010** (FR-016, FR-017). Close the app sessions and prune the two prunable admin directories.
  - Paths: `.git\worktrees\dynamic-jvd-labs-offline-preview` and `.git\worktrees\ok-make-that-change-then-reun-that-report`.
  - Acceptance: Both admin directories are gone. Or the record names the lock error and marks the blocker. Permissions stay unchanged.
  - Check: TST-022 and TST-023. Gate: no row in the local gates table applies.
  - Depends on: T007. Status: open.

- **T011** (FR-007, FR-008). Delete the two merged local branches with `git branch -d`.
  - Paths: `refs/heads/feat/4631-offline-jvd-preview` at tip `02d7d1798d9d5ab17d9de33da122d0b224adaf64`, and `refs/heads/agents/ok-make-that-change-then-reun-that-report` at tip `d29cfd3984bcd00074d7b73c6d786be9edce249c`.
  - Acceptance: Each deletion succeeds. No command uses `-D`.
  - Check: TST-011 and TST-013. Gate: no row in the local gates table applies.
  - Depends on: T007, T009, T010. Status: open.

- **T012** (FR-009). Run the secret review on the nine snapshots and four recovery branches.
  - Paths: The snapshot tags, the recovery branches, and the private archives.
  - Acceptance: The review records match counts only. No matched text appears in the issue.
  - Check: TST-014 and the recorded counts. Gate: no row in the local gates table applies.
  - Depends on: T006. Status: open.

- **T013** (FR-009). Record the owner decision on publication.
  - Paths: One comment on issue #4822.
  - Acceptance: The comment approves or holds publication. The decision follows D-2. This decision needs a human.
  - Check: TST-014. Gate: no row in the local gates table applies.
  - Depends on: T012. Status: open.

## Phase 3: Report and verify

- **T014** (FR-011, FR-012). Post the blocker report and the recovery identifiers on issue #4822.
  - Paths: One comment on issue #4822. No repository file changes.
  - Acceptance: Seven blockers from `analysis.md` appear. Each names a cause and a next action. No private path appears.
  - Check: TST-016 and TST-017. Gate: no row in the local gates table applies.
  - Depends on: T006, T008, T009, T010, T011. Status: open.

- **T015** [P] (FR-013). Run the focused offline tests from exported trees.
  - Paths: `tests/unit/juniper_docs/test_content_dedup.py` from an export of main, and `tests/integration/web_portal/labs` from an export of `refs/heads/feat/4631-recovered-offline-preview`. Both exports go under `test-artifacts/`.
  - Acceptance: Counts are recorded. No test fails.
  - Check: TST-018. Gate: Tests row, `python -m pytest tests/unit/juniper_docs/test_content_dedup.py`.
  - Depends on: T008. Status: open.

- **T016** (FR-010, FR-014). Confirm that the main checkout and product paths are unchanged.
  - Paths: `refs/heads/main`, `src/`, `tests/`, `scripts/`, and `MistHelper.py`.
  - Acceptance: The main commit is unchanged. No product path appears in the change.
  - Check: TST-015 and TST-019. Gate: no row in the local gates table applies.
  - Depends on: T010, T011. Status: open.

## Phase 4: Final gates and delivery

- **T-LOCAL-GATES** (FR-015). Run the writing gate and the route guard tests.
  - Paths: The nine files in the record folder.
  - Acceptance: Each file scores 80 or above in every mode that `documentation/quality-gates.md` describes. Both guard tests pass.
  - Check: TST-020 and TST-021. Gate: STE row and Tests row of the local gates table.
  - Depends on: T001 to T016. Status: open.

- **T-PR** (FR-011, FR-014). Commit the record and open the pull request.
  - Paths: The nine files in the record folder only.
  - Acceptance: The commit subject is `chore(specs): preserve pending work before branch cleanup`. The body holds `Closes #4822`, the gate results, and the reason for no changelog fragment.
  - Check: TST-019. Gate: STE row of the local gates table.
  - Depends on: T-LOCAL-GATES. Status: open.

- **T-REMOTE-CI** (FR-015). Watch the required checks on the pull request.
  - Paths: The pull request for branch `chore/4822-preserve-pending-work`.
  - Acceptance: Each required check reports success on the latest commit.
  - Check: Repository CI result on the pull request. Gate: no row in the local gates table applies.
  - Depends on: T-PR. Status: open.

- **T-MERGE** (FR-010). Enable auto-merge only after CI passes and the orchestrator authorizes the merge.
  - Paths: The pull request for branch `chore/4822-preserve-pending-work`.
  - Acceptance: A blocker issue exists before the merge. The auto-merge label appears only after each check passes.
  - Check: TST-016. Gate: no row in the local gates table applies.
  - Depends on: T-REMOTE-CI, T014. Status: open.

## Test Cases

- **TST-001** (FR-001). Run `git for-each-ref refs/tags/recovery/4822`. Expected: nine snapshot tags.
- **TST-002** (FR-001). Run `git rev-parse` on each of the four recovery branch names in T002. Expected: tips that begin with `c06ea6ce1bb5`, `591b6b86697b`, `a9a2d36dfc75`, and `01e0a701608d`.
- **TST-003** (FR-002). Run `git diff-tree` on each snapshot and compare each blob with main. Expected: files, identical, different, and absent counts in the order of the research table.
- **TST-004** (FR-005). Compare the blobs of the twenty-nine shared paths in `labs-original` and `labs-preview`. Expected: twenty-nine identical, zero different, and zero absent.
- **TST-005** (FR-005). Compare each shared file in the two private Labs folders by SHA-256. Expected: twenty-nine identical. The owner runs this check.
- **TST-006** (FR-003). Compute the SHA-256 hash of each private archive and compare it with the manifest. Expected: nine matches.
- **TST-007** (FR-003). Count the ZIP entries in each archive and sum the counts. Expected: 73,903 entries, as the owner reports.
- **TST-008** (FR-004). List the ignored files in each worktree folder and compare them with the archive manifest. Expected: zero ignored paths are missing from the archive.
- **TST-009** (FR-006). Run `git bundle verify` on the private bundle. Expected: exit code 0.
- **TST-010** (FR-006). Restore the bundle into an independent bare repository and run `git fsck --full --no-reflogs`. Expected: exit code 0 and thirteen references.
- **TST-011** (FR-007). Count the commits in `main..feat/4631-offline-jvd-preview` and in the agents branch. Expected: zero for each, and an ancestor exit code of 0.
- **TST-012** (FR-007). Confirm the four removed-branch recovery tags exist. Expected: tags for http-tests, pdf-dedup, requirements, and release.
- **TST-013** (FR-008). Search the cleanup command transcript for `branch -D` and for `--delete-branch`. Expected: zero matches. The owner keeps the transcript in the private recovery store.
- **TST-014** (FR-009). Query GitHub for the four recovery branches and the recovery tag namespace. Expected: HTTP 404 for each branch, and an empty tag list, until the owner approves publication.
- **TST-015** (FR-010). Compare `git rev-parse main` before and after the cleanup. Expected: the same commit. The local branch count changes only by the removed branches.
- **TST-016** (FR-011). Search the record files and the issue report for local profile path prefixes, cloud sync folder names, app data folder names, and session folder names. The owner keeps the exact pattern list in the private recovery store. Expected: zero matches.
- **TST-017** (FR-012). Count the blockers in `analysis.md` and in the issue report. Expected: seven blockers in each count.
- **TST-018** (FR-013). Run `python -m pytest tests/unit/juniper_docs/test_content_dedup.py` on an export of main. Run the Labs tests on a recovery export. Expected: no failure. The owner reports 43 passed and 1 skipped.
- **TST-019** (FR-014). List the changed paths against main. Expected: every path begins with the record folder path.
- **TST-020** (FR-015). Run `ste-linter` with `--min-score 80` on the nine record files, in each mode of the writing gate. Expected: each file scores 80 or above.
- **TST-021** (FR-015). Run `python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py`. Expected: all tests pass.
- **TST-022** (FR-016). After the app sessions close, run `git worktree prune -v` and list the registrations. Expected: no prunable entries for the two names. Or the record names the lock error.
- **TST-023** (FR-017). Capture the ACL of each admin directory before and after the prune. Expected: identical output.
