# Research: Rogue PCI Evidence Pack

## Decision: Use `listOrgWlans` for approved org SSIDs

**Rationale**: Existing menu 46 uses `mistapi.api.v1.orgs.wlans.listOrgWlans` in `src/operations/exporting/export/org_config_exporter.py`. The OpenAPI operation is `GET /api/v1/orgs/{org_id}/wlans` with `org_id`, optional `limit`, and optional `page`. The installed SDK exposes `mistapi.api.v1.orgs.wlans.listOrgWlans`.

**Alternatives considered**: Site WLAN reads were rejected because the acceptance rule names organization WLAN SSIDs.

## Decision: Use `listOrgSites` for the site inventory

**Rationale**: The settings report must include every site. The OpenAPI operation is `GET /api/v1/orgs/{org_id}/sites` with `org_id`, optional `limit`, and optional `page`. The installed SDK exposes `mistapi.api.v1.orgs.sites.listOrgSites`.

**Alternatives considered**: Reading `SiteList.csv` was rejected because the evidence pack needs fresh site coverage.

## Decision: Use `getSiteSetting` once per site with the shared pacer

**Rationale**: The site settings fields live under `site_setting.rogue`. The OpenAPI operation is `GET /api/v1/sites/{site_id}/setting` with `site_id`. The installed SDK exposes `mistapi.api.v1.sites.setting.getSiteSetting`. The request cost is one `getSiteSetting` call for each site returned by `listOrgSites`.

**Alternatives considered**: Reusing `APIFetchUtils.all_site_settings()` was rejected because it does not expose per-call pacing data for this feature.

## Decision: Use `listSiteRogueAPs` as the primary detection source

**Rationale**: Existing menu 30 uses `mistapi.api.v1.sites.insights.listSiteRogueAPs` in `src/operations/exporting/export/org_client_security_exporter.py`. The OpenAPI operation is `GET /api/v1/sites/{site_id}/insights/rogues` with `site_id`, optional `type`, `limit`, `start`, `end`, `duration`, and `interval`. The response schema contains `ssid`, `bssid`, `channel`, `avg_rssi`, `ap_mac`, `num_aps`, `seen_on_lan`, and `times_heard`. The installed SDK exposes `mistapi.api.v1.sites.insights.listSiteRogueAPs`.

**Alternatives considered**: Only reading site rogue events was rejected because menu 30 already proves that the insight endpoint is the raw rogue AP export path.

## Decision: Record the `searchOrgRogueEvents` discrepancy and use available event reads

**Rationale**: The assignment names `searchOrgRogueEvents`, but the local OpenAPI file has no operation with that identifier. The installed SDK also has no `mistapi.api.v1.orgs.rogues` module. The local OpenAPI file exposes `searchOrgEvents` at `GET /api/v1/orgs/{org_id}/events/search`, and `searchSiteRogueEvents` at `GET /api/v1/sites/{site_id}/rogues/events/search`. The installed SDK exposes `mistapi.api.v1.orgs.events.searchOrgEvents` and `mistapi.api.v1.sites.rogues.searchSiteRogueEvents`.

**Alternatives considered**: A direct `apisession.mist_get` call to an undocumented `/api/v1/orgs/{org_id}/rogues/events/search` path was rejected because the local OpenAPI file does not define that path.

## Decision: Classify honeypots before rogues and neighbors

**Rationale**: The feature requires a honeypot when the detection SSID equals an org WLAN SSID and the BSSID is not an org AP radio BSSID. Rogue APs are unauthorized APs connected to the wired network. Neighbor APs are nearby APs that are not connected to the network. Honeypots advertise the organization SSID to capture credentials or impersonate service. Source: `juniper-mist-wireless/05-wlan-security-radius-and-psk/05-wlan-threat-client-and-pci-controls.md`.

**Alternatives considered**: Classifying by `is_rogue` first was rejected because it can hide an SSID impersonation.

## Decision: Use site `rogue` settings for detection status and approved counts

**Rationale**: The local OpenAPI schema `site_rogue` contains `enabled`, `honeypot_enabled`, `min_rssi`, `min_duration`, `min_rogue_duration`, `min_rogue_rssi`, `whitelisted_ssids`, and `whitelisted_bssids`. The Mist wireless source says `Detect Rogue and Neighbor APs`, `Detect Honeypot APs`, `Neighbor RSSI Threshold`, `Approved SSIDs`, and `Approved BSSIDs` are site-wide threat detection settings. Source: `juniper-mist-wireless/05-wlan-security-radius-and-psk/05-wlan-threat-client-and-pci-controls.md`.

**Alternatives considered**: Organization settings were rejected because the source page states that the feature is site-wide.

## Decision: State the PCI evidence boundary in the summary

**Rationale**: The Mist wireless source says the Mist cloud is outside the Cardholder Data Environment because it does not carry wireless packet data. The summary must cite `juniper-mist-wireless/05-wlan-security-radius-and-psk/05-wlan-threat-client-and-pci-controls.md`.

**Alternatives considered**: A generic PCI statement was rejected because the acceptance criteria require the source page name.

## Decision: Cite related Mist portal evidence pages

**Rationale**: The wired page documents Switches page tiles such as `Switch-AP Affinity`, `PoE Compliance`, `VLANs`, and `Potential Anomalies`. The WAN page documents WAN Edge tiles and `DHCP Statistics`. The AIOps page documents alert categories, the `Security` category, severity values, and `Network Security` links. These pages support the evidence context but do not change the rogue classifier.

**Alternatives considered**: Omitting these pages was rejected because the assignment requires citing the skill pages when page names or status words come from them.

