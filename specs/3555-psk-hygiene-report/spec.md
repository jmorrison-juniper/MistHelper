# Feature Specification: PSK Hygiene Report

**Feature Branch**: `feat/3555-psk-hygiene-report`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 274 PSK hygiene report. Menu 44 exports pre-shared keys, but no operation scores them. An expired key, a multi-use key with no usage cap, a rotation that still holds the old passphrase, and a key bound to an SSID that no WLAN carries are each a finding that an operator must compute by hand. PskHygiene.csv: one row per PSK with name, SSID, role, VLAN, usage, max usage, expire time, days remaining, rotation pending, WLAN match, and a findings column. A console summary counts expired keys, keys that expire in 30 days, uncapped multi-use keys, pending rotations, and orphan SSIDs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run PSK hygiene report without prompts (Priority: P1)

A NOC operator runs menu 274 in test mode and receives a PSK hygiene report without any prompt. The report helps the operator find risky or stale PSKs without manual spreadsheet work.

**Why this priority**: This is the main value of the feature. It changes manual review into one repeatable operation.

**Independent Test**: Run the operation after the integration pull request wires menu 274 into MistHelper. Confirm that it completes without a prompt and writes `data/PskHygiene.csv`.

**Acceptance Scenarios**:

1. **Given** test mode is active, **When** the operator runs menu 274, **Then** the operation completes without interactive input.
2. **Given** PSK data exists, **When** the operation finishes, **Then** `data/PskHygiene.csv` contains one row for each PSK.
3. **Given** a PSK row is written, **When** the operator opens the report, **Then** the row includes name, SSID, role, VLAN, usage, max usage, expire time, days remaining, rotation pending, WLAN match, and findings.

---

### User Story 2 - See clear findings for risky PSKs (Priority: P2)

A NOC operator reviews the report and sees a clear finding for each PSK that needs action. The operator can sort and filter the findings without exposing passphrases.

**Why this priority**: The report is useful only when each risky condition is visible and safe to share.

**Independent Test**: Use test data with expired keys, keys that expire soon, uncapped multi-use keys, pending rotations, and orphan SSIDs. Confirm that each matching row has the correct finding value.

**Acceptance Scenarios**:

1. **Given** a PSK has an expire time in the past, **When** the report is created, **Then** the findings column includes `expired`.
2. **Given** a PSK expires in 30 days or less and is not expired, **When** the report is created, **Then** the findings column includes `expires_soon`.
3. **Given** a PSK has no `mac`, no `macs`, and no `max_usage`, **When** the report is created, **Then** the findings column includes `uncapped_multi_use`.
4. **Given** a PSK has `old_passphrase` present, **When** the report is created, **Then** the findings column includes `rotation_pending` and the report records only that the old passphrase is present.
5. **Given** a PSK SSID matches no organization WLAN SSID, **When** the report is created, **Then** the findings column includes `orphan_ssid`.

---

### User Story 3 - Read a console summary of hygiene risk (Priority: P3)

A NOC operator reads the console summary after the run and sees the count for each finding. The operator can quickly decide whether PSK cleanup is needed.

**Why this priority**: The summary gives fast situational awareness before the operator opens the CSV file.

**Independent Test**: Run menu 274 with known test data and compare the console counts to the rows in `data/PskHygiene.csv`.

**Acceptance Scenarios**:

1. **Given** the report has findings, **When** the operation finishes, **Then** the console summary shows counts for expired keys, keys that expire in 30 days, uncapped multi-use keys, pending rotations, and orphan SSIDs.
2. **Given** no PSK has a finding, **When** the operation finishes, **Then** the console summary shows zero for each finding count.

---

### User Story 4 - Verify release and wiring evidence (Priority: P4)

A reviewer checks that the feature has the required planning and release artifacts before implementation is accepted.

**Why this priority**: The project requires traceable work and release notes for each change.

**Independent Test**: Confirm that `specs/3555-psk-hygiene-report/wiring.md` has every fleet contract section and that `changelog.d/issue-3555-psk-hygiene-report.md` exists before release.

**Acceptance Scenarios**:

1. **Given** the specification is complete, **When** the reviewer opens `specs/3555-psk-hygiene-report/wiring.md`, **Then** every fleet contract section is present.
2. **Given** the implementation is ready for release, **When** the reviewer checks release notes, **Then** `changelog.d/issue-3555-psk-hygiene-report.md` exists.

### Edge Cases

