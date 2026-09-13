# Feature Specification: Org Config Export/Import (Cross-Org Migration)

**Feature Branch**: `191-org-config-export-import`
**Created**: 2026-05-14
**Status**: Draft
**Input**: User description: "Two new menu operations (130/131) for exporting org-level WAN/gateway configuration from one Mist org and importing into a different org"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Org WAN/Gateway Configuration (Priority: P1)

A NOC engineer needs to migrate WAN/gateway infrastructure configuration from a staging org to a production org. They select Menu 176, which retrieves all 6 org-level config types (service policies, services, gateway device profiles, VPNs, networks, gateway templates) and saves them into a single timestamped JSON bundle in the `data/` directory.

**Why this priority**: Export is the prerequisite for import. Without a reliable, complete export, no migration is possible. This is the foundational operation.

**Independent Test**: Can be fully tested by running Menu 130 against any org with WAN/gateway config. The output JSON file can be inspected to verify all 6 object types are present, correctly structured, and contain metadata.

**Acceptance Scenarios**:

1. **Given** a connected Mist org with gateway templates, VPNs, networks, services, service policies, and gateway device profiles configured, **When** the user selects Menu 176, **Then** a single JSON file is saved to `data/OrgConfig_Export_{org_name}_{timestamp}.json` containing all 6 object types with source org_id, export timestamp, and MistHelper version metadata.
2. **Given** a connected Mist org with some config types empty (e.g., no VPNs), **When** the user selects Menu 176, **Then** the export completes successfully with empty arrays for the missing types, and the user sees a summary showing counts per type (including zero counts).
3. **Given** the export process encounters an API error for one config type, **When** the error occurs, **Then** the export continues with remaining types, logs the error, and the summary clearly indicates which type failed.

---

### User Story 2 - Import Org Config Into Destination Org (Priority: P1)

A NOC engineer has an export bundle from a source org and wants to import it into their current org (configured in `.env`). They select Menu 177, choose the export file, and the system creates all config objects in the destination org while skipping any that conflict with existing objects.

**Why this priority**: Import is the other half of the migration workflow and equally critical. Without import, export has no value.

**Independent Test**: Can be tested by first running an export (User Story 1), then running Menu 131 against a different org (or a clean org). Verify objects are created, conflicts are detected, and the summary report is accurate.

**Acceptance Scenarios**:

1. **Given** a valid export bundle and a destination org with no conflicting objects, **When** the user selects Menu 177, confirms the import, **Then** all objects from the bundle are created in the destination org and a success summary is displayed showing each object created by type and name.
2. **Given** a valid export bundle and a destination org where some objects already exist with the same name, **When** the user confirms the import, **Then** conflicting objects are skipped, non-conflicting objects are created, and the final report shows which objects were imported, skipped (with conflict reason), or failed.
3. **Given** a valid export bundle, **When** the user is prompted for confirmation, **Then** they must type "IMPORT" to proceed, and any other input cancels the operation gracefully.

---

### User Story 3 - Conflict Detection and Reporting (Priority: P1)

Before creating any objects in the destination org, the import process checks each object against existing objects using name match, ID match, and IP/subnet overlap detection. A comprehensive conflict report is presented after import completes.

**Why this priority**: Conflict detection prevents accidental overwrites and duplicate configurations. This is a safety-critical feature for production org operations.

**Independent Test**: Can be tested by importing the same bundle twice. The second run should skip all objects (detected as conflicts from the first import) and report 100% conflicts.

**Acceptance Scenarios**:

1. **Given** a destination org with a network named "Corporate-LAN", **When** importing a bundle containing a network also named "Corporate-LAN", **Then** that network is skipped with conflict reason "Name match: existing object 'Corporate-LAN' found".
2. **Given** a destination org with a network using subnet 10.0.0.0/24, **When** importing a bundle containing a network with an overlapping subnet 10.0.0.0/16, **Then** that network is skipped with conflict reason "IP/Subnet overlap: 10.0.0.0/16 overlaps with existing network 'Corporate-LAN' (10.0.0.0/24)".
3. **Given** an import that completed partially (some created, some skipped), **When** the import finishes, **Then** a table is displayed with three sections: successfully imported objects, skipped objects with conflict reasons, and failed objects with error details.

---

### User Story 4 - Cross-Reference ID Remapping (Priority: P2)

When importing objects that reference other objects by ID (e.g., a service policy referencing a service ID from the source org), the import process remaps those IDs to the newly created object IDs in the destination org.

