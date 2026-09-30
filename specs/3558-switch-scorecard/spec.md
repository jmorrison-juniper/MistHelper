# Feature Specification: Organization Switch Scorecard

**Feature Branch**: `3558-switch-scorecard`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "Menu 277 organization switch scorecard. The Mist Switches page shows Switch-AP Affinity, PoE Compliance, Version Compliance, Switch Uptime, Config Success, and Potential Anomalies for one site. No operation computes those tiles for every site of an organization. Every field is already in the listOrgDevicesStats payload that menu 15 pulls. SwitchScorecard.csv: one row per switch with site, name, model, version, predominant version for the model, version compliant, config status, AP count, affinity flag (more than 12 APs), APs with switch redundancy, PoE budget and draw per module, pending BIOS or FPGA version, backup partition version, fan and PSU errors, uptime days, and last trouble. SwitchScorecardBySite.csv: one row per site with the tile percentages. A console summary prints the org-wide percentages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Every Switch in an Organization (Priority: P1)

A NOC engineer runs menu 277 during normal health review. The engineer receives one row for each switch in the organization. The row gives site, identity, compliance, power, module, uptime, and anomaly fields.

**Why this priority**: This is the main value. It gives one organization-wide report instead of repeated site checks.

**Independent Test**: Run the operation with switch statistics for more than one site. Confirm that `data/SwitchScorecard.csv` has one row for each switch and all required fields.

**Acceptance Scenarios**:

1. **Given** an organization has switches in multiple sites, **When** the engineer runs menu 277, **Then** `data/SwitchScorecard.csv` contains one row for each switch.
2. **Given** a switch has version, model, AP, power, module, uptime, and trouble fields, **When** the report is written, **Then** the row contains those values in named columns.
3. **Given** a switch has no `module_stat`, **When** the report is written, **Then** the row has empty module columns and the operation continues.

---

### User Story 2 - Compare Sites by Scorecard Tile (Priority: P2)

A NOC engineer compares sites without opening each site page. The engineer receives one row for each site with the six scorecard tile percentages and the switch count behind each tile.

**Why this priority**: Site comparison shows where the engineer must look first.

**Independent Test**: Run the operation with switch statistics that include two sites. Confirm that `data/SwitchScorecardBySite.csv` has one row for each site and gives the six tile percentages with switch counts.

**Acceptance Scenarios**:

1. **Given** switches belong to two or more sites, **When** the site scorecard is written, **Then** each site row states Switch-AP Affinity, PoE Compliance, Version Compliance, Switch Uptime, Config Success, and Potential Anomalies percentages.
2. **Given** each site row has a tile percentage, **When** a reviewer reads the row, **Then** the same row states the switch count used for that percentage.
3. **Given** one site has zero switches, **When** the scorecard is written, **Then** the site is omitted from the site scorecard.

---

### User Story 3 - Use the Scorecard in Test Mode (Priority: P3)

A maintainer runs the safe test path to prove that the operation does not prompt. The operation writes both files under `data/` and prints an organization summary.

**Why this priority**: Test mode must stay unattended so the operation can run in local gates.

**Independent Test**: Run the safe test path for the operation. Confirm that no prompt appears and both output files are written under `data/`.

**Acceptance Scenarios**:

1. **Given** the operation runs through `--test`, **When** test execution reaches menu 277, **Then** it completes without a prompt.
2. **Given** the operation finishes, **When** the console output is reviewed, **Then** it states the organization-wide percentages for the six tiles.
3. **Given** the operation finishes, **When** the data folder is reviewed, **Then** both scorecard files exist under `data/`.

### Edge Cases

- If `SWITCH_AP_AFFINITY_LIMIT` is not set, use 12 APs as the default limit.
- If `SWITCH_AP_AFFINITY_LIMIT` is set to a valid positive integer, use that value as the limit.
- If `SWITCH_AP_AFFINITY_LIMIT` is invalid, use the default limit and state the fallback in the console output.
- If a switch has no `module_stat`, write empty module columns and do not raise an exception.
- If two versions tie for the predominant version for a model, choose a stable predominant version and state the selected value in each row.
- If a switch misses an optional anomaly field, treat that missing field as no anomaly for that field.
- If no switches are returned, write both files with headers and print zero-count summary values.

## Requirements *(mandatory)*

### Issue Acceptance Criteria

- The operation runs in `--test` with no prompt and writes both files under `data/`.
- The affinity threshold defaults to 12 APs and reads `SWITCH_AP_AFFINITY_LIMIT` from the environment when set.
- Version compliance compares each switch against the predominant version of its model inside the organization, and the row names both versions.
- A switch with no `module_stat` produces a row with empty module columns and no exception.
- The per-site file states the percentage for each tile and the switch count behind it.
- The wiring manifest `specs/3558-switch-scorecard/wiring.md` exists with every section of the contract.
- The release note fragment `changelog.d/issue-3558-switch-scorecard.md` exists.

