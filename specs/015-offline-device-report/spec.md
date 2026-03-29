# Feature Specification: Offline Device Report

**Feature Branch**: `015-offline-device-report`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Create a menu operation that scans org inventory and lists devices offline for a user-definable duration with a default of 48 hours, displays results on screen and saves human-friendly CSV to data folder"

## Assumptions

- The Mist API `listOrgDevicesStats` endpoint (`/api/v1/orgs/{org_id}/stats/devices`) provides `last_seen` (epoch seconds), `status` (`connected`/`disconnected`), `name`, `serial`, `mac`, `model`, `type`, and `site_id` for each device. This endpoint supports `status` and `type` query filters and is accessed via `mistapi.api.v1.orgs.stats.listOrgDevicesStats()`.
- "Offline" means the device `status` is not `connected` AND the device's `last_seen` timestamp is older than the user-specified duration threshold.
- All device types are in scope: access points (APs), switches, and gateways.
- The operation is read-only; it does not modify any device configuration or state.
- The duration threshold is entered in hours for simplicity (NOC engineers think in hours/days, not minutes).
- Devices that have never connected (`last_seen` is null or zero) are included in the report as "Never Connected" with maximum offline duration.
- The screen display uses PrettyTable for consistent formatting.
- The CSV output follows existing MistHelper conventions: timestamped filename, saved to the `data/` directory, using `DataExporter`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Devices Offline Beyond Threshold (Priority: P1)

A NOC engineer selects the "Offline Device Report" menu operation. The system prompts for an offline duration threshold (defaulting to 48 hours). The system scans the entire org inventory, identifies all devices that have been offline for at least that duration, displays a summary table on screen with device name, type, site, MAC address, last seen time, and offline duration, then saves the full report as a human-readable CSV in the data folder.

**Why this priority**: This is the core value of the feature -- the primary reason the engineer runs it. Without this, nothing else matters.

**Independent Test**: Can be fully tested by selecting the menu operation, accepting the default 48-hour threshold, and verifying both the on-screen table and the CSV file contain the expected offline devices.

**Acceptance Scenarios**:

1. **Given** an organization with devices in various states, **When** the engineer selects this menu operation and accepts the default 48-hour threshold, **Then** the system displays a table of all devices offline for 48 hours or more, sorted by offline duration (longest first), and saves a CSV file to the data folder.
2. **Given** an organization where all devices are online, **When** the engineer runs the report, **Then** the system displays a clear message stating no devices were found offline beyond the threshold and no CSV is generated.
3. **Given** an organization with devices, **When** the engineer specifies a custom threshold (e.g., 12 hours), **Then** only devices offline for 12 hours or more appear in the results.

---

### User Story 2 - Summary Statistics on Screen (Priority: P2)

After scanning, the system displays a quick summary before the detailed table: total devices in org, total offline beyond threshold, breakdown by device type (APs, switches, gateways), and breakdown by site (top sites with most offline devices). This gives the engineer an at-a-glance understanding of the problem scope.

**Why this priority**: Summary context helps engineers prioritize response without reading every row. Depends on P1 data collection.

**Independent Test**: Can be tested by running the report against an org with known device states and verifying the summary counts match expected values.

**Acceptance Scenarios**:

1. **Given** an organization with a mix of online and offline devices, **When** the report runs, **Then** the summary shows total org device count, total offline count, and per-type breakdown (APs: X, Switches: Y, Gateways: Z).
2. **Given** an organization with offline devices spread across sites, **When** the report runs, **Then** the summary lists the top 5 sites with the most offline devices.

---

### User Story 3 - Human-Friendly CSV Output (Priority: P2)

The CSV file saved to the data folder uses clear column headers (Device Name, Device Type, Site Name, MAC Address, Serial Number, Model, Last Seen, Offline Duration, Status), human-readable timestamps (not epoch), and offline duration expressed in days and hours (e.g., "3 days 12 hours"). The filename includes a timestamp so multiple runs do not overwrite each other.

**Why this priority**: The CSV is a deliverable the engineer shares with management or uses for ticketing. Readability is critical for non-technical consumers.

**Independent Test**: Can be tested by running the report and opening the CSV in a spreadsheet application to verify readability, column headers, and timestamp formatting.

**Acceptance Scenarios**:

1. **Given** a completed scan with offline devices, **When** the CSV is generated, **Then** it contains columns: Device Name, Device Type, Site Name, MAC Address, Serial Number, Model, Last Seen (formatted as YYYY-MM-DD HH:MM:SS), Offline Duration (e.g., "3 days 12 hours"), Status.
2. **Given** multiple report runs, **When** each run completes, **Then** each CSV has a unique timestamped filename (e.g., `OfflineDeviceReport_20260327_143000.csv`) and previous files are not overwritten.

---

### Edge Cases

