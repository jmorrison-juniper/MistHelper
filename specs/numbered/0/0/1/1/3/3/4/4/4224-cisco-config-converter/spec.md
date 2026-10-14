# Feature Specification: Mist Cisco Config Converter

**Feature Branch**: `jmorrison-juniper-4224-cisco-config-converter`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Integrate Mist Cisco config converter" (Issue #4224)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview a Configuration Conversion (Priority: P1)

A network operator opens the converter in the MistHelper portal, provides a Cisco IOS configuration, selects a gateway role and hardware model, reviews the parsed input, and inspects the proposed Mist settings.

**Why this priority**: The preview lets an operator assess a conversion without changing the Mist cloud or requiring Mist credentials.

**Independent Test**: Use a valid sample configuration without Mist credentials. Confirm that the operator can review the parsed configuration and a proposed conversion.

**Acceptance Scenarios**:

1. **Given** a valid Cisco IOS configuration, **When** the operator selects a gateway role and hardware model, **Then** the portal shows the parsed configuration and conversion proposal.
2. **Given** that Mist credentials are not configured, **When** the operator requests a preview, **Then** the portal completes the preview without requiring credentials.
3. **Given** an unsupported command or a documented conversion gap, **When** the portal parses the configuration, **Then** it identifies the unsupported item and does not present it as converted.

### User Story 2 - Export a Reviewed Proposal (Priority: P2)

An operator exports a conversion proposal after reviewing the parsed configuration and the proposed Mist settings.

**Why this priority**: A reviewed export lets an operator use or retain the proposed settings without applying a cloud change.

**Independent Test**: Convert a valid sample configuration, review the proposal, and export it. Confirm the exported content represents the proposal and contains no credentials.

**Acceptance Scenarios**:

1. **Given** a completed conversion proposal, **When** the operator exports it, **Then** the portal provides the proposed settings as JSON.
2. **Given** a configuration with unsupported items, **When** the operator exports its proposal, **Then** the unsupported items and feature gaps remain visible in the review or export.
3. **Given** an invalid configuration, **When** the operator requests an export, **Then** the portal rejects the request and explains the input problem.

### User Story 3 - Create a Gateway Template (Priority: P3)

An operator creates a new gateway template in the selected Mist organization from a reviewed proposal. This action does not update an existing template or assign a template to a site or device.

**Why this priority**: Apply completes the conversion workflow while keeping cloud changes behind explicit operator review and confirmation.

**Independent Test**: Use mocked Mist responses to verify that valid confirmation creates one new organization template, while missing credentials or rejected confirmation prevents a cloud request.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal and valid Mist credentials, **When** the operator selects the target organization and types the required confirmation phrase, **Then** the portal creates one new organization gateway template and reports the result.
2. **Given** missing credentials, **When** the operator views a proposal, **Then** preview and export remain available, and template creation is unavailable.
3. **Given** a template creation request without the required confirmation, **When** the operator submits it, **Then** the portal makes no Mist cloud request.
4. **Given** a failed Mist request, **When** the portal reports the failure, **Then** it does not report success or expose credentials.
5. **Given** an existing gateway template, **When** the operator creates a template from the proposal, **Then** the portal does not update, replace, or assign the existing template.

### Edge Cases