### Functional Requirements

- **FR-001**: The operation MUST produce `data/SwitchScorecard.csv` with one row for each switch in the organization.
- **FR-002**: Each switch row MUST include site, name, model, version, predominant version for the model, version compliant, config status, AP count, affinity flag, APs with switch redundancy, PoE budget, PoE draw per module, pending BIOS or FPGA version, backup partition version, fan errors, PSU errors, uptime days, and last trouble.
- **FR-003**: The operation MUST produce `data/SwitchScorecardBySite.csv` with one row for each site that has one or more switches.
- **FR-004**: Each site row MUST state the percentage for Switch-AP Affinity, PoE Compliance, Version Compliance, Switch Uptime, Config Success, and Potential Anomalies.
- **FR-005**: Each site row MUST state the switch count used for each tile percentage.
- **FR-006**: The console summary MUST state organization-wide percentages for Switch-AP Affinity, PoE Compliance, Version Compliance, Switch Uptime, Config Success, and Potential Anomalies.
- **FR-007**: The operation MUST run in `--test` with no prompt and write both files under `data/`.
- **FR-008**: The affinity threshold MUST default to 12 APs and read `SWITCH_AP_AFFINITY_LIMIT` from the environment when set.
- **FR-009**: Version compliance MUST compare each switch against the predominant version of its model inside the organization.
- **FR-010**: Each switch row MUST name the switch version and the predominant version used for the version compliance decision.
- **FR-011**: A switch with no `module_stat` MUST produce a row with empty module columns and no exception.
- **FR-012**: The per-site file MUST state the percentage for each tile and the switch count behind it.
- **FR-013**: The wiring manifest `specs/3558-switch-scorecard/wiring.md` MUST exist with every section of the contract before implementation planning completes.
- **FR-014**: The release note fragment `changelog.d/issue-3558-switch-scorecard.md` MUST exist before the pull request is ready for review.
- **FR-015**: The detailed scorecard MUST use the same switch statistics source as menu 15, filtered to switches.
- **FR-016**: The operation MUST avoid a second pagination design and use the existing organization device statistics export path.
- **FR-017**: The switch detail report MUST identify switches whose AP count is greater than the affinity limit.
- **FR-018**: The site and organization Switch-AP Affinity percentage MUST represent switches at or below the active AP limit.
- **FR-019**: The site and organization PoE Compliance percentage MUST represent switches without a module whose draw exceeds its budget.
- **FR-020**: The site and organization Version Compliance percentage MUST represent switches that match the predominant version for their model.
- **FR-021**: The site and organization Switch Uptime percentage MUST represent switches with a positive uptime value.
- **FR-022**: The site and organization Config Success percentage MUST represent switches with a successful config status.
- **FR-023**: The site and organization Potential Anomalies percentage MUST represent switches that have at least one anomaly indicator.

### Key Entities

- **Switch Scorecard Row**: One switch and its site, identity, version, AP affinity, power, module, uptime, and anomaly values.
- **Site Scorecard Row**: One site and the six scorecard tile percentages with the switch counts behind them.
- **Organization Summary**: Organization-wide percentages for the same six scorecard tiles.
- **Affinity Limit**: The active AP count threshold that marks a switch as over the affinity limit.
- **Predominant Model Version**: The version seen most often for one switch model inside the organization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A test run completes with no prompt and writes both scorecard files under `data/`.
- **SC-002**: The detail file contains exactly one data row for each switch returned by the switch statistics source.
- **SC-003**: The site file contains exactly one data row for each site that has at least one switch.
- **SC-004**: Every site row contains six tile percentages and six switch count values.
- **SC-005**: Every switch row states both the switch version and the predominant version for its model.
- **SC-006**: A switch without `module_stat` appears in the detail file and has empty module columns.
- **SC-007**: The console summary displays the six organization-wide percentages in one run.
- **SC-008**: A valid `SWITCH_AP_AFFINITY_LIMIT` value changes the affinity decision in both the detail and site reports.

## Assumptions

- The target user is a NOC engineer who needs a safe organization-wide health report.
- A switch with no optional field remains in the report with an empty value for that field.
- A missing optional anomaly field does not create an anomaly by itself.
- A switch without a reported uptime does not count as successful for the Switch Uptime percentage.
- A switch without module power data does not fail PoE Compliance unless a module shows draw above budget.
- The wiring manifest and release note fragment are downstream deliverables for later steps.
