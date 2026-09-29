# Wiring Manifest: Organization WAN Edge Scorecard

**Issue**: #3560
**Feature directory**: `specs/3560-wan-edge-scorecard/`
**Operation**: Menu 279, organization WAN edge scorecard

## 1. Scope

Build one organization-level WAN edge scorecard operation. The operation reports every WAN gateway in the organization and adds site and organization summaries.

## 2. Menu Wiring

- Add menu 279 with the label "Organization WAN Edge Scorecard".
- Register menu 279 as `safe`.
- Use handler class `WanEdgeScorecard` with static `run()`.
- The operation must run in `--test` without a prompt.
- The operation must write outputs under `data/`.

## 3. Data Source Contract

- Use `listOrgDevicesStats` with `type=gateway`.
- Reuse the gateway statistics fetch that menu 18 or menu 15 already holds.
- Do not add a second pagination implementation for gateway statistics.
- Read gateway statistics once for the organization data set when possible.
- Before coding, read `src/export/org_device_stats_exporter.py`.
- Before coding, read the menu 18 gateway stats path named `_dispatch_gateway_stats_device_stats_with_freshness`.
- Before coding, read `stats_gateway`, `dhcpd_stat_lan`, `vpn_peers`, and `bgp_peers` in `documentation/mist-api-openapi3json.json`.

## 4. Gateway Scorecard Output Contract

Write `data/WanEdgeScorecard.csv`.

Required row grain: one row per gateway.

Required columns:

- Site
- Name
- Model
- Version
- Predominant version
- Version compliant
- Config status
- HA state
- Cluster peer state
- Service status summary
- DHCP pool count
- Worst pool utilization percent
- VPN peers up
- VPN peers down
- BGP peers established
- BGP peers not established
- Uptime days
- Last trouble

## 5. DHCP Pool Output Contract

Write `data/WanEdgeDhcpPools.csv`.

Required row grain: one row per gateway and DHCP pool.

Required values:

- Gateway identity
- Pool identity
- Leased address count
- Total address count
- Utilization percent

## 6. Site Scorecard Output Contract

Write `data/WanEdgeScorecardBySite.csv`.

Required row grain: one row per site.

Required tile percentages:

- Config Success
- Version Compliance
- WAN Edge Uptime
- Potential Anomalies

## 7. Console Summary Contract

Print organization-wide values for these tile percentages:

- Config Success
- Version Compliance
- WAN Edge Uptime
- Potential Anomalies

## 8. DHCP Threshold Contract

- Default DHCP warning threshold: 80 percent.
- If `DHCP_POOL_WARN_PERCENT` is set to a valid percent, use that value.
- Invalid threshold values must not stop the run. Use the default and report a clear warning.

## 9. Peer State Contract

- A VPN peer with `up` false counts as down.
- The gateway row must name the down peer count.
- BGP established peers count as established.
- BGP peers that are not established count as not established.

## 10. Missing Data Contract

- If `dhcpd_stat` is absent, write the gateway row with DHCP pool count `0`.
- Missing optional gateway fields must not cause an exception.
- Use empty values or clear unknown values for missing optional fields.

## 11. Test Contract

Acceptance tests must prove these results:

- The operation runs in `--test` with no prompt and writes the three files under `data/`.
- The DHCP warning threshold defaults to 80 percent.
- The DHCP warning threshold reads `DHCP_POOL_WARN_PERCENT` from the environment when set.
- A gateway with `dhcpd_stat` absent produces a row with pool count `0` and no exception.
- A VPN peer with `up` false counts as down, and the row names the down peer count.
- The scorecard reuses the gateway statistics fetch that menu 18 or menu 15 already holds.
- This wiring manifest exists with every section of the contract.
- The release note fragment `changelog.d/issue-3560-wan-edge-scorecard.md` exists before release.

## 12. Output Safety Contract

- All output files must be written under `data/`.
- Collected API data must use the project output behavior for configured backends.
- No secrets or credentials may be written to output or logs.

## 13. Release Note Contract

Add `changelog.d/issue-3560-wan-edge-scorecard.md` during implementation. This specify step does not create it because the fleet contract allows edits only under `specs/3560-wan-edge-scorecard/**`.

## 14. Out of Scope

- Site-only operation mode.
- Changes to the Mist UI.
- Manual edits to the generated output files.
- A second gateway statistics pagination path.
