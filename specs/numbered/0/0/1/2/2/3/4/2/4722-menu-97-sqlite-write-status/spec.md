# Feature Specification: Menu 97 SQLite Write Status

**Feature Branch**: `fix/4722-sqlite-partial-batch` (planned)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4722, "Runtime: menu 97 reports SQLite success after a failed write". The evidence snapshot is remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Clarifications

### Session 2026-11-26

- Q: Does remote main already stop on a False SQLite result? A: Yes. PR #4834 merged on 2026-11-19 and added the first-batch and later-batch guards. Issue #4722 stays open because the partial batch is not fixed.
- Q: Does a partial batch count as a failed write? A: Yes. Issue comment IC_kwDOQltU8c8AAAABkoggfg states that a False check does not detect a partial batch. Menu 97 must not report success for it.
- Q: Does this record include the CSV resume defect? A: No. Issue #4721 owns the CSV resume path. PR #4834 also changed that path.
- Q: Does this record include the timestamp-only key collapse? A: No. Issue #4723 owns the key defect.
- Q: Does the default writer result change for other callers? A: No. Callers that do not request a full batch keep the result from issue #3350. A partial batch still returns True for them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop on a failed SQLite batch (Priority: P1)

Menu 97 stops and keeps its checkpoint when the SQLite writer returns False. The operator sees no completion message. Remote main already does this. This record keeps the behavior under regression tests.

**Why this priority**: A false success message hides a failed export from the operator.

**Independent Test**: Read the first-batch and later-batch SQLite tests in `tests/unit/test_device_events_52w_exporter_extended.py`. Both tests exist on remote main. PR #4834 CI reported success before its merge.

**Acceptance Scenarios**:

1. **Given** the SQLite writer returns False for the first batch, **When** the export runs, **Then** it raises RuntimeError and logs no completion message.
2. **Given** the SQLite writer returns False for a later batch, **When** the export runs, **Then** the checkpoint keeps the last saved continuation token.

**Status**: verified present on remote main.

---

### User Story 2 - Stop on a partial SQLite batch (Priority: P1)

A partial batch stores some rows and rejects others. The writer returns True today. The exporter then removes the checkpoint and logs completion. The operator cannot see the rejected rows. A full-batch request makes a batch with any rejected row fail.

**Why this priority**: This is the open defect in issue #4722.

**Independent Test**: In the extended exporter test module, the real SQLite writer rejects one row of a later batch. The export raises RuntimeError and keeps the checkpoint (TC-10).

**Acceptance Scenarios**:

1. **Given** a later batch has one rejected row, **When** the export runs with a full-batch request, **Then** it raises RuntimeError.
2. **Given** the same rejected batch, **When** the export stops, **Then** the checkpoint keeps its token and the table holds no row of the batch.
3. **Given** a later batch with no rejected row, **When** the export runs, **Then** the export completes and removes the checkpoint (TC-11).

**Status**: absent on remote main.

---

### User Story 3 - Keep other SQLite callers unchanged (Priority: P2)

Other menus write SQLite without a full-batch request. Their result must not change.

**Why this priority**: A change to the default writer result would affect every SQLite export.

**Independent Test**: The existing writer test `test_partial_failure_logs_one_summary_line_and_returns_true` passes with no edit.

**Acceptance Scenarios**:

1. **Given** a writer call without the flag and a partial batch, **When** the write runs, **Then** the writer returns True and logs one summary line.
2. **Given** a CSV write with the flag set, **When** the write runs, **Then** the CSV output matches the output without the flag.

**Status**: verified present on remote main. Keep it.

### Edge Cases

