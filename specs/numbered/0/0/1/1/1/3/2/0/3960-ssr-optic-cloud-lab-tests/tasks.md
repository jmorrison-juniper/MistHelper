# Tasks: SSR optic and Mist cloud path lab tests

**Input**: Numeric record `specs\numbered\0\0\1\1\1\3\2\0\3960-ssr-optic-cloud-lab-tests`.

**Prerequisites**: spec.md (required), plan.md (required), design/research.md, design/quickstart.md, design/contracts/.

**Format**: Each task names its ID, `[P]` marker, status, owner, requirements, paths, acceptance, gate, and dependencies.

- **[P]**: Safe in parallel with other `[P]` tasks that touch other files.
- **Status**: open, verified-present, partial, or absent.
- **Owner**: agent, or owner-only human step. The agent never runs an owner-only step.
- **Gate**: The local gates table command for an edit task. A read-only task names a read-back command from design/quickstart.md.

## Phase 1: Preconditions

### T001 verified-present | agent

- **Requirements**: FR-006, FR-015
- **Paths**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, lines 347 to 366
- **Acceptance**: Main holds the section 14 subsection and six rows that read Not run (C-16, C-17). The blob equals 4fe23574f2f66792139b4c84132a85a21f3dda03 (C-01).
- **Gate**: TEST-01 on the current file as a baseline, then RB-1 read-back.
- **Depends on**: none.

### T002 open [P] | agent

- **Requirements**: FR-013
- **Paths**: None. GitHub issue #3960 and the open pull request list only.
- **Acceptance**: Issue #3960 carries the in-progress label and a claim comment (C-41, C-44). RB-2 shows no open pull request that changes the runbook or the planned fragment name.
- **Gate**: TEST-17 with RB-2 and RB-3.
- **Depends on**: none.

## Phase 2: Owner-only human steps

Each task in this phase is an owner-only human step. The agent does not run these steps. The owner returns each sanitized output by the route in design/contracts/lab-output-record.md.

### T003 open | owner-only human step H-0

- **Requirements**: FR-001, FR-002
- **Paths**: None. The change touches no repository file.
- **Action**: Name one lab SSR that runs SSR 7.0.x and one lab SSR that runs SSR 7.1.0-50r1 or later. Confirm console access by the owner's own method.
- **Acceptance**: The owner posts the release strings only in a comment on #3960. The comment holds no address and no serial number.
- **Gate**: TEST-17 with RB-3.
- **Depends on**: T002.

### T004 open [P] | owner-only human step H-1

- **Requirements**: FR-001, FR-003, FR-004
- **Action**: On SSR 7.0.x, run `show device-interface <name> optics-statistics`.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, section 11 table, row at line 245. Record the exact error text in the What happens cell. Row 360 then names the release string.
- **Acceptance**: TEST-08 passes.
- **Gate**: TEST-08 read-back, then TEST-01 in T012.
- **Depends on**: T003.

### T005 open [P] | owner-only human step H-2

- **Requirements**: FR-001, FR-003, FR-004
- **Action**: On SSR 7.0.x, run `show device-interface name <name> optics-statistics`.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, section 11 table. Add one row for this corrected command and record the exact error text in it. Row 361 then names the release string and points to that row (D-7).
- **Acceptance**: TEST-09 passes.
- **Gate**: TEST-09 read-back, then TEST-01 in T012.
- **Depends on**: T003.

### T006 open [P] | owner-only human step H-3

- **Requirements**: FR-001, FR-003, FR-004
- **Action**: On SSR 7.0.x, run `show device-interface name <name>`. Confirm the admin status, the operational status, the speed, and the error counters named in step 1.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, step 1 of section Check an optic without optics-statistics, at line 117. Record the port names that the output lists for the 10GbE SFP+ ports (U-2). Row 362 then names the release string.
- **Acceptance**: TEST-10 passes. The port names appear in step 1.
- **Gate**: TEST-10 read-back, then TEST-01 in T012.
- **Depends on**: T003.

### T007 open [P] | owner-only human step H-4

- **Requirements**: FR-001, FR-003, FR-004
- **Action**: On SSR 7.1.0-50r1 or later, run `show device-interface name <name> optics-statistics` on a fiber port.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, step C2, row at line 104. Add the names of the power level fields and the threshold fields. Row 363 then names the release string.
- **Acceptance**: TEST-11 passes.
- **Gate**: TEST-11 read-back, then TEST-01 in T012.
- **Depends on**: T003.

### T008 open [P] | owner-only human step H-5

- **Requirements**: FR-001, FR-003, FR-004
- **Action**: Run `show mist detail`. Confirm the Agent field and the Connection field.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, step D7, row at line 141. Record the healthy values as the baseline for T009. Row 364 then names the release string.
- **Acceptance**: TEST-12 passes.
- **Gate**: TEST-12 read-back, then TEST-01 in T012.
- **Depends on**: T003.

### T009 open | owner-only human step H-6

- **Requirements**: FR-001, FR-003, FR-004, FR-012
- Caution: blocking TCP port 443 stops Mist management of the lab router. Run this step on a lab router only.
- **Action**: Confirm the baseline from T008. Type the confirmation phrase from D-8 with the lab router name. Block TCP port 443 to the Mist cloud. Test the Testing Tools in the Mist portal. Remove the block rule. Run `show mist detail` again and confirm that Connection reads up.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, the last sentence of section Test the path to the Mist cloud, at line 166, when the tools operate. Row 365 then names the release string.
- **Acceptance**: TEST-13 passes. The block rule is removed. The baseline from T008 repeats.
- **Gate**: TEST-13 read-back, then TEST-01 in T012.
- **Depends on**: T008.

