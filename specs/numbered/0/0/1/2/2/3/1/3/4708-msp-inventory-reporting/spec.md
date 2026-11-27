# Feature Specification: MSP inventory batch coverage

**Feature Branch**: `fix/4708-msp-inventory-reporting`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Issue #4708. The MSP inventory batch reports skipped organizations as processed. Count successful results and label partial batches."

**Issue**: `jmorrison-juniper/MistHelper` #4708. The issue is open, with the labels `bug`, `tests`, and `in-progress`.

## Clarifications

### Session 2026-11-26

- Q: Does a complete batch change its output? A: No. A complete batch keeps its footer text, its `All Orgs` headings, and its export names.
- Q: Does a partial batch change its export names? A: Yes. Each export name gets the `_Partial` marker. Complete batches keep their names.
- Q: Does a successful result with empty device lists count as successful? A: Yes. The per-organization runner returned a result.
- Q: Does the owner-held publication decision block this specification? A: No. The specification proceeds. Push, pull request, and merge wait for owner authorization.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the exact batch coverage (Priority: P1)

The operator runs the MSP batch for every organization under one MSP. The footer shows how many organizations succeeded. It also shows how many organizations were skipped or failed.

**Why this priority**: A wrong count hides missing inventory from the operator.

**Independent Test**: Use mocked collaborators with three organization records. Read the footer and the console lines. No network call occurs.

**Acceptance Scenarios**:

1. **Given** three successful organization records, **When** the batch ends, **Then** the footer reads `MSP inventory summary complete. Processed 3 organizations.`
2. **Given** one successful record, one record without an ID, and one failing record, **When** the batch ends, **Then** the footer reads `MSP inventory summary partial. Processed 1 of 3 organizations. Skipped or failed: 2.`
3. **Given** a record without an ID, **When** the batch reaches it, **Then** the console prints the skipped line with the cause.
4. **Given** two records without an ID, **When** the batch ends, **Then** the footer reads `Processed 0 of 2 organizations. Skipped or failed: 2.` and no combined report is written.

### User Story 2 - Identify partial combined reports (Priority: P1)

After a partial batch, each combined report must show that it covers fewer organizations than the MSP returned. The heading and the export name both show this state.

**Why this priority**: An unqualified heading or export name claims full coverage for an incomplete report.

**Independent Test**: Use two successful records and one failing record. Read each heading and each export name that the test captures.

**Acceptance Scenarios**:

1. **Given** two successful records and one failure, **When** the combined reports are written, **Then** each heading contains `(Partial: 2 successful, 1 skipped or failed)`.
2. **Given** two successful records and one failure, **When** combined reports are written, **Then** each export name contains `_Partial`, and rows name only successful organizations.
3. **Given** three successful records, **When** the combined reports are written, **Then** each heading contains `(All Orgs)`, and no export name contains `_Partial`.

### User Story 3 - Continue the batch after an excluded record (Priority: P2)

A missing ID or a runner exception excludes one organization. The batch continues with each valid organization that follows it.

**Why this priority**: A stopped batch loses inventory for valid organizations.

**Independent Test**: Place a failing record before a valid record. Confirm that the runner receives both records.

**Acceptance Scenarios**:

1. **Given** a failing record before a valid record, **When** the batch runs, **Then** the runner receives both records.

### Edge Cases

- An empty organization list keeps the existing no-organizations message. No footer prints.
- A successful result with empty device lists counts as successful.
- One successful result does not meet the two-result threshold. No combined report is written.
- A failure before a success does not stop the later organization.
- A record with no `name` and no `id` prints `unnamed record` in its skipped line.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The batch MUST count successful per-organization results as the processed count.
- **FR-002**: The batch MUST count skipped or failed organizations as one number. A partial batch MUST NOT print a complete footer.
- **FR-003**: The console MUST print each skipped record with its position, its name or `unnamed record`, and its cause.
- **FR-004**: Each combined-report heading MUST show `(Partial: S successful, E skipped or failed)` for a partial batch. S is the successful count. E is the skipped or failed count.
- **FR-005**: A complete batch MUST keep its footer text, its `(All Orgs)` headings, its export names, its export fields, and its two-result threshold.
- **FR-006**: The batch MUST continue after a skipped record or a runner exception.
- **FR-007**: The tests MUST use mocked collaborators. The tests MUST block sockets and DNS lookups.
- **FR-008**: Each export name for a partial batch MUST contain `_Partial` before the export suffix. Each export row MUST come from a successful result.
- **FR-009**: The test module MUST assert the displayed pivot rows and the displayed TOTAL row.
- **FR-010**: The change MUST add one release note fragment named `issue-4708-msp-inventory-reporting.md`.
- **FR-011**: The repair MUST start from `main`. The legacy commits MUST serve as reference only. The record MUST NOT copy an unverified legacy claim.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The batch uses one mistapi REST method, `mistapi.api.v1.msps.orgs.listMspOrgs`. The change keeps this call and its arguments unchanged.
- The change adds no owned WebSocket transport. The SDK insufficiency contract tests do not apply.
- The change makes no direct HTTP request. Authentication and endpoint behavior come from the existing SDK session.

### Key Entities

- **Organization record**: One item from the MSP organization list. The batch reads `id` and `name`. A record without `id` is skipped.
- **Organization result**: The tuple that the per-organization runner returns. A returned tuple is a successful result. A raised exception is a failed result.
- **Batch coverage**: Two counts for one batch. The first count is the number of organization records. The second count is the number of successful results. The skipped or failed count, the partial flag, the heading label, and the file marker derive from these two counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each tested batch prints the exact successful count and the exact skipped or failed count.
- **SC-002**: Each partial batch heading and each partial export name shows the partial state.
- **SC-003**: Each complete batch keeps its footer, its `(All Orgs)` headings, and its unmarked export names.
- **SC-004**: Each export row of a partial batch names a successful organization. The export field order does not change.

## Non-Goals

- This specification does not change the `getSelf` refusal behavior. Issue #4713 owns that behavior.
- This specification does not change the umbrella issues #1794 and #2753.
- This specification does not change the single-organization path of menu 13, modes 1 and 2.
- This specification does not change the export schema, the API identifiers, or the write backend.
- This specification does not verify live organization paging. The analysis record names that gap as AN-10.
- This specification does not push, merge, or close anything on GitHub. Owner authorization controls each of those steps.

## Assumptions

- A per-organization runner that returns a tuple counts as successful, even when its device lists are empty.
- A batch with fewer than two successful results writes no combined report. The threshold stays unchanged.
- The pinned `mistapi` range `>=0.64.0,<0.65` stays in force. The local environment holds mistapi 0.64.1.
- The repository requires Python 3.15 or newer, as `pyproject.toml` states.
- Verification uses mocks only. No live Mist call, SSH call, firmware action, or database write occurs.
- The local commits `5b25a48e` and `eaae12d3` serve as reference only. The repair starts from `main`.
