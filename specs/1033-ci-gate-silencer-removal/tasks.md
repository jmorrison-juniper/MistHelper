# Tasks: CI Gate Silencer Removal

**Feature**: `1033-ci-gate-silencer-removal`

**Branch**: `ci/891-893-gate-silencers`. Do not create a branch. Do not switch a branch. Non-goal NG-010 and requirement FR-003 state this rule.

**Input**: Design documents in `specs/1033-ci-gate-silencer-removal/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/review-comment.md](contracts/review-comment.md)

**GitHub Issues**: This work closes [#891](https://github.com/jmorrison-juniper/MistHelper/issues/891), [#892](https://github.com/jmorrison-juniper/MistHelper/issues/892), and [#893](https://github.com/jmorrison-juniper/MistHelper/issues/893) through one pull request.

**Tests**: This feature adds no automated test. The specification requests none. No Python source file changes, so the `pytest` suite is unaffected. Every task carries a measured verification command instead.

**Organization**: The five phases below come from the Execution Phases section of [plan.md](plan.md). Phase A holds the two proven edits. Phase B holds the CodeQL experiment setup. Phase C holds one push and one pull request. Phase D reads the CodeQL result and branches on it. Phase E closes the record.

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: The task can run in parallel with another task. The two tasks touch different files and hold no dependency.
- **[Story]**: The user story that owns the task. The values are `[US1]`, `[US2]`, `[US3]`, and `[US4]`.
- A task inside a `Shared` subsection carries no story label. That task serves every story in the phase.
- Every task names an exact file path or an exact command.

---

## The four traps

The plan found four traps. Each one has a task that guards it. Read this table before you start.

| Trap | Where the plan records it | The task that guards it |
| - | - | - |
| The vulture default appears at line 35 and at line 51 of the same file. A change to one site alone leaves a `workflow_call` caller at confidence 90. | Discovered risk 1, research decision R2 | T007, T008, and T011 |
| CodeQL runs only on a pull request against `main`. A push to the feature branch starts no workflow. | Discovered risk 3 | T018, T019, and T021 |
| A finding count of zero is ambiguous. It can mean a clean result, or it can mean a query that the default suite never ran. | Discovered risk 4, research decision R7 | T023 |
| An empty `query-filters:` key parses as `null`. A `null` value can stop the whole analysis. The key must go when the last exclusion goes. | Research decision R4 | T014 and T015 |

---

## Phase A: The two proven edits

**Goal**: Remove the pylint ignore flag and lower the vulture confidence floor. Prove both changes on the workstation before any push.

**Independent Test**: A reviewer reads `.github/workflows/ci.yml` and finds no `--ignore` flag on the pylint step and the value `70` at both vulture sites. The two local gate commands exit 0.

### Shared preflight

- [X] T001 Run `git branch --show-current` in the repository root. The output must read `ci/891-893-gate-silencers`. Stop and report any other name. Do not create a branch. Do not switch a branch.
- [X] T002 [P] Record the tool versions for the pull request evidence. Run `.venv\Scripts\python.exe -m pylint --version` and `.venv\Scripts\python.exe -m vulture --version`. Use `.venv\Scripts\python.exe` for every command. The global `python` on this machine is broken.

### User Story 1 - See every pylint message from every source package (Priority: P1)

**Goal**: The pylint gate reads `src/maps`, `src/ssh`, and `src/ui` alongside the rest of `src/`.

**Issue**: #891. **Requirements**: FR-004, FR-005, FR-006, FR-007. **Criteria**: SC-001, SC-002, SC-003.

**REVERTED 2026-07-28. Status on `main` is not done.** The four tasks below were applied and then reverted inside pull request #1723. A Windows checkout scores 9.71 without the ignore flag, which passes. The `ubuntu-latest` runner scores 9.41 for the same commit, which fails the 9.5 threshold and exits 30. A local run is therefore not a safe proxy for this gate. The flag stays in `.github/workflows/ci.yml` at line 303 and carries a review comment that names issue #891. Issue #891 stays open and holds the remaining work.

**Measured backlog on 2026-08-04**: `src/maps`, `src/ssh`, and `src/ui` report 683 messages. The five largest groups are `broad-exception-caught` at 142, `import-outside-toplevel` at 123, `invalid-name` at 93, `protected-access` at 71, and `use-dict-literal` at 61. The gate needs a Linux score above 9.5 before the flag can leave.

- [ ] T003 [US1] Delete `--ignore=maps,ssh,ui` from the end of the pylint `run` line at line 291 of `.github/workflows/ci.yml`. Keep `${{ env.SRC_PATH }}` and keep `--fail-under=${{ env.PYLINT_THRESHOLD }}` unchanged. Non-goal NG-006 and non-goal NG-007 forbid a change to either one. **Applied and then reverted in pull request #1723.**
- [ ] T004 [US1] Add the forward-looking review comment above the `- name: Run Pylint` step at line 290 of `.github/workflows/ci.yml`. Copy the accepted example from [contracts/review-comment.md](contracts/review-comment.md). The comment states the review date of 2026-07-28 and the measured counts of 757 and 1259. The comment also states the rule that any future ignore flag needs the three facts. Use ASCII characters only. Keep each line inside 100 characters. **A different comment shipped instead. It records the revert and names issue #891 as the next review trigger.**
- [ ] T005 [US1] Verify the gate on the workstation. Run `.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5` and then print `"exit=$LASTEXITCODE"`. The exit code must be 0. Record the message count. The expected count is about 1259. A small drift is acceptable when the pylint version differs. **The workstation result misled the team. A Linux run is the only valid check for this gate.**
- [ ] T006 [US1] Confirm that the three packages now report messages. Run `.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5 2>&1 | Select-String -Pattern 'src\\maps|src\\ssh|src\\ui'`. Each of the three paths must return at least one line. This proves success criterion SC-001. **Blocked by the revert of T003.**

### User Story 2 - Lower the vulture confidence floor to a measured safe value (Priority: P2)

**Goal**: The dead code gate runs at a confidence floor of 70 at every trigger path.

**Issue**: #892. **Requirements**: FR-008, FR-009, FR-010, FR-011. **Criteria**: SC-004.

- [X] T007 [US2] Change `default: '90'` to `default: '70'` under the `vulture-confidence` input at line 35 of `.github/workflows/ci.yml`. This is the `workflow_call` input default. This is the first of two sites. Research decision R2 states why both sites matter.
- [X] T008 [US2] Edit line 51 of `.github/workflows/ci.yml`. That line holds the `env` fallback for the vulture confidence. Change the value `'90'` to `'70'`. Line 51 is the second of two sites. A `workflow_call` caller stays at confidence 90 when only line 51 changes.
- [X] T009 [US2] Add the threshold review comment above the `- name: Detect dead code` step at line 338 of `.github/workflows/ci.yml`. Copy the accepted example from [contracts/review-comment.md](contracts/review-comment.md). The comment states the review date of 2026-07-28 and the measured counts at confidence 90, 70, and 60. The comment also names issue #1703 as the condition that triggers the next review. Requirement FR-010 and requirement FR-011 state this content.
- [X] T010 [US2] Verify the gate on the workstation. Run `.venv\Scripts\python.exe -m vulture src/ --min-confidence 70` and then print `"exit=$LASTEXITCODE"`. The finding count must be 0 and the exit code must be 0.
- [X] T011 [US2] Confirm that no `'90'` survives for the vulture setting. Run `Select-String -Path ".github\workflows\ci.yml" -Pattern "vulture-confidence|VULTURE_CONFIDENCE" -Context 0,2`. Both results must show `70`. This guards the two site trap. Also run `Select-String -Path ".github\workflows\ci.yml" -Pattern "--ignore=maps"`. It must return nothing.

**Checkpoint**: Both proven edits are in place. Both local gate commands exit 0. Do not push yet.

---

## Phase B: The CodeQL experiment setup

**Goal**: Remove both CodeQL exclusions and draft the changelog entry. No local command can predict the CodeQL result.

**Independent Test**: A reviewer reads `.github/codeql/codeql-config.yml` and finds only the `name` key. Both configuration files still parse as YAML.

### User Story 3 - Defend or remove the undocumented CodeQL exclusion (Priority: P3)

**Goal**: The exclusion of `py/stack-trace-exposure` leaves the file. That exclusion carries no rationale today.

**Issue**: #893. **Requirements**: FR-012. **Criteria**: SC-006.

- [X] T012 [US3] Delete the two lines `- exclude:` and `id: py/stack-trace-exposure` from `.github/codeql/codeql-config.yml`. These are lines 13 and 14. Do not comment the lines out. Research decision R4 rejects a commented suppression.

### User Story 4 - Correct the stale claim in the second CodeQL rationale (Priority: P4)

**Goal**: The exclusion of `py/clear-text-logging-sensitive-data` leaves the file together with its stale rationale.

**Issue**: #893. **Requirements**: FR-013, FR-016. **Criteria**: SC-007.

- [X] T013 [US4] Delete the two lines `- exclude:` and `id: py/clear-text-logging-sensitive-data` from `.github/codeql/codeql-config.yml`. These are lines 11 and 12. Also delete the eight line header comment above the `query-filters` key at lines 3 to 9. That comment holds the claim that the tool never logs an actual secret. Issue #1710 contradicts that claim.

### Shared

- [X] T014 Delete the now empty `query-filters:` key at line 10 of `.github/codeql/codeql-config.yml`. An empty key parses as `null`, and a `null` value can stop the whole analysis. A stopped analysis produces no finding count, which is the exact evidence that this work needs. The file must hold one line only, which is `name: "MistHelper CodeQL Configuration"`. Research decision R4 states this rule.
- [X] T015 Confirm that both configuration files still parse. Run `.venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); yaml.safe_load(open('.github/codeql/codeql-config.yml')); print('yaml ok')"`. The output must read `yaml ok`.
- [X] T016 Add the changelog entry under `## [Unreleased]` in `CHANGELOG.md`. Name issue #891, issue #892, and issue #893. Record the pylint result of 757 messages before and 1259 messages after at exit code 0. Record the vulture result of confidence 90 before and confidence 70 after at 0 findings, and record the 306 findings at confidence 60. Write a clear placeholder for the two CodeQL counts. The entry must not claim a CodeQL result before the CI run produces one. Requirement FR-019 states this rule.

