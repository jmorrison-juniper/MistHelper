# Feature Specification: Organization Access Point Scorecard

**Feature Branch**: `feat/3559-ap-scorecard`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 278 organization access point scorecard. The Mist Access Points page shows Connection Status, VLANs, Version Compliance, AP Switch Redundancy, and Potential Anomalies for one site, with green at 98.5 percent and red at 80 percent. No operation computes those tiles for every site. Every field is already in the listOrgDevicesStats payload. ApScorecard.csv: one row per AP with site, name, model, version, predominant version, version compliant, status, offline reason, inactive wired VLANs, switch redundancy count, power constrained, power operating mode, LLDP power allocated and needed, configuration reverted, last trouble, expiring certificate count, and uptime days. ApScorecardBySite.csv: one row per site with the tile percentages and the color band (green, orange, red). A console summary prints the org-wide percentages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export AP scorecard detail (Priority: P1)

An organization operator runs menu `278` to export a complete AP scorecard for all sites in the organization. The operator receives `ApScorecard.csv` in `data/`. The file has one row per AP and shows the AP site, identity, firmware, status, VLAN, redundancy, power, anomaly, certificate, and uptime fields needed to review health.

**Why this priority**: This is the main value. Operators need one file that shows which APs fail the same health checks that the Mist `Access Points` page shows per site.

**Independent Test**: Run the operation in `--test` mode. Confirm that it does not prompt. Confirm that `data/ApScorecard.csv` exists and has one row for each AP in the test payload, with all required columns filled from that payload.

**Acceptance Scenarios**:

1. **Given** an organization with AP device statistics, **When** the operator runs menu `278`, **Then** the AP detail export is written as `data/ApScorecard.csv`.
2. **Given** an AP has `inactive_wired_vlans` that is not empty, **When** the detail export is produced, **Then** that AP fails the VLAN tile and the row lists the VLAN IDs.
3. **Given** an AP has no `lldp_stat`, **When** the detail export is produced, **Then** the power columns are empty and the operation continues without an exception.

---

### User Story 2 - Summarize AP health by site (Priority: P1)

An organization operator receives `ApScorecardBySite.csv` in `data/`. The file has one row per site. Each row shows tile percentages and the color band for `Connection Status`, `VLANs`, `Version Compliance`, `AP Switch Redundancy`, and `Potential Anomalies`.

**Why this priority**: The site summary lets operators find weak sites first without opening each site on the Mist `Access Points` page.

**Independent Test**: Run the operation with a test payload that has APs in multiple sites. Confirm that `data/ApScorecardBySite.csv` exists, has one row per site, shows each tile percentage, and assigns the expected color band.

**Acceptance Scenarios**:

1. **Given** a site has AP health values at or above `98.5%`, **When** the site summary is produced, **Then** the related tile color band is `green`.
2. **Given** a site has AP health values above `80%` and below `98.5%`, **When** the site summary is produced, **Then** the related tile color band is `orange`.
3. **Given** a site has AP health values at or below `80%`, **When** the site summary is produced, **Then** the related tile color band is `red`.
4. **Given** APs have switch redundancy values of `1`, `2`, and `3` or more, **When** the site summary is produced, **Then** it reports counts for no redundancy, good redundancy, and excellent redundancy.

---

### User Story 3 - See organization-wide AP health (Priority: P2)

An organization operator sees a console summary with the organization-wide percentages for the same AP health tiles. The summary helps the operator decide if the organization needs immediate action before reviewing the CSV files.

**Why this priority**: The console summary gives a fast result in interactive and automated runs. It does not replace the CSV evidence.

**Independent Test**: Run the operation with a known test payload. Confirm that the console output reports the expected organization-wide percentages for all required tiles.

**Acceptance Scenarios**:

1. **Given** the organization has AP statistics for one or more sites, **When** the operation finishes, **Then** the console prints organization-wide percentages for `Connection Status`, `VLANs`, `Version Compliance`, `AP Switch Redundancy`, and `Potential Anomalies`.
2. **Given** the operation runs in `--test` mode, **When** it starts, **Then** it uses test-safe defaults, does not prompt, and still writes both output files under `data/`.

---

### User Story 4 - Prepare integration evidence (Priority: P3)

A maintainer receives the supporting feature files needed for integration and release tracking. The wiring manifest exists at `specs/3559-ap-scorecard/wiring.md` with every section required by the fleet contract. The release note fragment exists at `changelog.d/issue-3559-ap-scorecard.md`.

**Why this priority**: These files let the integration pull request add menu wiring and release notes without editing shared files in this feature step.

**Independent Test**: Confirm that the wiring manifest path exists and contains every contract section. Confirm that the release note fragment path exists and has one `### Added` heading with an issue `#3559` bullet.

**Acceptance Scenarios**:

1. **Given** the implementation phase is complete, **When** the maintainer checks `specs/3559-ap-scorecard/wiring.md`, **Then** the file exists and includes every required section from the fleet contract.
2. **Given** the implementation phase is complete, **When** the maintainer checks `changelog.d/issue-3559-ap-scorecard.md`, **Then** the file exists and records the AP scorecard addition for issue `#3559`.

### Edge Cases