- A batch with zero rows returns True and writes nothing. The existing commit path handles it.
- A batch where every row is rejected returns False with or without the flag. The existing zero-insert path handles it.
- A partial batch on the first batch of a fresh run stops before any checkpoint write. No checkpoint exists yet.
- A checkpoint write failure after a stored batch logs a warning. The export continues. The existing non-fatal path handles it.
- The polyglot mirror can hold rows from a discarded SQLite batch. The next successful run sends the same rows again. Its upsert behavior is unverified (research U-6).
- A writer exception returns False and logs an error. The DataExporter helper keeps this behavior.
- A duplicate key replaces an earlier row without an error. The writer counts that row as stored. Issue #4723 owns this case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exporter MUST raise an error and stop when the first SQLite batch returns False. Status: verified present.
- **FR-002**: The exporter MUST stop and keep the checkpoint file bytes when a later SQLite batch returns False. Status: verified present.
- **FR-003**: The exporter MUST NOT remove the checkpoint file or log completion after a failed SQLite batch. Status: verified present.
- **FR-004**: The SQLite writer MUST return False for a full-batch write when it rejects any row. Status: absent.
- **FR-005**: A full-batch write that returns False MUST leave no row of its batch in the table. Status: absent.
- **FR-006**: The exporter MUST request a full-batch write for every SQLite batch, first and later. Status: absent.
- **FR-007**: The SQLite writer MUST keep True for a partial batch when the caller does not request a full batch. Status: verified present. Keep it.
- **FR-008**: DataExporter MUST pass a full-batch request to the SQLite writer. It MUST return False with an error log when the writer raises. Status: absent.
- **FR-009**: CSV output and empty-result output MUST NOT change. Status: verified present. Keep it.
- **FR-010**: The change MUST add one release-note fragment under `changelog.d/` that names issue 4722 and uses an allowed file name. Status: absent.

### Mist Cloud Transport Requirements

- The feature uses one mistapi REST method, `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents`. The change keeps its arguments unchanged.
- The change adds no direct HTTP request and no owned WebSocket transport.
- Contract evidence: the existing test `test_fetch_kwargs_includes_search_after_when_token_present` covers the request arguments. TC-10 covers failure safety. TC-11 covers output. The change logs no credential.

### Key Entities

- **Checkpoint file**: `data/OrgDeviceEvents_52w.<org_id>.checkpoint`. It holds one continuation token for one organization. The exporter writes it after each stored batch and removes it after completion.
- **Continuation token**: The text value that the next page request uses. The exporter passes it as `search_after`.
- **Batch**: The rows from one page, or from the preload pages, that the exporter writes in one SQLite call.
- **Row rejection**: One row that the SQLite writer cannot insert. The writer logs the row and counts it as failed.
- **Partial batch**: A batch with at least one row rejection and at least one stored row.
- **Failed batch**: A batch with no stored row.
- **Full-batch write**: A SQLite write that sets `require_full_batch`. It returns False for a partial batch and for a failed batch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All eleven planned tests, TC-01 through TC-11, pass after the change. Each new test fails before the change.
- **SC-002**: After a rejected later batch, the checkpoint file bytes equal the bytes before that batch.
- **SC-003**: After a rejected full-batch write, the table row count equals the row count before that batch.
- **SC-004**: The existing writer test for the default partial result passes with no edit.
- **SC-005**: Each applicable local gate exits 0. The run records the count for each gate.
- **SC-006**: Every required check passes on the pull request. Merging the pull request closes issue 4722.

## Assumptions

- The pinned mistapi version is 0.64.1. The local package metadata shows this version.
- The Mist API keeps the parameter and response shapes in the local OpenAPI file.
- The polyglot mirror does not decide the export result. The existing code returns the SQLite result only.
- One agent edits `src/operations/exporting/export/data_exporter.py` at a time.
- The owner runs the serial merge process.

## Non-Goals

- CSV resume and CSV overwrite behavior. Issue #4721 owns them.
- Duplicate key collapse in SQLite. Issue #4723 owns it.
- The default writer contract for callers that do not request a full batch. Issue #3350 owns it.
- The format of the `next` value from the Mist API. Analysis item A-8 records it.
- The polyglot mirror result. This record keeps the current behavior.
- New menus, registry changes, and documentation for menu 97 write behavior.
