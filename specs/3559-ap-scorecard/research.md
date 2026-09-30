# Research: Organization Access Point Scorecard

## Decision: Use `listOrgDevicesStats` for AP runtime data

Use `GET /api/v1/orgs/{org_id}/stats/devices` with query `type=ap`.

Rationale:

- The OpenAPI file names the operation `listOrgDevicesStats`.
- The path parameter is `org_id`.
- The query parameters include `type`, `status`, `site_id`, `mac`, `evpntopo_id`, `evpn_unused`, `fields`, `start`, `end`, `duration`, `limit`, and `page`.
- The `200` response is an array. The OpenAPI description says pagination is assumed and returned in the response header because the response is an array.
- The response item schema is `stats_device`, which is a `oneOf` union of `stats_ap`, `stats_switch`, and `stats_gateway`.
- The `stats_ap` schema contains the required AP fields: `status`, `last_trouble`, `inactive_wired_vlans`, `switch_redundancy`, `power_constrained`, `power_opmode`, `power_budget`, `lldp_stat`, `config_reverted`, `expiring_certs`, `version`, `model`, `uptime`, `auto_upgrade_stat`, `name`, `site_id`, `mac`, and `type`.
- The installed SDK exposes `mistapi.api.v1.orgs.stats.listOrgDevicesStats`.
- The installed SDK signature is `listOrgDevicesStats(mist_session, org_id, type=None, status=None, site_id=None, mac=None, evpntopo_id=None, evpn_unused=None, fields=None, start=None, end=None, duration=None, limit=None, page=None)`.

Alternatives considered:

- `listSiteDevicesStats` was rejected because it would require one call for each site and would not follow the assignment.
- Direct `apisession.mist_get` was rejected because the installed SDK exposes the operation.

## Decision: Reuse the existing pagination seam

Use `APIDataFetcher` when it can return rows for custom post-processing. If that shape does not fit, call `mistapi.get_all` in the client module with the same seam used by `APIDataFetcher`.

Rationale:

- `src/export/org_device_stats_exporter.py` calls `APIDataFetcher` with `mistapi.api.v1.orgs.stats.listOrgDevicesStats`, `type="all"`, and `limit=1000`.
- `src/api/api_data_fetcher.py` calls the SDK function, rejects HTTP failures, then paginates with `mistapi.get_all(response=response, mist_session=SourceDependencyResolver.apisession)`.
- The AP scorecard must not add a second custom pagination loop.

Alternatives considered:

- A custom `while page` loop was rejected because it would duplicate the existing pagination seam.

## Decision: Use Mist Access Points tile thresholds

Use `green` when the percentage is `98.5` or higher. Use `red` when the percentage is `80` or lower. Use `orange` for values above `80` and below `98.5`.

Rationale:

- The skill page `juniper-mist-wireless/01-architecture-and-ap-platforms/03-ap-dashboard-insights-and-utilities.md` states that the `Access Points` page shows `Connection Status`, `VLANs`, `Version Compliance`, `AP Switch Redundancy`, and `Potential Anomalies`.
- The same page states that green means `98.5%` or higher, orange means `80%` to `98.5%`, and red means `80%` or fewer APs meet the standard.

Alternatives considered:

- The organization Insights site color thresholds were rejected because they score sites, not AP tile compliance.

## Decision: Score each AP from available `stats_ap` fields

Calculate AP detail rows and site summaries with pure functions in the model module.

Rationale:

- `status` drives `Connection Status`.
- `inactive_wired_vlans` drives the `VLANs` tile. An empty or missing list passes. A non-empty list fails and appears in the AP row.
- `version`, `model`, and `auto_upgrade_stat` support `Version Compliance`. If no explicit expected version is present, the model computes the predominant version per model in the payload.
- `switch_redundancy` drives `AP Switch Redundancy`. Value `1` means no redundancy. Value `2` means good redundancy. Value `3` or more means excellent redundancy.
- `config_reverted`, `last_trouble`, and available anomaly indicators drive `Potential Anomalies` until a later implementation confirms a more specific payload field.
- `power_constrained`, `power_opmode`, `power_budget`, and `lldp_stat.power_allocated` describe reduced power behavior.
- `lldp_stat.power_needed` is requested by the feature. If the payload lacks `power_needed`, the implementation uses a safe empty value. The OpenAPI examples show `power_requested`, but they do not define it as the same value as `power_needed`.
- `expiring_certs` is a map of certificate serial numbers to expiry timestamps for certificates that expire within `30` days.
- `uptime` is in seconds and must be converted to uptime days for the AP row.

