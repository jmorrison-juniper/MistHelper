# Feature Specification: SQLite schema context errors

**Feature Branch**: `fix/4712-schema-context-errors`

**Created**: 2026-11-26

**Status**: Specified

**Input**: GitHub issue #4712, "Runtime: local context errors select the default SQLite schema". A local failure in the API context detector selects the default SQLite strategy.

## Clarifications

### Session 2026-11-26

- Q: Should a local failure in the frame walk return `unknown`?
  A: No. The failure propagates to the caller. Only a completed walk with no matching frame returns `unknown`.
- Q: Should the SQLite writer or the exporter stop the write?
  A: The exporter stops the write already. It catches writer exceptions, logs them, and returns `False`. The writer does not change.
- Q: Should the legacy unit test move to the storage domain package now?
  A: No. Its expectation changes in place. The move belongs to open issue #4142.
- Q: May the local candidate commit `b4b81164` become the pull request?
  A: No. The candidate base is 84 commits behind `main`. It validated with Python 3.14.7. Its design is reused. Its commits are not.
- Q: May the pull request open now?
  A: Not yet. The issue comments hold publication. Tasks T-PR and T-MERGE wait for the owner and the orchestrator.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop a SQLite write on a local failure (Priority: P1)

An export writes to SQLite and has no API function name. A local failure occurs during detection. The write stops. The table does not take the default strategy.

**Why this priority**: A silent strategy change writes rows with a wrong key and wrong indexes. The operator cannot see that change in the output.

**Independent Test**: Call the exporter dispatch from a function named `getOrgInventory`, with the detector logger raising an error. The call returns `False`, logs one error, and opens no database connection.

**Acceptance Scenarios**:

1. **Given** a matched `getOrgInventory` frame, **When** the logger raises after the match, **Then** the detector raises that error and returns no name.
2. **Given** a non-matching first frame, **When** reading the parent frame raises, **Then** the caller receives the original error.
3. **Given** a local failure during an export, **When** the SQLite write runs, **Then** the exporter logs the table and format, returns `False`, and writes no table.

---

### User Story 2 - Keep normal detection unchanged (Priority: P2)

An export with a matching API function keeps its endpoint strategy. A walk with no matching frame keeps the `unknown` result.

**Why this priority**: The repair must not change normal exports or the absent-frame result.

**Independent Test**: Run the existing detection tests in `tests/unit/db/test_database_schema_utils.py` without a change to them. All pass.

**Acceptance Scenarios**:

1. **Given** a matching frame, **When** the walk finds it, **Then** the nearest matching name returns, as before.
2. **Given** no matching frame, **When** the walk ends, **Then** the detector returns `unknown`, as before.
3. **Given** the name `getOrgInventory`, **When** the strategy is selected, **Then** the strategy type is `natural_pk`, as before.

---

### Edge Cases

- The interpreter provides no current frame. The detector returns `unknown`, because no frame exists to match.
- The first frame does not match. Reading its parent raises `AttributeError`. The error propagates to the caller.
- The logger raises after a match. The error propagates. No name returns.
- An API function name is already set. The detector does not run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A local failure during the frame walk MUST propagate to the caller as the original error.
- **FR-002**: A local failure in the detected-name log call MUST propagate and MUST NOT return `unknown`.
- **FR-003**: The detector MUST return `unknown` only after a completed walk with no matching frame.
- **FR-004**: The detector MUST keep the six name patterns, the nearest-match order, and the `finally` cleanup of its frame reference.
- **FR-005**: A SQLite write whose detector call fails MUST stop, MUST log an error that names the table and the output format, and MUST return `False`.
- **FR-006**: The expectation of `test_handles_stack_inspection_error` MUST change in the same change as the source.
- **FR-007**: The README MUST state the new failure behavior, as the constitution requires for each behavior change.
- **FR-008**: The operator guide MUST describe the log line and the operator action for a stopped SQLite write.
- **FR-009**: The change MUST add the changelog fragment `changelog.d/issue-4712-schema-context-errors.md` with a Fixed bullet that names issue #4712.
- **FR-010**: The regression tests for FR-001, FR-002, and FR-005 MUST fail on the unchanged source.
- **FR-011**: The change MUST NOT add a broad exception handler that does not use the caught exception.
- **FR-012**: The change MUST NOT move or rename `tests/unit/db/test_database_schema_utils.py`.
- **FR-013**: The record MUST be stored at `specs\numbered\0\0\1\2\2\3\2\2\4712-schema-context-errors`, and its route MUST come from `Resolve-SpecFeaturePath`.

### Key Entities *(include if feature involves data)*

- **API function name**: The endpoint function name, such as `getOrgInventory`, that selects an endpoint strategy.
- **Endpoint strategy**: The configured key rule for one endpoint in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- **Default strategy**: The strategy built from the `default` template when no endpoint strategy matches.
- **Unknown result**: The value `unknown` that the detector returns only for an absent frame.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The three new regression tests fail before the source change and pass after it.
- **SC-002**: The updated legacy test fails before the source change and passes after it.
- **SC-003**: Each applicable gate in task T-LOCAL-GATES reports its expected result.
- **SC-004**: The exporter regression test records zero database connections on the failure path.
- **SC-005**: The blind handler ratchet guard reports no new blind handler.
- **SC-006**: Each changed Markdown file scores 80 or above in the STE linter.
- **SC-007**: Each directory in the record holds five children or fewer.

## Assumptions

- The local environment uses Python 3.15.2, as `pyproject.toml` requires.
- The owner lifts the publication hold before the pull request opens.
- The remote `main` code has the defect path that `research.md` records.
- Pull request #4813 changes `data_exporter.py`. This change does not touch that file.
- Only the design of the earlier candidate is reused.

## Non-Goals

- Renaming or moving the legacy unit test. Open issue #4142 tracks the move.
- Splitting `DatabaseSchemaUtils`. This is existing debt under constitution Principle I.
- Removing other blind handlers. Open issue #1794 tracks them.
- Changing the endpoint strategy table, the SQL DDL, or any existing table.
- Changing `sqlite_database_writer.py`, `data_exporter.py`, or any menu operation.