**Checkpoint**: All three edits are in place. Both files parse. The changelog holds a draft entry with a marked placeholder.

---

## Phase C: One push and one pull request

**Goal**: One push starts one Quality Gates run and one CodeQL run. A push to this branch alone starts neither workflow.

**Independent Test**: The pull request is open against `main`. The pylint job and the vulture job pass. The CodeQL Analysis workflow completes.

- [X] T017 Stage and commit every Phase A edit and every Phase B edit on `ci/891-893-gate-silencers`. Stage `.github/workflows/ci.yml`, `.github/codeql/codeql-config.yml`, `CHANGELOG.md`, and `specs/1033-ci-gate-silencer-removal`. Use the message `ci: remove the pylint, vulture, and CodeQL gate silencers (#891, #892, #893)`. **The US1 edit was reverted before the commit landed.**
- [X] T018 Push the branch with `git push origin ci/891-893-gate-silencers`. This push starts no workflow. Both workflows trigger on a pull request against `main` and on a push to `main`. The branch is not `main`.
- [X] T019 Open the pull request with `gh pr create --base main --head ci/891-893-gate-silencers`. The body must hold five items. The first item is `Closes #891`, `Closes #892`, and `Closes #893`. The second item is the grouping reason from requirement FR-002. The third item is the note that `.github/quality-gates-portable.yml` still holds `'90'` and stays out of scope, which research decision R3 states. The fourth item is a placeholder for the two CodeQL counts. The fifth item is the sequencing note that this work must merge before issue #888 starts. **Pull request #1723. It merged and closed issue #892 and issue #893. Issue #891 stays open.**
- [X] T020 Watch the gate results with `gh pr checks --watch`. The Pylint job must pass inside its 10 minute timeout. The Vulture job must pass inside its 5 minute timeout. The local run in Phase A already predicted both results. **The pylint job failed on `ubuntu-latest` with a score of 9.41. That failure forced the US1 revert.**
- [X] T021 Confirm that the CodeQL Analysis workflow started and completed for the pull request. If the workflow did not start, stop and check the trigger. Do not start Phase D without a completed CodeQL run. The CodeQL workflow accepts no `workflow_dispatch` trigger, so the pull request is the only path to a result.

