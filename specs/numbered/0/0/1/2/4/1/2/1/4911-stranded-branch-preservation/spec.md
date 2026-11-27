# Feature Specification: Preserve the named branches of the stranded branch report

**Feature Branch**: `chore/4911-stranded-branch-preservation`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4911. A weekly report names 505 branches. Each branch holds commits above `main`, and the report finds no pull request that holds its tip.

## Clarifications

### Session 2026-11-26

- Q: Must each named branch get its own pull request, as the issue body states?
  A: No. Decision D-2 replaces that rule with one preservation tag for each named branch. A pull request opens only when the owner selects a branch for review or merge. Each pull request starts the full CI workflow, and failed gates open issues per pull request.
- Q: Does the report name the right branches?
  A: Only in part. 248 of 505 tips equal a PR head commit, so `refs/pull/<n>/head` already keeps those commits. The report compares names, not commit IDs. The other 257 tips have no PR head commit.
- Q: Which branches serve as evidence?
  A: Two branches. Exemplar A is the first table row, `archive/laptop-20261121/preservation/2746-pr3011-turn0`. It is held by closed PR 3954. Exemplar B is `fix/3158-wip-controls`. It is the oldest row with no PR head commit.
- Q: Does this change close issue 4911?
  A: No. The report keeps naming rows until its upstream rule accepts preservation tags. The closing keyword follows decision D-7.
- Q: Does this change delete any branch?
  A: No. A later issue handles deletion, and it cites the verified preservation tags.
- Q: Does this change need a changelog fragment?
  A: Yes. The constitution requires one fragment for each change. The rule in `changelog.d/README.md` allows no fragment for an internal change. Analysis records that conflict.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep each named branch recoverable (Priority: P1)

An operator gives each named branch a preservation tag at its tip. The commits then stay reachable after a later branch deletion.

**Why this priority**: A branch with no durable copy has one copy on origin. A deletion of that branch removes the copy, and git prints no warning.

**Independent Test**: List the tags under `refs/tags/preserve/` on origin. Expect 505 tags. Each tag points to the tip recorded for its branch.

**Acceptance Scenarios**:

1. **Given** 505 named branches exist, **When** the procedure finishes, **Then** 505 `preserve/<branch name>` tags exist at the recorded tips.
2. **Given** one batch push fails, **When** the procedure reaches it, **Then** no later batch starts, and the ledger names its rows.
3. **Given** a named branch no longer exists, **When** its row runs, **Then** the ledger records it as absent, and no tag is created.

### User Story 2 - State the durable copy rule correctly (Priority: P2)

A maintainer reads the branch cleanup section of the contribution guide. The section names a pushed tag as a durable copy, as `AGENTS.md` states. The section keeps the pull request rule for each branch that the owner selects.

**Why this priority**: The guide now says that a pull request is the only durable copy. That statement conflicts with `AGENTS.md` and with this procedure.

**Independent Test**: Read the branch cleanup section in `documentation/contributing.md`. The section names the preservation tag. The section keeps the warning against deletion.

**Acceptance Scenarios**:

1. **Given** the updated guide, **When** the Markdown link guard runs, **Then** each relative link in the file resolves.
2. **Given** the updated guide, **When** the STE gate runs, **Then** the file scores 80 or above.

### User Story 3 - Keep one tracking issue and track the follow-up work (Priority: P3)

The maintainers keep one open tracking issue for the report. They file separate issues for the upstream report change, for branch deletion, and for the folder debt.

**Why this priority**: The shared report workflow promises one open tracking issue. Five open issues now share the report title. The report keeps naming every row until its rule changes.

**Independent Test**: List the open issues with the report title. Expect one issue, the tracking issue. Expect links to the three follow-up issues in the tracking issue.

**Acceptance Scenarios**:

1. **Given** four duplicate tracking issues are open, **When** each duplicate closes with a link to issue 4911, **Then** only issue 4911 stays open.
2. **Given** the upstream report change is filed, **When** the link is added to issue 4911, **Then** the link is readable from the tracking issue.

### Edge Cases

- A named branch is deleted before its batch runs. The ledger records the row as absent, and no tag is created.
- A tag with the same name already points to the same tip. The procedure records the row as verified-present and pushes nothing.
- A tag with the same name points to a different tip. The procedure stops and reports the row. The procedure never overwrites a tag.
- A branch receives a new tip after the report. The procedure tags the new tip. The report holds no tip commit IDs, so a rewrite after the report cannot be detected from the report alone.
- A tag push starts a workflow run. The procedure stops at the pilot. The rollback command removes the pilot tags.
- The report names new rows before the procedure ends. The procedure records the new rows as a later batch.
- Two branch names point to one commit. Each name gets its own tag, and both tags point to that commit.
- A branch name is an archive copy of a PR branch name. The procedure tags it the same way as any other named branch.

