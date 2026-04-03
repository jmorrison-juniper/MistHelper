# API Contract: SSID Template Consolidation

**Feature Branch**: `018-ssid-template-consolidation`
**Date**: 2025-07-02
**Type**: Mist API Interactions (via mistapi SDK)

---

## API Calls by Phase

### Phase 1: Data Collection (Read-Only)

| Operation | mistapi Method | Scope | Rate Impact |
|-----------|---------------|-------|-------------|
| List all WLAN templates | `orgs.templates.listOrgTemplates(session, org_id)` | 1 call | Low |
| Get template detail | `orgs.templates.getOrgTemplate(session, org_id, template_id)` | 1 per template (~170) | Medium |
| List org WLANs | `orgs.wlans.listOrgWlans(session, org_id)` | 1 call (paginated) | Low |
| List all sites | `orgs.sites.listOrgSites(session, org_id)` | 1 call (paginated) | Low |
| List Mist Edge tunnels | `orgs.mxtunnels.listOrgMxTunnels(session, org_id)` | 1 call | Low |
| List site groups | `orgs.sitegroups.listOrgSiteGroups(session, org_id)` | 1 call | Low |

**Total Phase 1 API calls**: ~175 (dominated by per-template detail fetches)
**Optimization**: Use `listOrgWlans` to get all WLANs in one paginated call, then group by `template_id` locally. This reduces ~170 individual calls to 1-2 paginated calls.

### Phase 2: Site Variable Configuration (Write)

| Operation | mistapi Method | Scope | Rate Impact |
|-----------|---------------|-------|-------------|
| Read site settings | `sites.setting.getSiteSetting(session, site_id)` | 1 per site (~170) | Medium |
| Update site settings | `sites.setting.updateSiteSettings(session, site_id, body)` | 1 per site (~170) | Medium |

**Total Phase 2 API calls**: ~340
**Body for updateSiteSettings**: Partial update containing only the `vars` key:
```json
{
  "vars": {
    "SSID_CONSOL_VLAN_ID": "100",
    "SSID_CONSOL_MXTUNNEL": "tunnel-name"
  }
}
```
**Note**: `updateSiteSettings` is a PUT that merges — existing settings outside `vars` are not affected. Within `vars`, existing keys not in the payload are preserved by merging client-side (read current vars, merge, write back).

### Phase 3: Site Group Assignment (Write)

| Operation | mistapi Method | Scope | Rate Impact |
|-----------|---------------|-------|-------------|
| List existing site groups | `orgs.sitegroups.listOrgSiteGroups(session, org_id)` | 1 call | Low |
| Create site group | `orgs.sitegroups.createOrgSiteGroup(session, org_id, body)` | 0-5 calls | Low |
| Update site group (add sites) | `orgs.sitegroups.updateOrgSiteGroup(session, org_id, sg_id, body)` | 5 calls | Low |

**Total Phase 3 API calls**: ~6-11
**Note**: Site group membership is managed via the `site_ids` array on the site group object. All sites for a group are added in a single PUT call per group (not per-site).

**Body for createOrgSiteGroup**:
```json
{
  "name": "SSID-Consol-ClusterA"
}
```

**Body for updateOrgSiteGroup** (adding sites):
```json
{
  "name": "SSID-Consol-ClusterA",
  "site_ids": ["<site-uuid-1>", "<site-uuid-2>", "..."]
}
```

### Phase 4: Template Creation (Write)

| Operation | mistapi Method | Scope | Rate Impact |
|-----------|---------------|-------|-------------|
| List existing templates | `orgs.templates.listOrgTemplates(session, org_id)` | 1 call | Low |
| Create template | `orgs.templates.createOrgTemplate(session, org_id, body)` | 0-5 calls | Low |
| Update template | `orgs.templates.updateOrgTemplate(session, org_id, tmpl_id, body)` | 0-5 calls | Low |
| Create org WLAN (in template) | `orgs.wlans.createOrgWlan(session, org_id, body)` | 5 calls | Low |
| List org WLANs (verify existing) | `orgs.wlans.listOrgWlans(session, org_id)` | 1 call | Low |

**Total Phase 4 API calls**: ~12-17

**Body for createOrgTemplate**:
```json
{
  "name": "SSID-Consol-ClusterA",
  "applies": {
    "sitegroup_ids": ["<sitegroup-uuid>"]
  }
}
```

**Body for createOrgWlan** (with template binding and variable refs):
```json
{
  "ssid": "CorpSecure",
  "template_id": "<template-uuid>",
  "enabled": true,
  "auth": {
    "type": "eap",
    "pairwise": ["wpa2-ccmp", "wpa3"]
  },
  "vlan_enabled": true,
  "vlan_id": "{{SSID_CONSOL_VLAN_ID}}",
  "interface": "mxtunnel",
  "mxtunnel_ids": ["{{SSID_CONSOL_MXTUNNEL}}"]
}
```

### Phase 5: Disable Old SSIDs (Write)

| Operation | mistapi Method | Scope | Rate Impact |
|-----------|---------------|-------|-------------|
| Update org WLAN (disable) | `orgs.wlans.updateOrgWlan(session, org_id, wlan_id, body)` | 1 per old SSID (~170) | Medium |

**Total Phase 5 API calls**: ~170

**Body for updateOrgWlan** (disable only):
```json
{
  "enabled": false
}
```

---

## Rate Limit Budget

| Phase | API Calls | Risk Level |
|-------|-----------|------------|
| Phase 1 | ~5 (optimized) | Low |
| Phase 2 | ~340 | **Medium** — requires retry/backoff |
| Phase 3 | ~11 | Low |
| Phase 4 | ~17 | Low |
| Phase 5 | ~170 | **Medium** — requires retry/backoff |
| **Total** | ~543 | Within 5000/hour limit |

**Mitigation**: Use existing `API_REQUEST_MAX_RETRIES` (default 3) and `API_REQUEST_RETRY_DELAY` (default 5.0s) with exponential backoff. Phase 2 and Phase 5 are the highest-volume phases.

---

## Variable Reference Syntax

Mist templates use `{{VARIABLE_NAME}}` syntax for site variable substitution. When a template WLAN field contains `{{VAR}}`, the Mist cloud resolves it per-site from that site's `vars` dictionary.

**Variables defined by this feature**:

| Variable Name | Example Value | Used In |
|---------------|---------------|---------|
| `SSID_CONSOL_VLAN_ID` | `"100"` | WLAN `vlan_id` field |
| `SSID_CONSOL_MXTUNNEL` | `"edge-cluster-east"` | WLAN `mxtunnel_name` field |

**Note**: All variable values are strings in the Mist API, even when representing numbers.