### T010 open | owner-only human step H-7

- **Requirements**: FR-017
- **Action**: Find the source of the 2026-10-05 observation at line 149. Add a source link, or remove the sentence.
- **Target**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, line 149.
- **Acceptance**: TEST-14 passes. Unresolved item U-1 closes.
- **Gate**: TEST-14 read-back, then TEST-01 in T012.
- **Depends on**: none.

### T011 open | owner-only human step H-8

- **Requirements**: FR-018
- **Paths**: None in the repository. The local worktree folder and the local branch agents/kms-optic-health-ping-commands are removed.
- Caution: branch deletion can cause a loss of work. Compare the branch with main before you delete it.
- **Action**: After the session in the worktree closes, run `git -C` with the worktree path and `status --short`. Remove the worktree and the local branch `agents/kms-optic-health-ping-commands` only when the status prints no line.
- **Acceptance**: TEST-19 passes.
- **Gate**: TEST-19 read-back.
- **Depends on**: none. Pull request #3951 merged on 2026-10-06 (C-64).

## Phase 3: Agent recording

### T012 open | agent

- **Requirements**: FR-003, FR-004, FR-016
- **Paths**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, lines 104, 117, 141, 149, 166, and 240 to 246.
- **Action**: Apply each returned output to its target from T004 to T010. Run the sanitization checklist in design/contracts/lab-output-record.md for each output.
- Warning: a committed address or customer name stays in the public repository history after a revert.
- **Acceptance**: TEST-06 finds no added address, serial number, or customer name. Each output keeps its release string.
- **Gate**: TEST-01 and TEST-06.
- **Depends on**: T004, T005, T006, T007, T008, T009, T010.

### T013 open | agent

- **Requirements**: FR-005, FR-006, FR-016
- **Paths**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, the table at lines 358 to 365.
- **Action**: Replace each Not run cell in rows 360 to 365 with a release string, as design/contracts/verification-status-table.md requires. Keep six rows and add no table.
- **Acceptance**: TEST-07 passes. Each cell that reads Not run has no output.
- **Gate**: TEST-01 and TEST-07.
- **Depends on**: T012.

### T014 open [P] | agent

- **Requirements**: FR-014
- **Paths**: changelog.d/issue-3960-ssr-lab-results.md (new file)
- **Action**: Add one `###` heading and one bullet. The bullet names the change type Changed and ends with `Issue #3960.` Keep this name after the pull request opens.
- **Acceptance**: TEST-02 and TEST-05 pass.
- **Gate**: TEST-02 and TEST-05.
- **Depends on**: T012.

## Phase 4: Final gates and pull request

### T-LOCAL-GATES open | agent

- **Requirements**: FR-008, FR-009, FR-010, FR-011
- **Paths**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md and changelog.d/issue-3960-ssr-lab-results.md
- **Action**: Run TEST-01 to TEST-06 in the worktree. Compare the changed path list with the two planned paths. Record each result in the pull request body.
- **Acceptance**: Each changed file scores 80 or above. No link breaks. The guard test passes. The changed path list holds only the two planned paths. The scan finds no address, serial number, customer name, or credential word.
- **Gate**: TEST-01 to TEST-06.
- **Depends on**: T013, T014.

### T-PR open | agent

- **Requirements**: FR-007, FR-013
- **Paths**: documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md and changelog.d/issue-3960-ssr-lab-results.md, committed on branch docs/3960-ssr-lab-results.
- **Action**: Create branch `docs/3960-ssr-lab-results` from main in a separate worktree. Commit with the title `docs(noc-runbooks): record SSR lab results for the optic and cloud path steps`. Write the body with the closing keyword from FR-007, the changed-file summary, the local gate results, and the rollback note. Set the labels `chore` and `docs`. Push once.
- **Acceptance**: The body holds `Refs #3960` until all six outputs exist. The body holds `Closes #3960` only after that. The commit message ends with the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
- **Gate**: TEST-17.
- **Depends on**: T-LOCAL-GATES.

### T-REMOTE-CI open | agent

- **Requirements**: FR-010, FR-011
- **Paths**: None in the repository. The check results come from the pull request.
- **Action**: Run `gh pr checks --watch` for the branch. Wait for CodeQL and for each other check that the pull request reports.
- **Acceptance**: TEST-15 passes. No required check fails.
- **Gate**: TEST-15.
- **Depends on**: T-PR.

### T-MERGE open | agent after orchestrator authorization

- **Requirements**: FR-007, SC-005, SC-006
- **Paths**: None in the repository. The merge and the branch removal happen on GitHub and in the local worktree.
- **Action**: After the orchestrator authorizes the merge, add the auto-merge label. The auto-merge workflow squash merges after each required check passes (C-52). Then run TEST-16 and TEST-17. Remove the branch and the worktree after the merge.
- **Acceptance**: TEST-16 and TEST-17 pass. The issue closes only when the merged body held `Closes #3960`.
- **Gate**: TEST-16 and TEST-17.
- **Depends on**: T-REMOTE-CI and the orchestrator authorization.
