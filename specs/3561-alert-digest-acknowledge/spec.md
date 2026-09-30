# Feature Specification: Alert Digest Acknowledge

**Feature Branch**: `3561-alert-digest-acknowledge`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 280 alert digest and menu 281 alarm acknowledge. Menu 20 exports the alarms of the past day as raw rows. A shift handover needs the alarms grouped into the four Mist categories (infrastructure, Marvis, security, certificate) with severity, recurrence, first seen, and last seen. No operation acknowledges an alarm, so an operator must open the Mist UI for that step. Menu 280 writes AlertDigest.csv with one row per alarm type and site: category, severity, alarm type, site, recurrence, first seen, last seen, sample device or client, and acknowledged state. It also writes AlertDigest.md, a handover summary with one section per category. Menu 281 lists the unacknowledged alarms from the same window, asks the operator to type ACK and the count, and then acknowledges them with one bulk request. It writes AlertAcknowledgeLog.csv with the result of each alarm id."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create shift handover digest (Priority: P1)

A NOC operator runs menu 280 before shift handover. The operator gets a concise digest of recent alarms, grouped by Mist category, without using prompts in test mode.

**Why this priority**: The digest gives the next shift a clear view of active operational risk. It also avoids manual review of raw alarm rows.

**Independent Test**: Run menu 280 in `--test` mode with sample alarm data. Confirm that `data/AlertDigest.csv` and `data/AlertDigest.md` are written, that no prompt appears, and that the digest groups alarms by category.

**Acceptance Scenarios**:

1. **Given** sample alarms in the default 24-hour window, **When** the operator runs menu 280 in `--test` mode, **Then** `data/AlertDigest.csv` and `data/AlertDigest.md` are created with no prompt.
2. **Given** two alarms with the same alarm type and site in the lookback window, **When** the digest is created, **Then** the CSV has one grouped row for that alarm type and site with recurrence equal to 2, the earliest first seen value, and the latest last seen value.
3. **Given** alarms in infrastructure, Marvis, security, and certificate categories, **When** the Markdown digest is created, **Then** it has one section for each category that has alarms.
4. **Given** an alarm type that is not present in the alarm definitions constant, **When** the digest is created, **Then** that alarm has category `unknown`.

---

### User Story 2 - Review and acknowledge recent alarms (Priority: P2)

A NOC operator runs menu 281 after reviewing the digest. The operation lists unacknowledged alarms from the same lookback window, requires a precise confirmation, and acknowledges the selected alarms in one bulk action.

**Why this priority**: Alarm acknowledgement is destructive because it changes the alarm state in Mist. The operator must make an explicit human decision before any acknowledgement occurs.

**Independent Test**: Run menu 281 with sample unacknowledged alarms. Confirm that no request is sent until the operator types `ACK` and the exact alarm count. Confirm that any other input cancels and logs the cancellation.

**Acceptance Scenarios**:

1. **Given** three unacknowledged alarms in the lookback window, **When** the operator types `ACK 3`, **Then** menu 281 sends one bulk acknowledgement request and writes one result row per alarm id to `data/AlertAcknowledgeLog.csv`.
2. **Given** three unacknowledged alarms in the lookback window, **When** the operator types any input other than `ACK 3`, **Then** menu 281 sends no acknowledgement request and writes a log line that records the cancellation.
3. **Given** menu 281 is run with `--dry-run`, **When** unacknowledged alarms are found, **Then** the operation prints the alarm ids that it would acknowledge and sends no acknowledgement request.
4. **Given** no unacknowledged alarms are found in the lookback window, **When** menu 281 runs, **Then** the operation sends no acknowledgement request and reports that there is nothing to acknowledge.

---

### User Story 3 - Control the lookback window (Priority: P3)

A NOC lead changes the lookback window for special handovers by setting `ALERT_DIGEST_HOURS`. Menu 280 and menu 281 use the same window.

**Why this priority**: Most handovers need the past day. Some incidents need a shorter or longer window, but both digest and acknowledgement must use the same time range.