Alternatives considered:

- Calling extra site or insights APIs was rejected because the assignment states that the fields are in the organization AP statistics payload.

## Decision: Keep site names opportunistic

Use `site_name` when it appears in the runtime payload. Otherwise use `site_id` as the site value.

Rationale:

- The OpenAPI `stats_ap` schema lists `site_id`, but it does not list `site_name`.
- The feature requires a site column and one row per site.
- A fallback to `site_id` keeps the operation prompt-free and avoids an extra API call.

Alternatives considered:

- Calling `listOrgSites` was rejected because the specified data source is `listOrgDevicesStats`.

## Decision: Match related Mist inventory tile behavior

Use comparable tile semantics from other Mist inventory pages only for context.

Rationale:

- `juniper-mist-wired/09-wired-visibility-and-switch-management/01-switches-page-metrics-and-front-panel.md` states that the `Switches` page has `VLANs`, `Version Compliance`, and `Potential Anomalies` tiles.
- The same wired page states that two anomalous switches in ten gives `80%`.
- `juniper-mist-wan/10-monitoring-sles-and-troubleshooting/01-wan-edge-inventory-insights-and-alerts.md` states that the `WAN Edges` page has `Config Success`, `Version Compliance`, `WAN Edge Uptime`, and `Potential Anomalies`.
- The same WAN page states that two WAN Edges with anomalies out of ten gives `80%`.
- These pages support the percentage method for anomaly-free device tiles across domains.

Alternatives considered:

- Reusing switch-specific or WAN-specific health limits was rejected because the AP page defines the AP score thresholds.

## Decision: Include power and certificate context in the row

Export power and certificate columns but do not create separate site tiles for them.

Rationale:

- `juniper-mist-wireless/01-architecture-and-ap-platforms/02-ap-ports-poe-and-power-modes.md` states that the AP details page shows required power, requested power, and allocated power in the `Power Mode` section.
- The same page states that a power warning appears when an AP has reduced functionality or can only reach the cloud.
- `juniper-mist-aiops/04-alerts/01-alerts-dashboard-categories-and-severity.md` states that certificate alerts are a separate category for expired or soon-to-expire certificates.
- The scorecard exports `expiring_certs` count as certificate context without changing the AP tile meanings.

Alternatives considered:

- A separate certificate tile was rejected because the assignment defines five AP tiles.

## Decision: Treat potential anomalies as early-warning context

Use a boolean model method that marks an AP as anomaly-free when no selected anomaly signal is present.

Rationale:

- `juniper-mist-aiops/05-marvis-actions/08-potential-anomalies-and-event-card.md` states that potential anomalies appear on the Insights page and each one carries a recommended remediation step.
- The same page states that AP anomalies include `Bad Cable`, `Missing VLAN`, `Ethernet Error`, `AP Loop Detected`, `Low Power`, and `Low Ethernet Speed`.
- The `Access Points` skill page says `Potential Anomalies` is the percentage of APs with no current Marvis anomaly.

Alternatives considered:

- Fetching Marvis Actions was rejected because potential anomalies are Insights events, not Marvis Actions.

## Decision: Defer shared wiring to the manifest

Create [wiring.md](wiring.md) and do not edit shared files in this plan step.

Rationale:

- The fleet contract forbids edits to `MistHelper.py`, `src/utils/operation_registry.py`, `src/refactors/endpoint_primary_key_strategies.py`, `README.md`, generated docs, scripts, and copilot instructions during this step.
- The user explicitly requested that shared wiring changes be deferred to [wiring.md](wiring.md).

Alternatives considered:

- Direct shared file edits were rejected because they violate strict ownership.
