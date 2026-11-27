# Feature Specification: WAN history replay safety

**Feature Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (the candidate branch of pull request #4208)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4793, "Runtime: duplicate API sample in WAN history refresh". A repeated completed-hour refresh can fail when the API returns a previously retained sample timestamp.

## Clarifications

### Session 2026-11-26

- Q: Which branch carries the repair? A: The candidate branch of pull request #4208. The repair exists only there, from commit d7a706d onward. Main holds no WAN history writer. Decision D-1.
- Q: What happens when a changed source value reaches an existing sample key? A: The whole write stops. Prior rows stay unchanged. The error names the source time. Decisions D-2 and D-6.
- Q: What happens when one API response gives two values for one metric and timestamp? A: The sample builder rejects the response before any write. Identical duplicates collapse to one sample. Decision D-3.
- Q: Does the Arango writer report success before its commit is confirmed? A: No. A commit result other than True raises an error. Decision D-4.
- Q: Does the portal show the conflict text to the operator? A: Not in this change. The generic 503 text stays. A follow-up issue adds the conflict text. Decision D-6.
- Q: Does this work need a live ArangoDB or a live Mist call? A: No. Tests use real SQLite under `tmp_path` and mocks. Decision D-7.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Refresh a selected port twice in one hour (Priority: P1)

An operator refreshes one selected port twice in the same completed hour. The second refresh completes with no error.

**Why this priority**: The defect stops the refresh. The operator then loses the port history for that hour.

**Independent Test**: Run `LiveService.refresh_port` twice with the same six API samples and real SQLite under `tmp_path`. Verify one stored row for each API sample.

**Acceptance Scenarios**:

1. **Given** a stored API sample, **When** a later refresh returns it, **Then** the refresh completes and the store keeps one row.
2. **Given** two refreshes with the same six API samples, **When** the samples are read, **Then** the read returns six API samples and no duplicate.
3. **Given** two refreshes at different collection times, **When** the samples are read, **Then** the two poll samples stay distinct.

---

### User Story 2 - Refuse changed source data (Priority: P1)

The tool receives a changed value for a stored sample. The write stops before any change. The prior history stays unchanged.

**Why this priority**: Append-only history protects past measurements. A silent replacement changes evidence that operators already read.

**Independent Test**: Store one sample. Write the same sample key with one changed raw field. Verify the error and the unchanged rows.

**Acceptance Scenarios**:

1. **Given** a stored API sample, **When** a write with the same key changes a raw field, **Then** the write raises ValueError and no row changes.
2. **Given** the same changed write, **When** the error text is read, **Then** the text names the source time of the sample.
3. **Given** the mocked Arango path, **When** the payload changes, **Then** the transaction aborts and no insert occurs.

---

### User Story 3 - Confirm each Arango write (Priority: P2)

A maintainer runs the Arango writer. The writer reports an error when the database does not confirm the commit. A failed rollback does not hide the original error.

**Why this priority**: The constitution forbids a success report before a verified durable write.

**Independent Test**: Mock a commit result of False and a rollback that raises OSError. Verify the error types and messages.

**Acceptance Scenarios**:

1. **Given** the commit returns False, **When** the writer runs, **Then** it raises ConnectionError.
2. **Given** a write error and a failing rollback, **When** the writer runs, **Then** it raises the original write error.

---

### User Story 4 - Reject conflicting duplicates in one API response (Priority: P2)

An API response gives two different values for one metric and timestamp. The sample builder rejects the response. Two equal values produce one sample.

**Why this priority**: A silent overwrite hides a changed source value. The issue requires an explicit report.

**Independent Test**: Build samples from a response with two different values and from a response with two equal values.

**Acceptance Scenarios**:

1. **Given** two different values for one metric and timestamp, **When** the samples are built, **Then** the builder raises ValueError before any write.
2. **Given** two equal values for one metric and timestamp, **When** the samples are built, **Then** the builder returns one sample.

---

### Edge Cases

- The same identity and source time with a different collection time is a replay. The store keeps the first row.
- A batch with two identical samples for one key stores one row.
- A batch with two different samples for one key stops before any write.
- A poll sample with an equal payload at the same collection time stores one row.
- A failed rollback after a failed write raises the original write error.
- An empty sample batch writes no sample row and raises no error.
- A missing SQLite file stays missing. The writer does not create it.

## Requirements *(mandatory)*

### Functional Requirements

Replay and key rules:

- **FR-001**: The SQLite writer MUST accept an unchanged repeated API sample and store one row for its key.
- **FR-002**: The Arango writer MUST accept an unchanged repeated API sample and insert no second document for its key.
- **FR-003**: A batch MUST collapse identical samples with one key to one sample before any write.
- **FR-005**: The sample key MUST use the identity and the source time. The source comparison MUST ignore the collection time.
- **FR-006**: Each stored sample MUST keep its source time and its collection time in separate fields.

Changed data and commit rules:

- **FR-004**: A changed source payload at an existing key MUST stop the whole write and keep prior rows unchanged.
- **FR-007**: The Arango writer MUST raise an error when the transaction commit result is not True.
- **FR-008**: The Arango writer MUST keep the original write error when the rollback fails.
- **FR-013**: The error for a changed source payload MUST name the source time of the sample.

Response and refresh rules:

- **FR-009**: One API response MUST NOT give two different values for one metric and timestamp. The sample builder MUST reject such a response before any write.
- **FR-010**: A selected-port refresh that receives the same API samples twice MUST store each API sample once. Each poll sample MUST stay distinct.
- **FR-011**: Hourly records MUST keep the existing replacement rule.
- **FR-012**: The change MUST add no Mist request. The fixed refresh path MUST stay unchanged.
- **FR-014**: `documentation/wan-performance.md` and `changelog.d/pr-4208.md` MUST state the rules in FR-004, FR-007, and FR-009.

### Mist Cloud Transport Requirements

Not applicable. This change adds no Mist REST request and no WebSocket transport. FR-012 keeps the fixed refresh path. The only collector call site is `GatewayInsights.collect_for_port`, which this change does not edit.

### Key Entities

- **SampleMeasurement**: One raw measurement with identity, source time, collection time, metrics, raw fields, and timestamp source.
- **Sample key**: The identity natural key plus the source time in UTC.
- **Hourly record**: One projection for each identity and UTC hour. Each write replaces it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tests N1 to N4 fail before Phase 3 of `tasks.md` and pass after Phase 3. Tests N5 to N7 guard existing behavior, so they pass before and after Phase 3.
- **SC-002**: The three changed test modules pass in full with no failing test.
- **SC-003**: Each applicable local gate reports its expected result for the changed files.
- **SC-004**: After merge, `main` holds the changed files, and issue #4793 closes.
- **SC-005**: The structure guard for `specs/numbered` reports no new direct child in a noncompliant folder.

## Assumptions

- The candidate branch head stays at `843be63bc837513b4442dae69da9f0db922e0ed1` until implementation starts.
- The pinned `python-arango==8.3.7` returns a boolean from `commit_transaction`. Evidence: rows RC-28 and RC-63 in `design/research.md`.
- The SQLite file exists before the first write. The writer does not create it.
- The owner keeps PR #4208 as the carrier of this repair. Decision D-8 covers the publication step.
- Live API data has no measured rate of changed source values. This spec does not assume one.

Caution: a force push moves the candidate branch head. Confirm the head SHA again after each push.

## Out of Scope

- The operator-visible conflict text in the portal. Decision D-6 defers it.
- A live ArangoDB test or a live Mist test. Decision D-7 excludes both.
- Changes to hourly summary calculations or to summary weighting.
- Remediation of existing structure debt. `plan.md` records each debt item.
- Issues #4794 and #4795. Each issue has its own record.
- Publication of PR #4208 to `main`. Decision D-8 requires owner approval.
