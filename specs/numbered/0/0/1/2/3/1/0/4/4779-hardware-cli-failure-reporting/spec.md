# Feature Specification: Hardware CLI failure reporting

**Issue**: #4779, "Runtime: hardware CLI hides programming errors and failure details"

**Feature Branch**: `feat/4773-transceiver-master-report`, the publication branch (decisions D-1 and D-2 in `design/research.md`)

**Record Folder**: `specs/numbered/0/0/1/2/3/1/0/4/4779-hardware-cli-failure-reporting`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 4779, the owner comment on issue 4773, and the local commits on branch `3999-transceiver-master-report`.

## Current State

The hardware CLI and its tests exist only in local commits. GitHub has no commit `8140bb37c` (research R-39). The CLI file is absent on `main` (research R-03).

The committed CLI catches `StreamRequestError`, `OSError`, and `RuntimeError` only. The clauses appear at `cli.py` lines 70 and 243. Static reading predicts that the three regression cases pass. No test ran during this specification step.

Three gaps remain. `NotImplementedError` and `RecursionError` are reported as operational failures, because both subclass `RuntimeError`. An uncertain admission logs `Admitted: False` and prints no caution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Programming errors stop the collection (Priority: P1)

An engineer runs the hardware CLI during development. A programming error stops the workflow with its original exception. The CLI does not return an incomplete result for that error.

**Why this priority**: A hidden programming error looks like a normal incomplete collection. The defect then reaches operators without a visible cause.

**Independent Test**: Run the CLI test module with a synthetic start request that raises a programming error. The test expects the same exception type and message.

**Acceptance Scenarios**:

1. **Given** the start request raises `TypeError`, **When** the CLI runs, **Then** the `TypeError` propagates and no incomplete result returns.
2. **Given** the start request raises `NotImplementedError` or `RecursionError`, **When** the CLI runs, **Then** the error propagates and the start request is sent once.
3. **Given** the summary request raises `NotImplementedError` during cancellation, **When** the CLI cancels, **Then** the error propagates.

---

### User Story 2 - Operational failures show a cause and an admission state (Priority: P1)

An operator sees the stable cause of an operational failure. The operator also sees whether the collection may exist on the server. The operator checks the portal before starting another collection.

**Why this priority**: A lost start reply can hide an admitted collection. A second start request can create a duplicate collection.

**Independent Test**: Use synthetic services that raise `OSError`, `RuntimeError`, or `KeyboardInterrupt` at each stage. The test checks the printed cause, the caution, and the single start request.

**Acceptance Scenarios**:

1. **Given** the start request raises `OSError`, **When** the CLI runs, **Then** it prints `Hardware collection failed (OSError).`, prints the uncertain-admission caution, and returns status `incomplete`.
2. **Given** the start reply has no session identifier, **When** the CLI runs, **Then** it prints cause `admission_unverified` and the uncertain-admission caution.
3. **Given** the summary request raises `OSError` after admission, **When** the CLI runs, **Then** it prints the admitted-collection caution and no durable directory.
4. **Given** an `OSError` occurs at the first prompt, **When** the CLI runs, **Then** it prints no caution and sends no start request.

---

### User Story 3 - Maintainer verifies the repair before publication (Priority: P2)

A maintainer verifies the repair on the publication branch before the pull request opens. The maintainer also confirms that GitHub holds each changed path.

**Why this priority**: The CLI is not on GitHub `main`. A local result does not prove a committed repair.

**Independent Test**: Read the remote tree after the push. Read the pull request body. Run the local gates on the publication branch.

**Acceptance Scenarios**:

1. **Given** the publication branch is pushed, **When** the maintainer reads the remote tree, **Then** each of the five changed files shows a blob SHA.
2. **Given** the pull request is open, **When** the maintainer reads its body, **Then** the body contains `Closes #4779` and `Refs #4773`.

### Edge Cases

