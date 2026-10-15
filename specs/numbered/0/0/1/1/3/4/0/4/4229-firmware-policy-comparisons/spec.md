# Feature Specification: Firmware policy comparisons

**Feature Branch**: `jmorrison-juniper-firmware-policy-comparisons`

**Created**: 2026-10-15

**Status**: Draft

**Input**: Issue #4229 requests inspectable saved, current, and proposed firmware
policies, historical inspection, clear preparation phases, safe preparation
locking, maximum supported list pages, and a highest-version initial selection.
The complete user feedback and confirmed scope are recorded in issue #4229.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Examine changes before confirmation (Priority: P1)

An operator expands a verified organization or site row before configuration
or restoration. The row shows saved, current, and proposed firmware policies.
It marks changed values with text and visual emphasis.

**Why this priority**: Operators must detect incorrect changes before approval.

**Independent Test**: Prepare synthetic policies in each workflow and expand a
row without entering a confirmation word.

**Acceptance Scenarios**:

1. **Given** verified configuration backups, **When** the operator expands a
   row, **Then** saved, current, and proposed policies show explicit differences.
2. **Given** verified restoration preparation, **When** the operator expands a
   row, **Then** historical policies and recovery policies remain distinguishable.
3. **Given** a missing site policy, **When** a comparison appears, **Then**
   inherited policy is not labeled disabled or empty.
4. **Given** changed current settings, **When** a row is read again, **Then**
   its observation time changes but the prepared plan does not change.

### User Story 2 - Inspect historical policies without restoration (Priority: P1)

An operator selects a historical backup in recovery and inspects its firmware
policies. An explicit comparison control reads current policies without
preparation, backup creation, confirmation, or settings writes.

**Why this priority**: Recovery investigation must not start a restoration.

**Independent Test**: Inspect a historical bundle before and after a synthetic
settings change and compare the unchanged bundle bytes.

**Acceptance Scenarios**:

1. **Given** a verified bundle, **When** a record is viewed, **Then** only
   supported firmware policy fields and the snapshot time appear.
2. **Given** a viewed record, **When** current comparison is requested,
   **Then** current differences show their observation time.
3. **Given** foreign or changed ownership, **When** inspection is requested,
   **Then** the request fails without exposing saved values.
4. **Given** a ready restoration, **When** inspection occurs, **Then** its
   restoration proof remains unused.

### User Story 3 - Understand and control preparation (Priority: P2)

An operator sees distinct capture, freshness, private save, and verification
phases. Preparation cannot repeat while its result is pending or ready.
A definite preparation failure permits a deliberate retry.

**Why this priority**: Repeated progress must not imply duplicate backups.

**Independent Test**: Hold preparation, reload the browser, and simulate both
definite failure and unavailable status.

**Acceptance Scenarios**:

1. **Given** running or ready preparation, **When** the operator clicks or
   reloads, **Then** the preparation control remains locked.
2. **Given** definite preparation failure, **When** the operator retries,
   **Then** one new preparation starts.
3. **Given** uncertain transport or application status, **When** the browser
   reports the failure, **Then** it does not authorize automatic repetition.
4. **Given** mixed numeric version names, **When** a model is first selected,
   **Then** the highest available version is selected.

### Edge Cases

- Empty, missing, disabled, inherited, and malformed policy values differ.
- Normalized schedule defaults differ from saved raw values.
- Unknown policy keys, private siblings, and masked values must not escape.
- A missing scope, replaced bundle, unavailable worker, or failed read stops
  comparison and shows an explicit error.
- Large selections retain bounded row responses and complete pagination.
- A manually selected version remains selected after checkbox reselection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both workflows MUST provide accessible expandable comparisons
  before typed confirmation.
- **FR-002**: Inspection MUST expose only known fields within `auto_upgrade`,
  `switch.auto_upgrade`, `ssr.auto_upgrade`, and `juniper_srx.auto_upgrade`.
- **FR-003**: Each comparison MUST label snapshot time and current observation
  time. It MUST disclose normalization and distinguish missing policy from disabled policy.
- **FR-004**: Historical inspection MUST use existing verified private bundles
  without rewriting them or creating another backup.
- **FR-005**: Inspection MUST preserve ownership, membership, source integrity,
  request admission, and complete private backup requirements.
- **FR-006**: Inspection MUST NOT consume proofs, prepare restoration, apply
  settings, or execute firmware upgrades.
- **FR-007**: Preparation MUST remain locked through pending, unknown, and ready
  status. Only definite preparation failure or deliberate selection change can permit preparation again.
- **FR-008**: Progress MUST explain separate initial reads, freshness reads,
  private save, and local verification. Counts MUST refer to their named phase.
- **FR-009**: Supported lists MUST use their documented maximum page size and
  complete pagination. Single-target settings reads MUST remain complete.
- **FR-010**: Initial model selection MUST select the highest naturally ordered
  available version without replacing a later manual choice.
- **FR-011**: Existing exact confirmation words and application freshness checks
  MUST remain required.

### Mist Cloud Transport Requirements

Existing checked SDK operations remain authoritative: `getOrg`,
`listOrgSites`, `getOrgSettings`, `getSiteSetting`, `listMspOrgs`,
`getOrgInventory`, device model/version catalogs, and `getSelfApiUsage`.
Comparison uses only these read operations. Tests must cover rejected status,
complete pagination, quota admission, ownership, and secret redaction.
No direct HTTP or firmware execution method is permitted.

### Key Entities

- **Saved policy**: A firmware-only view from an immutable verified bundle.
- **Current policy**: A firmware-only read with an explicit observation time.
- **Proposed policy**: The policy effect of an already prepared private plan.
- **Comparison row**: One supported field with presence, values, and differences.
- **Preparation phase**: A named operation with its own observed counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both workflows show all four supported policy types for one
  expanded row without exposing unrelated values. At 800 pixels, field names,
  values, and differences remain visible without horizontal comparison scrolling.
- **SC-002**: Historical inspection and comparison create zero backups and
  perform zero settings writes.
- **SC-003**: A 4,001-target selection remains complete while each requested
  comparison returns at most one scope.
- **SC-004**: Repeated preparation clicks and reloads create one preparation
  until a definite failure or deliberate selection change.
- **SC-005**: Numeric version ordering selects the highest version for all
  supported hardware classes on first selection.

## Assumptions

- Parent owns production investigation, connected acceptance, and release.
- This branch uses synthetic evidence only.
- Current comparison is explicit and does not authorize application.
- Historical files retain their existing private retention and format.
- No new menu or general raw-data browser is required.
- Two capture passes are expected because freshness checks are mandatory.
