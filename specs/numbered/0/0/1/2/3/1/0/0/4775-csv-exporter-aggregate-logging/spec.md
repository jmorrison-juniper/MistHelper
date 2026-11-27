# Feature Specification: Exported cell values stay out of DEBUG logs

**Feature Branch**: `fix/4775-csv-exporter-aggregate-logging`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4775. The shared CSV exporter writes cell values to DEBUG logs during row emission. A derived hardware report needs aggregate-only action logs. The issue asks for row and field counts in place of row content.

## Clarifications

### Session 2026-11-26

- Q: Does the change cover only the two locations that the issue names? A: No. It also covers the site device exporter and the sites by AP model exporter. Each logs the same kind of value at DEBUG. See D-1.
- Q: Does the shared writer log field names or only a count? A: Only a count. See D-3.
- Q: Does a parse failure keep a DEBUG line? A: Yes. The line names the error type and omits the address. See D-6.
- Q: Does the change start before pull request #4813 merges? A: No. Both changes edit `data_exporter.py` and its test file. See D-12.
- Q: Does the change remove the other DEBUG tables in the repository? A: No. Those tables sit outside the exporter package. See D-9.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The shared CSV writer logs counts only (Priority: P1)

An operator runs an export with `--debug`. The shared CSV writer writes every row. The DEBUG output names the row count and the field count. No cell value appears in the output or in `data/script.log`.

**Why this priority**: The shared writer serves the CSV exports, including the EX hardware inventory report. One leak here reaches each of those exports.

**Independent Test**: Write rows that hold synthetic marker values with DEBUG logging active. Capture the log. Verify that no marker value appears and that the count message appears.

**Acceptance Scenarios**:

1. **Given** marker values in the rows, **When** the writer runs at DEBUG, **Then** no marker value appears in the log.
2. **Given** the same rows, **When** the write ends, **Then** one DEBUG message names the row count and the field count.

---

### User Story 2 - The exported CSV keeps every cell value (Priority: P1)

An operator exports a CSV file. The file keeps each cell value in its column. The column order does not change.

**Why this priority**: The fix must not remove data from the export. Operators depend on the CSV content.

**Independent Test**: Write rows that hold synthetic marker values to a temporary CSV file. Read the file back. Verify the rows and the column order.

**Acceptance Scenarios**:

1. **Given** rows with marker values, **When** the writer writes the CSV, **Then** each value stays in its column.
2. **Given** a row that lacks one field, **When** the shared writer writes it, **Then** that cell holds an empty string.

---

### User Story 3 - Inventory exporters log no device values and no tables (Priority: P2)

An operator runs the organization inventory export or the site device export with `--debug`. The log holds no device name, no MAC address, no site address, and no inventory table.

**Why this priority**: These exports hold device identifiers and location fields. The summary tables repeat those values for every device.

**Independent Test**: Run each exporter with synthetic device values and DEBUG logging active. Verify that no synthetic value appears in the captured log.

**Acceptance Scenarios**:

1. **Given** device marker values, **When** the enrichment runs at DEBUG, **Then** no device value appears in the log.
2. **Given** an organization inventory export, **When** the export ends, **Then** no summary table appears in a log message.
3. **Given** inventory marker values, **When** the site device export runs at DEBUG, **Then** no inventory value appears in the log.

---

### User Story 4 - A parse failure logs the error type only (Priority: P2)

An operator runs an export that reads a site address that cannot be split. The DEBUG log names the error type. The log omits the address.

**Why this priority**: A support engineer still sees that a failure occurred. The address stays out of the log.

**Independent Test**: Split a synthetic address that has no separator. Capture the DEBUG log. Verify that the error type appears and that the address does not.

**Acceptance Scenarios**:

1. **Given** a site address that cannot be split, **When** the split runs, **Then** the log names only the error type.

### Edge Cases