- What happens when a device has a `last_seen` value of 0 or null (never connected)? It is included in the report with "Never Connected" as the last seen value and sorted to the top of the list.
- What happens when the user enters 0 hours as the threshold? The system rejects it with a message that the minimum threshold is 1 hour.
- What happens when the user enters non-numeric input for the threshold? The system displays an error and re-prompts or falls back to the default 48 hours.
- What happens when the organization has no devices? The system displays a clear message and exits gracefully.
- What happens when the API call fails or returns an error? The system logs the error and displays a user-friendly message suggesting the engineer check their API credentials or network connection.
- What happens when there are thousands of offline devices? The screen display shows the first 50 with a note about the full count, while the CSV contains all results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST scan the entire organization inventory across all sites and all device types (APs, switches, gateways) using a single `listOrgDevicesStats` call with `type="all"` and `status="all"`.
- **FR-001a**: System MUST pre-fetch all sites via `listOrgSites`, build a `site_id` → `site_name` lookup dict, and resolve site names in-memory for display and CSV output.
- **FR-002**: System MUST prompt the user for an offline duration threshold in hours, with a default value of 48 hours.
- **FR-003**: System MUST identify devices whose `status` is not `connected` and whose `last_seen` timestamp exceeds the user-specified threshold.
- **FR-004**: System MUST display results on screen in a formatted table, sorted by offline duration (longest first), limited to 50 rows with a total count shown.
- **FR-005**: System MUST save the complete results as a human-readable CSV in the `data/` folder with a timestamped filename.
- **FR-006**: System MUST display a summary before the detail table showing: total devices, total offline, per-type breakdown, and top 5 affected sites.
- **FR-007**: System MUST handle devices with null/zero `last_seen` values by treating them as "Never Connected" and including them in the report.
- **FR-008**: System MUST validate the user-entered threshold (minimum 1 hour, maximum 8760 hours / 1 year) and reject invalid input gracefully.
- **FR-009**: System MUST format the "Last Seen" column as a human-readable timestamp (YYYY-MM-DD HH:MM:SS) and the "Offline Duration" as days and hours (e.g., "3 days 12 hours").
- **FR-010**: System MUST be accessible as menu operation `158` in MistHelper's menu system, classified as `safe` in `OperationRegistry` (automated in `--test` mode using default 48-hour threshold).

### Key Entities

- **Device**: A network device (AP, switch, or gateway) in the Mist organization inventory. Key attributes: name, type, site, MAC address, serial number, model, status, last seen timestamp.
- **Offline Duration Threshold**: A user-configurable time period (in hours) that defines the minimum offline duration for a device to appear in the report. Default: 48 hours.
- **Offline Device Report**: The output artifact containing all devices exceeding the threshold, available both as an on-screen table and a CSV file.

## Clarifications

### Session 2026-03-27

- Q: Which Mist API endpoint should be used for scanning org device status? → A: `listOrgDevicesStats` (`/api/v1/orgs/{org_id}/stats/devices`) — confirmed via OpenAPI spec and mistapi library inspection. This is the only org-level endpoint that has both a `status` filter parameter (`connected`/`disconnected`/`all`) AND returns `last_seen`, `status`, `name`, `serial`, `mac`, `model`, `type`, `site_id` in the response. `searchOrgDevices` was initially considered but lacks `status` filter and does not return `last_seen`/`status`/`name`/`serial` fields.
- Q: How to query all device types (APs, switches, gateways) in a single scan? → A: Use `type="all"` in a single `listOrgDevicesStats` call. Confirmed working — already used in MistHelper at line 12058 (`OrgDeviceStatsExporter`) and lines 40445/42501 (`SiteInventoryHealthAnalyzer`). No need for three separate calls per type.
- Q: What menu number and OperationRegistry category? → A: Menu `158`, category `safe`. This is a read-only GET operation that uses the default 48-hour threshold in `--test` mode (no user interaction required). Follows the existing menu numbering sequence (157 is the current highest).
- Q: How to resolve `site_id` UUIDs to human-readable site names for the report? → A: Pre-fetch `listOrgSites` once at report start, build an ID-to-name lookup dict, join in-memory. This is the standard MistHelper pattern (used by `OrgDeviceStatsExporter`, `SiteInventoryHealthAnalyzer`, etc.) and avoids per-device API calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: NOC engineer can run the report and review results in under 60 seconds for an organization with up to 10,000 devices.
- **SC-002**: 100% of devices offline beyond the threshold are captured in both the screen output and CSV file (no missed devices).
- **SC-003**: The CSV file opens correctly in common spreadsheet tools (Excel, Google Sheets, LibreOffice Calc) without formatting issues or encoding errors.
- **SC-004**: An engineer with no prior MistHelper experience can understand and use the report output without additional documentation, based on clear column headers and human-readable formatting.
- **SC-005**: The operation handles organizations with zero devices, zero offline devices, or thousands of offline devices gracefully without errors or crashes.
