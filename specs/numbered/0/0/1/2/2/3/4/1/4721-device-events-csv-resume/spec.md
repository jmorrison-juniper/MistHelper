# Feature Specification: Resumed 52-week device-event CSV export

**Feature Branch**: `fix/4721-device-events-csv-resume`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4721, "Runtime: resumed 52-week device-event CSV overwrites earlier rows". The record uses `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## User Scenarios & Testing *(mandatory)*

Menu 97 exports 52 weeks of device events to one CSV file. An interrupted export stores a checkpoint token. A resumed run must keep the rows that the earlier run wrote.

### User Story 1 - Keep earlier rows on a resumed run (Priority: P1)

An operator resumes an interrupted menu 97 export. The CSV file keeps every earlier row. The new rows follow the earlier rows.

**Why this priority**: Earlier rows exist only in the CSV file. Rows older than the 52-week window do not return on a later fetch.

**Independent Test**: Run one resumed export with one earlier row and one checkpoint token. The CSV file must hold the earlier row and the new rows.

**Acceptance Scenarios**:

1. **Given** a matching CSV file and a checkpoint token, **When** menu 97 resumes, **Then** the earlier rows stay and the new rows follow.
2. **Given** a resumed run that finishes, **When** the run ends, **Then** the checkpoint file is removed.

---

### User Story 2 - Stop before any write when the checkpoint is unreadable or empty (Priority: P1)

An operator starts an export while the checkpoint file cannot be read, or while it holds no token. The exporter must stop before it requests a page or writes a row.

**Why this priority**: An empty or unreadable checkpoint can hide a valid resume point. A fresh run then replaces the CSV file.

**Independent Test**: Start a run with an unreadable checkpoint file. Start a run with an empty checkpoint file and a CSV file. Both files must keep their bytes.

**Acceptance Scenarios**:

1. **Given** a checkpoint file the operating system denies, **When** the export starts, **Then** the exporter stops before any page request and keeps both files.
2. **Given** an empty checkpoint file and an existing CSV file, **When** the export starts, **Then** the exporter refuses the resume and keeps both files unchanged.
3. **Given** an empty checkpoint file and no CSV file, **When** the export starts, **Then** the exporter starts a fresh run.

---

### User Story 3 - Refuse a resume that does not match the CSV file (Priority: P2)

An operator resumes a run after the CSV file changed. The exporter must refuse when the CSV file is missing, when its header differs, or when its last row is partial.

**Why this priority**: Appending to a mismatched file mixes incompatible rows into one output.

**Independent Test**: Resume once for each mismatch. Each run must refuse and keep the CSV bytes.

**Acceptance Scenarios**:

1. **Given** a checkpoint token and no CSV file, **When** the export starts, **Then** the exporter refuses before any page request.
2. **Given** a CSV header that differs from the export fields, **When** the export starts, **Then** the exporter refuses and keeps the CSV bytes.
3. **Given** a CSV file whose last row lacks a line break, **When** the export starts, **Then** the exporter refuses and keeps the CSV bytes.

---

### User Story 4 - Keep the last good checkpoint when a checkpoint write fails (Priority: P2)

A checkpoint write fails during a run. The checkpoint file must keep the previous token.

**Why this priority**: The checkpoint file is the only resume point. An empty or partial token starts a fresh run that replaces the CSV file.

**Independent Test**: Force a failure when the temporary checkpoint file replaces the checkpoint file. The checkpoint file must keep the previous token.

**Acceptance Scenarios**:

1. **Given** a valid checkpoint token, **When** the replace step fails, **Then** the checkpoint keeps the previous token and logs one warning.
2. **Given** a checkpoint write, **When** the write runs, **Then** the live checkpoint file is never opened for writing.

---

### User Story 5 - Keep both files unchanged when a resumed run finds no new rows (Priority: P3)

A resumed run finds no rows after its checkpoint token. The run must keep both files and must log that no rows follow the checkpoint.

**Why this priority**: The current code logs a misleading "No device events found" message. An API failure can also return an empty page, so the checkpoint must survive for a later retry.

**Independent Test**: Resume with a checkpoint token and an empty API page. The CSV bytes and the checkpoint bytes must stay the same.

**Acceptance Scenarios**:

1. **Given** a checkpoint token, **When** the resumed page has no rows, **Then** the CSV bytes and the checkpoint bytes do not change.
2. **Given** the same run, **When** the run ends, **Then** no completion message is logged.

### Edge Cases

- A checkpoint file that holds only whitespace counts as empty.
- A zero-byte CSV file with a checkpoint token causes a header mismatch refusal.
- A failed checkpoint write after a CSV append repeats the last batch on the next resume. Caution: The CSV file then holds duplicate rows.
- A `.tmp` checkpoint file can remain after a failed write. The next successful write replaces it.
- Windows can block the replace step when another process holds the checkpoint file. The result matches a failed write.
- An API connection error or HTTP error can return an empty page. The exporter treats it as the end of data. Caution: A streaming run then logs completion and removes the checkpoint. This behavior is out of scope (finding A-19).
- The SQLite output format with an empty checkpoint file starts a fresh run, because SQLite writes are idempotent.
- A field that first appears after the preload window is dropped from the CSV file. This behavior exists before this change and is out of scope.
- A checkpoint from another organization can extend a CSV file from another run when the headers match. This behavior exists before this change and is out of scope.
- Warning: A fresh run replaces the CSV file. Copy the file before the run when its rows matter.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exporter MUST keep every earlier CSV row during a valid resumed run.
- **FR-002**: The exporter MUST refuse a resumed run before any page request when the CSV file is missing.
- **FR-003**: The exporter MUST refuse a resumed run when the CSV header differs from the export fields.
- **FR-004**: The exporter MUST refuse a resumed run when the last CSV row lacks a line break.
- **FR-005**: The exporter MUST stop before any page request when the checkpoint file cannot be read, and keep both files unchanged.
- **FR-006**: The exporter MUST refuse a resumed run when the checkpoint file is empty and the CSV file exists.
- **FR-007**: The exporter MUST write each checkpoint token through the temporary checkpoint file, so a failed write keeps the previous token.
- **FR-008**: The exporter MUST keep the CSV file and the checkpoint file unchanged when a resumed run finds no new rows. It MUST log that no rows follow the checkpoint.
- **FR-009**: Each refusal MUST log an error that names the CSV file and the reason.
- **FR-010**: The CSV file name, the checkpoint file name, and the checkpoint token format MUST NOT change.
- **FR-011**: The SQLite output path MUST NOT change in this feature.
- **FR-012**: Each touched block MUST log before and after each action. Each changed line MUST carry an inline comment.
- **FR-013**: The operator guide MUST describe the resume rules and the duplicate-row risk. The README MUST link to that section.
- **FR-014**: The change MUST add one changelog fragment named `issue-4721-device-events-csv-resume.md`.
- **FR-015**: The change MUST add no module, no directory, and no test file. New tests MUST go into the existing extended test module.

### Mist Cloud Transport Requirements

- The feature uses the mistapi method `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents`. The installed signature is in `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py`, line 259.
- The feature owns no transport. It adds no direct HTTP request and no WebSocket path.
- SDK endpoint parity: the installed signature accepts `device_type`, `limit`, `duration`, and `search_after`.
- Failure safety: tests N4 and N5 prove that a failed checkpoint write keeps the previous token.
- Secret redaction: the change adds no credential log. The checkpoint token is a pagination cursor. The existing resume log line prints it.

### Key Entities

- **CSV file**: `data\OrgDeviceEvents_52w.csv`. It holds one header and one row for each device event. It has no row key.
- **Checkpoint file**: `data\OrgDeviceEvents_52w.<org_id>.checkpoint`. It holds one checkpoint token as UTF-8 text.
- **Temporary checkpoint file**: `<checkpoint file>.tmp`. It exists during a checkpoint write, or after a failed write.
- **Checkpoint token**: The text in the checkpoint file. The exporter sends it as `search_after`.
- **Preload**: The first three pages of a run. The exporter builds the CSV header from these rows.
- **Refusal**: A stop before any write. The exporter logs an error and raises `RuntimeError`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the change, all seven planned tests pass. Before the change, tests N1, N4, N5, and N6 fail.
- **SC-002**: In each fixture scenario, the CSV file keeps every earlier row. The scenarios are a valid resume, an unreadable checkpoint, an empty checkpoint, and a zero-row resume.
- **SC-003**: Line coverage of `device_events_52w_exporter.py` stays at 99 percent or above.
- **SC-004**: Each applicable gate in T-LOCAL-GATES reports its expected result.
- **SC-005**: The pull request passes each required CI check. `main` receives one squash commit from the pull request.

## Assumptions

- The runtime uses Python 3.15 or newer. `pyproject.toml` requires it at line 23.
- The `next` value holds a cursor string. The live response form is unverified in this record. See `design\research.md`.
- One export run per organization runs at a time. The exporter has no lock.
- A fresh run may replace the CSV file. This behavior already exists, and the refusal message names it.
- The data directory accepts writes from the runtime account.

## Out of Scope

- SQLite identity and SQLite write status, tracked by issues #4723 and #4722.
- Redis identity, tracked by issue #4724.
- The broad exception handlers, tracked by issue #1794.
- Binding the checkpoint to an organization. A follow-up issue must track it.
- A backup copy before a fresh run. A follow-up issue must track it.
- Field drift after the preload window. A follow-up issue must track it.
- Any change to the CSV file name, the checkpoint file name, or the checkpoint token format.

## Clarifications

### Session 2026-11-26

- Q: Does PR #4834 close issue #4721? A: No. The PR uses `Refs #4721` and leaves the issue open.
- Q: Which file owns the repair? A: `src/operations/exporting/export/device_events_52w_exporter.py`, per the issue comment of 2026-11-09. PR #4834 changed it on 2026-11-19.
- Q: May the new test module live in `tests/unit/export/`? A: No. That folder has 55 children, and Principle I forbids a new child there.
- Q: What happens to the files when recovery is ambiguous? A: Both files keep their bytes, per the issue comment of 2026-11-09.
- Q: Does the stale ownership note block the repair? A: No. PR #4358 merged on 2026-11-13. The ownership note no longer applies.
- Q: Which menu does the repair cover? A: Menu 97, per the issue comment of 2026-11-09.
- Q: Can an API error end a streaming run as complete? A: Yes. The SDK returns error responses without an exception. The defect is out of scope (finding A-19). A follow-up issue must track it.