**Checkpoint**: The pull request is open. Two gates confirm the local result. One gate holds new evidence.

---

## Phase D: Read the CodeQL result and branch on it

**Goal**: Record a finding count and a verdict for each of the two queries. The outcome is not knowable before the run.

**Independent Test**: A reviewer reads the pull request and finds a count, a verdict, and a run link for each query. The two records are independent. One query may end in the `removed` state while the other ends in the `restored` state.

### Shared reading

- [X] T022 Count the alerts for each query. Set `$repo = "jmorrison-juniper/MistHelper"` and `$ref = "refs/heads/ci/891-893-gate-silencers"`. Then run `gh api "repos/$repo/code-scanning/alerts?ref=$ref&per_page=100" --jq '[.[] | select(.rule.id == "py/stack-trace-exposure")] | length'` and repeat the command for `py/clear-text-logging-sensitive-data`. Record both counts. **Measured on `refs/heads/main` on 2026-08-04. `py/stack-trace-exposure` reports 0 open alerts. `py/clear-text-logging-sensitive-data` reports 21 open alerts.**
- [X] T023 Confirm that each query actually ran. A count of zero is ambiguous on its own. It can mean a clean result, or it can mean a query that the default suite never ran. The two meanings lead to opposite conclusions. Download the SARIF report and list the rule identifiers with the two commands in Step 6 of [quickstart.md](quickstart.md). A printed value of `True` means the query ran. A printed value of `False` means the exclusion was always inert. Research decision R7 states this rule. **The 21 alerts prove that `py/clear-text-logging-sensitive-data` ran. The alert set carries no `py/stack-trace-exposure` row, so that query reports a clean result.**

