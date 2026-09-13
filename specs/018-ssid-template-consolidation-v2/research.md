# Research: SSID Template Consolidation Rewrite

**Spec**: 018-ssid-template-consolidation-v2
**Date**: 2026-04-08

---

## R1: Mist API — WLAN Template CRUD

**Question**: What mistapi SDK methods exist for creating, updating, and listing WLAN templates?

**Finding**: The codebase uses `mistapi.api.v1.orgs.templates.listOrgTemplates(session, org_id)` for listing. The Mist API provides:
- `listOrgTemplates` — GET all WLAN templates (bulk, paginated)
- `createOrgTemplate` — POST a new WLAN template
- `updateOrgTemplate` — PUT update an existing template
- `getOrgTemplate` — GET a single template by ID
- `deleteOrgTemplate` — DELETE a template

Templates have an `applies` field with `sitegroup_ids`, `site_ids`, and `org_id` to control scope. WLANs are embedded inside the template object.

**Decision**: Use `listOrgTemplates` for Phase 1 bulk read. Use `createOrgTemplate` / `updateOrgTemplate` for Phase 4.
**Rationale**: Matches existing E911 pattern (`_fetch_org_wlan_templates`). Org-level calls avoid per-site overhead.

---

## R2: Mist API — MxTunnel (Edge Cluster) Listing

**Question**: How to resolve site-to-Edge-cluster mapping using the Mist API?

**Finding**: The spec states `mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels(session, org_id)` returns all Mist Edge clusters. Each MxTunnel object has `id` and `name`. Sites are **not** directly linked to clusters — the mapping is done through WLANs: each WLAN has `mxtunnel_ids` (list of cluster IDs) or `mxtunnel_name` (string name). By cross-referencing the WLAN's `mxtunnel_ids` with the MxTunnel list, we resolve which cluster each site connects through.