- **Warning:** A deletion of a named branch before its tag exists removes the only copy of its commits. Do not delete a named branch in this change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The procedure MUST cover each of the 505 branch rows named in issue 4911.
- **FR-002**: The procedure MUST create one lightweight tag named `preserve/<branch name>` at the tip of each named branch.
- **FR-003**: The procedure MUST NOT delete, rename, or force update any branch or tag. The procedure MUST NOT open a pull request for a named branch.
- **FR-004**: The procedure MUST check each tag name with `git check-ref-format`. The procedure MUST NOT overwrite an existing tag.
- **FR-005**: The procedure MUST read the tips from GitHub in the same session as the pushes. The procedure MUST push only the tips from that read. The procedure MUST stop when a named branch returns a not-found error.
- **FR-006**: The procedure MUST push at most 50 tags in each batch. The procedure MUST stop at the first failed batch. The procedure MUST retry a failed push at most three times with exponential backoff.
- **FR-007**: The procedure MUST verify each batch with `git ls-remote --tags`. The procedure MUST record one ledger row for each named branch.
- **FR-008**: The procedure MUST confirm that the pilot tag pushes start no workflow run. The procedure MUST stop and roll back the pilot when a run starts.
- **FR-009**: The contribution guide MUST keep the pull request rule for each branch that the owner selects for review or merge.
- **FR-010**: The contribution guide MUST name a pushed tag as a durable copy. The contribution guide MUST NOT state that a pull request is the only durable copy.
- **FR-011**: The pull request for this record MUST use `Refs #4911` until the report names no row. The pull request MUST use `Closes #4911` after the report names no row.
- **FR-012**: Branch deletion MUST wait for a separate issue. That issue MUST cite the verified preservation tags.
- **FR-013**: The change MUST add one changelog fragment named `issue-4911-stranded-branch-preservation.md`.
- **FR-014**: The change MUST file one upstream issue in `jmorrison-juniper/misthelper-devtools`. The issue MUST ask that the report treat a tip as held when it equals a PR head commit or a preservation tag.
- **FR-015**: The repository MUST have one open tracking issue with the report title after the duplicate handling.
- **FR-016**: The change MUST NOT change `requirements-dev.txt` or any workflow pin.
- **FR-017**: The change MUST track one remediation issue for the folder debt of `changelog.d` and `specs`.

### Key Entities *(include if feature involves data)*

- **Named branch**: One row of the report. The natural key is the branch name. Each named branch has one tip.
- **Tip**: The commit at the end of a named branch. The natural key is the commit ID.
- **PR head commit**: The head commit of a pull request, read as `headRefOid`. A tip that equals a PR head commit is held.
- **Preservation tag**: The lightweight tag `preserve/<branch name>` on origin. The natural key is the tag name.
- **Batch**: A group of at most 50 tag refspecs. The natural key is the batch index.
- **Ledger row**: The result for one named branch. The natural key is the branch name.
- **Tracking issue**: The open issue that carries the report. The natural key is the issue number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 505 of 505 preservation tags exist on origin, and each tag points to its recorded tip.
- **SC-002**: 505 of 505 named branch names still exist on origin after the procedure.
- **SC-003**: Each changed Markdown file scores 80 or above with the STE gate, and the two guard tests pass.
- **SC-004**: The pilot tag pushes start no workflow run.
- **SC-005**: One open tracking issue carries the report title after the duplicate handling.
- **SC-006**: The repository record holds the same files as the draft, and the counts in the STATUS file match the research table.

## Assumptions

- The local clone holds the commit objects for all 505 tips. The check on 2026-11-26 found all 505 with `git rev-list`.
- The account that runs the procedure can push tags to origin.
- GitHub accepts lightweight tags whose names contain slashes. The pilot verifies that behavior.
- No workflow starts from a tag under `refs/tags/preserve/`. The pilot verifies that behavior, because the GitHub event documentation was not readable during this research.
- The report keeps naming the same rows until its upstream rule changes.

## Out of Scope

- Deleting any named branch.
- Merging any named branch.
- Opening a pull request for a named branch, unless the owner selects that branch.
- Changing the report tool, its workflow pin, or the tool pin in `requirements-dev.txt`.
- Changing any CI workflow.
- Rewriting `documentation/stranded-branch-review.md`, which is a historical review.
- Cleaning the `changelog.d` or `specs` folders. FR-017 tracks that work in a separate issue.
