# Feature Specification: Browser capture statistics

**Feature Branch**: `jmorrison-juniper-browser-capture-statistics`

**Created**: 2026-10-01

**Status**: Specified

**Issue**: [#3494](https://github.com/jmorrison-juniper/MistHelper/issues/3494)

**Retained requirements**: [The comment that preserves #3359](https://github.com/jmorrison-juniper/MistHelper/issues/3494#issuecomment-5937045284)

**Base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

## User Scenarios & Testing

### User Story 1 - Read each running version change (Priority: P1)

An operator selects the existing pre-check and post-check captures in the comparison picker.
The page reports three firmware version changes.
Each device row shows `version: 0.14.29216 to 0.15.1`.

**Why this priority**: A comparison test must prove that the page shows the firmware change.

**Independent Test**: Run the new journey with Chromium and the isolated portal.
Require the count and all three rendered device rows.

**Acceptance Scenarios**:

1. **Given** the unchanged global seeds, **when** the new assertions run, **then** the version-change assertions fail.
2. **Given** the repaired global seeds, **when** the operator selects the existing capture pair, **then** the count is `3`.
3. **Given** that comparison, **when** the operator reads each device row, **then** the row shows both expected versions.

### User Story 2 - Read faithful device statistics (Priority: P1)

Each seed supplies one statistics record for each device to the shipped device-index builder.
The index holds the capture version, `connected`, the device address, and representative uptime.
Each three-device capture counts three connected devices and zero disconnected devices.

**Why this priority**: The index and the count map must describe the same test devices.

**Independent Test**: Read all five global captures without a browser.
Check the builder inputs, index fields, and count maps against explicit expectations.

**Acceptance Scenarios**:

1. **Given** a seed inventory, **when** the seed calls the shipped builder, **then** each inventory MAC has one statistics record.
2. **Given** a pre-check seed, **when** the builder joins the records, **then** each running version is `0.14.29216`.
3. **Given** a post-check seed, **when** the builder joins the records, **then** each running version is `0.15.1`.
4. **Given** any global seed, **when** the shipped count builder runs, **then** its device counts are `3`, `3`, and `0`.

### User Story 3 - Detect missing test input (Priority: P2)

Direct guards reject missing statistics and incorrect index fields.
Each failure states the number of records that the guard checked.
The guard tests use independent records and need no server.

**Why this priority**: A guard that accepts empty input cannot prevent this defect.

**Independent Test**: Give each guard valid records and deliberately damaged records.
Require an explicit failure for each damaged input.

**Acceptance Scenarios**:

1. **Given** a nonempty inventory and an empty statistics list, **when** the guard runs, **then** it fails with checked counts.
2. **Given** a missing statistics record, **when** the guard runs, **then** it names the mismatch.
3. **Given** an empty or incorrect version, state, or address, **when** the guard runs, **then** it fails.

### Edge Cases

- An empty inventory must not produce a passing guard over zero records.
- Duplicate or mismatched statistics MACs must fail the guard.
- MAC checks must use the shipped normalization rule.
- Statistics must not copy an inventory version as a product fallback.
- Required new journeys must not skip when a count or row is absent.
- Existing adjacent skips must remain visible and have separate baseline evidence.

## Requirements

### Functional Requirements

- **FR-001**: The seed must call the shipped device-index builder with representative per-device statistics.
- **FR-002**: Each statistics record must match its inventory MAC and explicit capture version.
- **FR-003**: Each index entry must hold the expected running version, state, address, and uptime.
- **FR-004**: Each global three-device capture must count three connected devices and zero disconnected devices.
- **FR-005**: The browser journey must select the existing pre-check and post-check capture IDs through the picker.
- **FR-006**: The rendered comparison must report exactly three firmware version changes.
- **FR-007**: Each rendered device row must show the expected version field and both versions.
- **FR-008**: Direct negative guards must reject missing or incorrect statistics and index fields, with checked counts.
- **FR-009**: The repair must preserve capture IDs, organizations, sites, roles, tiers, inventory fields, and fake versions.
- **FR-010**: The repair must preserve the existing API refusal behavior and shipped MAC and virtual-chassis rules.
- **FR-011**: The repair must run every upgrade-portal browser test after the shared seed change.
- **FR-012**: The repair must change no product code or lifecycle-state contract.

### Key Entities

- **Seed inventory**: The existing three device records for each nonempty stand-in site.
- **Seed statistics**: One representative running-state record for each seeded device.
- **Capture comparison**: The shipped comparison of the existing pre-check and post-check captures.

## Success Criteria

- **SC-001**: The unchanged global seed fails assertions for three running version changes and three connected devices.
- **SC-002**: All five repaired global seeds satisfy the direct statistics, index, and count contracts.
- **SC-003**: Chromium renders the expected count and version rows without a skip in any required new case.
- **SC-004**: All upgrade-portal browser journeys run, and every existing skip has an explicit reason.
- **SC-005**: Changed executable regions receive complete coverage without changing coverage exclusions.
- **SC-006**: Configured quality checks report their exact results and unavailable capabilities.

## Scope and Safety

The reserved files are the shared browser conftest, one new browser module, and one new unit module.
This feature owns its specification directory and release-note fragment.
The parent confirmed that these paths do not overlap its local reservations.

Do not change product capture, comparison, firmware, authentication, storage, route, or template code.
Do not change dependencies, SDK pins, primary keys, schemas, baselines, or suppressions.
Do not change `README.md`, `CHANGELOG.md`, shared SpecKit state, or another owner's files.
Do not address the separate lifecycle-state gap in issue #3375.

Use only the isolated test server and synthetic records.
Use no cloud credentials, live Mist requests, production stores, or containers.
Keep new artifacts in the session directory or `tmp_path`.
Commit locally only.
Publication requires a separate parent release after position 18.

## Workflow Constraints

Run specify, plan, tasks, implement, and analyze within this feature's reserved directory.
The configured specify agent refused the mandatory branch hooks because the app already owns the branch.
Use the repository templates without shared-state or branch hooks.
Record that limitation instead of claiming that the configured hooks ran.

## Assumptions

The existing two fake versions remain test input, not a production firmware decision.
The existing loader accepts the selected captures without a lifecycle-state change.
If the shipped selection refuses the capture pair, report the exact red test before any scope change.