- An interrupt before the start request creates no run and prints no caution.
- An interrupt during the start request leaves the admission state uncertain. The CLI returns status `cancelled` and prints the uncertain-admission caution.
- A start reply that is not a mapping counts as uncertain admission.
- A programming error inside cancellation propagates to the caller.
- A plain `RuntimeError` remains an operational failure.
- A `StreamRequestError` before admission prints its code and sends no start request.
- Log lines contain no session identifier, no raw exception text, and no operator answer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST propagate `TypeError` from the `run` and `cancel` boundaries. It MUST NOT return an incomplete result for it.
- **FR-002**: The CLI MUST treat `OSError`, `RuntimeError`, and `StreamRequestError` as operational failures. It MUST print the stable cause, which is the class name or the error code.
- **FR-003**: The CLI MUST propagate `NotImplementedError` and `RecursionError` from the `run` and `cancel` boundaries. Both classes signal programming errors.
- **FR-004**: The CLI MUST send the start request at most once for each collection. It MUST NOT retry after any failure.
- **FR-005**: The CLI MUST track the admission state as `not_started`, `uncertain`, or `admitted`. It MUST print the matching caution on each incomplete result for `uncertain` or `admitted`.
- **FR-006**: The CLI MUST log the admission state and the stable cause. It MUST NOT log raw exception text, session identifiers, or operator answers. It MUST log before and after each preview request and start request.
- **FR-007**: The CLI MUST NOT print an admission caution for a failure that occurs before the start request.
- **FR-008**: The CLI MUST treat a start reply that is not a mapping, or that lacks a non-empty string `session_id`, as uncertain admission. It MUST raise the operational code `admission_unverified`.
- **FR-009**: The publication MUST commit the repair on the publication branch before the pull request opens. The pull request body MUST contain `Closes #4779` and `Refs #4773`.
- **FR-010**: The operator guide CLI section and the #4773 changelog fragment MUST describe the caution texts and the stable causes.
- **FR-011**: Each statement that code exists on GitHub MUST cite a remote check. The publication MUST verify each changed path and its blob SHA after the push.

### Key Entities

- **Admission state**: The state of the start request. Its values are `not_started` (no start request sent), `uncertain` (start request sent, no verified reply), and `admitted` (verified reply with a session identifier).
- **Admitted parent**: The server-side parent that a verified start reply names. Its natural key is the `session_id` value.
- **Collection**: The operator workflow that sends one start request and waits for one admitted parent.
- **Operational failure**: A failure from I/O, a runtime condition, or a stable service code. The CLI prints the cause and returns an incomplete result.
- **Programming error**: A defect, such as `TypeError`, `NotImplementedError`, or `RecursionError`. The CLI propagates it.
- **Verified completion**: A terminal batch status that the CLI reads after its artifact metadata verifies. Only verified completion prints a durable directory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the publication branch, the selector `-k never_retries` runs the three existing cases, and each case passes.
- **SC-002**: All 10 new or changed pytest cases in `test_cli.py` pass. Plan.md and tasks.md list them.
- **SC-003**: The CLI file contains no `except Exception` clause and no `Admitted:` log text after the repair.
- **SC-004**: After the push, the remote tree shows the five changed files with blob SHAs.

## Assumptions

- The publication branch keeps the commits that the #4773 owner preserved. The repair starts from commit `8140bb37c` or from a later commit on that branch.
- No other agent pushes to the publication branch before T-PR.
- Unit tests use synthetic services. No live Mist cloud or lab device runs for this issue.
- The #4607 ownership request merged on 2026-11-13. Menu registration remains outside this issue.
- The `.venv` interpreter runs Python 3.15 on Windows 11.

## Out of Scope

- Numbered menu registration and changes to `MistHelper.py`.
- Broad catches in report publication on the branch. See follow-up F-2 in `analysis.md`.
- Stopping an admitted parent after an operational failure. See follow-up F-1.
- Malformed polling replies after admission. See follow-up F-3.
- Splitting the test module and the package for the five-children rule. See follow-up F-4.
- Live lab acceptance, README changes, and portal changes.

## Clarifications

### Session 2026-11-26

- Q: Is the CLI on GitHub `main`? A: No. Remote checks R-01, R-03, and R-04 return absent.
- Q: Does the committed CLI catch `Exception`? A: No. It catches `StreamRequestError`, `OSError`, and `RuntimeError` at `cli.py` lines 70 and 243.
- Q: Did the three regression cases fail on the committed code? A: Static reading predicts a pass. Task T001 runs the cases to confirm.
- Q: Which branch carries the repair? A: The #4773 publication branch. Decisions D-1 and D-2 record the reason.
- Q: Does this issue need live lab testing? A: No. Issue 4779 names unit cases only.
