# Feature Specification: Main workflow recovery

**Feature Branch**: `docs/4763-post-merge-consumer`

**Created**: 2026-11-26

**Status**: Draft. The recovery code is on `main`. Hosted acceptance for the delayed path remains open.

**Input**: Issue #4763, reopened on 2026-11-16. Each merge to `main` must start the main workflows.

**Record route**: `specs\numbered\0\0\1\2\3\0\2\3\4763-post-merge-consumer`

## Glossary

Each term names one concept. Use each term only as defined here.

- **Token merge**: A merge that the workflow token performs. The merging account is `app/github-actions`.
- **Tip**: The commit at the head of `main`.
- **Enable step**: The step `Enable auto-merge` in the job `enable-auto-merge` of the shared workflow.
- **Confirmed merge**: The enable step logs `Verified pull request N: merged.` and sets `merged=true`.
- **Pending request**: The enable step logs `Verified pull request N: enabled.` and sets no merged output.
- **Dispatch job**: The job `dispatch-main-workflows`. It starts each main workflow that lacks tip coverage.
- **Recovery**: The start of each missing main workflow by the dispatch job.
- **Main workflows**: The files `ci.yml`, `codeql.yml`, `container-build.yml`, and `ste-lint.yml`.
- **Immediate path**: A confirmed merge in a labeled run. The dispatch job runs in the same run.
- **Delayed path**: A pending request followed by a later merge. A closed run or a scheduled run starts recovery.
- **Merged-close path**: A closed and merged event run. The dispatch job runs in that run.
- **Scheduled path**: A run from the six-hour schedule. The dispatch job checks tip coverage.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Main workflows start after an immediate token merge (Priority: P1)

A maintainer labels a pull request whose checks already pass. The token merges it. The same run starts each main workflow that lacks tip coverage. The gates then examine the merge commit.

**Why this priority**: Without this path, the quality gates and the container image describe an older commit.

**Independent Test**: Open the labeled run. Confirm one `Verified pull request N: merged.` line and four `Started` lines for the merge commit.

**Acceptance Scenarios**:

1. **Given** a labeled pull request that passes its checks, **When** the enable step merges it, **Then** the dispatch job starts main workflows lacking tip coverage.
2. **Given** a main workflow that already covers the tip, **When** the dispatch job checks the tip, **Then** the job starts no duplicate run.

**Status**: Verified on eight merges (RC-56 to RC-63).

---

### User Story 2 - A pending request does not count as a merge (Priority: P1)

A labeled pull request has checks that still run. The enable step records a pending request. The dispatch job waits for a later confirmed merge, a closed event, or a scheduled run.

**Why this priority**: Recovery that starts before the merge repeats runs or checks the wrong commit.

**Independent Test**: Open the labeled run. Confirm `enabled` in the log and a skipped dispatch job. Then confirm recovery for the later merge commit.

**Acceptance Scenarios**:

1. **Given** a pending request, **When** the labeled run ends, **Then** the dispatch job reports skipped.
2. **Given** the later merge, **When** a closed run or a scheduled run starts, **Then** each main workflow covers the merge commit within six hours.

**Status**: Open. The surveyed runs show no pending request (RC-68).

---

### User Story 3 - Merged-close and scheduled recovery remain available (Priority: P2)

A human merge starts a closed run. A scheduled run repairs a tip that no event covered.

**Why this priority**: A human merge and a missed event need the same repair path.

**Independent Test**: Open the closed run for a human merge. Open one scheduled run and read its coverage lines.

**Acceptance Scenarios**:

1. **Given** a closed and merged pull request, **When** its closed run starts, **Then** the dispatch job runs for that merge.
2. **Given** a scheduled run, **When** the tip has coverage, **Then** the job logs the coverage and starts nothing.

**Status**: Partial. RC-49 and RC-64 verify the merged-close path. The scheduled path checks coverage (RC-65). No scheduled run started a workflow in the surveyed window (RC-67).

---

### User Story 4 - A workflow-file change needs a manual merge (Priority: P3)

The workflow token cannot write a workflow file. The guard step blocks a token merge of such a pull request and posts a notice.

**Independent Test**: Open the labeled run for a pull request that edits `.github/workflows/`. Confirm the block message.

**Acceptance Scenarios**:

1. **Given** a labeled workflow-file pull request, **When** the enable step runs, **Then** the step reports the block, posts the notice, and merges nothing.

**Status**: Verified (RC-27, RC-54, RC-55).

### Edge Cases