- An empty configuration, invalid encoding, malformed line, or file larger than the verified existing portal upload limit is rejected with a clear message.
- An uploaded file with an unsupported type or a path outside the configured input area is rejected.
- A configuration with no supported commands produces no misleading proposal.
- A configuration with both supported and unsupported commands preserves the distinction during review and export.
- A proposal that does not match the selected role or hardware model cannot be applied.
- An interrupted or failed apply request reports an unknown or failed outcome accurately and does not claim success.
- Logs, generated files, and browser storage do not contain Mist credentials or passwords.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST provide the converter as a tab in the existing MistHelper web portal.
- **FR-002**: The portal MUST allow an operator to upload or select a Cisco IOS configuration for conversion.
- **FR-003**: The portal MUST validate the configuration file type, size, encoding, and path before processing it.
- **FR-004**: The portal MUST allow the operator to select a gateway role and hardware model before conversion.
- **FR-005**: The portal MUST show the parsed configuration and conversion proposal for review before export or apply.
- **FR-006**: The portal MUST identify unsupported commands and documented conversion limits or feature gaps instead of presenting them as converted settings.
- **FR-007**: The portal MUST allow preview without Mist credentials.
- **FR-008**: The portal MUST allow an operator to export a reviewed proposal as JSON without applying it to the Mist cloud. The export MUST include unsupported items and known gaps.
- **FR-009**: The portal MUST require valid Mist credentials, a selected organization, a reviewed proposal, and typed confirmation before it creates a new organization gateway template.
- **FR-010**: The portal MUST report template creation success or failure accurately and MUST NOT indicate success after a failed or indeterminate request.
- **FR-011**: The portal MUST use the existing MistHelper credential configuration and MUST NOT store credentials in browser storage, uploaded configurations, generated files, logs, or test fixtures.
- **FR-012**: The integration MUST use the existing MistHelper runtime, Compose group, database, and Redis service where required. It MUST NOT add a separate application database or an independent Compose stack.
- **FR-013**: The integration MUST preserve existing MistHelper portal routes and behavior.
- **FR-014**: Unit and integration tests MUST cover parsing and conversion rules, unsupported commands, invalid inputs, preview and export, and gateway template creation using mocked SDK responses without live Mist credentials.
- **FR-015**: Browser tests MUST cover upload, role and hardware selection, review, and proposal preview. New interactive controls MUST have stable test identifiers.
- **FR-016**: The implementation MUST use original code and assets unless maintainers approve a license-compatible path. It MUST NOT copy source code or images from the source repository before that approval.

### Mist Cloud Transport Requirements

- Cloud apply MUST use a working `mistapi` REST method. The selected method and its input and result contract MUST be recorded in planning before implementation.
- The feature does not require an owned WebSocket transport.
- Contract tests MUST verify SDK authentication, endpoint parity, failure safety, and secret redaction for cloud apply. Tests MUST use mocked SDK responses.

### Key Entities

- **Source Configuration**: The operator-provided Cisco IOS text and validated file metadata used as conversion input.
- **Gateway Selection**: The operator-selected gateway role and hardware model that constrain the conversion.
- **Conversion Proposal**: The parsed configuration, proposed Mist settings, unsupported items, and known conversion gaps presented for review.
- **Apply Request**: The reviewed proposal, target organization, operator confirmation, and result of a requested Mist cloud change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete the primary preview journey from file selection through proposal review without Mist credentials.
- **SC-002**: Every unsupported command and documented feature gap in the tested sample configurations is visible before export or apply.
- **SC-003**: Every template creation test without valid credentials or the required typed confirmation results in zero cloud requests.
- **SC-004**: All tested successful and failed template creation outcomes are reported accurately, with no credentials in outputs, files, browser storage, or logs.
- **SC-005**: The existing portal route and behavior tests pass without feature-related regressions.
- **SC-006**: Unit, integration, edge-case, and browser tests cover the acceptance scenarios without live Mist credentials.

## Assumptions

- The operator has access to the existing MistHelper web portal.
- The first release supports Cisco IOS configuration input and gateway roles and hardware models identified by the converter's approved mapping.
- The plan proposes creation of a new organization gateway template as the apply effect. This cloud effect is not confirmed by the issue and requires product-owner approval before implementation.
- The conversion uses documented mappings and reports unsupported input. It does not promise full configuration parity.
- The proposal export uses JSON that matches the verified Mist gateway template request shape and includes unsupported items and known gaps.
- The feature uses the existing portal upload limit. The exact limit must be verified and recorded before implementation begins. Do not guess or add a feature-specific limit.
- Existing MistHelper credentials and shared services remain the only credentials and services used by the integration.
- Preview and export do not change the Mist cloud. New organization template creation is a separate, explicit action. It does not assign a template to a site or device.
- The issue's licensing constraint blocks source code and image reuse until maintainers approve a compatible path. A decision on source reuse is a prerequisite to implementation, not a reason to copy source material during specification.