### The decision table

Read the two recorded counts against this table. Take the action in the third column. Write the artifact in the fourth column. [data-model.md](data-model.md) holds the same table with the state transitions.

| The query ran | Finding count | Team judgment | Verdict | Action | Required artifact |
| - | - | - | - | - | - |
| No | Not applicable | Not applicable | `inert` | Keep the removal. | A pull request note that the exclusion never had an effect. |
| Yes | 0 | Not applicable | `clean` | Keep the removal. | The count and the CodeQL run link in the pull request. |
| Yes | Above 0 | The alerts are false positives. | `false_positive` | Restore that one exclusion with a Review Record. | A comment with the review date, the CodeQL run link, the reason, and the next review trigger. |
| Yes | Above 0 | An alert is real and a fix fits this feature. | `real` | Keep the removal and land the fix in this pull request. | The fix and the count in the pull request body. |
| Yes | Above 0 | An alert is real and a fix does not fit. | `real` | Restore that one exclusion with a Review Record. | A Review Record and a follow-up issue that the pull request links. |

A restored exclusion returns the `query-filters` key together with the exclusion. Follow the restored exclusion format in [contracts/review-comment.md](contracts/review-comment.md). Use ASCII characters only.

- [X] T024 [US3] Apply the decision table to the `py/stack-trace-exposure` query. Edit the file `.github/codeql/codeql-config.yml` only when the verdict asks for a restoration. Record the verdict. **Verdict `clean`. The query ran and reports 0 alerts. The removal stays. The configuration file needs no edit.**
- [X] T025 [US4] Apply the decision table to the `py/clear-text-logging-sensitive-data` query. Edit the file `.github/codeql/codeql-config.yml` only when the verdict asks for a restoration. A restored rationale must not claim that the tool never logs an actual secret. A restored rationale must also link issue #1710 as the evidence. Requirement FR-016 states this rule. Record the verdict. **Verdict `real`. The query reports 21 alerts across 6 files. The counts are `src/site/address_audit/address_resolver.py` 10, `src/capture/packet_capture.py` 4, `MistHelper.py` 2, `src/ssh/ssh_runner_manager.py` 2, `starlink_dashboard.py` 2, and `src/device/_utility_commands_action.py` 1. The removal stays. Issue #1710 owns the fix.**
- [X] T026 Push any restoration as a second commit. The commit lands on the same pull request. Then re-run `gh pr checks --watch`. Skip this task when both queries end in the `removed` state. **Skipped. Both queries end in the `removed` state.**
- [X] T027 Record both counts and both verdicts in the pull request body. Also record the CodeQL run link. Neither record may stay in the `pending` state when the pull request merges. Requirement FR-014 states this rule. **Pull request #1723 merged before the counts arrived. Task T030 writes the counts and the verdicts into `CHANGELOG.md` instead.**

**Checkpoint**: Both queries hold a recorded count and a recorded verdict. Every exclusion that survives carries a Review Record.

---

## Phase E: Close the record

**Goal**: Open the follow-up work, complete the changelog, and pass the prose gate.

