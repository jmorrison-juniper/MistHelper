# Feature Specification: Organization WAN Edge Scorecard

**Feature Branch**: `3560-wan-edge-scorecard`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 279 organization WAN edge scorecard. The Mist WAN Edges page shows Config Success, Version Compliance, WAN Edge Uptime, and Potential Anomalies for one site, and DHCP Pool Exhausted is one of the six Top Alerts. No operation computes DHCP pool use, VPN peer state, BGP peer state, and cluster state for every gateway of an organization. WanEdgeScorecard.csv: one row per gateway with site, name, model, version, predominant version, version compliant, config status, HA state, cluster peer state, service status summary, DHCP pool count, worst pool utilization percent, VPN peers up and down, BGP peers established and not established, uptime days, and last trouble. WanEdgeDhcpPools.csv: one row per gateway and pool with leased, total, and percent. WanEdgeScorecardBySite.csv: one row per site with the tile percentages. A console summary prints the org-wide values."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export an organization WAN edge scorecard (Priority: P1)

A NOC engineer needs one organization-level report for all WAN gateways. The report shows health, configuration, software version, peer state, DHCP pool risk, uptime, and last trouble for each gateway.

**Why this priority**: This is the main operator value. It closes the gap between one-site WAN edge tiles and organization-wide gateway review.

**Independent Test**: Run menu 279 in test mode. Confirm that the operation completes with no prompt and creates `data/WanEdgeScorecard.csv` with one row for each gateway.

**Acceptance Scenarios**:

1. **Given** an organization with gateways, **When** the operator runs menu 279 in `--test`, **Then** the operation writes `WanEdgeScorecard.csv`, `WanEdgeDhcpPools.csv`, and `WanEdgeScorecardBySite.csv` under `data/`.
2. **Given** gateway statistics include DHCP, VPN, BGP, cluster, version, configuration, service, uptime, and trouble fields, **When** the scorecard is generated, **Then** each gateway row includes the requested scorecard columns.
3. **Given** the operation runs in automated test mode, **When** no operator is present, **Then** it completes without an interactive prompt.

---

### User Story 2 - Review DHCP pool pressure across gateways (Priority: P2)

A NOC engineer needs to find gateways with high DHCP pool use. The engineer also needs pool-level rows to confirm which pool creates the risk.

**Why this priority**: DHCP Pool Exhausted is a top alert. Early warning helps operators act before clients lose service.

**Independent Test**: Run menu 279 with sample gateway statistics that include normal pools, pools at or above the warning threshold, and gateways with no DHCP statistics. Confirm that gateway rows and pool rows match the sample data.

**Acceptance Scenarios**:

1. **Given** no environment override is set, **When** DHCP pool use is scored, **Then** the warning threshold is 80 percent.
2. **Given** `DHCP_POOL_WARN_PERCENT` is set to a valid percent, **When** DHCP pool use is scored, **Then** that value is used as the warning threshold.
3. **Given** a gateway has no `dhcpd_stat`, **When** the operation creates scorecard rows, **Then** the gateway row has DHCP pool count `0` and the operation does not fail.
4. **Given** a gateway has DHCP pool statistics, **When** the operation writes `WanEdgeDhcpPools.csv`, **Then** it includes one row per gateway and pool with leased, total, and percent values.

---

### User Story 3 - Summarize site and organization health (Priority: P3)

A NOC engineer needs site-level tile percentages and an organization-level console summary. The summary must match the same concepts shown on the Mist WAN Edges page.

**Why this priority**: Site and organization summaries help operators choose where to investigate first.

**Independent Test**: Run menu 279 with gateways from multiple sites. Confirm that `WanEdgeScorecardBySite.csv` has one row per site and that the console summary shows organization-wide values.

**Acceptance Scenarios**:

1. **Given** gateways belong to multiple sites, **When** the operation completes, **Then** `WanEdgeScorecardBySite.csv` has one row per site with Config Success, Version Compliance, WAN Edge Uptime, and Potential Anomalies percentages.
2. **Given** gateway scorecard values exist, **When** the operation prints the console summary, **Then** it shows the organization-wide values for the same tile concepts.
3. **Given** a VPN peer has `up` set to false, **When** peer counts are calculated, **Then** the peer counts as down and the gateway row names the down peer count.

### Edge Cases

