# Research: SSID Template Consolidation

**Feature Branch**: `018-ssid-template-consolidation`
**Research Date**: 2025-07-02
**Status**: Complete

---

## R-001: Mist WLAN Template ↔ Site Linkage Mechanism

**Decision**: Templates are linked to sites via the `applies` field, which supports `org_id`, `site_ids`, and `sitegroup_ids`. Per FR-017, this feature uses **`sitegroup_ids` exclusively** — no direct `site_id` bindings.

**Rationale**: The `applies.sitegroup_ids` array on the template object is the native Mist mechanism for group-based template assignment. When a site is a member of a site group referenced in a template's `applies.sitegroup_ids`, that site inherits the template. This is the cleanest approach because adding/removing a site from the group automatically adds/removes the template — no template update needed.

**How it works**:
```json
// Template object
{
  "name": "Consolidated-WLAN-ClusterA",
  "applies": {
    "sitegroup_ids": ["<sitegroup-uuid>"]
  },
  "exceptions": {
    "site_ids": [],
    "sitegroup_ids": []
  }
}
```

**API methods**:
- `mistapi.api.v1.orgs.templates.listOrgTemplates(session, org_id)` — list all
- `mistapi.api.v1.orgs.templates.getOrgTemplate(session, org_id, template_id)` — get detail
- `mistapi.api.v1.orgs.templates.createOrgTemplate(session, org_id, body)` — create
- `mistapi.api.v1.orgs.templates.updateOrgTemplate(session, org_id, template_id, body)` — update

**Existing code reference**: MistHelper.py already has `_is_template_assigned_to_site()` that checks the `applies` field — including `org_id`, `site_ids`, `sitegroup_ids`, and `wxtag_ids`.

**Alternatives considered**:
- Direct `site_ids` in `applies` — Rejected because it requires updating the template whenever a site is added/removed, and does not scale for ~170 sites.
- `wxtag_ids` — Rejected because WxTags are a more complex mechanism not needed for this use case.

---

## R-002: Site Variables — Storage and API Mechanism

**Decision**: Site variables are stored in the `vars` dictionary within site settings. Read via `getSiteSetting()`, write via `updateSiteSettings()` with a partial `vars` update.

**Rationale**: The `vars` field is a native Mist feature specifically designed for template variable substitution. Templates can reference `{{VAR_NAME}}` and each site resolves it from its own `vars` dictionary.

**How it works**:
```json
// Site Settings — vars field
{
  "vars": {
    "RADIUS_IP1": "172.31.2.5",
    "VLAN_SECURED": "100",
    "MXTUNNEL_ID": "<mxtunnel-uuid>"
  }
}
```

**API methods**:
- `mistapi.api.v1.sites.setting.getSiteSetting(session, site_id)` — read current settings
- `mistapi.api.v1.sites.setting.updateSiteSettings(session, site_id, body)` — partial update
- `mistapi.api.v1.orgs.vars.searchOrgVars(session, org_id)` — search org-level vars

**Variable naming convention**: Use uppercase with underscores, prefixed to avoid conflicts:
- `SSID_CONSOL_VLAN_ID` — VLAN for the consolidated SSID
- `SSID_CONSOL_MXTUNNEL_NAME` — Mist Edge tunnel name reference

**Update strategy**: Read existing `vars`, merge new values (preserving existing keys not owned by this feature), write back. This prevents clobbering variables set by other features.

**Alternatives considered**:
- Org-level variables — Rejected because each site needs unique values (VLAN, Edge cluster).
- Custom tags/labels — Rejected because tags cannot be referenced in template variable substitution.

---

## R-003: WLAN Object Structure and PSK Detection

**Decision**: PSK detection is performed by checking `auth.type` on the WLAN object. Values `psk`, `psk-tkip`, `psk-wpa2-tkip` indicate PSK authentication. Values `eap`, `eap192` indicate enterprise/802.1X. Value `open` indicates open/guest.

**Rationale**: The `auth` object is the definitive source for authentication type. The `auth.type` field is an enum with values: `eap`, `eap192`, `open`, `psk`, `psk-tkip`, `psk-wpa2-tkip`, `wep`.

