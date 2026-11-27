# Tasks: Repository Sync Branch Preservation

**Input**: Numeric record from `specs/numbered/0/0/1/1/1/3/3/4/3969-repository-sync-branch-preservation/`.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, and design/quickstart.md.

**Tests**: The verification commands VC-01 to VC-16 in design/quickstart.md. Each task names one command.

**Format**: `[ID] [P?] [FR-###] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Status is one of open, verified-present, partial, or absent.

## Phase 1: Claim and verify

- [ ] T001 [FR-002] Comment the claim on issue #3969 with one writer name and the start time in UTC.
  - Path: GitHub issue #3969, comment only. No file changes.
  - Acceptance: One claim comment exists before the first write.
  - Verify: VC-02.
  - Status: absent.

- [ ] T002 [P] [FR-001] Rerun the 106 remote checks in design/research.md and record each changed result.
  - Path: specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\research.md, rows R01 to R106.
  - Acceptance: Each row repeats its result, or the row records the change.
  - Verify: VC-01.
  - Status: verified-present.

- [ ] T003 [FR-010] [FR-009] Owner records the worktree inventory and a keep or discard decision for each modified path. HUMAN-DECISION-REQUIRED (D-5).
  - Path: the five modified paths in the main checkout (design/research.md, local check L1). Worktree paths are unverified (U-1).
  - Acceptance: One comment on issue #3969 lists each worktree, its branch, and its modified path count. The owner records each decision.
  - Verify: VC-10.
  - Status: open.

## Phase 2: Preserve

- [ ] T004 [P] [FR-003] [FR-004] Create 129 lightweight tags at the class C tips. Name each tag with the prefix archive/preservation/3969-, the branch slug, and the UTC date.
  - Path: refs/tags/archive/preservation/3969- followed by the branch slug and the UTC date, for each class C branch. Example: archive/preservation/3969-chore-3910-stale-comments-20261127.
  - Acceptance: Each local tag resolves to its branch tip. No tag uses a force option.
  - Verify: VC-03.
  - Status: absent.

- [ ] T005 [P] [FR-003] [FR-004] Create 47 lightweight tags at the class D tips, named by the same rule as T004.
  - Path: refs/tags/archive/preservation/3969- followed by the branch slug and the UTC date, for each class D branch. The class D names appear in design/research.md, section Class lists.
  - Acceptance: Each local tag resolves to its branch tip.
  - Verify: VC-03.
  - Status: absent.

- [ ] T006 [P] [FR-005] [FR-004] Create 5 lightweight tags at the commits of pull request heads #3954, #3955, #3956, #3957, and #3973.
  - Path: refs/tags/archive/preservation/3969-pr3954-head-20261127 and the four other pull request numbers.
  - Acceptance: Each commit exists locally before tagging. Each tag resolves to that commit. The tag for #3956 may name the same commit as a class C tag.
  - Verify: VC-05.
  - Status: absent.

- [ ] T007 [FR-003] [FR-004] Push the 181 new tags, each with an explicit refspec.
  - Path: refs/tags/archive/preservation/3969-* on origin.
  - Acceptance: GitHub lists 181 tags with the prefix. The writer does not use the all-tags push option.
  - Verify: VC-04.
  - Status: absent.

- [ ] T008 [FR-011] Comment one preservation proof on issue #3969. The proof lists the tag count and one tag-to-tip row for each class.
  - Path: GitHub issue #3969, comment only. No file changes.
  - Acceptance: One proof comment exists. It states the count and the check result.
  - Verify: VC-11.
  - Status: absent.

## Phase 3: Delete at passed gates

- [ ] T009 [FR-006] Delete the 4 class A local branches after a zero-commit recheck.
  - Path: refs/heads/agents/ok-make-that-change-then-reun-that-report, refs/heads/feat/4631-offline-jvd-preview, refs/heads/fix/4863-interactive-login-output, and refs/heads/jmorrison-juniper-github-sync-update-merge.
  - Acceptance: Each branch shows zero commits beyond origin/main before its deletion.
  - Verify: VC-06.
  - Status: absent.

- [ ] T010 [FR-006] Delete the 135 class B local branches after a tip-equality recheck.
  - Path: the class B names from the classification loop in design/quickstart.md, step S5.
  - Acceptance: Each tip equals the head of its merged pull request.
  - Verify: VC-06.
  - Status: absent.

- [ ] T011 [FR-003] Delete the 129 class C and 47 class D local branches after their tags resolve.
  - Path: the class C and class D names from the classification loop in design/quickstart.md, step S5.
  - Acceptance: Each tag resolves to its branch tip before deletion. Each command deletes one local branch.
  - Verify: VC-03.
  - Status: absent.

- [ ] T012 [FR-007] Delete the 7 class E local branches after a recheck with no merge commit and one minus line.
  - Path: refs/heads/agents/kms-optic-health-ping-commands, refs/heads/chore/4569-hypothesis-rebase, refs/heads/chore/4570-react-router-rebase, refs/heads/jmorrison-juniper-fix-3168-silent-completion-classifier, refs/heads/jmorrison-juniper-fix-3380-skip-visibility, refs/heads/test/2743-timeout-failure-mode, and refs/heads/tmp/2729-rebase.
  - Acceptance: Each branch shows zero merge commits and one minus line before deletion.
  - Verify: VC-07.
  - Status: absent.

- [ ] T013 [FR-008] Keep the 7 class F local branches.
  - Path: refs/heads/jmorrison-jnpr-test-4035-menu-92-selection-result, refs/heads/jmorrison-juniper-assessment-4026, refs/heads/jmorrison-juniper-false-success-family-4028, refs/heads/jmorrison-juniper-fix-2863-identifier-defaults-batch-1, refs/heads/jmorrison-juniper-fix-4031-partial-failure, refs/heads/jmorrison-juniper-issue-2746, and refs/heads/jmorrison-juniper-issue-3416-lint-pattern.
  - Acceptance: Each class F tip equals its GitHub branch tip.
  - Verify: VC-08.
  - Status: verified-present.

## Phase 4: Other state and pull requests

- [ ] T014 [FR-009] Keep the 5 modified paths unchanged unless T003 approves a change.
  - Path: src\foundation\support\utils\logger_utils.py, src\interfaces\wan_performance\collection\request_admission.py, src\mist\intelligence\reports\subscription_expiry\client.py, tests\unit\marvis\mist\intelligence\reports\audits\credentials\subscription_expiry\test_client.py, and tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py.
  - Acceptance: The status command shows the same five modified paths.
  - Verify: VC-09.
  - Status: verified-present.

- [ ] T015 [FR-012] Confirm that each of the 14 named pull requests stays merged or closed.
  - Path: GitHub pull requests #3954 to #3967 and #3820, 14 pull requests in total.
  - Acceptance: Each pull request shows merged or closed. The writer changes no pull request.
  - Verify: VC-12.
  - Status: verified-present.

- [ ] T016 [FR-013] Refresh the `misthelper` container after the claim is released. Keep both named volumes.
  - Path: compose.yml and scripts\compose.ps1 (R38, R39). The build and start commands appear in copilot-instructions (R20, R21).
  - Acceptance: The container runs the rebuilt image. Both named volumes remain.
  - Verify: VC-13.
  - Status: absent.

## Phase 5: Record gates

- [ ] T017 [FR-014] Confirm the route and the child count of each directory in the record.
  - Path: specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation and its design and checklists folders.
  - Acceptance: Each directory holds five children or fewer.
  - Verify: VC-14.
  - Status: absent.

- [ ] T018 [FR-016] Keep the unverified list in design/research.md complete, with a reason for each item.
  - Path: specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation\design\research.md, section Unverified.
  - Acceptance: Each unverified item states its reason.
  - Verify: VC-16.
  - Status: verified-present.

## Final tasks

- [ ] T-LOCAL-GATES [FR-015] Run the STE gate on each Markdown file in the record.
  - Path: the eight Markdown files in the record folder.
  - Acceptance: Each file scores 80 or above.
  - Verify: VC-15.
  - Status: absent.

- [ ] T-PR [FR-001] Commit the record with a Conventional Commits message, push branch docs/3969-repository-sync-branch-preservation, and open a pull request that contains Closes #3969.
  - Path: the record folder and the branch name (R03 and R04 set the naming and commit rules).
  - Acceptance: The commit subject starts with `docs:`. The pull request body contains `Closes #3969` (R05).
  - Verify: `gh pr view` with the pull request number, showing title and body.
  - Status: absent.

- [ ] T-REMOTE-CI [FR-001] Wait for each required check with `gh pr checks` and the watch option.
  - Path: the pull request from T-PR.
  - Acceptance: Each required check shows success (R06).
  - Verify: `gh pr checks` with the pull request number and the watch option.
  - Status: absent.

- [ ] T-MERGE [FR-001] Add the `auto-merge` label after every check shows success and the orchestrator authorizes the merge.
  - Path: the pull request from T-PR.
  - Acceptance: The label exists only after the checks pass and the authorization exists (R06, R07).
  - Verify: `gh pr view` with the pull request number, showing labels.
  - Status: absent.