- If an AP has no `lldp_stat`, the AP row shows empty LLDP power allocated and LLDP power needed values, and no exception occurs.
- If `inactive_wired_vlans` is empty or missing, the AP passes the VLAN tile.
- If `inactive_wired_vlans` has one or more VLAN IDs, the AP fails the VLAN tile and the row lists those VLAN IDs.
- If `switch_redundancy` is `1`, the AP counts as no redundancy.
- If `switch_redundancy` is `2`, the AP counts as good redundancy.
- If `switch_redundancy` is `3` or more, the AP counts as excellent redundancy.
- If a site has no APs in the input data, the site is not included in the per-site output.
- If an AP is offline and has an offline reason, the detail row keeps the reason so the operator can act on it.
- If a site percentage is exactly `98.5%`, the color band is `green`.
- If a site percentage is exactly `80%`, the color band is `red`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add menu `278` as the organization access point scorecard operation.
- **FR-002**: The operation MUST run in `--test` mode with no prompt and write both output files under `data/`.
- **FR-003**: The operation MUST create `data/ApScorecard.csv` with one row per AP.
- **FR-004**: Each `ApScorecard.csv` row MUST include site, AP name, model, version, predominant version, version compliant, status, offline reason, inactive wired VLANs, switch redundancy count, power constrained, power operating mode, LLDP power allocated, LLDP power needed, configuration reverted, last trouble, expiring certificate count, and uptime days.
- **FR-005**: The operation MUST create `data/ApScorecardBySite.csv` with one row per site.
- **FR-006**: Each `ApScorecardBySite.csv` row MUST include tile percentages and color bands for `Connection Status`, `VLANs`, `Version Compliance`, `AP Switch Redundancy`, and `Potential Anomalies`.
- **FR-007**: The color band MUST use the Mist `Access Points` page thresholds: `green` at `98.5%` or higher, `orange` above `80%` and below `98.5%`, and `red` at `80%` or lower.
- **FR-008**: The operation MUST count an AP with `switch_redundancy` value `1` as no redundancy, value `2` as good redundancy, and value `3` or more as excellent redundancy.
- **FR-009**: The per-site file MUST report no-redundancy, good-redundancy, and excellent-redundancy AP counts for each site.
- **FR-010**: The VLAN tile MUST fail for an AP when `inactive_wired_vlans` is not empty, and the AP detail row MUST list the VLAN IDs.
- **FR-011**: The operation MUST handle an AP with no `lldp_stat` by leaving LLDP power fields empty and continuing without an exception.
- **FR-012**: The operation MUST print a console summary with organization-wide percentages for all five tiles.
- **FR-013**: The operation MUST use fields already present in the organization AP device statistics payload for its scorecard values.
- **FR-014**: The wiring manifest MUST exist at `specs/3559-ap-scorecard/wiring.md` and contain every section required by the fleet contract.
- **FR-015**: The release note fragment MUST exist at `changelog.d/issue-3559-ap-scorecard.md`.
- **FR-016**: The release note fragment MUST have one `### Added` heading and one bullet that names issue `#3559`.

### Key Entities *(include if feature involves data)*

- **Access Point Scorecard Row**: One AP health record. It contains the AP site, identity, firmware compliance, operational status, VLAN health, redundancy health, power state, anomaly evidence, certificate count, and uptime.
- **Site Scorecard Row**: One site health summary. It contains the tile percentages and color bands for the APs at that site, plus redundancy category counts.
- **Organization Summary**: The organization-wide tile percentages that summarize all AP rows included in the run.
- **Tile Color Band**: The health category for a tile. It uses the Mist `Access Points` page thresholds: `green`, `orange`, or `red`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In `--test` mode, the operation completes without a prompt and writes `data/ApScorecard.csv` and `data/ApScorecardBySite.csv` in one run.
- **SC-002**: `ApScorecard.csv` has exactly one data row for each AP in the input payload.
- **SC-003**: `ApScorecardBySite.csv` has exactly one data row for each site that has one or more APs in the input payload.
- **SC-004**: Color band tests pass at the threshold boundaries: `98.5%` maps to `green`, a value between `80%` and `98.5%` maps to `orange`, and `80%` maps to `red`.
- **SC-005**: Redundancy tests pass for all required categories: `1` maps to no redundancy, `2` maps to good redundancy, and `3` or more maps to excellent redundancy.
- **SC-006**: An AP with inactive wired VLANs is visible in the AP detail export with the VLAN IDs listed and is counted as a VLAN tile failure.
- **SC-007**: An AP with no LLDP data is exported with empty LLDP power columns and no run failure.
- **SC-008**: The console summary reports all five organization-wide tile percentages in every successful run.
- **SC-009**: The support files required for integration are present before implementation is complete: `specs/3559-ap-scorecard/wiring.md` and `changelog.d/issue-3559-ap-scorecard.md`.

## Assumptions

- The feature-owned tests prove the handler no-prompt path and export-name seam. The integration pull request proves `MistHelper.py --test` and the final `data/` paths after menu `278` is registered.
- The source of the tile names, health meanings, and color thresholds is the Mist `Access Points` page.
- The operation is for organization-wide AP reporting, not a site-only report.
- The scorecard uses only data that is already in the organization AP device statistics payload.
- The predominant version is calculated per AP model within the report data unless an AP has explicit upgrade compliance data that defines the expected version.
- The potential anomalies tile passes for an AP that has no current trouble or configuration-reverted signal in the available data.
- Uptime is shown in days so operators can compare AP stability without converting seconds.
- Integration changes to shared files are deferred to the wiring manifest and are not made during this specification step.
