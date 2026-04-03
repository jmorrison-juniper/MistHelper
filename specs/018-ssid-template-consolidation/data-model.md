# Data Model: SSID Template Consolidation

**Feature Branch**: `018-ssid-template-consolidation`
**Date**: 2025-07-02

---

## Entities

### 1. ConsolidationMatrix (Phase 1 Output)

One row per site. The primary audit artifact used by all subsequent phases.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `site_name` | string | `listOrgSites` | Human-readable site name |
| `site_id` | UUID | `listOrgSites` | Mist site UUID (PK) |
| `template_name` | string | `listOrgTemplates` | Assigned WLAN template name |
| `template_id` | UUID | `listOrgTemplates` | Assigned WLAN template UUID |
| `target_ssid_name` | string | WLAN `ssid` field | Name of the matched target SSID |
| `target_ssid_id` | UUID | WLAN `id` field | UUID of the matched target SSID |
| `target_ssid_enabled` | boolean | WLAN `enabled` field | Whether target SSID is currently active |
| `auth_type` | string | WLAN `auth.type` | Authentication type: eap, open, psk, etc. |
| `ssid_classification` | string | Derived | "secured", "open_guest", or "anomaly" |
| `psk_detected` | boolean | Derived | True if auth_type is psk/psk-tkip/psk-wpa2-tkip |
| `vlan_enabled` | boolean | WLAN `vlan_enabled` | Whether VLAN tagging is on |
| `vlan_id` | string | WLAN `vlan_id` | VLAN assignment (may contain variable refs) |
| `interface_type` | string | WLAN `interface` | Connection: mxtunnel, site_mxedge, eth0, etc. |
| `mxtunnel_cluster_name` | string | Cross-ref mxtunnels | Mist Edge cluster name |
| `mxtunnel_cluster_id` | UUID | WLAN `mxtunnel_ids[0]` | Mist Edge cluster UUID |
| `other_ssid_names` | string | Template WLANs | Comma-separated names of non-target SSIDs |
| `other_ssid_ids` | string | Template WLANs | Comma-separated UUIDs of non-target SSIDs |
| `ssid_count` | integer | Template WLANs | Total SSIDs in template |
| `anomaly_flag` | boolean | Derived | True if ssid_count != 2 or other anomaly |
| `anomaly_reason` | string | Derived | e.g., "0 SSIDs", "1 SSID", "3+ SSIDs", "no template" |
| `consolidation_group` | string | Derived | Target group: cluster name or "pilot_test" |
| `collected_at` | ISO timestamp | Runtime | When this data was collected |

**Primary Key**: `site_id`
**Strategy**: `natural_pk`

### 2. DeviationReport (Phase 1 Output — Per-Cluster)

One row per deviating field per consolidation group.

| Field | Type | Description |
|-------|------|-------------|
| `consolidation_group` | string | Cluster name or "pilot_test" |
| `field_name` | string | Flattened WLAN field path (e.g., `auth_type`, `vlan_id`) |
| `unique_values` | string | JSON array of unique values found |
| `value_counts` | string | JSON object of value → site count |
| `site_count` | integer | Total sites in this group |
| `is_unanimous` | boolean | True if all sites have the same value |

**Primary Key**: Composite (`consolidation_group`, `field_name`)
**Strategy**: `composite_pk`

### 3. CrossClusterDrift (Phase 1 Output)

One row per field that differs between clusters.

| Field | Type | Description |
|-------|------|-------------|
| `field_name` | string | Flattened WLAN field path |
| `cluster_values` | string | JSON object of cluster_name → canonical value |
| `is_uniform` | boolean | True if all clusters agree |

**Primary Key**: `field_name`
**Strategy**: `natural_pk`

### 4. SiteVariableConfig (Phase 2)

One row per site per variable to be written.

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | UUID | Target site |
| `site_name` | string | Human-readable site name |
| `variable_name` | string | Variable key (e.g., `SSID_CONSOL_VLAN_ID`) |
| `proposed_value` | string | Value to write |
| `current_value` | string | Existing value if any (empty if new) |
| `conflict` | boolean | True if current_value exists and differs |
| `status` | string | "pending", "success", "failed", "skipped" |

**Primary Key**: Composite (`site_id`, `variable_name`)
**Strategy**: `composite_pk`

### 5. SiteGroupAssignment (Phase 3)

One row per site showing its target group assignment.

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | UUID | Target site |
| `site_name` | string | Human-readable site name |
| `target_group_name` | string | Name of the consolidation site group |
| `target_group_id` | UUID | Site group UUID (populated after creation) |
| `already_member` | boolean | True if site is already in the group |
| `status` | string | "pending", "success", "failed", "skipped" |

**Primary Key**: `site_id`
**Strategy**: `natural_pk`

### 6. ConsolidatedTemplateConfig (Phase 4)

One row per template to be created/updated.

| Field | Type | Description |
|-------|------|-------------|
| `template_name` | string | Target template name |
| `template_id` | UUID | Template UUID (populated after creation) |
| `sitegroup_name` | string | Associated site group name |
| `sitegroup_id` | UUID | Associated site group UUID |
| `is_pilot` | boolean | True if this is the pilot/test template |
| `target_ssid_name` | string | SSID being added this run |
| `ssid_config_json` | string | Full WLAN config JSON (with variable refs) |
| `existing_ssids` | string | Comma-separated names of already-present SSIDs |
| `action` | string | "create", "update_append", "no_change" |
| `status` | string | "pending", "success", "failed" |

