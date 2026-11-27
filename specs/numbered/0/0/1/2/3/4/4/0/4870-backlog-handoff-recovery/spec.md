# Feature Specification: Backlog Handoff Recovery

**Feature Branch**: `chore/4870-backlog-handoff-recovery`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Handoff issue 4870, "Backlog handoff: MistHelper open issues, PRs, and recovery state (2026-11-21)". The handoff was verified against GitHub main at commit f03c6c9b3.

## Clarifications

### Session 2026-11-21

- Q: Who decides the open questions in the handoff? A: The user gave full decision authority on 2026-11-21, as comment 3 records.

### Session 2026-11-22

- Q: Which text governs the handoff body? A: The decision comment governs. It supersedes sections 9, 11, 12, and 13 of the body.
- Q: What restored the feature pointer? A: PR 4884 restored `.specify/feature.json` to its pre-4846 value. Its merge commit is 00d9a16e9.
- Q: Which open issue count is correct? A: Comment 5 corrects the count to 133. The live count on 2026-11-26 is 166 (R-10).

### Session 2026-11-26

- Q: Does the handoff match GitHub main? A: No. Seven PRs are open (R-12). Issue 4867 is closed (R-09). Issue 4762 is open (R-08).
- Q: Does the feature pointer still hold the restored value? A: Yes. Blob b86bcad0 matches the pre-4846 value (R-33).
- Q: Which route applies to issue 4870? A: The numbered route is 0/0/1/2/3/4/4/0 (R-34, TST-19).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify the handoff against main (Priority: P1)

A maintainer checks each named claim of the handoff against GitHub main before any action. The maintainer records each claim as present, partial, stale, or absent.

**Why this priority**: Each later action depends on the current state. The handoff already changed after its snapshot.

**Independent Test**: Run TST-01 to TST-18 in design/quickstart.md. Compare each result with the remote table in design/research.md.

**Acceptance Scenarios**:

1. **Given** the 2026-11-21 snapshot, **When** the maintainer runs the open checks, **Then** the record shows 166 open issues and seven open PRs.
2. **Given** a stale claim, **When** the maintainer records it, **Then** the row states the current value and its source.

---

### User Story 2 - Apply routine decisions and isolate human decisions (Priority: P1)

A maintainer applies each routine decision and records its reason and risk. The maintainer sends the four human decisions to the user, one at a time.

**Why this priority**: Work stops while a decision is open. Human decisions need a separate list so that they do not block routine work.

**Independent Test**: Count the decisions in design/research.md and in the STATUS file. Confirm that exactly four decisions need a human.

**Acceptance Scenarios**:

1. **Given** decisions D-2, D-12, D-13, and D-14, **When** the summary is read, **Then** each human decision names its options and its recommended option.
2. **Given** a routine decision, **When** the record stores it, **Then** the record stores its alternatives, reason, and risk.

---

### User Story 3 - Triage the open backlog in order (Priority: P2)

A maintainer assigns one census category to each open issue. The maintainer starts with issues 4721 and 4722 in one branch. That branch keeps the existing rows of the device-event CSV.

**Why this priority**: The handoff names these issues as the next candidates. Triage makes the 166 open issues usable.

**Independent Test**: Count the open issues that have no category in the refreshed inventory. The count must be zero after triage.

**Acceptance Scenarios**:

1. **Given** issues 4721 and 4722, **When** the fix branch runs its tests, **Then** the resume test shows that existing rows remain (TST-33).
2. **Given** an open issue outside the inventory, **When** triage runs, **Then** the issue gets a category in the refreshed inventory.

---

### User Story 4 - Merge only through the serial procedure (Priority: P2)

A maintainer merges one PR at a time. Each merge follows handoff section 4 and decision D-9. A pip update follows handoff section 5.

**Why this priority**: The handoff asks for one merge at a time (section 3). The serial procedure keeps each merge checked before the next one starts.

**Independent Test**: For each merge, record the head SHA, the Quality Gates run on the previous main head, and the hold-phrase check result.

**Acceptance Scenarios**:

1. **Given** a PR body with the phrase "staging hold", **When** the hold-phrase check runs, **Then** the merge stops until a reviewer decides.
2. **Given** a Dependabot PR with a failing gate, **When** the maintainer reviews it, **Then** the PR waits without a merge.

---

### User Story 5 - Keep recovery work until review (Priority: P3)

A maintainer keeps each recovery branch and archive tag on origin until its review ends. This work deletes no ref.

**Why this priority**: The recovery branches hold unreviewed work. A deletion from the checkout cannot be undone.

**Independent Test**: Count the recovery refs and archive tags before and after the work. The counts stay equal until a review decision exists.

**Acceptance Scenarios**:

1. **Given** 63 recovery refs, **When** the review starts, **Then** the count stays 63 until a decision exists.
2. **Given** a local commit tip, **When** a local branch is removed, **Then** GitHub already holds that tip (TST-06).

## Edge Cases