**Key WLAN fields for this feature**:
| Field | Type | Purpose |
|-------|------|---------|
| `ssid` | string | SSID name — used for target SSID matching |
| `enabled` | boolean | Whether WLAN is active (Phase 5 sets to `false`) |
| `auth.type` | string | Authentication type — PSK detection |
| `vlan_enabled` | boolean | Whether VLAN tagging is on |
| `vlan_id` | object | VLAN assignment (can be string with variable ref) |
| `interface` | string | Connection type: `mxtunnel`, `site_mxedge`, `eth0`, etc. |
| `mxtunnel_ids` | array | Mist Edge tunnel IDs (when `interface`=`mxtunnel`) |
| `mxtunnel_name` | array | Tunnel names (when `interface`=`site_mxedge`) |
| `template_id` | string | Parent template UUID |
| `id` | string | WLAN UUID |

**Metadata fields to exclude from deviation analysis** (per FR-010a):
`id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`

**Alternatives considered**:
- Using `wlan_type` field — Does not exist in the documented API schema; `auth.type` is the correct field.

---

## R-004: Site Group CRUD Operations

**Decision**: Use `mistapi.api.v1.orgs.sitegroups` for all site group operations. Site groups have a simple structure: `name`, `id`, and `site_ids` array.

**Rationale**: The sitegroups API is straightforward. Creating a site group only requires a `name`. Adding sites requires updating the `site_ids` array via PUT. The module exists in mistapi (confirmed in library inspection) even though MistHelper.py does not currently call it.

**API methods**:
- `mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups(session, org_id)` — list all
- `mistapi.api.v1.orgs.sitegroups.createOrgSiteGroup(session, org_id, body)` — create
- `mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup(session, org_id, sitegroup_id)` — get
- `mistapi.api.v1.orgs.sitegroups.updateOrgSiteGroup(session, org_id, sitegroup_id, body)` — update

**Site group body structure**:
```json
{
  "name": "SSID-Consol-ClusterA",
  "site_ids": ["<site-uuid-1>", "<site-uuid-2>"]
}
```

**Idempotency**: Before adding a site to a group, read current `site_ids`, check membership, only update if the site is not already present.

**Alternatives considered**:
- Using tags instead of site groups — Rejected because templates use `sitegroup_ids` for assignment, not tags.

---

## R-005: Mist Edge Cluster Discovery

**Decision**: Use `mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels(session, org_id)` to enumerate all Mist Edge clusters. Cross-reference with WLAN `mxtunnel_ids` or `mxtunnel_name` fields to determine which cluster each site's template references.

**Rationale**: The mxtunnels API lists all org-level Mist Edge tunnel configurations. Each tunnel has a `name` and `id`. The WLAN object's `interface` field indicates whether the SSID uses Mist Edge (`mxtunnel` or `site_mxedge`), and the `mxtunnel_ids` array contains the specific tunnel UUIDs.

**Cluster-to-group mapping**: Each of the 4 Mist Edge clusters maps 1:1 to a production site group. The 5th group is pilot/test (sites not assigned to any Edge cluster, or manually designated).

**Alternatives considered**:
- Hardcoding cluster names — Rejected for maintainability; dynamic discovery is required.

---

## R-006: Caching Strategy for Multi-Phase Workflow

**Decision**: Extend the existing `CacheUtils.check_and_generate_csv()` pattern with phase-specific cache files. Cache key is `{phase}_{target_ssid}_{timestamp}`.

**Rationale**: The existing caching mechanism uses CSV files in `data/` with `CSV_FRESHNESS_MINUTES` for expiration. This feature needs richer caching because Phase 1 data feeds all subsequent phases. The cache must include the target SSID name in the filename to support running the workflow for different SSIDs.

**Cache file naming**:
- `data/ssid_consol_phase1_matrix_{ssid_name}.csv` — Phase 1 matrix
- `data/ssid_consol_phase1_deviations_{ssid_name}.csv` — Phase 1 deviations
- `data/ssid_consol_results_phase{N}_{ssid_name}.csv` — Per-phase results log

**Freshness check**: Same pattern as existing — compare file modification time against `CSV_FRESHNESS_MINUTES`. Display "Using cached data (collected X minutes ago)" when fresh.

**Force-fresh override**: Prompt user "Cached data found (X minutes old). Use cached data? (Y/n):" — if 'n', delete cache and re-collect.

**Alternatives considered**:
- SQLite-only caching — Rejected because CSV is the standard cache format in MistHelper. Both CSV and SQLite are generated as outputs per constitution, but CSV is the cache medium.
- In-memory caching — Rejected because the workflow may span multiple sessions and needs persistence.