**Why this priority**: Without ID remapping, imported service policies and gateway templates would reference non-existent IDs, making them non-functional. This is critical for a working migration but depends on the core import flow.

**Independent Test**: Can be tested by exporting a config where service policies reference specific services, importing into a clean org, and verifying the imported service policies reference the newly created service IDs (not the source org IDs).

**Acceptance Scenarios**:

1. **Given** a service policy in the export bundle that references service ID "abc-123" from the source org, **When** service "abc-123" is imported as new ID "xyz-789" in the destination org, **Then** the service policy is created with the reference updated to "xyz-789".
2. **Given** a service policy that references a service ID that was skipped due to conflict, **When** the import processes that service policy, **Then** the system attempts to find the matching existing object in the destination org by name and remaps the reference. If no match is found, the service policy is skipped with an explanation.

---

### User Story 5 - Idempotent Re-Import (Priority: P3)

Running the same import file against the same destination org multiple times produces the same result -- all objects are detected as conflicts on subsequent runs and skipped cleanly.

**Why this priority**: Idempotency provides operational safety. Engineers can retry without fear of creating duplicates.

**Independent Test**: Run import twice with the same file against the same org. Verify the second run reports all objects as "skipped (conflict)" with zero new creates.

**Acceptance Scenarios**:

1. **Given** a successful first import of a bundle, **When** the same bundle is imported again into the same org, **Then** all objects are skipped as conflicts, zero objects are created, and the report clearly shows this is a repeat import.

---

### Edge Cases

- What happens when the export file is corrupt or not valid JSON? The import should detect this immediately and display a clear error message without proceeding.
- What happens when the export file was created by a different MistHelper version? The import should display a warning but allow the user to proceed.
- What happens when the destination org has API rate limits triggered during import? The existing adaptive delay system handles retry logic; the import continues after delays.
- What happens when the user cancels mid-import (Ctrl+C)? Objects already created remain in the destination org. The user is informed that a partial import occurred and can re-run (idempotent behavior skips already-created objects).
- What happens when a referenced object type was entirely skipped in the export (e.g., all services were empty)? The import handles empty arrays gracefully and continues with other types.
- What happens when the export bundle references an object type not supported by the destination org's subscription? The API error is caught, logged, and included in the failure section of the report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST export all 6 org-level config types (service policies, services, gateway device profiles, VPNs, networks, gateway templates) into a single JSON bundle file.
- **FR-002**: System MUST include metadata in the export bundle: source org_id, source org_name, export timestamp, MistHelper version, and object counts per type.
- **FR-003**: System MUST save the export file to the `data/` directory with naming pattern `OrgConfig_Export_{org_name}_{timestamp}.json`.
- **FR-004**: System MUST produce human-readable JSON output (indented formatting).
- **FR-005**: System MUST filter device profiles to gateway type only during export (`type=gateway` parameter).
- **FR-006**: System MUST detect conflicts before importing by checking name match, ID match, and IP/subnet overlap for applicable object types.
- **FR-007**: System MUST automatically import objects with no detected conflicts using the corresponding create API endpoint.
- **FR-008**: System MUST skip objects with detected conflicts, log the conflict reason, and include them in the final summary report.
- **FR-009**: System MUST strip source-org-specific fields (`id`, `org_id`, `created_time`, `modified_time`) before creating objects in the destination org.
- **FR-010**: System MUST remap cross-reference IDs (e.g., service IDs referenced in service policies) to newly created IDs in the destination org.
- **FR-011**: System MUST require explicit typed confirmation ("IMPORT") before proceeding with the import operation.
- **FR-012**: System MUST display a post-import summary table showing objects imported, skipped (with reason), and failed (with error).
- **FR-013**: System MUST handle partial export failures gracefully, continuing with remaining types and reporting which types failed.
- **FR-014**: System MUST be idempotent -- re-importing the same bundle should detect all objects as conflicts and skip them.
- **FR-015**: System MUST use the existing adaptive delay / rate limiting system for all API calls during export and import.
- **FR-016**: System MUST import objects in dependency order: networks and services first, then VPNs and gateway templates, then device profiles, then service policies (since service policies reference services, and gateway templates may reference networks).
- **FR-017**: System MUST validate the export file format and structure before attempting import, displaying a clear error for invalid files.
- **FR-018**: System MUST wrap all user input with `safe_input()` for EOF handling in SSH/container contexts.

### Key Entities