- Main moves during the work: the maintainer runs TST-03, TST-04, and TST-05 again, and checks the head before each merge.
- GitHub returns HTTP 403 or 429: the maintainer waits 60 seconds and retries up to three times. A check that still fails is recorded as unverified.
- An issue closes or reopens during triage: the newest state from TST-15 wins, and the row changes.
- A hold phrase appears in ordinary text: a reviewer decides the match, and the merge waits.
- A recovery branch may duplicate merged work. The handoff says PR 4850 probably replaced the dialog branch. The branch stays unmerged until its review ends.
- A local-only claim cannot be checked from this checkout: the claim stays in the Unverified list.
- Quality Gates fails on main after a merge: no further merge starts until a new issue explains the failure.
- The Windows host fails a local guard (issues 4877, 4878, and 4917 report this): the local result is recorded, and the CI run decides.
- The spec-route helper changes again (issues 4873 and 4910 are open): TST-09 and TST-22 run again before the change PR.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST check each named issue, PR, commit, branch, and path against GitHub main before any action.
- **FR-002**: The record MUST state the open issue count, the open PR set, and each drift from the handoff. Each statement MUST carry its check date.
- **FR-003**: The record MUST treat the decision comment and its corrections as the current state. It MUST mark handoff sections 9, 11, 12, and 13 as superseded.
- **FR-004**: PR 4813 MUST stay a draft under the staging hold. No merge MUST occur until a human records staging acceptance.
- **FR-005**: PR 4208 MUST stay a draft until a human decides H-3. Its merge conflicts MUST be resolved on its own branch before any merge.
- **FR-006**: The feature pointer MUST keep the value of blob b86bcad0 unless a reviewed change names another feature.
- **FR-007**: The record MUST choose its route with Resolve-SpecFeaturePath. The record MUST NOT run create-new-feature.ps1 or change the feature pointer.
- **FR-008**: After task T027, the Python pins and the workflow uses lines MUST name the same devtools commit.
- **FR-009**: Each merge MUST follow the serial procedure of handoff section 4 and decision D-9.
- **FR-010**: Each pip update MUST follow handoff section 5. The update MUST refresh the lock, regenerate both exports, and match the uv pin.
- **FR-011**: No recovery branch and no archive tag MUST be merged or deleted until its owner reviews it and records a decision.
- **FR-012**: Each local commit tip named in the handoff MUST resolve on GitHub before any local branch or worktree is removed.
- **FR-013**: The triage MUST assign one census category to each open issue in the inventory and to each open issue outside it.
- **FR-014**: The first fix branch MUST cover issues 4721 and 4722 together. It MUST keep the existing rows of the device-event CSV.
- **FR-015**: The record MUST list each human decision with its options and its recommended option. The record MUST NOT decide a human decision.
- **FR-016**: No command MUST prune Podman volumes. A volume removal MUST name one test volume that the test naming rule created.
- **FR-017**: The record MUST NOT write a secret, token, or password value to any file, comment, or pull request.
- **FR-018**: Before each GitHub write, the operator MUST confirm that the login is jmorrison-juniper.
- **FR-019**: Each Markdown file in the record MUST pass the STE gate at a score of 80 or above.
- **FR-020**: The handoff body MUST change after each merge and each decision. Each decision MUST have a dated comment on issue 4870.
- **FR-021**: Each claim that the record cannot verify MUST appear in the Unverified list with its reason.
- **FR-022**: The change MUST add files only in the record folder and in one changelog fragment. It MUST NOT change the coordinator laptop.
- **FR-023**: The merge procedure MUST apply the hold phrases of decision D-9 as whole-word matches in each PR body.
- **FR-024**: The change MUST add one changelog fragment with one ### heading and one bullet. The bullet MUST name issue 4870.
- **FR-025**: Each directory in the record MUST hold five children or fewer. The route MUST use eight base-5 segments.

### Key Entities *(include if feature involves data)*

- **BacklogIssue**: A GitHub issue in the handoff. Natural key: the issue number. It carries a state and a census category.
- **PullRequest**: A GitHub pull request. Natural key: the PR number. It carries a draft flag, a merge state, and a head SHA.
- **RecoveryBranch**: A `recovery/` ref on origin. Natural key: the full ref name. It stays until its review ends.
- **ArchiveTag**: An `archive/` tag on origin. Natural key: the full tag name.
- **CommitTip**: A local branch tip named in the handoff. Natural key: the full 40-character SHA.
- **Decision**: A numbered choice with its alternatives, reason, and risk. Natural key: the decision ID.
- **HumanDecision**: A decision that needs the user. It is a subset of Decision.

The state transitions appear in design/data-model.md.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each claim that the handoff names has one row in the remote table. Each row has a result of present, partial, stale, or absent.
- **SC-002**: The remote table has 79 rows. The STATUS file and the summary report the same count.
- **SC-003**: The record reports the open issue count of GitHub on the day of the update. On 2026-11-26, the count is 166.
- **SC-004**: No merge occurs unless the Quality Gates run on the previous main head is green.
- **SC-005**: The record lists exactly four human decisions. No other decision stays undecided.
- **SC-006**: The count of recovery refs stays at 63 until each ref has a review decision.
- **SC-007**: The feature pointer blob stays at b86bcad0 after the change PR is merged.
- **SC-008**: The layout guard and the route contract test pass in task T-LOCAL-GATES.

## Assumptions

- GitHub main is the truth order for each code, configuration, and document claim.
- The user authority of 2026-11-21 covers every routine decision in this record.
- The coordinator laptop is outside this checkout. Its claims stay unverified until task T036 runs on that host.
- The label `chore` names the type, and the label `docs` names the scope.
- The `gh` CLI runs under the jmorrison-juniper account for this work.
- Local gates run on the implementer machine. The authoring session runs no gate.

## Out of Scope

- Fixing any inventory issue. Each fix is a separate issue and PR.
- Changing branch protection, required checks, or the merge queue. The owner approves each of these changes.
- Closing, labeling, or commenting on an issue during this authoring session.
- Merging or deleting a recovery branch or an archive tag.
- Cleaning the coordinator laptop, its worktrees, or its Podman volumes.
- The vmm-topology-automation repository and every other repository.
- Staging acceptance for PR 4813 and PR 4806.
- Correcting the mistapi floor in `.github/copilot-instructions.md`. That is a follow-up documentation change.
- Activating the merge queue that issue 3071 describes.