- An empty row list: the writer keeps its existing warning and writes no file. No cell value appears in a log message.
- A row that lacks one field: the writer writes an empty string. The log holds counts only.
- An organization with no devices: the enrichment logs a count of zero.
- A site address with no separator: the split fails. The log names `IndexError` and omits the address.
- A cell value that holds a line break: the writer escapes it as before. The log holds no cell value.
- A caller passes an explicit field list: the field count uses that list.
- A warning that holds exception text: the warning keeps its text. Decision D-8 records the residual risk.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shared CSV writer MUST NOT log any cell value at any level.
- **FR-002**: The shared CSV writer MUST log only counts in its DEBUG output.
- **FR-003**: The shared CSV writer MUST write the same CSV bytes for the same input rows and field list.
- **FR-004**: The organization inventory exporter MUST NOT log a device name, a MAC address, or a site address.
- **FR-005**: The organization inventory exporter MUST NOT log a summary table.
- **FR-006**: The site device exporter MUST NOT log its inventory table.
- **FR-007**: The sites by AP model exporter MUST NOT log a site address.
- **FR-008**: A parse failure log MUST name the error type and MUST NOT name the address.
- **FR-009**: Each changed line MUST carry an inline comment. Each changed action MUST keep an INFO line before it and a DEBUG line after it.
- **FR-010**: Each new regression test MUST use synthetic marker values and assert that no marker appears in DEBUG output.
- **FR-011**: The security documentation MUST state that exported cell values stay out of logs.
- **FR-012**: The change MUST add one release-note fragment under `changelog.d/`.
- **FR-013**: The change MUST NOT alter `MistHelper.py`, the menu registry, Mist API calls, command-line flags, or the log file path.
- **FR-014**: The implementation MUST NOT start before pull request #4813 merges, or before its owner hands over the shared files.
- **FR-015**: The change MUST NOT add a suppression comment, such as `noqa`, `nosec`, or `type: ignore`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Not applicable: the change calls no Mist REST method and opens no WebSocket transport.

### Key Entities *(include if feature involves data)*

- Not applicable: the change adds no data entity, natural key, or state.
- **Cell value**: One value in one CSV cell.
- **Row**: One data line of a CSV file.
- **Field**: One CSV column name.
- **Count-only log**: A log message that names counts, error type names, or file paths. It holds no cell value.
- **Marker value**: A synthetic test value that starts with `SYNTHETIC-MARKER`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero marker values appear in the captured DEBUG output of the six absence tests.
- **SC-002**: The CSV round-trip test reads back three rows in the planned column order.
- **SC-003**: A search of the four changed exporter files finds no removed log pattern.
- **SC-004**: Every applicable local gate in `design/quickstart.md` exits with its expected result.
- **SC-005**: Every required check on the pull request passes before auto-merge starts.
- **SC-006**: The changed paths equal the paths in `plan.md`. No other path changes.

## Assumptions

- Operators enable DEBUG output with `--debug`. That flag sets the file handlers to DEBUG (`MistHelper.py`, lines 7686 to 7693).
- Local `main` matches remote `main` for each changed file. The blob SHAs match (`design/research.md`, section "Remote verification").
- Pull request #4813 merges before this change starts. Its owner reviews the shared files.
- The test environment supports the pytest `caplog` fixture. Existing tests use it.
- The repository holds no private inventory. The issue states that no private inventory is attached.

## Dependencies

- Pull request #4813 (issue #4776) edits the same files. This change waits for it (FR-014).
- Issue #4773 is open and related. Issue #4775 was found while the team implemented #4773.
- Issue #4920 is closed. Its hardware report writes through the shared writer (`src/operations/exporting/ex_hardware_inventory/report/export.py`).

## Non-Goals

- DEBUG tables in `src/interfaces/visualization/ui/display_utils.py`, `src/mist/access/api/api_data_fetcher.py`, and `src/mist/resources/device/arp_command_manager.py`. They sit outside the exporter package.
- Warnings and errors that carry exception text. Decision D-8 keeps them.
- Purging log files that already exist on operator hosts.
- Spreadsheet formula protection for CSV cells. Issue #4773 covers that work.
- Any change to the EX hardware inventory report logic.
- Any change to `--debug`, the log file path, or the menu registry.