---

## R-007: Existing MistHelper Patterns to Follow

**Decision**: Follow established patterns exactly to maintain consistency:

| Pattern | Implementation |
|---------|---------------|
| Class naming | `SSIDTemplateConsolidationManager` |
| Constructor | `__init__(self)` with `self.org_id = ConfigUtils.get_cached_or_prompted_org_id()` |
| API session | Use global `apisession` variable |
| Menu integration | Register as menu option `159` in `menu_actions` dict |
| Confirmation | `InputUtils.safe_input("Type 'CONFIRM' to proceed: ", context="ssid_consolidation_phaseN")` |
| Data export | `DataExporter.write_with_format_selection(data, filename, api_function_name=...)` |
| Logging | `logging.info()` for user-facing, `logging.debug()` for internal state |
| .env variable | `MIST_TARGET_SSID` read via `os.getenv("MIST_TARGET_SSID", "")` |
| Error handling | Try/except with logging, graceful return on failure |

**Primary Key Strategies to register**:
```python
"listOrgTemplates": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name", "org_id"],
    "unique_constraints": [],
    "description": "Org WLAN templates with UUID primary keys"
}
```

---

## R-008: Template WLAN Ownership — How WLANs Belong to Templates

**Decision**: WLANs within a template are org-level WLANs (`/api/v1/orgs/{org_id}/wlans`) that have a `template_id` field linking them to their parent template. To add a WLAN to a template, create the WLAN with `template_id` set, or update the template object.

**Rationale**: The Mist API documentation shows that the template object at `/api/v1/orgs/{org_id}/templates/{template_id}` is a container. Org-level WLANs created with a `template_id` are bound to that template. The `getOrgTemplate` response includes the template metadata (applies, name, etc.) but WLANs are managed separately via the org WLANs endpoint.

**Workflow for adding SSID to template**:
1. Create template via `createOrgTemplate()` if it doesn't exist
2. Create WLAN via `createOrgWlan()` with `template_id` set to the new template's ID
3. The WLAN inherits the template's `applies` scope (sites/sitegroups)

**For appending a second SSID to an existing template**:
1. Get existing template ID
2. List org WLANs filtered by `template_id` to verify first SSID is intact
3. Create new WLAN with same `template_id`

**Alternatives considered**:
- Site-level WLANs — Not applicable; consolidated templates use org-level WLANs.

---

## R-009: Deviation Analysis Approach

**Decision**: For each WLAN field (excluding metadata), collect all unique values across sites within a consolidation group. Report deviations as `{field: {value1: count, value2: count}}`. During template creation, present deviations and require engineer selection.

**Rationale**: Full-object comparison (per FR-010a) catches all divergence. The metadata exclusion list (`id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`) removes fields that are inherently unique per-WLAN. Everything else must match for safe consolidation.

**Implementation**:
1. Flatten each WLAN JSON (using existing `flatten_dict()`)
2. Remove metadata fields
3. Group by consolidation group (Edge cluster)
4. For each field, collect unique values and count sites per value
5. Fields with >1 unique value are deviations
6. Cross-cluster: compare canonical (majority) values across groups

**Alternatives considered**:
- Hash-based comparison — Rejected because it only detects differences, not which fields differ.
- Whitelist comparison (only compare known fields) — Rejected per FR-010a which requires full-object comparison.

---

## R-010: Resume-After-Interruption Strategy

**Decision**: Each modification phase writes a results log CSV line-by-line as sites are processed. On re-run, read the results log to identify already-completed sites and offer to resume.

**Rationale**: MistHelper does not currently have a resume mechanism (interruptions are logged but require manual re-execution). This feature adds resume capability by leveraging the per-site results log (FR-024a). Each completed site is written immediately, so even if the process crashes, the log reflects progress.

**Implementation**:
1. Before starting a phase, check for an existing results log for that phase + SSID
2. If found, parse it and identify sites with `status=success`
3. Display "Found X/Y sites already processed. Resume from where you left off? (Y/n):"
4. If yes, skip already-completed sites; if no, start fresh (after confirmation)

**Alternatives considered**:
- Checkpoint file — Rejected; the results log already serves this purpose.
- Database-based tracking — Over-engineered for this use case; CSV results log is sufficient.