- **Export Bundle**: A JSON file containing all 6 config object types plus metadata. Represents a point-in-time snapshot of an org's WAN/gateway configuration.
- **Config Object**: An individual org-level configuration item (service policy, service, gateway device profile, VPN, network, or gateway template) with its full API representation.
- **Conflict Record**: A detection result indicating why an object cannot be imported (name match, ID match, or IP/subnet overlap) with references to the conflicting existing object.
- **ID Remap Table**: A mapping from source org object IDs to destination org object IDs, built during import as objects are created, used to update cross-references.
- **Import Report**: A structured summary of the import operation showing counts and details of imported, skipped, and failed objects by type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A NOC engineer can export all 6 WAN/gateway config types from one org and import them into a different org in under 10 minutes for a typical deployment (50 or fewer objects total).
- **SC-002**: 100% of name-based conflicts are detected before any objects are created in the destination org.
- **SC-003**: Re-running the same import bundle against the same org results in zero new objects created (idempotent behavior).
- **SC-004**: Cross-reference IDs (e.g., service IDs in service policies) are correctly remapped in 100% of cases where both the referenced and referencing objects are imported.
- **SC-005**: The post-import summary report accurately reflects the outcome of every object (imported, skipped, or failed) with zero discrepancies.
- **SC-006**: The entire export/import workflow is completable by a junior NOC engineer without requiring documentation beyond the on-screen prompts.

## Scope Boundaries

### In Scope

- Org-level export and import of the 6 specified config object types
- Conflict detection by name, ID, and IP/subnet overlap
- Cross-reference ID remapping between imported objects
- Post-import summary reporting
- Menu 176 (export) and Menu 177 (import) integration into existing menu system

### Out of Scope

- Site-level configuration migration
- Selective import (choosing which objects to import per type)
- Two-way sync or diff/merge between orgs
- Modifying or updating existing objects in the destination org (create-only)
- Migrating device assignments, device-to-site mappings, or site-level overrides
- Backup/restore functionality (this is migration, not backup)

## Clarifications (Post-Review)

### Cross-Reference Dependency Graph

The 6 object types have the following reference relationships, which dictate import order and ID remapping:

| Object Type | References | Referenced By |
| - | - | - |
| **networks** | standalone (no refs) | VPNs, gateway templates, service policies |
| **services** | standalone (no refs) | service policies |
| **VPNs** | network IDs in `networks[]` | gateway templates |
| **gateway templates** | network IDs, VPN IDs | device profiles |
| **device profiles** | gateway template IDs | (none in this scope) |
| **service policies** | service IDs, network IDs in rules | (none in this scope) |

**Import order** (FR-016): networks → services → VPNs → gateway templates → device profiles → service policies

**ID remapping scope**: Top-level ID reference fields only. Nested objects within gateway templates (port configs, routing policies, DHCP relay targets) are NOT remapped in v1 — this is documented as a known limitation.

### Import File Selection UX

Menu 131 lists all `OrgConfig_Export_*.json` files found in the `data/` directory, numbered for selection. The user picks by number (consistent with existing menu patterns). If only one file exists, it is auto-selected with a confirmation prompt. If no files exist, a clear message directs the user to run Menu 130 first.

### IP/Subnet Overlap Detection Scope

IP/subnet overlap detection applies to:
- **networks**: `subnet` field (CIDR notation) — primary overlap target
- **services**: `addresses[]` field when present (IP addresses or CIDR ranges)
- **VPNs**: No direct IP fields — overlap detected indirectly through referenced networks

Service policies, device profiles, and gateway templates do NOT have direct IP fields requiring overlap checks.

### Dry-Run Mode

Import supports an optional dry-run mode. When selected, the import performs all conflict detection and reports what WOULD happen without making any API calls. The user is prompted: "Run as dry-run (preview only)? [Y/n]" before the "IMPORT" confirmation. Dry-run output uses the same summary table format but prefixes all actions with "[DRY RUN]".

## Assumptions

- The user has API credentials configured in `.env` with read access to the source org (for export) and write access to the destination org (for import).
- The mistapi SDK (0.59+) provides all necessary create API endpoints for the 6 config object types.
- Export and import operate on different orgs -- the user switches the org context in `.env` between export and import, or provides the source org credentials at export time.
- The export file format is forward-compatible within MistHelper versions (minor version differences do not break import).
- Network/service objects use standard IP address and subnet notation (CIDR) for overlap detection.
- The 6 config object types cover the essential WAN/gateway infrastructure; additional types can be added in future iterations.
- Rate limiting from the Mist API is handled transparently by the existing adaptive delay system.
- The destination org has sufficient license entitlements for the imported configuration types.
