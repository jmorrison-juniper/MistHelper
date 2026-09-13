# Feature Specification: E911 BSSID Compliance Report

**Feature Branch**: `182-e911-bssid-report`  
**Created**: 2026-04-07  
**Status**: Draft  
**Input**: User description: "New menu operation (Menu 160) that generates a CSV report of all BSSIDs per radio on each AP across the entire Mist organization, organized by site and floor (map), for E911 compliance purposes."

## Assumptions

- The Mist API `listOrgApsMacs` endpoint (`GET /api/v1/orgs/{org_id}/devices/radio_macs`) is the purpose-built E911 endpoint that returns each AP's base MAC and its radio MAC addresses. Accessed via `mistapi.api.v1.orgs.devices.listOrgApsMacs()`.
- Each radio MAC base address produces exactly 16 BSSIDs by enumerating the last nibble from 0x0 to 0xF (e.g., base `5c5b35000040` yields `5c:5b:35:00:00:40` through `5c:5b:35:00:00:4f`).
- A dual-band AP has 2 radio MACs (32 BSSIDs); a tri-band AP has 3 radio MACs (48 BSSIDs). The count depends on the `radio_macs` array length returned by the API.
- Site physical addresses come from the `address` field in the site object returned by `listOrgSites`.
- AP-to-site and AP-to-map assignments come from `listOrgDevicesStats` (which includes `site_id` and `map_id` per device).
- Map names are retrieved per-site via `listSiteMaps` and cached in a `map_id -> map_name` lookup.
- The operation is read-only and classified as `safe` in OperationRegistry.
- BSSIDs are formatted as colon-separated MAC addresses (e.g., `5c:5b:35:00:00:40`) for E911 system compatibility.
- The `radio_macs` endpoint supports pagination via `limit` and `page` parameters for large organizations.
- APs not assigned to a map or site are still included in the report with "Unassigned" placeholders and flagged in the summary as compliance gaps.

## Clarifications

### Session 2026-04-07

- Q: How should the CSV rows be sorted for E911 compliance reviewers? → A: Sort by Site Name, then Map Name, then AP Name, then BSSID (location hierarchy). This groups BSSIDs by physical location, which is how E911 systems and compliance reviewers typically process the data (building-by-building, floor-by-floor).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate E911 BSSID Compliance Report (Priority: P1)

A NOC engineer selects Menu 160 ("E911 BSSID Compliance Report"). The system queries the Mist API for all AP radio MACs across the organization, resolves each AP's site name, site address, map/floor name, and AP name, then generates all derived BSSIDs. The output is a CSV file in the `data/` directory with one row per BSSID containing Site Name, Site Address, Map Name, AP Name, and BSSID. A summary is displayed on screen showing total sites, total APs, and total BSSIDs.

**Why this priority**: This is the entire value of the feature -- the E911 compliance report itself. Without this, the feature has no purpose.

**Independent Test**: Can be fully tested by selecting Menu 160, confirming the CSV is generated in `data/` with the correct columns and BSSID format, and verifying the on-screen summary counts.

**Acceptance Scenarios**:

1. **Given** an organization with APs assigned to sites with maps, **When** the engineer selects Menu 160, **Then** a CSV is generated in `data/` with filename `E911_BSSID_Report_YYYYMMDD_HHMMSS.csv` containing columns Site Name, Site Address, Map Name, AP Name, BSSID (one row per BSSID), and a summary is displayed on screen.
2. **Given** an organization with no APs, **When** the engineer selects Menu 160, **Then** the system displays a clear message ("No APs found in this organization") and no CSV is generated.
3. **Given** an AP with 3 radios (tri-band), **When** the report runs, **Then** that AP produces exactly 48 BSSID rows in the CSV (3 radios x 16 BSSIDs each).
4. **Given** an AP with 2 radios (dual-band), **When** the report runs, **Then** that AP produces exactly 32 BSSID rows in the CSV (2 radios x 16 BSSIDs each).

---

### User Story 2 - Compliance Gap Detection (Priority: P2)

After generating the report, the system displays a compliance gap summary identifying APs that lack a map/floor assignment. Since E911 requires mapping every BSSID to a physical location, APs without floor plans represent compliance risks.

**Why this priority**: The gap detection transforms this from a data dump into an actionable compliance tool. It depends on P1 data collection being complete.

**Independent Test**: Can be tested by having at least one AP in the org that is not placed on any map, running the report, and verifying the gap summary lists it.

**Acceptance Scenarios**:

1. **Given** an organization where some APs have no map assignment, **When** the report runs, **Then** the summary includes a "Compliance Gaps" section listing the count and names of APs without map assignments.
2. **Given** an organization where all APs are assigned to maps, **When** the report runs, **Then** the summary shows "No compliance gaps detected -- all APs are assigned to floor plans."
3. **Given** APs not assigned to any site, **When** the report runs, **Then** those APs appear in the CSV with "Unassigned" for Site Name, Site Address, and Map Name, and are flagged in the compliance gap summary.

---

### User Story 3 - SQLite Dual Output (Priority: P3)

The report uses MistHelper's `DataExporter.write_with_format_selection()` so that the BSSID data is also written to the SQLite database when the user has selected SQLite output mode, enabling historical tracking and queries.

**Why this priority**: Dual output is a standard MistHelper convention. The CSV is sufficient for immediate E911 filing; SQLite adds value for historical tracking and is low-effort since the infrastructure exists.