**Independent Test**: Run both menus with and without `ALERT_DIGEST_HOURS`. Confirm that both menus use 24 hours by default and use the environment value when it is set to a valid hour count.

**Acceptance Scenarios**:

1. **Given** `ALERT_DIGEST_HOURS` is not set, **When** menu 280 or menu 281 runs, **Then** the lookback window is 24 hours.
2. **Given** `ALERT_DIGEST_HOURS` is set to `8`, **When** menu 280 or menu 281 runs, **Then** the lookback window is 8 hours.
3. **Given** `ALERT_DIGEST_HOURS` is set to an invalid value, **When** menu 280 or menu 281 runs, **Then** the operation rejects the value with a clear message and sends no destructive request.

### Edge Cases

- If there are no alarms in the lookback window, menu 280 still writes the CSV and Markdown files with clear empty-state content.
- If an alarm has no device or client name, the sample device or client field is blank or uses a clear placeholder.
- If an alarm has no acknowledgement state, the acknowledged state field uses a clear unknown value instead of failing.
- If multiple alarm rows have missing first seen or last seen values, the digest keeps the available values and leaves unavailable cells blank.
- If the bulk acknowledgement returns mixed results, the acknowledgement log records the result for each alarm id and reports the failed ids to the operator.
- If the output directory is not writable, the operation reports failure and does not report success.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 280 MUST create an alert digest for alarms in the lookback window.
- **FR-002**: Menu 280 MUST write `data/AlertDigest.csv` with one row per alarm type and site.
- **FR-003**: Each digest CSV row MUST include category, severity, alarm type, site, recurrence, first seen, last seen, sample device or client, and acknowledged state.
- **FR-004**: Menu 280 MUST write `data/AlertDigest.md` as a handover summary with one section per alarm category that appears in the window.
- **FR-005**: The category of an alarm MUST come from the alarm definitions constant. Unknown alarm types MUST receive the category `unknown`.
- **FR-006**: Menu 280 MUST run in `--test` mode with no prompt and MUST still write both digest files under `data/`.
- **FR-007**: Menu 281 MUST list unacknowledged alarms from the same lookback window used by menu 280.
- **FR-008**: Menu 281 MUST send no acknowledgement request until the operator types `ACK` followed by the exact count of unacknowledged alarms shown.
- **FR-009**: Menu 281 MUST cancel on any other input, send no acknowledgement request, and write a log line for the cancellation.
- **FR-010**: Menu 281 MUST support `--dry-run` by printing the alarm ids it would acknowledge and sending no acknowledgement request.
- **FR-011**: Menu 281 MUST acknowledge eligible alarms with one bulk request after valid confirmation.
- **FR-012**: Menu 281 MUST write `data/AlertAcknowledgeLog.csv` with the result of each alarm id.
- **FR-013**: The lookback window MUST default to 24 hours and MUST read `ALERT_DIGEST_HOURS` from the environment when it is set.
- **FR-014**: The feature MUST expose `AlertDigestOperation.run_digest` and `AlertDigestOperation.run_acknowledge`. `AlertDigestOperation.run` MAY exist only if it is useful.
- **FR-015**: The wiring contract MUST name `AlertDigestOperation.run_digest` for menu 280 and `AlertDigestOperation.run_acknowledge` for menu 281.
- **FR-016**: The wiring manifest at `specs/3561-alert-digest-acknowledge/wiring.md` MUST exist and MUST include every section of the contract.
- **FR-017**: The release note fragment at `changelog.d/issue-3561-alert-digest-acknowledge.md` MUST exist before implementation is complete.
- **FR-018**: Menu 281 MUST be treated as destructive and MUST require human review before it is used against live alarms.
- **FR-019**: Unit tests MUST cover missing sample, missing acknowledgement state, missing timing values, ASCII-only Markdown output, and local grouping performance.

### Required Acceptance Criteria

