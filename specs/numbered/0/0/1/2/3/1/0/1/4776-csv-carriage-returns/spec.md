# Feature Specification: Preserve CSV Carriage Returns

**Feature Branch**: `fix/4776-csv-carriage-returns`

**Created**: 2026-11-26

**Status**: Ready for implementation

**Input**: Issue #4776 reports that the shared multiline escaping removes carriage returns. For the value apostrophe, carriage return, and `plain`, the CSV cell must read apostrophe, backslash, `r`, and `plain`.

## Clarifications

### Session 2026-11-26

- Q: Does the reproduction path in the issue exist? A: No. The file `tests/unit/websocket_streams/web/hardware/test_report.py` is absent on `main` and on PR #4813. The tests on `main` replace it. See D-7.
- Q: Which CSV writers change? A: `DataExporter.write_to_csv` and the CSV branches of `DeviceEvents52wExporter`. See D-3.
- Q: What happens to PR #4813? A: The work moves to branch `fix/4776-csv-carriage-returns`. PR #4813 closes after the new branch is pushed. See D-8.
- Q: Does the EX hardware report change? A: No. Its writer does not use the shared normalizer. See D-6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read carriage returns in CSV cells (Priority: P1)

An operator opens an exported CSV file. A text value with a carriage return shows a visible backslash and `r` in its cell. No character is lost.

**Why this priority**: A lost character changes the meaning of the exported text. The defect affects every CSV export that uses the shared writer.

**Independent Test**: Call `DataExporter.write_to_csv` with one synthetic row. Read the file with `csv.DictReader`. Check the cell text.

**Acceptance Scenarios**:

1. **Given** a text value with a carriage return, **When** `write_to_csv` writes the row, **Then** the cell holds a backslash and `r` there.
2. **Given** a text value with a carriage return and a line feed, **When** `write_to_csv` writes the row, **Then** the cell holds `\r\n` as text.
3. **Given** a list value with a carriage return in one item, **When** `write_to_csv` writes the row, **Then** the joined cell holds `\r` for that item.

---

### User Story 2 - Keep raw text for the database (Priority: P1)

The SQLite store keeps each carriage return as one raw character. The CSV presentation does not change stored text or caller rows.

**Why this priority**: Database rows feed other reports. A presentation change in stored text would damage the saved value.

**Independent Test**: Store one row with a carriage return through `SQLiteDatabaseWriter`. Read the stored value. Write the same raw row through `write_to_csv`. Read the caller row.

**Acceptance Scenarios**:

1. **Given** a text value with a carriage return, **When** the SQLite writer stores the row, **Then** the stored value keeps the carriage return character.
2. **Given** a raw row with a carriage return, **When** `write_to_csv` writes that row, **Then** the caller row still holds the carriage return character.

---

### User Story 3 - Apply the same CSV rule to the 52-week export (Priority: P2)

The 52-week device events export writes its CSV with its own writer. Its CSV cells show a backslash and `r`. Its SQLite output keeps raw carriage returns.

**Why this priority**: The export writes the same kind of CSV. Without this change, its cells would show raw carriage returns after the shared change.

**Independent Test**: Run the CSV branch of `DeviceEvents52wExporter` with one row that holds a carriage return. Read the CSV file.

**Acceptance Scenarios**:

1. **Given** a row with a carriage return and CSV output, **When** the first batch is written, **Then** the cell shows a backslash and `r`.
2. **Given** a row with a carriage return and SQLite output, **When** the first batch is written, **Then** the stored value keeps the carriage return character.

### Edge Cases

- A value holds only a carriage return, only a line feed, or repeated line breaks. Each character follows FR-002 and FR-006.
- A value already holds the two characters backslash and `r`. The presentation keeps those characters unchanged.
- A value starts with `=`, `+`, `-`, `@`, a tab, or a carriage return. The shared CSV path adds no apostrophe. The EX hardware report keeps its own rule.
- A row holds a non-text value, such as an integer or an empty value. The presentation keeps that value unchanged.
- A row passes through `export_with_processing` before `write_to_csv`. The presentation runs once, and the text is not escaped twice.
- A list value holds a line feed inside one item. The join keeps that line feed raw, as it does today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `DataProcessingUtils.escape_multiline` MUST keep each carriage return in each string value.
- **FR-002**: The CSV presentation MUST replace each carriage return in a text value with a backslash and the letter `r`. It MUST keep the order of all other characters.
- **FR-003**: Each CSV writer that receives normalized rows MUST apply the CSV presentation. This includes `DataExporter.write_to_csv` and the CSV branches of `DeviceEvents52wExporter`.
- **FR-004**: The CSV presentation MUST NOT change the raw rows that a caller passes in.
- **FR-005**: The SQLite writer and the polyglot writer MUST keep raw carriage returns. They MUST NOT receive the two-character text from the CSV presentation.
- **FR-006**: The shared line feed escaping, the list join, and the handling of non-text values MUST stay unchanged.
- **FR-007**: The existing test that asserts carriage return removal MUST assert that the carriage return is kept.
- **FR-008**: Each changed function MUST stay at 25 lines or fewer. Each new action MUST have an info log before it and a debug log after it. Each new executable line MUST carry an inline comment.
- **FR-009**: The release note MUST use the name `changelog.d/issue-4776-csv-carriage-returns.md`. It MUST pass `tests/guardrails/test_changelog_fragment_policy.py`.
- **FR-010**: The EX hardware report writer and its CSV contract MUST NOT change.

### Key Entities

- **Raw row**: A row before CSV presentation. It holds the values that a caller passes to a writer.
- **Normalized row**: A raw row after `escape_multiline`. Carriage returns stay raw. Line feeds become a backslash and `n`.
- **CSV cell**: One text value in a CSV file. It holds the CSV presentation of a normalized value.
- **Database row**: One stored SQLite row. It holds normalized values with raw carriage returns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each tested carriage return in a CSV text cell reads back as a backslash and the letter `r`.
- **SC-002**: Each tested raw row keeps its original values after a CSV write.
- **SC-003**: Each tested SQLite value keeps its raw carriage return.
- **SC-004**: The 52-week CSV branch shows the same CSV presentation as `write_to_csv`.
- **SC-005**: Each applicable local gate passes. The record gives a reason for each gate that does not apply.
- **SC-006**: Each required remote check passes on the new pull request before the `auto-merge` label is added.

## Assumptions

- The runtime is Python 3.15 or newer, as the constitution requires (RC-71).
- The eight existing files that the change modifies match remote `main` commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Their blob SHAs appear in the remote table of `design/research.md`.
- Stored database values from earlier runs stay unchanged. This change plans no data migration.
- The implementer runs the local gates on Windows 11 in the project `.venv` environment.

## Out of Scope

- The EX hardware report writer, its CSV contract, and the work of issue #4773.
- Escaping line feeds inside list values. The current behavior stays (FR-006).
- Rewriting stored database rows.
- Changing the primary key strategies in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.
- Changing `README.md`, `documentation/operator-guide.md`, or `CHANGELOG.md`.
- Deploying the container image (constitution Principle IV, steps 10 to 12).
- Splitting the classes and folders that exceed the five-item limit. That work belongs to separate remediation issues.
