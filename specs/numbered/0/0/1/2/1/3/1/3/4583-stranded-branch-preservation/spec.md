# Feature Specification: Stranded Branch Preservation

**Feature Branch**: `chore/4583-stranded-branch-preservation`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4583, "chore(git): a branch holds work with no pull request". The stranded branch report names each branch that holds commits above `main` and has no pull request that keeps its head.

## Key Terms

- **Stranded branch**: A branch with commits above `main` and no pull request that keeps its head.
- **In-scope branch**: A stranded branch under the report rule in FR-002.
- **Ready branch**: An in-scope branch with no open pull request that shares a changed file.
- **Held branch**: An in-scope branch that shares a changed file with an open pull request.
- **Preservation pull request**: A draft pull request that names one in-scope branch and closes without merge.
- **Proof comment**: The closing comment of a preservation pull request.
- **Work order**: The ordered rows that command Q-2 in `design/quickstart.md` prints.
- **Snapshot**: The GitHub state that this record reads on 2026-11-26.
- **Report issue**: An issue that carries the report body and the report title.

## Clarifications

### Session 2026-11-26

- Q: Which branches does the record cover? A: Every in-scope branch of the live report rule, which is 543 at the snapshot. The issue body lists only 52 names. (D-3)
- Q: How does a branch keep its head? A: A draft pull request opens and closes without merge in the same step, with a proof comment. (D-1)
- Q: What happens when an open pull request shares a file? A: The branch waits until that pull request closes or merges. (D-2)
- Q: Are branches deleted or renamed? A: No. The record deletes and renames no branch. (D-4, D-6)
- Q: Which keyword does the record pull request use? A: `Closes #4583`, and it merges only after the final scope check. (D-7)
- Q: How are the duplicate report issues handled? A: A separate defect issue handles them. (D-8)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep a pull request head for each in-scope branch (Priority: P1)

The maintainer keeps the head of each ready branch in a closed pull request. The branch stays on origin, and the report then treats the branch as protected.

**Why this priority**: A branch with no pull request has one copy. Cleanup can remove that copy without any warning from git.

**Independent Test**: Run the create, close, and verify steps for one ready branch. The closed pull request names the snapshot head SHA, and the branch still points to that SHA.

**Acceptance Scenarios**:

1. **Given** a ready branch at head SHA X, **When** the procedure runs, **Then** a closed, unmerged draft pull request names X.
2. **Given** the same branch after the close, **When** the verify step runs, **Then** the branch still points to X.
3. **Given** a close that fails, **When** the procedure detects the failure, **Then** no further pull request opens until the open pull request closes.

### User Story 2 - Show that the report names no branch (Priority: P2)

The maintainer confirms that no in-scope branch remains after the last batch and every hold releases.

**Why this priority**: The report closes its issue only when no branch is stranded.

**Independent Test**: Run command Q-2 after the last batch. The output shows `in_scope=0`.

**Acceptance Scenarios**:

1. **Given** every ready branch is preserved and every hold is released, **When** Q-2 runs, **Then** the output shows `in_scope=0`.
2. **Given** a branch younger than seven days, **When** Q-2 runs, **Then** the branch is excluded and the next scope check includes it.

### User Story 3 - Hold a branch that shares a file with an open pull request (Priority: P3)

The maintainer waits before a preservation pull request opens for a branch that shares a changed file with an open pull request.

**Why this priority**: AGENTS.md forbids two open pull requests on one file.

**Independent Test**: Run Q-2 while pull request #4208 is open. The row for `recovery/3213-handoff-20261004` shows lane `#4208`, because both diffs change `deploy/.env.example`.

**Acceptance Scenarios**:

1. **Given** a branch that changes a file that open pull request #4208 also changes, **When** Q-2 runs, **Then** the branch shows lane `#4208`.
2. **Given** pull request #4208 closes, **When** Q-2 runs after the release check, **Then** the branch shows lane `ready`.

## Edge Cases