- Menu 280 runs in --test with no prompt and writes AlertDigest.csv and AlertDigest.md under data/.
- The category of an alarm comes from the alarm definitions constant, and an unknown type receives the category unknown.
- Menu 281 sends no request until the operator types ACK followed by the exact alarm count, and any other input cancels with a log line.
- Menu 281 supports --dry-run, which prints the alarm ids it would acknowledge and sends nothing.
- The lookback window defaults to 24 hours and reads ALERT_DIGEST_HOURS from the environment when set.
- The wiring manifest specs/3561-alert-digest-acknowledge/wiring.md exists with every section of the contract.
- The release note fragment changelog.d/issue-3561-alert-digest-acknowledge.md exists.

### Safety Requirements

- **SR-001**: Menu 280 MUST be safe and non-destructive.
- **SR-002**: Menu 281 MUST be destructive only after explicit confirmation.
- **SR-003**: Menu 281 MUST send no request in `--dry-run` mode.
- **SR-004**: Menu 281 MUST send no request when confirmation is absent, malformed, or has the wrong count.
- **SR-005**: All user-facing logs and files MUST use ASCII text.

### Integration Constraints

- **IC-001**: There MUST be two menu entries: menu 280 for safe digest and menu 281 for destructive acknowledgement.
- **IC-002**: Required integration changes MUST be recorded in `specs/3561-alert-digest-acknowledge/wiring.md` before implementation.
- **IC-003**: The implementation MUST NOT edit `MistHelper.py`, `operation_registry.py`, `endpoint_primary_key_strategies.py`, `README.md`, copilot instructions, `menu_reference.md`, `web_portal`, `scripts`, guardrails, or existing `src/tests` owned by other work.
- **IC-004**: The wiring manifest MUST carry the exact primary key, README, registry, and menu registration changes for the integration pull request because the fleet contract owns those files outside this branch.

### Key Entities

- **Alarm Row**: One raw alarm record from the lookback window. Key attributes include alarm id, alarm type, site, severity, first seen, last seen, device or client, and acknowledgement state.
- **Alarm Group**: The grouped digest unit for one alarm type and one site. Key attributes include category, severity, recurrence, first seen, last seen, sample device or client, and acknowledged state.
- **Category**: The Mist alarm category used in the handover summary. Valid known categories are infrastructure, Marvis, security, and certificate. Unknown alarm types use category `unknown`.
- **Acknowledgement Candidate**: An unacknowledged alarm id that menu 281 can include in the bulk acknowledgement after confirmation.
- **Acknowledgement Result**: The per-alarm outcome written to the acknowledgement log after a bulk acknowledgement attempt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A shift operator can run menu 280 and receive both digest files in under 60 seconds for a normal 24-hour alarm volume.
- **SC-002**: The digest reduces handover review to one grouped row per alarm type and site, with recurrence and time range visible for 100% of grouped alarms that have source timing data.
- **SC-003**: 100% of unknown alarm types are still included in the digest with category `unknown`.
- **SC-004**: Menu 281 sends zero acknowledgement requests when the operator gives no confirmation, a wrong word, or a wrong count.
- **SC-005**: Menu 281 dry runs send zero acknowledgement requests and show 100% of alarm ids that would be acknowledged.
- **SC-006**: The acknowledgement log contains one result row for 100% of alarm ids included in a confirmed bulk acknowledgement attempt.
- **SC-007**: Both menu 280 and menu 281 use the same lookback window in 100% of runs.
- **SC-008**: Local grouping of 500 alarm rows completes in under 1 second, which preserves the 60 second operation budget for normal volumes.

## Assumptions

- Operators are NOC staff who already have valid Mist access through the existing application session.
- The existing alarm export used by menu 20 provides enough alarm fields to build the digest and acknowledgement candidate list.
- The alarm definitions constant is the source of truth for known category mapping.
- The default 24-hour window means the 24 hours before the operation starts.
- `ALERT_DIGEST_HOURS` is an integer hour count when it is valid.
- The release note fragment is required by the full feature workflow, but this specify step creates or updates only files in `specs/3561-alert-digest-acknowledge/`.
