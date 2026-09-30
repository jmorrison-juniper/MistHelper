# Contract: Rogue PCI Evidence Pack

## Operation Entry Point

Menu 282 calls `RoguePciEvidencePack.run()` with no positional arguments. The handler resolves the organization through `SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()` and reads the session through `SourceDependencyResolver.apisession`.

## Output Files

All output files are written under `data/`.

### `RogueEvidence.csv`

Required columns:

```text
org_id, site_id, site_name, classification, ssid, bssid, channel, band, rssi,
first_seen, last_seen, client_count, impersonated_org_ssid
```

### `RogueSiteSettings.csv`

Required columns:

```text
org_id, site_id, site_name, rogue_enabled, honeypot_enabled,
neighbor_rssi_threshold, approved_ssid_count, approved_bssid_count,
read_status, run_started_at
```

### `RogueEvidenceSummary.md`

Required content:

- Run time.
- Detection count.
- Honeypot count.
- Rogue count.
- Neighbor count.
- Site count.
- Detection-off site count.
- Incomplete site count.
- PCI statement that the Mist cloud sits outside the Cardholder Data Environment.
- Source page name `05-wlan-threat-client-and-pci-controls.md`.

## API Read Contract

The client reads:

- `listOrgWlans`.
- `listOrgSites`.
- `getSiteSetting`, one call per site, paced by the shared adaptive pacer.
- `listSiteRogueAPs`.
- Available event rows through `searchOrgEvents` or `searchSiteRogueEvents`, because `searchOrgRogueEvents` is not present in the local OpenAPI file or SDK.

## No Network Test Contract

Tests use fake API callables, fake response objects, and fake exporter objects. Tests do not call Mist.