**Primary Key**: `template_name`
**Strategy**: `natural_pk`

### 7. DeviationResolution (Phase 4 — Audit Log)

One row per deviation resolved by the engineer.

| Field | Type | Description |
|-------|------|-------------|
| `consolidation_group` | string | Cluster name or "all_clusters" |
| `field_name` | string | Deviating field path |
| `candidate_values` | string | JSON array of all unique values |
| `selected_value` | string | Value chosen by engineer |
| `resolution_type` | string | "per_cluster" or "cross_cluster" |
| `confirmed_at` | ISO timestamp | When engineer confirmed selection |

**Primary Key**: Composite (`consolidation_group`, `field_name`)
**Strategy**: `composite_pk`

### 8. DisableRecord (Phase 5)

One row per old template SSID to be disabled.

| Field | Type | Description |
|-------|------|-------------|
| `site_name` | string | Site name |
| `site_id` | UUID | Site UUID |
| `old_template_name` | string | Old per-site template name |
| `old_template_id` | UUID | Old template UUID |
| `ssid_name` | string | SSID to disable |
| `ssid_id` | UUID | SSID UUID |
| `already_disabled` | boolean | True if SSID was already disabled |
| `status` | string | "pending", "success", "failed", "skipped" |
| `skip_reason` | string | "psk", "anomaly", or empty |

**Primary Key**: `ssid_id`
**Strategy**: `natural_pk`

### 9. PhaseCompletionTracker (Cross-Phase State)

Tracks which phases have been completed for dependency enforcement.

| Field | Type | Description |
|-------|------|-------------|
| `phase_number` | integer | Phase 1-5 |
| `target_ssid` | string | SSID name this run targeted |
| `status` | string | "not_started", "in_progress", "completed", "interrupted" |
| `started_at` | ISO timestamp | When phase began |
| `completed_at` | ISO timestamp | When phase finished (null if incomplete) |
| `sites_processed` | integer | Count of sites processed |
| `sites_total` | integer | Total sites targeted |

**Primary Key**: Composite (`phase_number`, `target_ssid`)
**Strategy**: `composite_pk`

---

## Relationships

```text
ConsolidationMatrix (1) ──→ (0..N) SiteVariableConfig     [by site_id]
ConsolidationMatrix (1) ──→ (1)    SiteGroupAssignment     [by site_id]
ConsolidationMatrix (N) ──→ (1)    ConsolidatedTemplateConfig [by consolidation_group]
ConsolidationMatrix (1) ──→ (1)    DisableRecord           [by site_id + ssid_id]
DeviationReport     (N) ──→ (N)    DeviationResolution     [by group + field_name]
CrossClusterDrift   (N) ──→ (N)    DeviationResolution     [by field_name, group="all_clusters"]
```

---

## Validation Rules

1. **PSK exclusion**: Any row with `psk_detected = true` is excluded from Phases 2-5 processing
2. **Anomaly exclusion**: Any row with `anomaly_flag = true` is excluded from Phases 2-5 processing
3. **Phase dependency**: Phase N cannot start unless Phase N-1 has `status = "completed"` in PhaseCompletionTracker
4. **SSID match**: Target SSID matching is case-sensitive exact match against `ssid` field
5. **Variable name uniqueness**: Variable names must not conflict with existing non-consolidation variables (warn, don't block)
6. **Template naming**: Consolidated template names must be unique within the org (checked before creation)

---

## State Transitions

### Site Processing State (per phase)
```
pending → success    (API call succeeded)
pending → failed     (API call failed, logged with error)
pending → skipped    (PSK/anomaly, logged with reason)
```

### Phase State
```
not_started → in_progress → completed     (all sites processed)
not_started → in_progress → interrupted   (process killed mid-run)
interrupted → in_progress → completed     (resume succeeded)
```

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Additions

```python
"listOrgTemplates": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name", "org_id"],
    "unique_constraints": [],
    "description": "Org WLAN templates keyed by Mist UUID"
},
"listOrgSiteGroups": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name"],
    "unique_constraints": [],
    "description": "Org site groups keyed by Mist UUID"
},
"listOrgMxTunnels": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name"],
    "unique_constraints": [],
    "description": "Org Mist Edge tunnels keyed by Mist UUID"
},
"ssidConsolidationMatrix": {
    "type": "natural_pk",
    "primary_key": ["site_id"],
    "indexes": ["site_name", "template_id", "consolidation_group"],
    "unique_constraints": [],
    "description": "SSID consolidation audit matrix, one row per site"
},
"ssidConsolidationDeviations": {
    "type": "composite_pk",
    "primary_key": ["consolidation_group", "field_name"],
    "indexes": ["is_unanimous"],
    "unique_constraints": [],
    "description": "Per-cluster SSID deviation analysis"
},
"ssidConsolidationResults": {
    "type": "composite_pk",
    "primary_key": ["site_id", "phase_number"],
    "indexes": ["status", "site_name"],
    "unique_constraints": [],
    "description": "Per-phase per-site operation results log"
}
```
