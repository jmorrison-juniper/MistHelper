# Feature Specification: Mixed WAN History Summaries

**Feature Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (candidate branch for this repair, see D-1)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4794: Runtime: missing flap_count in mixed WAN history summaries. A period that mixes complete hours and snapshot hours raises KeyError in the link-event summary.

## Clarifications

### Session 2026-11-26

- Q: Does GitHub main hold the defective code? A: No. Main has no `summary.py` and no WAN calendar test. The candidate branch holds both. See design/research.md, remote checks 37 to 39.
- Q: Does the repair commit close the issue? A: No. The issue stays open until the repair reaches main, as the issue comment of 2026-11-13 states.
- Q: Does the reproduction commit exist? A: No. Commit 15c69b11, which the issue cites, returns HTTP 422 on GitHub.
- Q: Which branch holds the repair? A: The candidate head 843be63 contains repair commit d7a706d as an ancestor.
- Q: Does the repair start a new branch from main? A: No. Main lacks the module, and AGENTS.md forbids branching from a feature branch.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a mixed history without a failure (Priority: P1)

An operator opens a WAN port detail page. The port history holds snapshot hours from ordinary polls and complete hours from a selected-port refresh. The page loads, and the event totals use complete hours only.

**Why this priority**: The current code stops with KeyError for this history. The operator then loses the history view for the port.

**Independent Test**: Build summaries from one complete hour and one snapshot hour for one identity. Each summary returns, and each event total matches the complete hour.

**Acceptance Scenarios**:

1. **Given** one complete hour and one snapshot hour, **When** the summaries build, **Then** no exception occurs.
2. **Given** the same records, **When** the daily summary reads, **Then** complete hours is 1 and up minutes is 60.
3. **Given** the same records, **When** the weekly, monthly, and rolling summaries read, **Then** each reports complete hours 1 and known hours 1.

---

### User Story 2 - Keep missing evidence unknown (Priority: P1)

An operator reviews a period with incomplete event evidence, or with a known zero flap count. The page shows Unknown for each total that the evidence does not measure. The page never shows a healthy zero.

**Why this priority**: A false zero hides a link problem from the operator.

**Independent Test**: Build summaries from incomplete event hours, and from one complete hour with a zero flap count and no duration metrics.

**Acceptance Scenarios**:

1. **Given** incomplete event hours only, **When** the daily summary reads, **Then** complete hours is 0, and each total is unknown.
2. **Given** a complete hour with zero flaps and no duration, **When** the daily summary reads, **Then** flaps is 0 and minutes are unknown.
3. **Given** snapshot hours only, **When** the summaries build, **Then** the link-event summary is absent.

---

### User Story 3 - Show Unknown in the live portal block (Priority: P2)

An operator opens the live port page for a period with incomplete event evidence. The link-event block shows Unknown for each unmeasured value.

**Why this priority**: The portal shows the same evidence to the operator, so the text must match the summary.

**Independent Test**: Render the live port page with unmeasured event metrics, and read the block text.

**Acceptance Scenarios**:

1. **Given** unmeasured event metrics, **When** the live port page renders, **Then** the page shows "Known state duration: Unknown." and "Matching transitions: Unknown."

### Edge Cases

- A period with no matching records returns no link-event summary. Existing test: `test_summary_without_matching_records_is_empty`.
- A complete hour with up minutes and no down minutes counts as complete but not known. Its flap count still counts. Observed up percent stays unknown.
- A known hour with 0 up minutes and 0 down minutes gives no observed up percent.
- A rolling window with snapshot hours only returns no link-event summary, while another window in the same build can return one.
- Records for two identities in one call: only the selected identity contributes to a summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The summary builder MUST NOT raise an error for a period that mixes complete hours and snapshot hours.
- **FR-002**: Event totals MUST sum only complete hours and known minutes.
- **FR-003**: A snapshot hour MUST NOT add zero flaps or zero minutes.
- **FR-004**: Complete, known, and expected hour counts MUST describe the evidence in the period.
- **FR-005**: A period with no flap evidence MUST report no link-event summary.
- **FR-006**: An incomplete event hour MUST leave each total unknown, not zero.
- **FR-007**: A known zero flap count MUST leave duration totals unknown when duration is unmeasured.
- **FR-008**: Each period kind MUST follow FR-001 to FR-007.
- **FR-009**: The live portal block MUST render each unknown total as Unknown and MUST NOT fail.
- **FR-010**: The mixed-hour, missing-evidence, and known-zero tests MUST fail on the parent commit and pass on the repaired head.
- **FR-011**: Each changed block MUST carry inline comments and action logging, as Principles VI and VII require.
- **FR-012**: The issue MUST stay open until the repair reaches main, and the PR MUST close it by a closing keyword.

### Mist Cloud Transport Requirements

- The repair adds no Mist REST call. It keeps the existing mistapi method `searchOrgDeviceEvents`, which `snapshot_client.py` calls at line 468.
- The repair owns no WebSocket transport, so SDK insufficiency tests do not apply.
- The repair changes no SDK call, so SDK endpoint parity tests keep their current scope.

### Key Entities

- **Complete hour**: An hour whose `flap_count` metric has a measured value. It increases the complete hour count.
- **Incomplete event hour**: An hour whose `flap_count` metric exists with no value. It adds no totals.
- **Snapshot hour**: An hour with no `flap_count` metric. It adds no event evidence.
- **Link-event summary**: The `LinkEventSummary` value for one period. It is absent when no hour in the period has a `flap_count` metric.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The five-step reproduction in the issue returns one complete hour, 60 known up minutes, zero flaps, 24 expected hours, and no exception.
- **SC-002**: The three regression tests fail on parent commit 07b7751 and pass on the repaired head.
- **SC-003**: Each applicable gate in the local gates table reports its expected result for the changed files.
- **SC-004**: The remote CI run for the repaired head reports no failed required check.
- **SC-005**: After the merge, a remote read of main returns `summary.py` with the None-safe event code.

## Assumptions

- **A-1**: The candidate branch remains the repair base. Its head is `843be63bc837513b4442dae69da9f0db922e0ed1` at research time.
- **A-2**: The snapshot premise holds. `snapshot_records.py` names `flap_count` only in the gateway insight set (remote check 72).
- **A-3**: The issue expected behavior is the target. Event totals use measured minutes and measured flaps only.
- **A-4**: Tests run on Python 3.15.2 in a worktree venv, as `.github/copilot-instructions.md` lines 25 to 29 describe.
- **A-5**: The portal assertion strings in `live.html` remain unchanged.

## Out of Scope

- Changing the history store, duplicate-sample handling, or gateway history visibility. Issues 4793 and 4795 cover those concerns.
- Splitting PR 4208 or closing issue 4200.
- Changing the mistapi pin or any Mist API call.
- Changing `_has_events` to a measured-value check. See D-3.
- Publishing PR 4208 to main. See D-5.
- Fixing the mistapi version wording drift. See D-11.
