# Feature Specification: CI Gate Silencer Removal

**Feature Branch**: `ci/891-893-gate-silencers`

**GitHub Issues**:

- [#891](https://github.com/jmorrison-juniper/MistHelper/issues/891) — "quality: remove pylint '--ignore=maps,ssh,ui' CLI silencer in ci.yml"
- [#892](https://github.com/jmorrison-juniper/MistHelper/issues/892) — "quality: lower vulture '--min-confidence 90' to surface hidden dead code"
- [#893](https://github.com/jmorrison-juniper/MistHelper/issues/893) — "security: re-evaluate CodeQL query exclusions (py/clear-text-logging, py/stack-trace-exposure)"

**Created**: 2026-07-28

**Status**: Draft

**Input**: Remove the last command line suppression and the last configuration suppression from three CI quality gates. Keep a suppression only when a written rationale defends it. Do not fix the newly visible findings in this feature.

---

## Background

Three CI quality gates still hide findings from the reviewer. A gate that hides a finding reports success while a real defect stays out of view. The team closed the same class of problem for bandit in issue [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889) and for pip-audit in issue [#890](https://github.com/jmorrison-juniper/MistHelper/issues/890). This feature closes the class for pylint, for vulture, and for CodeQL.

### Grouping decision

One specification and one pull request cover all three issues. The team records the decision here, because a reviewer will ask why three issues share one specification.

The reasons follow.

1. All three issues remove the last command line suppression or the last configuration suppression from a CI quality gate. The issues share one goal and one acceptance rule.
2. Issue #891 and issue #892 edit the same file. That file is `.github/workflows/ci.yml`. Two pull requests against the same file create an avoidable merge conflict.
3. Issue #891 edits line 291 of that file. Open issue [#888](https://github.com/jmorrison-juniper/MistHelper/issues/888) also edits line 291. A split into three pull requests would create a three way conflict on one line.
4. All three issues share the same review rule from issue #890. A single review comment style applies to every suppression that survives.

### The three suppressions today

| Issue | File | Line | Suppression | Effect |
| - | - | - | - | - |
| #891 | `.github/workflows/ci.yml` | 291 | `--ignore=maps,ssh,ui` | Hides `src/maps`, `src/ssh`, and `src/ui` from the pylint gate. |
| #892 | `.github/workflows/ci.yml` | 51 | `VULTURE_CONFIDENCE: 90` | Raises the vulture confidence floor to the maximum value. |
| #893 | `.github/codeql/codeql-config.yml` | 10 to 14 | Two `query-filters` exclusions | Hides two CodeQL query results from the security gate. |

### Measured baseline for the pylint gate

A maintainer ran the pylint gate against the current checkout in both configurations.

| Configuration | Messages | Gate exit code |
| - | - | - |
| With `--ignore=maps,ssh,ui`, which CI runs today | 757 | 0, the gate passes |
| Without the ignore list | 1259 | 0, the gate passes |

The removal makes 502 more messages visible. The score gate still passes at `--fail-under=9.5`. The change is a one line deletion. No code fix comes first.

### Measured baseline for the vulture gate

A maintainer ran the vulture gate at five confidence values.

| Confidence | Findings |
| - | - |
| 90, which CI runs today | 0 |
| 80 | 0 |
| 70 | 0 |
| 60 | 306 |
| 50 | 306 |

A move from 90 to 70 costs nothing. The cliff sits between 70 and 60. This feature stops at 70.

The 306 findings at confidence 60 carry a high false positive rate. Two patterns drive that rate. The first pattern is module level dependency injection. The second pattern is a dynamic `mh.*` lookup that vulture cannot resolve. Issue [#1703](https://github.com/jmorrison-juniper/MistHelper/issues/1703) removes the second pattern. A move to confidence 60 belongs to a later slice that waits for issue #1703.

### The CodeQL exclusions

The file `.github/codeql/codeql-config.yml` excludes two queries.

```yaml
query-filters:
  - exclude:
      id: py/clear-text-logging-sensitive-data
  - exclude:
      id: py/stack-trace-exposure
```

The exclusion of `py/clear-text-logging-sensitive-data` carries an eight line rationale. The rationale argues that CodeQL misreads a MAC address and a device identifier as private data, because the variable name contains `mac`. The rationale also claims that the tool never logs a password, an API token, or an actual secret. Issue [#1710](https://github.com/jmorrison-juniper/MistHelper/issues/1710) found a partial API token value in `data/script.log`. That finding weakens the final claim of the rationale.

The exclusion of `py/stack-trace-exposure` carries no rationale. No comment names the author, the date, or the reason. `MistHelper.py` writes a full traceback in the global exception hook and in the session initialization path. The query may therefore report a real finding.

Nobody can measure a CodeQL result on a workstation, because CodeQL runs only in CI. The work for issue #893 is a CI experiment. The experiment has three steps. The first step removes an exclusion and pushes the branch. The second step reads the CodeQL result. The third step either fixes the finding or restores the exclusion with a written rationale.

### The review rule from issue #890

Issue #890 merged on 2026-07-28. It set the precedent that this feature follows. Any suppression that survives a review carries three facts in a comment.

1. The date of the review.
2. A link to the evidence.
3. The condition that triggers the next review.

A bare suppression does not pass review.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See every pylint message from every source package (Priority: P1)

A code reviewer wants the pylint gate to read every package under `src/`. The reviewer removes the `--ignore=maps,ssh,ui` flag from the pylint step. The gate then reports the messages for `src/maps`, `src/ssh`, and `src/ui` alongside the rest.

**Why this priority**: This story carries the highest value and the lowest risk. The measurement proves that the gate still passes. The change is a one line deletion. The story also holds the line that issue #888 edits, so it must land first.

**Independent Test**: A reviewer reads the pylint step in `.github/workflows/ci.yml` and finds no `--ignore` flag. A reviewer then runs the pylint job in CI and confirms an exit code of 0.

**Acceptance Scenarios**:

1. **Given** the updated workflow file, **When** a reviewer searches the pylint step for `--ignore`, **Then** the search returns no match.
2. **Given** the updated workflow file, **When** CI runs the pylint job, **Then** the job exits with code 0 inside the existing 10 minute timeout.
3. **Given** the CI log for the pylint job, **When** a reviewer searches the log for the path `src/maps`, **Then** the log holds at least one message for that path.
4. **Given** the CI log for the pylint job, **When** a reviewer searches the log for the path `src/ssh` and for the path `src/ui`, **Then** the log holds at least one message for each path.
5. **Given** a follow-up issue that tracks the newly visible messages, **When** a reviewer opens the pull request, **Then** the pull request links that issue.

---

### User Story 2 - Lower the vulture confidence floor to a measured safe value (Priority: P2)

A code reviewer wants the dead code gate to run below the maximum confidence value. The reviewer changes `VULTURE_CONFIDENCE` from 90 to 70. The gate then reports a dead code finding that a confidence of 90 would hide.

**Why this priority**: The measurement proves that the change costs nothing today. The story carries less value than User Story 1, because the finding count stays at zero. The story still removes a silencer that could hide a future defect.

**Independent Test**: A reviewer reads the `VULTURE_CONFIDENCE` value in `.github/workflows/ci.yml` and finds 70. A reviewer then runs the vulture job in CI and confirms an exit code of 0.

**Acceptance Scenarios**:

1. **Given** the updated workflow file, **When** a reviewer reads the `VULTURE_CONFIDENCE` default value, **Then** the value is 70.
2. **Given** the updated workflow file, **When** CI runs the vulture job, **Then** the job exits with code 0 inside the existing 5 minute timeout.
3. **Given** the updated workflow file, **When** a reviewer reads the comment above the vulture step, **Then** the comment states the review date, links the measurement evidence, and names issue #1703 as the condition that triggers the next review.
4. **Given** a pull request that adds unreachable code at a confidence of 70 or above, **When** CI runs the vulture job, **Then** the job fails and the log names the file and the symbol.

---

### User Story 3 - Defend or remove the undocumented CodeQL exclusion (Priority: P3)

A security reviewer wants a written reason for every CodeQL exclusion. The reviewer removes the exclusion of `py/stack-trace-exposure`, pushes the branch, and reads the CodeQL result. The reviewer then either fixes the reported finding or restores the exclusion with a full rationale.

**Why this priority**: This exclusion is the primary target of issue #893, because nobody documented it. The story ranks below the first two, because a CI round trip drives it and the outcome is unknown before the run.

**Independent Test**: A reviewer reads the CodeQL result for the branch. The reviewer then confirms that the repository holds either zero findings for the query or an exclusion with a full rationale.

**Acceptance Scenarios**:

1. **Given** the branch with the exclusion removed, **When** CI runs the CodeQL workflow, **Then** the run completes and the pull request records the finding count for `py/stack-trace-exposure`.
2. **Given** a CodeQL result of zero findings for the query, **When** a reviewer reads `.github/codeql/codeql-config.yml`, **Then** the file holds no exclusion for `py/stack-trace-exposure`.
3. **Given** a CodeQL result with one or more findings that the team accepts as safe, **When** a reviewer reads the restored exclusion, **Then** the comment states the review date, links the CodeQL run, and names the condition that triggers the next review.
4. **Given** a CodeQL result with one or more findings that the team accepts as real, **When** a reviewer reads the pull request, **Then** the pull request links a follow-up issue that tracks the fix.
5. **Given** the final state of the configuration file, **When** a reviewer reads every remaining exclusion, **Then** each one carries a rationale.

---

### User Story 4 - Correct the stale claim in the second CodeQL rationale (Priority: P4)

A security reviewer wants the rationale for `py/clear-text-logging-sensitive-data` to match the evidence. The current rationale claims that the tool never logs an actual secret. Issue #1710 contradicts that claim. The reviewer repeats the experiment for this query and then rewrites or removes the rationale.

**Why this priority**: This exclusion is the secondary target of issue #893, because a rationale already defends it. The story still matters, because a stale rationale hides a real risk. The story ranks last, because User Story 3 proves the experiment method first.

**Independent Test**: A reviewer reads the rationale for `py/clear-text-logging-sensitive-data` and confirms that no sentence contradicts issue #1710.

**Acceptance Scenarios**:

1. **Given** the branch with the exclusion removed, **When** CI runs the CodeQL workflow, **Then** the pull request records the finding count for `py/clear-text-logging-sensitive-data`.
2. **Given** a decision to keep the exclusion, **When** a reviewer reads the rationale, **Then** the rationale holds no claim that the tool never logs an actual secret.
3. **Given** a decision to keep the exclusion, **When** a reviewer reads the rationale, **Then** the rationale links issue #1710 and states the review date and the next review trigger.
4. **Given** a decision to remove the exclusion, **When** a reviewer reads `.github/codeql/codeql-config.yml`, **Then** the file holds no exclusion for the query and the CodeQL job passes.

---

### Edge Cases

- **The pylint score falls below the threshold on a later run.** A future pylint release can change a score. The gate threshold stays at 9.5 in this feature. A drop below the threshold is a new defect and belongs to a new issue.
- **Issue #888 merges before this feature.** Issue #888 rewrites line 291. The author of this feature rebases onto `main` and reapplies the deletion to the rewritten line.
- **This feature merges before issue #888.** The author of issue #888 rebases and reapplies the scope change to the shortened line.
- **The vulture gate reports a finding at confidence 70 after a dependency bump.** The finding is real dead code. The team fixes the code and does not raise the floor again.
- **The CodeQL run reports a finding that the team cannot fix inside this feature.** The team restores the exclusion with the three required facts and opens a follow-up issue for the fix.
- **The CodeQL run does not complete for the branch.** The team reads the result from the scheduled run on `main` after the merge and treats a late finding as a new issue.
- **A reviewer asks for the 502 pylint messages in this pull request.** The messages stay out of scope. The pull request links the follow-up issue that tracks them.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Scope and grouping

- **FR-001**: The feature MUST close issue #891, issue #892, and issue #893 through one pull request.
- **FR-002**: The pull request MUST state the grouping reason, because two of the three issues edit the same file and one of them edits a line that issue #888 also edits.
- **FR-003**: The feature MUST NOT create a new git branch. The work uses the existing branch `ci/891-893-gate-silencers`, which matches `origin/main`.

#### Pylint gate, issue #891

- **FR-004**: The pylint step in `.github/workflows/ci.yml` MUST run with no path ignore flag.
- **FR-005**: The pylint gate MUST keep the `--fail-under` threshold at its current value of 9.5.
- **FR-006**: The pylint job MUST exit with code 0 after the change, which the measured baseline of 1259 messages supports.
- **FR-007**: The pylint step MUST carry a comment that repeats the review rule from issue #890 for any future ignore flag.

#### Vulture gate, issue #892

- **FR-008**: The `VULTURE_CONFIDENCE` environment default in `.github/workflows/ci.yml` MUST hold the value 70.
- **FR-009**: The feature MUST NOT set the vulture confidence below 70.
- **FR-010**: The vulture step MUST carry a comment that states the review date of 2026-07-28, links the confidence measurement, and names issue #1703 as the condition that triggers the next review.
- **FR-011**: The comment MUST record that a confidence of 60 reports 306 findings and that a later slice owns that value.

#### CodeQL gate, issue #893

- **FR-012**: The feature MUST remove the exclusion of `py/stack-trace-exposure` from `.github/codeql/codeql-config.yml` and MUST read the CodeQL result from a CI run on the branch.
- **FR-013**: The feature MUST remove the exclusion of `py/clear-text-logging-sensitive-data` and MUST read the CodeQL result from a CI run on the branch.
- **FR-014**: The pull request MUST record the finding count for each query and the decision that follows the count.
- **FR-015**: A restored exclusion MUST carry a rationale, the review date, a link to the CodeQL run that produced the evidence, and the condition that triggers the next review.
- **FR-016**: A restored rationale for `py/clear-text-logging-sensitive-data` MUST NOT claim that the tool never logs an actual secret, because issue #1710 contradicts that claim. The rationale MUST link issue #1710.
- **FR-017**: The configuration file MUST hold zero undefended exclusions after the feature completes.

#### Review record and documentation

- **FR-018**: Every suppression that survives the feature MUST carry the three facts from the issue #890 precedent. Those facts are the review date, a link to the evidence, and the next review trigger.
- **FR-019**: The feature MUST add an entry under `## [Unreleased]` in `CHANGELOG.md` that names all three issues and states the measured counts.
- **FR-020**: The feature MUST open a follow-up issue for the 502 newly visible pylint messages and MUST link that issue from the pull request.
- **FR-021**: The feature MUST record the vulture confidence 60 slice as future work that waits for issue #1703. A follow-up issue or a note in the existing issue #1703 satisfies this requirement.
- **FR-022**: All prose, all comments, and all changelog text MUST follow the Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md`.

#### Sequencing

- **FR-023**: The pull request for this feature and the pull request for issue #888 MUST NOT stay open at the same time while both modify line 291 of `.github/workflows/ci.yml`.
- **FR-024**: This feature MUST merge before issue #888 starts, because this feature deletes part of line 291 and issue #888 rewrites the rest of it. If issue #888 merges first, this feature MUST rebase onto `main` before the pull request opens.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The pylint gate reads three source packages that it could not read before. A search of the pylint job log returns at least one message for `src/maps`, at least one for `src/ssh`, and at least one for `src/ui`.
- **SC-002**: The pylint job passes after the change and adds no build failure. The exit code is 0 and the run finishes inside the existing 10 minute timeout.
- **SC-003**: The number of hidden pylint messages falls from 502 to 0.
- **SC-004**: The vulture gate runs at a confidence floor of 70 and reports 0 findings. The exit code is 0 and the run finishes inside the existing 5 minute timeout.
- **SC-005**: The number of CI quality gates that carry a command line suppression falls from 2 to 0.
- **SC-006**: The number of undefended CodeQL exclusions falls from 1 to 0.
- **SC-007**: The number of stale claims in a CodeQL rationale falls from 1 to 0.
- **SC-008**: Every suppression that survives the feature carries all three required facts. The count of bare suppressions is 0.
- **SC-009**: A reviewer can name the reason for every remaining suppression without asking the author. The reviewer reads only the file that holds the suppression.
- **SC-010**: The full CI suite stays green on the branch. Every gate that passed before the change still passes.
- **SC-011**: The changelog holds one entry under `## [Unreleased]` that names issue #891, issue #892, and issue #893.
- **SC-012**: Every new sentence and every changed sentence scores at or above 80 on the Simplified Technical English linter.
- **SC-013**: The three issues close through one merge and produce zero merge conflicts with the work for issue #888.

---

## Non-Goals

The following work stays outside this feature. Each item belongs to separate follow-up work.

- **NG-001**: Fixing the 502 pylint messages that the removal makes visible. A follow-up issue tracks them.
- **NG-002**: Fixing the 306 vulture findings that a confidence of 60 reports.
- **NG-003**: Lowering the vulture confidence below 70. That slice waits for issue #1703.
- **NG-004**: Removing the `MistHelper` back reference from the `src` packages. Issue #1703 owns that work.
- **NG-005**: Stopping the partial API token value that reaches `data/script.log`. Issue #1710 owns that work. This feature only corrects the rationale that cites the old claim.
- **NG-006**: Removing the `SRC_PATH` scope cap from the mypy, pytest, pylint, and radon gates. Issue #888 owns that work.
- **NG-007**: Changing the pylint `--fail-under` threshold, the coverage threshold, or any other gate threshold.
- **NG-008**: Adding a new CodeQL query, a new query pack, or a new quality gate.
- **NG-009**: Refactoring `src/maps`, `src/ssh`, or `src/ui`. The feature only makes the existing messages visible.
- **NG-010**: Creating a git branch. The work reuses `ci/891-893-gate-silencers`.

---

## Sequencing and the line 291 collision

Line 291 of `.github/workflows/ci.yml` reads as follows today.

```yaml
run: pylint ${{ env.SRC_PATH }} --fail-under=${{ env.PYLINT_THRESHOLD }} --ignore=maps,ssh,ui
```

Two open issues change that one line.

| Issue | Change to line 291 |
| - | - |
| #891, this feature | Deletes `--ignore=maps,ssh,ui` from the end of the line. |
| #888 | Replaces `${{ env.SRC_PATH }}` with a wider scope. |

The two changes touch opposite ends of the same line. Git reports a conflict when both pull requests stay open.

The team applies the following rule.

1. This feature merges first, because it is a measured one line deletion with a known result.
2. The author of issue #888 rebases onto `main` after this merge and reapplies the scope change to the shortened line.
3. If issue #888 merges first, the author of this feature rebases onto `main` and deletes the ignore flag from the rewritten line.
4. No third pull request modifies line 291 while either of these two pull requests stays open.

---

## Assumptions

- The measured pylint counts and the measured vulture counts came from a local run against the current `origin/main` checkout. A CI run can differ by a small amount when the tool version differs. The direction of the result does not change.
- The pylint score gate stays at `--fail-under=9.5`, so the 502 extra messages do not fail the build.
- CodeQL runs on a pull request through `.github/workflows/codeql.yml`, so the branch produces a readable result before the merge.
- The team accepts one pull request that closes three issues, because the issues share one file and one acceptance rule.
- The vulture false positive rate at confidence 60 falls after issue #1703 lands. The team measures the rate again at that time and does not assume a value now.
- The `data/script.log` finding in issue #1710 is a real leak of a partial API token value. This feature treats that finding as fact and does not verify it again.
- The reviewer of the pull request has permission to read the CodeQL result for the branch.

---

## Dependencies

- **Issue #888** and this feature both change line 291 of `.github/workflows/ci.yml`. The sequencing rule above sets the order of the two merges.

- **Issue #1703** gates the later vulture slice at confidence 60. This feature does not wait for it.

- **Issue #1710** supplies the evidence that invalidates one claim in the `py/clear-text-logging-sensitive-data` rationale. This feature reads that evidence and does not fix the leak.

- **Issue #890** supplies the review comment precedent. That issue is closed and merged.

- The CodeQL workflow at `.github/workflows/codeql.yml` must run on the branch, because the team cannot measure a CodeQL result on a workstation.
