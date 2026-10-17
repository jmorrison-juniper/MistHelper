# Feature Specification: MistDSW Migration

**Feature Branch**: `jmorrison-juniper-spec-mistdsw-migration`

**Created**: 2026-10-15

**Status**: Planning complete. Implementation requires the release conditions in the plan.

**Input**: Consolidate MistDSW into MistHelper for issue [#4230](https://github.com/jmorrison-juniper/MistHelper/issues/4230).
Preserve useful workflows within one application, shared database, and Compose group.
Complete planning only. Do not implement product changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare Store Variables (Priority: P1)

A network operator prepares variables for one store or a batch of stores.
The operator reviews normalized addresses and errors before downloading a site-variable file.

**Why this priority**: Correct store addressing supports each later template and payload.

**Independent Test**: Prepare two synthetic stores without credentials, then compare the downloaded values with approved addressing examples.

**Acceptance Scenarios**:

1. **Given** a valid store address, **When** the operator generates variables, **Then** four consecutive store networks appear with valid gateways and DHCP ranges.
2. **Given** a nonaligned address, **When** the operator previews it, **Then** the normalized address appears and requires acknowledgment.
3. **Given** a batch with invalid rows, **When** the operator submits it, **Then** row-specific errors appear and no partial output becomes ready.
4. **Given** a valid batch, **When** the operator downloads its variables, **Then** each site has one column and each variable has one row.

### User Story 2 - Prepare Configuration Templates (Priority: P2)

An operator supplies their own switch or gateway export and receives a reviewed template.
The review distinguishes replaced settings, preserved settings, and removed metadata.

**Why this priority**: Operators need reusable templates without accidental changes to unrelated settings.

**Independent Test**: Transform synthetic switch and gateway exports independently of the store-variable workflow.

**Acceptance Scenarios**:

1. **Given** four supported switch networks, **When** the operator transforms the export, **Then** only their VLAN and subnet fields use site-variable references.
2. **Given** an approved gateway profile, **When** the operator transforms its export, **Then** ten network configurations and their DHCP settings appear.
3. **Given** several LAN ports or conflicting policies, **When** the operator previews changes, **Then** generation waits for explicit selections.
4. **Given** an export with credentials, **When** the operator previews it, **Then** secrets do not appear in the page, logs, or downloadable output.

### User Story 3 - Prepare Network and Service Payloads (Priority: P2)

An operator generates a consistent network and service bundle for manual review and deployment.
The application does not apply the bundle to Mist.

**Why this priority**: A complete bundle prevents drift between switch, gateway, network, and service definitions.

**Independent Test**: Generate a bundle from an approved profile without uploaded templates or store data.

**Acceptance Scenarios**:

1. **Given** an approved profile, **When** the operator generates a bundle, **Then** ten networks and four services use consistent names and references.
2. **Given** conflicting Guest or Realo settings, **When** the operator requests a bundle, **Then** generation stops with a profile error.
3. **Given** a valid bundle, **When** the operator views deployment guidance, **Then** the manual deployment order and production-change warning appear.

### Edge Cases

Reject malformed IPv4 values, IPv6 values, missing addresses, partial gateway columns, duplicate site names, and extra input columns.
Reject network and broadcast gateways, cross-subnet gateways, duplicate or overlapping store supernets, and DHCP ranges that contain a gateway.
Reject empty batches, oversized uploads, invalid JSON, duplicate JSON keys, and unexpected template shapes.
Do not select the first LAN port silently.
Do not drop a non-LAN tenant from a service policy silently.
Prevent path traversal, cross-session downloads, spreadsheet formulas, and disclosure of private exports.
If storage or export verification fails, show an error and leave the run unavailable for download.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preserve all four source workflows: store variables, switch templates, gateway templates, and network payload generation.
- **FR-002**: Support single-store input and the documented batch formats, including explicit VLAN gateways and optional management and WAN gateways.
- **FR-003**: Normalize each store into four `/24` networks within its `/22`, preserving valid explicit gateways.
- **FR-004**: Exclude gateway addresses from DHCP pools and validate every supplied gateway before generation.
- **FR-005**: Produce the transposed site-variable CSV with stable variable names, site order, and empty cells for absent optional variables.
- **FR-006**: Change only the supported switch VLAN and subnet fields. Preserve unrelated nonsecret fields.
- **FR-007**: Generate ten gateway network configurations, matching DHCP settings, selected LAN-port mappings, and reviewed service policies.
- **FR-008**: Produce ten individual network payloads, their combined reference, four service payloads, and their combined reference.
- **FR-009**: Preserve intentional site-variable references. Reject unknown references and inconsistent network, VLAN, gateway, or service definitions.
- **FR-010**: Require an approved addressing profile that resolves Guest VLAN, Guest subnet, and Realo subnet conflicts before output becomes ready.
- **FR-011**: Show validation errors, normalization changes, replacement scope, and metadata removal before download.
- **FR-012**: Provide a preparation page within MistHelper and an unattended preparation command using the same generation behavior.
- **FR-013**: Use one existing MistHelper database for run records and one existing Compose group. Introduce no feature-specific database or service.
- **FR-014**: Keep private inputs and outputs within managed storage. Restrict access to the submitting operator and expire artifacts after 24 hours.
- **FR-015**: Redact secrets at each output boundary. Reject exports whose secret fields cannot be identified safely.
- **FR-016**: Make no Mist or device changes. Preserve the source manual deployment sequence with an explicit production-change warning.
- **FR-017**: Prohibit source-code, test, template, and asset reuse until written permission or a suitable license covers the exact material.
- **FR-018**: Validate the completed specification, design, tasks, and checklist. This planning PR must contain no product code.

### Mist Cloud Transport Requirements

This preparation feature makes zero Mist Cloud requests and needs no API token.
Manual deployment remains outside the feature.
Any future automatic deployment needs a separate specification, typed confirmation, verified backups, and explicit mistapi method contracts.
No direct HTTP transport, WebSocket transport, or copied organization identifier is permitted.

### Key Entities

- **Store input**: Site name, source base, normalized supernet, optional gateways, and input row number.
- **Addressing profile**: Approved network names, VLANs, subnets, service rules, and review evidence.
- **Preparation run**: Operator ownership, selected workflow, profile revision, validation state, and expiration.
- **Artifact**: Verified output type, content digest, private location, and run relationship.
- **Validation finding**: Field or row, severity, reason, and required correction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All nine inspected source regression scenarios have independent synthetic acceptance tests with explicit expected values.
- **SC-002**: All four preparation workflows produce the approved output shapes. Every supported variable and network reference resolves.
- **SC-003**: A batch of 500 stores completes in five seconds or less on a four-core, 8 GB reference host, excluding file transfer.
- **SC-004**: Every invalid-input acceptance case produces a specific error and zero ready artifacts.
- **SC-005**: Secret-canary tests find zero secret values in pages, logs, errors, run records, and downloads.
- **SC-006**: Each workflow completes with zero cloud requests, zero new services, and zero feature-specific databases.
- **SC-007**: Unauthorized download tests deny every cross-session request. Expiration tests deny access after 24 hours.
- **SC-008**: Planning validation reports zero unresolved critical or high inconsistencies and complete requirement-to-task coverage.

## Assumptions

The source is CLI-only. There is no graphical interface to preserve.
The new preparation page supplements CLI workflows without replacing the current portal layout.
Service generation is included because source documentation and committed examples require services, although its network generator does not create them.
No source address, customer identifier, credential, or complete template becomes a default.
Operators provide their own exports and approve an addressing profile.
The first migration remains preparation-only. Automatic deployment is not an implied requirement.
The absent license is a reuse blocker, not evidence of permission.
The migration covers MistDSW only. MistHelper-Go, misthelper-devtools, and other repositories are excluded.
Performance and 24-hour retention are proposed acceptance limits, not measured source behavior.