**Decision**: Fetch MxTunnels in Phase 1, build a lookup dict by ID. For each site's matched SSID, read `mxtunnel_ids[0]` (first cluster) and resolve via lookup.
**Rationale**: No `site.edge_cluster_id` field exists. The WLAN → MxTunnel reference is the only path.
**Alternatives considered**: Per-site settings queries (too expensive, 170 API calls). Direct cluster→site mapping (doesn't exist in the API).

---

## R3: Mist API — Site Variables (vars)

**Question**: How to read and write site variables?

**Finding**: Site variables live in the site object's `vars` dictionary. Reading: `listOrgSites` returns each site with its `vars`. Writing: `mistapi.api.v1.sites.sites.updateSiteInfo(session, site_id, body={"vars": {...}})` performs a partial update. The `vars` dict is merged (not replaced) when using PUT with only the `vars` key.

Existing pattern in codebase (line ~24870, ~31810): `mistapi.api.v1.sites.sites.updateSiteInfo(apisession, site_id, body={...})` is used for site-level updates (gateway template assignment, RF template assignment).

**Decision**: Phase 2 reads `vars` from cached `listOrgSites` data. Writes use `updateSiteInfo` with `body={"vars": merged_vars}` per site.
**Rationale**: Matches existing codebase patterns. Must merge (not replace) to preserve existing variables.
**Risk**: Must GET current vars, merge new keys, then PUT. Race condition is acceptable for this tool (single operator).

---

## R4: Mist API — Site Group CRUD

**Question**: What APIs exist for creating and managing site groups?

**Finding**: The Mist API provides:
- `mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups(session, org_id)` — list all groups
- `mistapi.api.v1.orgs.sitegroups.createOrgSiteGroup(session, org_id, body={...})` — create group
- `mistapi.api.v1.orgs.sitegroups.updateOrgSiteGroup(session, org_id, sitegroup_id, body={...})` — update group (add/remove sites)
- `mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup(session, org_id, sitegroup_id)` — get single group

Site group body: `{"name": "...", "site_ids": ["id1", "id2", ...]}`.

**Decision**: Phase 3 lists existing groups, creates missing ones, updates `site_ids` by merging (not replacing) to preserve any pre-existing members.
**Rationale**: Additive approach prevents accidentally removing sites that other workflows added.

---

## R5: WLAN Auth Type — PSK Detection

**Question**: How to correctly detect PSK SSIDs?

**Finding**: The spec explicitly states: check `wlan["auth"]["type"]` for values `psk`, `psk-tkip`, `psk-wpa2-tkip`. The old implementation incorrectly checked `wlan.get("psk")` which is wrong.

WLAN auth structure: `{"auth": {"type": "psk"}}` or `{"auth": {"type": "open"}}` or `{"auth": {"type": "eap"}}`.

**Decision**: `wlan.get("auth", {}).get("type", "") in ("psk", "psk-tkip", "psk-wpa2-tkip")`
**Rationale**: Matches Mist API structure and spec FR-012.

---

## R6: Template `applies` Field Structure

**Question**: How do WLAN templates associate with sites/groups?

**Finding**: The template `applies` field structure:
```json
{
  "applies": {
    "org_id": "...",
    "site_ids": ["..."],
    "sitegroup_ids": ["..."]
  }
}
```
When `sitegroup_ids` is populated, all sites in those groups receive the template. This is the target pattern for consolidated templates (FR-029).

**Decision**: Phase 4 creates templates with `applies.sitegroup_ids` only. No direct `site_ids`.
**Rationale**: Site group-based assignment is the whole point of consolidation.

---

## R7: Deviation Analysis Strategy

**Question**: How to efficiently compare WLAN configs across sites within a cluster?

**Finding**: WLAN objects are flat-ish JSON dicts. The strategy:
1. For each cluster group, collect all matched SSIDs (WLAN JSON objects).
2. Build a set of all keys across all SSIDs (exclude metadata: `id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`).
3. For each key, collect unique values. If more than one unique value exists, it's a deviation.
4. Report: parameter name → {value: [site_names]}.

Cross-cluster drift: after per-cluster analysis, pick the canonical (majority) value per cluster, compare across clusters.

**Decision**: Implement as `_analyze_deviations(cluster_ssids: dict[str, list[dict]])` returning a structured report.
**Rationale**: Pure in-memory operation on cached data. No API calls needed.
**Alternatives considered**: Deep diff libraries (overkill, adds dependency). JSON Schema comparison (wrong tool for parameter-level diff).

---

## R8: Cache and Resume Strategy

**Question**: Best pattern for caching Phase 1 data and resuming write phases?

**Finding**: Existing E911 pattern uses a checkpoint JSON file (`data/e911_checkpoint.json`) with:
- Bulk data cached after org-level queries
- Per-site progress tracked (which sites completed)
- Checkpoint saved every N operations
- On resume: load checkpoint, skip completed sites

**Decision**: Adopt same checkpoint pattern:
- `data/ssid_consolidation_cache.json` — Phase 1 bulk data + freshness timestamp
- `data/ssid_consolidation_phase{N}_results.json` — per-phase results log (tracks success/failure per site)
- On resume: detect existing results file, count completed sites, offer resume.
**Rationale**: Proven pattern in E911. JSON is human-readable for debugging.

---

## R9: WLAN Template Update for Second SSID Append

**Question**: How to safely append a second SSID to an existing template?

**Finding**: Templates contain WLANs in their response data. To append:
1. GET the template (to get current state including first SSID)
2. Add the new WLAN config to the WLANs list
3. PUT the updated template

The `updateOrgTemplate` API replaces the template config, so we must include ALL existing WLANs plus the new one.

**Decision**: Phase 4 GETs existing template, checks for first SSID integrity, appends new SSID, PUTs entire template.
**Rationale**: No "append WLAN" API exists — must use full replacement with verification.
**Risk**: If another admin modifies the template between GET and PUT, changes could be overwritten. Acceptable for this tool (single operator, CONFIRM gate).

---

## R10: Pilot/Test Group Name Pattern Detection

**Question**: How to reliably identify pilot/test sites?

**Finding**: Spec says case-insensitive substring match on site name for "pilot", "test", or "lab".

**Decision**: `re.search(r'(?i)\b(pilot|test|lab)\b', site_name)` — word-boundary match to avoid false positives (e.g., "Westlabor" shouldn't match "lab").
**Rationale**: Word boundary prevents substring false positives while still catching "Test-Site" or "Lab Building".
**Alternative considered**: Simple `in` check (too many false positives). Config-based list (overkill for v1).
