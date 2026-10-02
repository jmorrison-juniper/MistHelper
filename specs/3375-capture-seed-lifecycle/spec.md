# Feature Specification: Capture seed lifecycle fidelity

**Feature Branch**: `jmorrison-juniper-capture-seed-lifecycle-fidelity`

**Created**: 2026-10-02

**Status**: Local preparation only

**Input**: Issue [#3375](https://github.com/jmorrison-juniper/MistHelper/issues/3375)
and [comment 5830646243](https://github.com/jmorrison-juniper/MistHelper/issues/3375#issuecomment-5830646243).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt a verified partial capture (Priority: P1)

The browser harness must adopt the same standalone pre-check as the shipped reader.
Lifecycle verification and content completeness answer different questions.

**Why this priority**: A content-only stand-in can hide a defect in lifecycle eligibility.

**Independent Test**: Compare the actual stand-in reader with the shipped query through an in-memory database boundary.

**Acceptance Scenarios**:

1. **Given** a standalone partial capture with verified lifecycle, **when** the pre-check card opens, **then** it adopts that capture.
2. **Given** complete content with pending lifecycle, **when** the reader searches, **then** it adopts no capture.
3. **Given** obsolete content `verified` without verified lifecycle, **when** the reader searches, **then** it adopts no capture.
4. **Given** several eligible captures, **when** the reader searches, **then** the existing origin, time, tie, and tier rules remain.

### User Story 2 - Store the shipped capture shape (Priority: P2)

Every global seed and every document from the actual stand-in runner must separate content status from lifecycle state.

**Why this priority**: Browser journeys must read documents that represent the shipped contracts.

**Independent Test**: Read the real native fixture module once and observe its actual builders and runner writes.

**Acceptance Scenarios**:

1. **Given** the five existing seeds, **when** the native fixture builds them, **then** each has verified lifecycle and native content status.
2. **Given** an existing partial Tier 3 seed, **when** its content status resolves, **then** it remains partial.
3. **Given** a standalone capture job, **when** the actual stand-in runner ends, **then** its stored document has both fields.
4. **Given** complete, partial, and failed content, **when** lifecycle is verified, **then** eligibility does not add a content policy.

### User Story 3 - Show the real capture fields (Priority: P3)

The browser must show all nine counts, device versions and statuses, and the serving device name.

**Why this priority**: A missing field can hide a visible column from every browser journey.

**Independent Test**: Read rendered capture and history tables with Chromium and the current shipped Flask application.

**Acceptance Scenarios**:

1. **Given** three native device records, **when** the capture page opens, **then** all nine counts retain their accepted values.
2. **Given** the accepted native statistics, **when** device rows render, **then** each version and connected status matches its statistics.
3. **Given** a matched client device address, **when** client rows render, **then** the parent name comes from the native device index.
4. **Given** a genuinely unmatched device address, **when** a client row renders, **then** its parent remains explicitly unknown.
5. **Given** stored complete or partial content, **when** history renders, **then** it shows that content value instead of obsolete `verified`.

### Edge Cases

- Pending, absent, unverified, and obsolete lifecycle records remain ineligible.
- Run-owned captures, wrong sites, and post-check roles remain ineligible.
- Equal start times retain the current last-stored winner.
- Missing or unusable tiers retain `DEFAULT_TIER` and `precheck_tier_number`.
- The accepted empty site remains empty with nine zero counts.
- Private partial scenarios must not change shared sites, captures, or fixture lifetime.
- A missing input or duplicate native fixture identity must fail with a measured count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Use `CAPTURE_STATE_FIELD` and `CaptureState.VERIFIED` for lifecycle fields and eligibility.
- **FR-002**: Use the shipped `resolve_status` contract for content status.
- **FR-003**: Use shipped `ClientRecord` values and `fill_device_names` for serving device names.
- **FR-004**: Preserve all accepted identifiers, versions, inventory, statistics, addresses, timestamps, roles, and ownership.
- **FR-005**: Preserve all nine `COUNT_KEYS` and their accepted values through the shipped count builder.
- **FR-006**: Preserve the newest-precheck, tier conversion, origin, run, site, role, and tie contracts.
- **FR-007**: Migrate obsolete expectations only at directly coupled and publicly reserved callers.
- **FR-008**: Prove the defects against immutable accepted main `a11c1189d8e861bd3683e669bfdb9b654ec1eeab`.
- **FR-009**: Use one real native fixture identity, controlled store boundaries, and process-owned browser resources.
- **FR-010**: Prove positive measured guards and independent negative controls without production writes or upgrade callbacks.
- **FR-011**: Run every new required case without skips and preserve existing browser dependency and ownership guards.
- **FR-012**: Keep all production source, runtime policies, dependency manifests, baselines, and shared documents unchanged.
- **FR-013**: Prepare a clean local commit only and wait for the parent publication grant.

### Key Entities

- **Capture document**: Content status, lifecycle state, native sections, and existing business identifiers.
- **Pre-check selection**: The existing standalone eligibility, newest start time, tie winner, and stored tier.
- **Native fixture**: The single pytest-loaded fixture identity that owns the existing seeds and stand-in runner.
- **Private scenario**: Fresh in-memory records and a private site that cannot change shared selections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Check all five existing seeds and each observed runner document for separate lifecycle and content fields.
- **SC-002**: Prove adoption of verified partial content and rejection of pending content through the actual pre-check card.
- **SC-003**: Check nine counts, three device version/status rows, three matched parent names, and one unmatched parent.
- **SC-004**: Preserve all 33 existing tier cases, all 87 statistics cases, and all four version-comparison browser cases.
- **SC-005**: Run the complete relevant portal unit suite and collect the complete current `tests/e2e/` scope.
- **SC-006**: Record exact nonzero measurements, changed-code coverage, negative controls, quality results, and resource cleanup.

## Assumptions

- The branch starts at `66b1a1832e069a467d25034bc6024c2c7353e11e`.
- The starting branch and immutable baseline have identical harness and capture-source bytes.
- The separate accepted #3215 template change remains read-only.
- Current `stored_progress` reports terminal lifecycle after #3378. History displays stored content status.
- Publication remains `LOCALONLY position45 after #3699` until the parent grants an exact verified main SHA.
- Native Windows, live Mist, production stores, deployment, remote checks, and another session's dictionary are unavailable or unauthorized.