- A PSK has no expire time. The report leaves days remaining blank and does not mark the key as expired or expiring soon.
- A PSK expires today. The report marks the key as expiring soon unless the time is already in the past.
- A PSK has an SSID value that differs only by leading or trailing spaces. The report uses the normalized SSID text for matching.
- A PSK has no SSID. The report marks the WLAN match as false and includes `orphan_ssid`.
- A PSK has both `mac` and `macs` empty, but `max_usage` is present. The report does not mark `uncapped_multi_use`.
- A PSK has `old_passphrase` present. The report never writes the old value. It records only that rotation is pending.
- Organization WLAN data is unavailable. The report marks WLAN match as unknown and states that orphan SSID findings could not be fully evaluated.
- Site-level WLANs exist. They are outside this report scope and must be stated as outside scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration pull request MUST add menu 274 as the PSK hygiene report operation.
- **FR-002**: The operation MUST run with no prompt when `org_id` or `ORG_ID` is already configured.
- **FR-003**: The operation MUST write `PskHygiene.csv` under `data/`.
- **FR-004**: The CSV MUST contain one row per PSK reviewed.
- **FR-005**: Each CSV row MUST include name, SSID, role, VLAN, usage, max usage, expire time, days remaining, rotation pending, WLAN match, and findings.
- **FR-006**: The report MUST NOT include `passphrase` values in any output file.
- **FR-007**: The report MUST NOT include `old_passphrase` values in any output file.
- **FR-008**: Log lines and console output MUST NOT include `passphrase` or `old_passphrase` values.
- **FR-009**: The report MUST record only whether `old_passphrase` is present.
- **FR-010**: A PSK whose SSID matches no organization WLAN SSID MUST receive the finding `orphan_ssid`.
- **FR-011**: The report MUST state that site-level WLANs are outside its scope.
- **FR-012**: A PSK with no `mac`, no `macs`, and no `max_usage` MUST receive the finding `uncapped_multi_use`.
- **FR-013**: A PSK whose expire time is in the past MUST receive the finding `expired`.
- **FR-014**: A PSK that expires in 30 days or less and is not expired MUST receive the finding `expires_soon`.
- **FR-015**: A PSK with `old_passphrase` present MUST receive the finding `rotation_pending`.
- **FR-016**: The console summary MUST state the count for each finding: expired keys, keys that expire in 30 days, uncapped multi-use keys, pending rotations, and orphan SSIDs.
- **FR-017**: The finding counts in the console summary MUST match the CSV rows.
- **FR-018**: The wiring manifest `specs/3555-psk-hygiene-report/wiring.md` MUST exist and include every fleet contract section.
- **FR-019**: The release note fragment `changelog.d/issue-3555-psk-hygiene-report.md` MUST exist before release.
- **FR-020**: The operation MUST keep all report output inside the `data/` directory.

### Key Entities

- **PSK**: A pre-shared key record. Key attributes are name, SSID, role, VLAN, usage, max usage, expire time, `mac`, `macs`, and old passphrase presence.
- **Organization WLAN**: A WLAN configured at the organization level. Key attribute is SSID. It is the only WLAN source used for orphan SSID matching.
- **Hygiene Finding**: A report label that marks a PSK risk. Values are `expired`, `expires_soon`, `uncapped_multi_use`, `rotation_pending`, and `orphan_ssid`.
- **Console Summary**: A user-facing count of PSKs in each finding category.
- **Wiring Manifest**: A traceability file for issue, branch, artifacts, overlap checks, hot files, gates, release note, and deployment evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After integration wiring exists, menu 274 completes without prompts in 100% of automated test runs.
- **SC-002**: For a controlled test set, 100% of PSKs receive the expected finding labels.
- **SC-003**: The console summary counts match the CSV findings counts exactly for all finding categories.
- **SC-004**: No passphrase or old passphrase value appears in logs, console output, or `PskHygiene.csv` during validation.
- **SC-005**: A reviewer can identify expired, soon-to-expire, uncapped multi-use, pending rotation, and orphan SSID PSKs from the CSV in less than 2 minutes.
- **SC-006**: The feature has 100% of required traceability artifacts before planning moves to implementation.

## Assumptions

- Menu 44 remains the source of PSK export behavior. Menu 274 wiring is deferred to the integration pull request.
- Organization WLAN SSIDs are the scope for WLAN matching. Site-level WLANs are out of scope for this report.
- The findings column can contain more than one finding for a PSK.
- Empty, missing, or null `mac`, `macs`, and `max_usage` values count as absent for uncapped multi-use detection.
- The report uses local run time to decide whether a key is expired or expires within 30 days.
- The release note fragment is created during implementation because this specify step must not edit files outside the feature spec directory.
