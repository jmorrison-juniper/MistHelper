# Feature Specification: Rejected Child Counts

**Feature Branch**: `jmorrison-juniper-rejected-child-outcome-counts`

**Created**: 2026-10-02

**Status**: Implemented locally. Publication is not authorized.

**Input**: Repair known refusal counts for issue #3329. Preserve uncertainty and prepare one unpublished, validated local commit.

**Issue**: [MistHelper #3329](https://github.com/jmorrison-juniper/MistHelper/issues/3329)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Known Failed Targets (Priority: P1)

An operator reads the progress of a multi-site upgrade operation.
One child has a known refusal or reports `not_submitted`.
A known refusal has `status=rejected` and HTTP 4xx `raw_status` evidence.
The operator needs its Failed count to show every explicit target that could not proceed.
A `not_submitted` child means that no upgrade write ran.
Neither outcome means that a device successfully upgraded.

**Why this priority**: A failed operation beside Failed 0 hides the affected targets and gives the operator conflicting information.

**Independent Test**: Read an operation with one known refusal and one explicit target.
The operation and child show Total 1, Upgraded 0, and Failed 1.
The child keeps its status and reason.

**Acceptance Scenarios**:

1. **Given** a known refusal with one explicit target, **When** the operator reads progress, **Then** its counts are Total 1, Upgraded 0, and Failed 1.
2. **Given** a `not_submitted` child with two explicit targets, **When** the operator reads progress, **Then** its counts are Total 2, Upgraded 0, and Failed 2.
3. **Given** both children in one operation, **When** the operator reads progress, **Then** the operation shows Total 3, Upgraded 0, and Failed 3.
4. **Given** either child, **When** the counts change, **Then** its status, reason, cancellation text, and device rows remain unchanged.
5. **Given** either child with an empty explicit target list, **When** the operator reads progress, **Then** all three counts remain zero.
6. **Given** either child with obsolete successful outcome evidence, **When** the operator reads progress, **Then** Upgraded remains zero.
   Failed equals its explicit target count without another contribution from that evidence.

---

### User Story 2 - Keep Genuine Outcomes and Uncertainty (Priority: P2)

An operator reads an operation with completed, rejected, active, or uncertain children.
The operator needs accurate totals without a false failure for an unknown outcome.
Existing cloud outcomes and proven completed outcomes must retain their counts.

**Why this priority**: A repair must not turn uncertainty into failure or erase a genuine upgrade result.

**Independent Test**: Read two completed targets beside one known refused target and two targets of a `not_submitted` child.
The operation shows Total 5, Upgraded 2, and Failed 3.
Each child contributes its counts once.

**Acceptance Scenarios**:

1. **Given** the mixed operation above, **When** the operator reads progress, **Then** the operation and child counts agree.
2. **Given** an active child with a genuine cloud failure, **When** the operator reads progress, **Then** that failure still counts.
3. **Given** three access points with two upgrades and one failure in nested site outcomes, **When** progress opens, **Then** their counts remain 3, 2, and 1.
4. **Given** a completed child with two targets and a proven postcheck, **When** progress opens, **Then** its existing proven counts remain 2, 2, and 0.
5. **Given** an uncertain child without failure evidence, **When** progress opens, **Then** uncertainty adds no failed targets.
6. **Given** a waiting, active, or cancelled child without failure evidence, **When** progress opens, **Then** its status adds no failed targets.
7. **Given** a proven completed child with a genuine failed target, **When** progress opens, **Then** the existing proof rule retains that failure.

---

### User Story 3 - See the Same Counts After Refresh (Priority: P3)

An operator opens the shipped progress page and selects Refresh status.
The operator needs the summary and each matching child row to retain the correct counts.
The refresh must not submit or change a firmware operation.

**Why this priority**: Correct internal counts do not help the operator if the page or refresh shows another value.

**Independent Test**: Open an owned operation with known failed targets in a real browser.
Read its summary and child rows before the refresh.
Select Refresh status and read them again after the status response.

**Acceptance Scenarios**:

1. **Given** a known refusal with one target, **When** the page first opens, **Then** the summary and matching child show Failed 1.
2. **Given** a `not_submitted` child with two targets, **When** the page first opens, **Then** the summary and matching child show Failed 2.
3. **Given** either page, **When** a real status refresh finishes, **Then** the response and page retain the same correct counts.
4. **Given** multiple children across sites and device families, **When** the page refreshes, **Then** the summary equals their combined counts.
   The child rows and device rows keep their original order.
5. **Given** the read-only journey, **When** the page opens and refreshes, **Then** no cloud call or firmware control action occurs.
6. **Given** a rejected or `not_submitted` child, **When** the page refreshes, **Then** the child keeps its status and reason.

### Edge Cases

- A known refusal with no explicit targets contributes zero targets, upgrades, and failures.
- Obsolete cloud lists cannot add successes or extra failures to a known refused or `not_submitted` child.
- A mixed operation retains counts from each child across several sites and device families.
- Nested site outcomes retain precedence over duplicate root outcomes.
- A completed child with a proven postcheck retains the existing rule for genuine failed targets.
- The statuses `unknown`, `submission_unknown`, and `read_unknown` do not themselves prove a failure.
- Waiting, active, and cancelled statuses do not themselves prove a failure.
- Genuine cloud failures remain visible for active or uncertain children.
- A refresh retains the reason, cancellation text, device content, and row order.
- An operation without children retains zero counts.
- A real HTTP 400 or HTTP 500 refresh error retains the last verified counts.
- A simulated SDK timeout or connection error retains durable counts without a real cloud call.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive each child outcome from its stored child status.
  An operation status must not replace that child status.
- **FR-002**: A `rejected` child with known HTTP 4xx refusal evidence MUST report every explicit target as failed.
  It must report zero upgraded targets.
  The legacy status word alone does not prove a refusal.
- **FR-003**: A `not_submitted` child MUST report every explicit target as failed and report zero upgraded targets.
  Its status continues to mean that no upgrade write ran.
- **FR-004**: The repair MUST leave each child's explicit target total unchanged.
  An empty explicit target list contributes three zero counts.
- **FR-005**: The system MUST count each child's outcomes once.
  Rejection counts must replace contradictory cloud counts rather than add to them.
- **FR-006**: The system MUST preserve genuine native cloud outcome counts for other child statuses.
- **FR-007**: The system MUST preserve counts from existing nested site outcomes.
  It must not count duplicate root outcomes again.
- **FR-008**: The system MUST preserve proven completed counts and their existing treatment of genuine failed targets.
- **FR-009**: The system MUST NOT infer failures from `unknown`, `submission_unknown`, or `read_unknown` alone.
- **FR-009a**: A legacy rejection with missing HTTP evidence, HTTP 5xx, or malformed HTTP 200 MUST retain its existing counts.
- **FR-010**: The system MUST NOT infer failures from waiting, active, or cancelled status alone.
- **FR-011**: The operation summary MUST equal the combined counts of its child rows.
- **FR-012**: The initial page and each completed status refresh MUST show the same counts for the same stored record.
- **FR-013**: The repair MUST preserve all status, reason, and cancellation text.
  It must preserve device rows, child rows, and their order.
- **FR-014**: The repair MUST change count reporting only.
  It must not change firmware decisions, submission, cancellation, retry, or reconciliation policy.
- **FR-015**: Acceptance proof MUST use owned records and make zero cloud calls.
  It must trigger zero startup/job actions and zero real plan, start, cancel, or retry callbacks.

### Key Entities *(include if feature involves data)*

- **Aggregate operation**: One multi-site upgrade operation with ordered child results and combined target counts.
- **Child result**: One planned device-family group with a status, explicit targets, reason, and existing outcome evidence.
- **Explicit target**: One device identity that contributes to the existing target total of a child.
- **Outcome evidence**: Existing root cloud lists, nested site lists, or a proven postcheck that determines counts for other statuses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A known refusal with one target reports exactly Total 1, Upgraded 0, and Failed 1.
- **SC-002**: A `not_submitted` child with two targets reports exactly Total 2, Upgraded 0, and Failed 2.
- **SC-003**: Two completed targets beside those three known failed targets report exactly Total 5, Upgraded 2, and Failed 3.
- **SC-004**: All acceptance records retain their genuine cloud counts, proven counts, text, device content, and row order.
- **SC-005**: All uncertainty and control cases add zero failures solely because of their status.
- **SC-006**: Every browser case shows matching summary and child counts before and after one real status refresh.
- **SC-007**: Every new read-only proof records zero cloud calls, startup/job actions, and real firmware control callbacks.
- **SC-008**: An operator can distinguish rejection from uncertainty through the existing status and reason.
  The operator needs no manual target count to understand a nonempty rejected child.
- **SC-009**: Proof reports positive checked-record and checked-row counts.
  A negative case rejects an observation that drops known failures while the uncertainty cases still pass.

## Assumptions

- Existing operation records contain the explicit target list that determines each child total.
- A `not_submitted` record proves that no upgrade write ran.
- A known refused or `not_submitted` child holds no valid successful cloud outcome.
- A known refusal uses the existing `OrgCancelLists.REFUSED_STATUSES` evidence.
  The parent explicitly confirmed this bounded interpretation.
- The literal issue text also names uncertain legacy rejected records.
  This repair intentionally preserves those counts and records `Part of #3329`, not `Closes #3329`.
- Existing completed proof and native cloud evidence remain authoritative for other child statuses.
- Existing ownership, authentication, storage, refresh, and display behavior remain unchanged.
- This request authorizes the reserved implementation, isolated tests, and one validated local commit.
  It does not authorize publication or a live operation.
- The coordinating parent controls later publication.
  A later phase requires its exact full verified-main SHA before publication.