**Independent Test**: Can be tested by configuring MistHelper for SQLite output mode, running Menu 160, and verifying the data appears in the SQLite database with proper primary keys.

**Acceptance Scenarios**:

1. **Given** the user has selected SQLite output mode, **When** the report runs, **Then** the BSSID data is written to the SQLite database with `bssid` as the primary key.
2. **Given** the report is run twice, **When** the second run completes, **Then** the SQLite data is upserted (no duplicate BSSIDs), reflecting the latest AP and site assignments.

---

### Edge Cases

- What happens when an AP has no map assignment? It is included in the report with "Unassigned" as Map Name and flagged in the compliance gap summary.
- What happens when an AP has no site assignment? It is included with "Unassigned" for Site Name, Site Address, and Map Name, and flagged as a compliance gap.
- What happens when a site has no physical address configured? The Site Address column is left blank (empty string) for that site's entries.
- What happens when the organization has no APs? The system displays a clear message and exits without generating a CSV.
- What happens when the radio_macs endpoint returns paginated results for a large org? The system paginates through all results before processing.
- What happens when an AP MAC from radio_macs is not found in the device stats lookup? The AP is included with "Unknown" as AP Name and flagged in the summary as a data discrepancy.
- What happens when a map_id from device stats is not found in any site's maps? The Map Name is set to "Unknown Map" and flagged in the summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST query `listOrgApsMacs` to retrieve all AP radio MAC addresses across the organization, handling pagination for large organizations.
- **FR-002**: System MUST query `listOrgSites` to build a `site_id -> {name, address}` lookup dictionary for resolving site names and physical addresses.
- **FR-003**: System MUST query `listOrgDevicesStats` with `type="ap"` to build an `ap_mac -> {name, site_id, map_id}` lookup dictionary for resolving AP names and assignments.
- **FR-004**: System MUST query `listSiteMaps` for each site that contains APs to build a `map_id -> map_name` lookup dictionary.
- **FR-005**: System MUST generate 16 BSSIDs per radio MAC base address by enumerating the last nibble from 0x0 through 0xF.
- **FR-006**: System MUST format all BSSIDs as colon-separated MAC addresses (e.g., `5c:5b:35:00:00:40`) for E911 system compatibility.
- **FR-007**: System MUST produce CSV output with columns in this exact order: Site Name, Site Address, Map Name, AP Name, BSSID. Rows MUST be sorted by Site Name, then Map Name, then AP Name, then BSSID (location hierarchy) so that compliance reviewers can process the data building-by-building and floor-by-floor.
- **FR-008**: System MUST save the CSV to the `data/` directory with filename format `E911_BSSID_Report_YYYYMMDD_HHMMSS.csv`.
- **FR-009**: System MUST use `DataExporter.write_with_format_selection()` for dual CSV/SQLite output support.
- **FR-010**: System MUST display an on-screen summary after report generation showing: total sites processed, total APs processed, total BSSIDs generated, and any compliance gaps (APs without map assignments).
- **FR-011**: System MUST handle APs without map assignments by using "Unassigned" as the Map Name and flagging them in the compliance gap summary.
- **FR-012**: System MUST handle APs without site assignments by using "Unassigned" for Site Name, Site Address, and Map Name.
- **FR-013**: System MUST display a clear message and skip CSV generation when the organization has no APs.
- **FR-014**: System MUST be registered as Menu 160 in MistHelper's menu system, classified as `safe` in OperationRegistry, and support `--test` mode with no user interaction.
- **FR-015**: System MUST pre-fetch all lookup data (sites, device stats, maps) before processing to avoid per-device API calls, supporting organizations with 10,000+ APs efficiently.

### Key Entities

- **AP (Access Point)**: A wireless access point in the Mist organization. Key attributes: MAC address, name, site assignment, map/floor assignment, radio MAC addresses.
- **Radio MAC**: A base MAC address for one radio on an AP. Each AP has 2-3 radio MACs depending on band support (2.4 GHz, 5 GHz, 6 GHz).
- **BSSID**: A Basic Service Set Identifier derived from a radio MAC base. Each radio MAC produces 16 BSSIDs (last nibble 0x0-0xF). This is the atomic unit of the report.
- **Site**: A Mist site representing a physical location. Attributes: name, physical address, site ID.
- **Map (Floor Plan)**: A floor plan within a site where APs are placed. Attributes: name, map ID, parent site.
- **Compliance Gap**: An AP that lacks a map/floor assignment, representing a risk for E911 compliance since the BSSID cannot be mapped to a physical location.

### Primary Key Strategy for SQLite

```python
'generateE911BSSIDReport': {
    'type': 'natural_pk',
    'primary_key': ['bssid'],
    'indexes': ['site_name', 'ap_name', 'map_name']
}
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: NOC engineer can generate the complete E911 BSSID report in under 2 minutes for an organization with up to 10,000 APs.
- **SC-002**: 100% of BSSIDs derived from the API response are present in the CSV output -- no missing APs or BSSIDs.
- **SC-003**: The CSV file is directly importable into E911 compliance systems without manual reformatting (correct column order, colon-separated BSSID format).
- **SC-004**: All APs without map/floor assignments are identified in the compliance gap summary, enabling the engineer to remediate before filing.
- **SC-005**: The operation handles organizations with zero APs, partial site data, and mixed AP types (dual-band, tri-band) without errors or crashes.
- **SC-006**: An engineer with no prior MistHelper experience can understand the report output and compliance gap summary without additional documentation.
