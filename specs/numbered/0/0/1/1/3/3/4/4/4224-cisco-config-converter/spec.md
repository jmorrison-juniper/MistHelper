# Feature Specification: Mist Cisco Config Converter

**Feature Branch**: `jmorrison-juniper-4224-cisco-config-converter`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Integrate Mist Cisco config converter" (Issue #4224)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview a Configuration Conversion (Priority: P1)

A network operator uploads a Cisco IOS text file, provides a gateway-template name, selects a
documented Mist gateway-template type, and reviews the proposed settings and unsupported commands.

**Why this priority**: The preview lets an operator assess a conversion without changing the Mist cloud or requiring Mist credentials.

**Independent Test**: Use a valid sample without Mist credentials. Confirm that global IPv4
`ip name-server` values appear in `dns_servers` and unsupported commands remain visible.

**Acceptance Scenarios**:

1. **Given** a valid template name and global IPv4 `ip name-server` command, **When** the
   operator selects `standalone` or `spoke`, **Then** the proposal includes its name, type, and
   DNS addresses in `dns_servers`.
2. **Given** that Mist credentials are not configured, **When** the operator requests a preview, **Then** the portal completes the preview without requiring credentials.
3. **Given** an unsupported command or a documented conversion gap, **When** the portal parses the configuration, **Then** it identifies the unsupported item and does not present it as converted.

### User Story 2 - Export a Reviewed Proposal (Priority: P2)

An operator exports a conversion proposal after reviewing the parsed configuration and the proposed Mist settings.

**Why this priority**: A reviewed export lets an operator use or retain the proposed settings without applying a cloud change.

**Independent Test**: Convert a valid sample configuration, review the proposal, and export it. Confirm the exported content represents the proposal and contains no credentials.

**Acceptance Scenarios**:

1. **Given** a reviewed conversion proposal, **When** the operator exports it, **Then** the
   portal provides the request object, unsupported commands, and known gaps as JSON.
2. **Given** a configuration with unsupported items, **When** the operator exports its proposal, **Then** the unsupported items and feature gaps remain visible in the review or export.
3. **Given** an invalid configuration, **When** the operator requests an export, **Then** the portal rejects the request and explains the input problem.

### Edge Cases

- Empty or whitespace-only files, invalid UTF-8, unsupported suffixes, path-like names, null
  characters, and files above 16 MiB are rejected.
- IPv6, malformed, and unknown commands remain visible as unsupported input.
- A configuration with no supported commands produces no misleading proposal.
- A configuration with both supported and unsupported commands preserves the distinction during review and export.
- An edited or stale proposal cannot be exported until the operator creates and reviews a new preview.
- Preview and export write no configuration files and make no Mist API requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shared MistHelper portal MUST provide the converter as a navigation tab.
- **FR-002**: The converter MUST accept an uploaded Cisco IOS text file and process it in memory.
- **FR-003**: The converter MUST accept `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log`
  files up to 16 MiB. It MUST decode UTF-8 strictly and reject path-like names.
- **FR-004**: The converter MUST accept `standalone` and `spoke` template types. It MUST NOT
  claim hardware-role or hardware-model mappings.
- **FR-005**: The converter MUST map only global IPv4 `ip name-server` commands to `dns_servers`.
- **FR-006**: The converter MUST preserve IPv6, malformed, unknown, and other commands as unsupported.
- **FR-007**: The portal MUST allow preview without Mist credentials.
- **FR-008**: The converter MUST allow an operator to export the exact reviewed proposal as JSON.
  The export MUST include unsupported items and known gaps without credentials.
- **FR-009**: Preview and export MUST NOT create, update, assign, or delete Mist resources.
- **FR-010**: The converter MUST NOT store configuration content or credentials in files, logs, or browser storage.
- **FR-011**: The integration MUST use the existing MistHelper runtime and MUST NOT add a database, Redis service, or Compose stack.
- **FR-012**: The integration MUST preserve existing portal routes and behavior.
- **FR-013**: Tests MUST cover conversion, unsupported input, upload boundaries, review binding, export shape, and no disk writes without live credentials.
- **FR-014**: Browser tests MUST cover upload, template-type selection, review, and export after portal registration. New controls MUST have stable test identifiers.
- **FR-015**: The implementation MUST use original code and public contract facts. It MUST NOT copy protected code, mappings, text, or assets from the CC BY-NC 4.0 source repository.
- **FR-016**: Every converter POST MUST use the existing portal CSRF protection. Multipart preview MUST include its token, and JSON requests MUST send the `X-CSRFToken` header.
- **FR-017**: The converter MUST require a template name that contains 1 to 120 non-whitespace characters.

### Mist Cloud Transport Requirements

- Cloud apply is outside the first release and MUST NOT be implemented by these tasks.
- The verified SDK contract is documented for future planning only. It does not authorize a cloud write.

### Key Entities

- **Source Configuration**: The operator-provided Cisco IOS text and validated file metadata used as conversion input.
- **Conversion Proposal**: The proposed gateway-template request object, unsupported commands, and known gaps presented for review and export.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete the primary preview journey from file selection through proposal review without Mist credentials.
- **SC-002**: Every unsupported command and documented gap remains visible in preview and export.
- **SC-003**: The export contains only documented request fields and conversion notes.
- **SC-004**: Preview and export make no Mist request and write no configuration file.
- **SC-005**: Portal registration and browser acceptance pass in the feature branch.
- **SC-006**: Unit, route, edge-case, and browser tests cover the acceptance scenarios without live credentials.

## Assumptions

- The operator has access to the existing MistHelper web portal.
- The first release supports only global IPv4 `ip name-server` commands and template types `standalone` and `spoke`.
- IPv6, malformed, unknown commands, hardware roles, hardware models, and other settings remain unsupported.
- The upload limit is 16 MiB with the six text suffixes documented in the portal contract. MistHelper has no shared portal upload-size setting.
- Uploads are processed in memory. Preview and export do not call Mist or write configuration files.
- Cloud apply is deferred pending separate scope and approval.
- The Cisco blueprint registers in the shared portal. Register WAN Performance only when its package is present.
- The implementation uses original code and public contracts. It does not copy material from the CC BY-NC 4.0 source repository.