- [X] T028 [P] Open the follow-up issue for the 502 newly visible pylint messages. Link that issue from the pull request. Requirement FR-020 states this rule. Non-goal NG-001 keeps the fix out of this feature. **Issue #891 holds this work. The review comment in `.github/workflows/ci.yml` names it as the next review trigger, so no second issue is needed.**
- [X] T029 [P] Record the vulture confidence 60 slice against issue #1703. A comment on issue #1703 satisfies this task. State that a confidence of 60 reports 306 findings today and that the team re-measures after issue #1703 lands. Requirement FR-021 states this rule. **Done on 2026-08-05. The comment reports 0 findings at the CI floor of 70 and 326 findings at 60. The count moved from 306 to 326, because menus 210 through 234 added export modules that vulture cannot resolve at that confidence.**
- [X] T030 [P] Fill the two CodeQL counts and the two verdicts into the changelog entry under `## [Unreleased]` in `CHANGELOG.md`. Replace the placeholder from T016.
- [X] T031 [P] Confirm that `.github/codeql/codeql-config.yml` holds zero undefended exclusions. Read every surviving exclusion. Each one must carry the review date, the evidence link, the reason, and the next review trigger. Requirement FR-017 and requirement FR-018 state this rule. **The file holds one line, which is the `name` key. Zero exclusions survive, so zero undefended exclusions survive.**
- [X] T032 Run the Simplified Technical English linter on every changed prose file. Run `.venv\Scripts\python.exe -m tools.ste_linter "CHANGELOG.md"` and repeat the command for each changed file in `specs/1033-ci-gate-silencer-removal/`. Each file must score 80 or above. Requirement FR-022 and success criterion SC-012 state this rule.
- [X] T033 Walk the acceptance checklist at the end of [quickstart.md](quickstart.md). Every line must be true before the merge. **Every line is true for US2, US3, and US4. The US1 lines stay false and issue #891 tracks them.**
- [X] T034 Confirm that the full CI suite is green on the branch. Wait for the CodeQL check to finish. Then add the `auto-merge` label. The repository rule forbids the label before CodeQL finishes on a code pull request. **Pull request #1723 merged with a green suite. Pull request #1726 restored the vulture floor of 70 that the US1 revert had undone.**

**Checkpoint**: The feature is complete. Every gate reports its findings. Every surviving suppression carries a written defense.

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase A** starts immediately. T001 gates every later task.
- **Phase B** starts after Phase A. The plan puts both edit sets in one commit, so Phase B waits for a clean Phase A.
- **Phase C** depends on Phase A and Phase B. The commit carries all three edits.
- **Phase D** depends on Phase C. The CodeQL result exists only after the pull request opens.
- **Phase E** depends on Phase D. The changelog needs the CodeQL counts.

### Task dependencies inside a phase

- T003 comes before T005 and before T006. The verification reads the edited file.
- T007 and T008 both come before T011. The guard checks both sites.
- T012, T013, and T014 come before T015. The parse check reads the final file.
- T012, T013, and T014 all edit the same file. Run them in order.
- T022 comes before T023. The SARIF check explains the count.
- T023 comes before T024 and before T025. A verdict needs a confirmed run.
- T024 and T025 come before T026 and before T027.
- T030 comes before T032. The linter reads the final changelog text.

### Parallel opportunities

Most tasks touch one of two files, so the parallel set is small.

- T002 runs in parallel with T001. Both read state and write nothing.
- T028, T029, T030, and T031 run in parallel. They touch four separate targets. Those targets are a new GitHub issue, issue #1703, `CHANGELOG.md`, and `.github/codeql/codeql-config.yml`.

User Story 1 and User Story 2 both edit `.github/workflows/ci.yml`. They cannot run in parallel. User Story 3 and User Story 4 both edit `.github/codeql/codeql-config.yml`. They cannot run in parallel either.

---

## Implementation Strategy

### Minimum viable scope

Phase A alone delivers the measured value. User Story 1 removes 502 hidden pylint messages from the dark. User Story 2 removes a silencer at zero cost. Both carry a local proof and neither needs a CI round trip.

Stop after Phase A only when the CodeQL experiment must wait. In that case the pull request closes issue #891 and issue #892, and issue #893 moves to its own branch after this work merges.

### The default path

Run every phase in one pass. The plan puts all three edits in one push, because only the CodeQL question needs CI. One push spends one round trip. Three pull requests would spend three round trips and would create a conflict on line 291 of `.github/workflows/ci.yml`.

### Sequencing against issue #888

Issue #888 also edits line 291. This work must merge before issue #888 starts. If issue #888 merges first, rebase onto `main` and reapply the deletion to the rewritten line. Requirement FR-023 and requirement FR-024 state this rule.