- A gateway has `dhcpd_stat` absent. The operation writes a gateway row with DHCP pool count `0` and no exception.
- A gateway has no DHCP pools. The operation writes no pool rows for that gateway and uses empty values where no worst pool percent exists.
- A DHCP pool has total size zero or missing. The operation avoids division by zero and reports a safe empty or zero percent value.
- A VPN peer has `up` set to false. The peer counts as down, not unknown.
- BGP peers can be established or not established. Non-established peers count in the not-established value.
- Cluster or high-availability data can be missing. The operation still writes the row and uses a clear empty or unknown value.
- A site has no gateways after filtering. It does not create an incorrect site percentage row.
- The operation runs in `--test`. It must not stop for operator input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide menu 279 as an organization WAN edge scorecard operation.
- **FR-002**: The operation MUST run in `--test` with no prompt and write the three files under `data/`.
- **FR-003**: The operation MUST write `WanEdgeScorecard.csv` with one row per gateway.
- **FR-004**: Each `WanEdgeScorecard.csv` row MUST include site, gateway name, model, version, predominant version, version compliant, configuration status, HA state, cluster peer state, service status summary, DHCP pool count, worst pool utilization percent, VPN peers up and down, BGP peers established and not established, uptime days, and last trouble.
- **FR-005**: The operation MUST write `WanEdgeDhcpPools.csv` with one row per gateway and DHCP pool.
- **FR-006**: Each `WanEdgeDhcpPools.csv` row MUST include gateway identity, pool identity, leased address count, total address count, and utilization percent.
- **FR-007**: The operation MUST write `WanEdgeScorecardBySite.csv` with one row per site.
- **FR-008**: Each `WanEdgeScorecardBySite.csv` row MUST include Config Success, Version Compliance, WAN Edge Uptime, and Potential Anomalies percentages.
- **FR-009**: The operation MUST print a console summary with organization-wide values for Config Success, Version Compliance, WAN Edge Uptime, and Potential Anomalies.
- **FR-010**: The DHCP warning threshold MUST default to 80 percent.
- **FR-011**: The DHCP warning threshold MUST read `DHCP_POOL_WARN_PERCENT` from the environment when it is set to a valid percent value.
- **FR-012**: A gateway with `dhcpd_stat` absent MUST produce a row with DHCP pool count `0` and no exception.
- **FR-013**: A VPN peer with `up` false MUST count as down, and the gateway row MUST name the down peer count.
- **FR-014**: The scorecard MUST reuse the gateway statistics fetch that menu 18 or menu 15 already holds instead of a second implementation of pagination.
- **FR-015**: The wiring manifest `specs/3560-wan-edge-scorecard/wiring.md` MUST exist and include every section of the implementation contract.
- **FR-016**: The release note fragment `changelog.d/issue-3560-wan-edge-scorecard.md` MUST exist before release.
- **FR-017**: The operation MUST use the configured data export behavior for collected API data so outputs follow project output rules.
- **FR-018**: Missing optional gateway fields MUST not stop the export. The related output value MUST be empty or a clear unknown value.
- **FR-019**: Percent values MUST be calculated from the same gateway set used to write the gateway scorecard.
- **FR-020**: The operation MUST keep organization-wide and site-wide summary values consistent with the gateway rows.

### Key Entities

- **Organization**: The reporting scope. It contains sites and gateways.
- **Site**: A location that owns zero or more WAN gateways. It is the grouping key for site scorecard percentages.
- **WAN Gateway**: A Mist WAN edge device. Key attributes include site, name, model, version, configuration status, HA state, service status, peer states, uptime, and last trouble.
- **DHCP Pool**: A pool on a gateway. Key attributes include pool identity, leased address count, total address count, and utilization percent.
- **VPN Peer**: A VPN peer for a gateway. Key attributes include identity and up or down state.
- **BGP Peer**: A BGP peer for a gateway. Key attributes include identity and established or not-established state.
- **Scorecard Summary**: A site-level or organization-level set of tile percentages for configuration success, version compliance, uptime, and potential anomalies.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In `--test`, menu 279 completes without operator input and creates all three expected output files in one run.
- **SC-002**: For a test organization with known gateway data, 100 percent of gateways appear once in `WanEdgeScorecard.csv`.
- **SC-003**: For known DHCP sample data, 100 percent of pool rows show the expected leased, total, and percent values.
- **SC-004**: For sample VPN data, every peer with `up` false increases the down peer count for its gateway.
- **SC-005**: For sample BGP data, every established and not-established peer is counted in the correct gateway column.
- **SC-006**: Site scorecard percentages match the gateway rows used for those sites within one percentage point.
- **SC-007**: Organization console percentages match all gateway rows within one percentage point.
- **SC-008**: A gateway without DHCP statistics is included in the gateway scorecard with DHCP pool count `0` in every test run.
- **SC-009**: The implementation has one gateway statistics pagination path for this scorecard and existing gateway statistics operations.
- **SC-010**: The feature package includes the wiring manifest and release note fragment before planning is marked complete.

## Assumptions

- The operation is for organization scope only. Site-only filtering is out of scope for this feature.
- The output file names are fixed: `WanEdgeScorecard.csv`, `WanEdgeDhcpPools.csv`, and `WanEdgeScorecardBySite.csv`.
- The feature reports CSV files. Other configured export formats can be handled by the existing project export behavior if enabled.
- The predominant version means the most common gateway version in the organization data set.
- Version compliant means the gateway version matches the predominant version unless the project already has a stronger compliance rule for WAN edges.
- Potential anomalies include DHCP warning conditions, peer-state problems, service-state problems, cluster-state problems, and other available gateway trouble indicators.
- Empty or missing optional fields are acceptable in output when Mist does not provide that field for a gateway.
- The release note fragment is part of the implementation work because this specify step can edit only the feature spec directory.