- **A body name moved to an archive name.** The procedure processes the archive name, because it holds the same head SHA (D-4).
- **A head SHA changed after the snapshot.** The procedure marks the row stale and reruns Q-2 before any create (FR-012).
- **A branch is younger than seven days.** The branch stays out of scope until a later check (D-5).
- **A branch name starts with `dependabot/`, `gh-readonly-queue/`, or `revert-`.** The report rule excludes the branch (D-5).
- **A closed pull request with the same name holds the head.** The report rule excludes the branch, so the procedure skips it.
- **A close fails after a create.** The procedure stops, and it closes the open pull request before any new create (FR-010).
- **GitHub returns HTTP 403 or 429.** The procedure waits 60, 120, and 240 seconds. After three retries, it stops (FR-010).
- **A blocking pull request closes during a batch.** The procedure rechecks the lane before the next create (FR-003).
- **The proof comment is missing after a close.** The procedure adds the proof as a new comment on the closed pull request, then verifies it (V-05).
- **The five report issues stay open after the scope empties.** A separate defect issue handles them (D-8).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The procedure MUST read the branch list and pull request data from GitHub on the day it runs.
- **FR-002**: The procedure MUST treat a branch as in scope under the report rule in decision D-3.
- **FR-003**: The procedure MUST hold each in-scope branch that shares a changed file with an open pull request.
- **FR-004**: The procedure MUST keep no more than one preservation pull request open at any time.
- **FR-005**: The procedure MUST open a draft pull request and close it without merge in the same step.
- **FR-006**: The procedure MUST title each preservation pull request in the Conventional Commits form and name the head SHA and `Refs #4583` in its body.
- **FR-007**: The procedure MUST NOT delete, rename, force-push, merge, or push a branch, and it MUST NOT run a checkout of a branch.
- **FR-008**: The procedure MUST write a proof comment on each preservation pull request when it closes.
- **FR-009**: The procedure MUST verify the closed state, the unmerged state, and the head SHA after each step.
- **FR-010**: The procedure MUST stop after a failed close, and it MUST back off on HTTP 403 or 429.
- **FR-011**: The procedure MUST print the work order and the holds before its first write in each run.
- **FR-012**: The procedure MUST rerun the scope check before each batch and add each new in-scope branch.
- **FR-013**: The procedure MUST release a held branch only after its blocking pull request closes or merges.
- **FR-014**: The record pull request MUST contain `Closes #4583`, and it MUST NOT merge before the final scope check passes.
- **FR-015**: The record MUST add files only under the record route, and it MUST pass the guard tests and the style checks.
- **FR-016**: The record MUST name the open duplicate report issues, and it MUST require a separate issue for the defect.
- **FR-017**: Each remote claim in the record MUST appear once in the remote checks and once in the remote table of `design/research.md`.
- **FR-018**: The status summary MUST stay within 2500 characters, and it MUST NOT contain a credential value.

### Mist Cloud Transport Requirements

Not applicable. This feature calls no Mist REST endpoint and no mistapi method. It uses GitHub through `gh`.

### Key Entities

- **BranchSnapshot**: One branch with its head SHA, counts, and lane. See `design/data-model.md`.
- **PreservationPullRequest**: One closed draft pull request for one branch head. See `design/contracts/preservation-pull-request.md`.
- **HoldRecord**: One held branch with its blocking pull request. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each in-scope branch at the snapshot has one closed preservation pull request, or a hold record that names an open blocking pull request.
- **SC-002**: The final scope check lists zero in-scope branches after every hold releases.
- **SC-003**: The number of branches on origin does not decrease during the run.
- **SC-004**: No more than one preservation pull request stays open between steps.
- **SC-005**: The two guard tests pass, and each record file scores 80 or above in the STE linter.

## Assumptions

- The report uses the rule in the shared report source at commit 79a5e45. The read-only emulation includes all 505 names of the 2026-11-23 report.
- The local git objects hold each in-scope head commit. Command Q-2 reads the commits without a fetch when they exist.
- The GitHub account can create and close draft pull requests in the repository.
- A closed pull request keeps its head commit on GitHub.

## Out of Scope

- Deleting, renaming, or rewriting a branch. A separate issue handles this after the report clears.
- Reviewing or merging branch content. The author of each branch handles this.
- Fixing the report workflow or its duplicate issues. The separate defect issue of task T026 handles this.
- Changing the report rule, the quiet period, or the prefixes. The misthelper-devtools maintainers handle this.
- Merging or closing the held pull requests #4208, #4813, #4886, #4887, and #4888. Each author handles its own pull request.
- Aligning the `misthelper-devtools` pin in `requirements-dev.txt` with the workflow pin. The owner of that file handles this.
- Product code changes. The feature makes none.

## Dependencies

- **Blocking pull requests**: #4208 (62 held branches), #4813 (12), #4886 (3), #4887 (4), and #4888 (21).
- **Related issues**: #1980 asked for the check, and #2251 recorded a branch loss.
- **Predecessor**: #3487 is a closed tooling issue that the workflow file cites.
- **Duplicate report issues**: #4302, #4719, #4818, and #4911 are open.
- **Issue prerequisites**: None.