- A canceled run starts no recovery. The dispatch job uses `!cancelled()` (RC-30).
- A closed pull request that did not merge starts no recovery (RC-29).
- The tip can move before a check runs. The job checks the tip at check time, so an older run proves nothing (RC-31).
- A failed tip lookup stops the job before any start (RC-31).
- A failed start call stops the job after the merge. The merge stays complete (RC-34).
- A failed enable step skips the dispatch job for that run. Later recovery depends on the closed path or the scheduled path.
- A pending request whose later merge starts no closed run waits up to six hours for the schedule (RC-05).
- `wiki-publish.yml` does not join the main workflows. Its daily schedule covers the wiki (D-4).

Caution: A test-only merge adds a commit to `main`. Revert that commit with a new pull request.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The consumer workflow must pin the upstream commit `d63a120487cecf750184cb178387cdc25c0a7635`. (RC-01, RC-08)
- **FR-002**: The consumer workflow must list `ci.yml`, `codeql.yml`, `container-build.yml`, and `ste-lint.yml`. (RC-02, RC-09)
- **FR-003**: The consumer workflow must keep its triggers, permissions, and close job. (RC-03 to RC-07)
- **FR-004**: The dispatch job must start only after a confirmed merge, a closed merged event, a scheduled run, or a manual start. (RC-28, RC-29)
- **FR-005**: A pending request must not count as a confirmed merge. (RC-26, RC-28)
- **FR-006**: Each start must check the current tip first. It must start nothing when the tip has coverage. (RC-31, RC-32)
- **FR-007**: The guard test must pin the same commit and the same four workflows as the consumer workflow. (RC-08, RC-09)
- **FR-008**: Each main workflow must accept a manual start and a push to `main`. (RC-36 to RC-39)
- **FR-009**: Acceptance evidence must use ordinary merges only. A test-only merge or a manual start of a main workflow does not count. (RC-93)
- **FR-010**: Issue #4763 must stay open until the immediate path and the delayed path both have evidence. (RC-93, RC-94)
- **FR-011**: A pull request that edits `.github/workflows/` must not depend on a token merge. (RC-27, RC-54)
- **FR-012**: `wiki-publish.yml` must stay out of the main-workflow list. This record must state the reason. (RC-40, RC-41, RC-42)

### Mist Cloud Transport Requirements

Not applicable. This feature calls no Mist REST endpoint and no mistapi method.

### Key Entities

- **Merge attempt**: One enable run for one pull request. Natural key: run ID and pull request number.
- **Main workflow**: One workflow file that the dispatch job may start. Natural key: file name.
- **Tip coverage**: One workflow run whose head commit equals the tip. Natural key: tip commit and file name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Eight immediate-path merges between 2026-11-20 and 2026-11-26 each log one confirmed merge and four start lines (RC-56 to RC-63).
- **SC-002**: One merged-close run covers or starts the four main workflows for its merge commit (RC-49).
- **SC-003**: One delayed-path merge logs a pending request and no dispatch at the labeled run. Later recovery covers the merge commit within six hours.
- **SC-004**: The three guard test files pass at the record branch head. The orchestrator records the pytest summary line.
- **SC-005**: Issue #4763 closes only after SC-003 passes and the orchestrator approves the closure.

## Assumptions

- **A-1**: GitHub starts no run from an event that the workflow token causes. The exceptions are `workflow_dispatch` and `repository_dispatch`. The shared workflow header states this rule (RC-23). Hosted data matches it (RC-51, RC-52).
- **A-2**: The `auto-merge` label is the approval step for an ordinary merge. AGENTS.md requires the label after green checks (RC-72).
- **A-3**: A closed run may or may not start for a merge that completes a pending request. The delayed-path evidence decides this question.
- **A-4**: The schedule runs every six hours (RC-05).

## Clarifications

### Session 2026-11-26

- **Q**: Does issue #4763 need a code change? **A**: No. The pin and the list match the reviewed shared revision and the four workflows (RC-01, RC-02, RC-47).
- **Q**: Does the main-workflow list include `wiki-publish.yml`? **A**: No. Decision D-4 records the reason.
- **Q**: Does the record pull request close issue #4763? **A**: No. Decision D-7 uses `Refs #4763`.
- **Q**: Do the eight immediate-path merges count as acceptance evidence? **A**: Yes, for the immediate path. Decision D-5 records the reason. The delayed path stays open.
- **Q**: Does the record reuse the legacy slug? **A**: Yes. Decision D-9 records the reason.
- **Q**: Does open pull request #4886 change the pin? **A**: It moves the pin to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Its guard check fails (RC-70, RC-71). Decision D-8 keeps `d63a120`.

## Out of Scope

- Changes to `misthelper-devtools`. The research table verifies the pinned revision. GitHub shows issue #86 as closed and pull request #87 as merged.
- A GitHub App token, a merge queue, or a removed guard (decisions D-1 and D-10).
- Changes to the close-job pin, the STE pin, or the wiki publish schedule.
- Live test merges, manual starts of main workflows, and branch protection changes.
- Changes to `auto-merge.yml`, its guard test, or its changelog fragment in this change.
