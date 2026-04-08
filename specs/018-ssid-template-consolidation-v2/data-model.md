# Data Model: SSID Template Consolidation Rewrite

**Spec**: 018-ssid-template-consolidation-v2
**Date**: 2026-04-08

---

## Entity Definitions

### 1. ConsolidationMatrix (Phase 1 Output)

One row per site. This is the primary report and the data foundation for all subsequent phases.

| Field | Type | Source | Description |
| - | - | - | - |
| site_name | str | listOrgSites.name | Human-readable site name |
| site_id | str (UUID) | listOrgSites.id | Mist site UUID |
| template_name | str | listOrgTemplates.name | Current WLAN template name |
| template_id | str (UUID) | listOrgTemplates.id | Current WLAN template UUID |
| ssid_name | str | WLAN.ssid | Matched target SSID name |
| ssid_id | str (UUID) | WLAN.id | Matched WLAN UUID within template |
| auth_type | str | WLAN.auth.type | Authentication type (eap, open, psk, etc.) |
| vlan_id | str | WLAN.vlan_id | VLAN assignment (may be variable ref) |
| mxtunnel_id | str (UUID) | WLAN.mxtunnel_ids[0] | First Mist Edge cluster UUID |
| mxtunnel_name | str | MxTunnel lookup | Resolved Edge cluster name |
| psk_detected | bool | auth_type check | True if auth.type in (psk, psk-tkip, psk-wpa2-tkip) |
| anomaly | bool | validation | True if template has != 2 SSIDs, no cluster, etc. |
| anomaly_reason | str | validation | Human-readable reason code |
| ssid_enabled | bool | WLAN.enabled | Current enabled state of matched SSID |
| ssid_count_in_template | int | len(template.wlans) | Number of SSIDs in the template |
| sitegroup_ids | str (JSON) | listOrgSites.sitegroup_ids | Current site group memberships |
| target_group | str | cluster mapping | Assigned consolidation group name |
| target_group_id | str (UUID) | Phase 3 | Assigned consolidation group UUID (populated after Phase 3) |

**Primary Key Strategy** (for ENDPOINT_PRIMARY_KEY_STRATEGIES):
```python
'ssidConsolidationMatrix': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'ssid_id'],
    'indexes': ['site_name', 'template_id', 'mxtunnel_id', 'target_group'],
    'unique_constraints': [],
    'description': 'SSID consolidation matrix — one row per site per target SSID',
}
```

**Anomaly Reason Codes**:
- `"0 SSIDs"` — template contains no WLANs
- `"1 SSID"` — template contains only 1 WLAN
- `"3+ SSIDs"` — template contains 3 or more WLANs
- `"target SSID not found"` — template exists but target SSID name not matched
- `"no Edge cluster mapping"` — WLAN has no mxtunnel_ids or ID not in cluster lookup
- `"no template assigned"` — site has no WLAN template

---

### 2. DeviationReport (Phase 1 Sub-report)

Per-cluster analysis of parameter differences for the target SSID.

| Field | Type | Description |
| - | - | - |
| cluster_name | str | Edge cluster name (or "cross_cluster") |
| cluster_id | str (UUID) | Edge cluster UUID (empty for cross_cluster) |
| parameter | str | WLAN JSON field name that differs |
| unique_values | list[dict] | Each unique value with site count: `[{"value": X, "sites": [...], "count": N}]` |
| canonical_value | Any | Majority value (most sites) — used as default in Phase 4 |

**Primary Key Strategy**:
```python
'ssidConsolidationDeviation': {
    'type': 'composite_pk',
    'primary_key': ['cluster_id', 'parameter'],
    'indexes': ['cluster_name'],
    'unique_constraints': [],
    'description': 'SSID parameter deviations within cluster groups',
}
```

---

### 3. SiteVariableAssignment (Phase 2)

Tracks which site variables are proposed/written for each site.

| Field | Type | Description |
| - | - | - |
| site_name | str | Site name |
| site_id | str (UUID) | Site UUID |
| variable_name | str | Variable key (e.g., `VLAN_ID`, `MXTUNNEL_ID`) |
| proposed_value | str | Value to be written |
| current_value | str | Existing value (empty if none) |
| status | str | `pending`, `written`, `already_configured`, `conflict`, `skipped`, `failed` |
| reason | str | Status explanation (e.g., "PSK site", "same value exists") |
| timestamp | str (ISO) | When the write occurred |

**Primary Key Strategy**:
```python
'ssidConsolidationSiteVars': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'variable_name'],
    'indexes': ['site_name', 'status'],
    'unique_constraints': [],
    'description': 'Site variable assignments for SSID consolidation',
}
```

---

### 4. SiteGroupAssignment (Phase 3)

Tracks site-to-group assignment results.

| Field | Type | Description |
| - | - | - |
| site_name | str | Site name |
| site_id | str (UUID) | Site UUID |
| group_name | str | Target site group name |
| group_id | str (UUID) | Target site group UUID |
| cluster_name | str | Source Edge cluster name (or "pilot") |
| status | str | `assigned`, `already_assigned`, `skipped`, `failed` |
| reason | str | Status explanation |
| timestamp | str (ISO) | When the assignment occurred |

**Primary Key Strategy**:
```python
'ssidConsolidationSiteGroups': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'group_id'],
    'indexes': ['group_name', 'status'],
    'unique_constraints': [],
    'description': 'Site group assignments for SSID consolidation',
}
```

---

### 5. TemplateCreationResult (Phase 4)

Tracks template creation/update results.

| Field | Type | Description |
| - | - | - |
| template_name | str | Consolidated template name |
| template_id | str (UUID) | Template UUID (after creation) |
| group_name | str | Associated site group name |
| group_id | str (UUID) | Associated site group UUID |
| ssid_name | str | SSID name added to this template |
| action | str | `created`, `updated_append`, `already_exists`, `failed` |
| deviation_resolutions | str (JSON) | Serialized list of deviation choices made |
| status | str | `success`, `failed` |
| error | str | Error message if failed |
| timestamp | str (ISO) | When the operation occurred |

**Primary Key Strategy**:
```python
'ssidConsolidationTemplates': {
    'type': 'composite_pk',
    'primary_key': ['template_id', 'ssid_name'],
    'indexes': ['template_name', 'group_name', 'status'],
    'unique_constraints': [],
    'description': 'Consolidated template creation results',
}
```

---

### 6. SSIDDisableResult (Phase 5)

Tracks old SSID disable operations.

| Field | Type | Description |
| - | - | - |
| site_name | str | Site name |
| site_id | str (UUID) | Site UUID |
| old_template_name | str | Old per-site template name |
| old_template_id | str (UUID) | Old template UUID |
| ssid_name | str | SSID that was disabled |
| ssid_id | str (UUID) | WLAN UUID that was disabled |
| previous_enabled | bool | Was it enabled before? |
| status | str | `disabled`, `already_disabled`, `skipped`, `failed` |
| reason | str | Status explanation |
| timestamp | str (ISO) | When the disable occurred |

**Primary Key Strategy**:
```python
'ssidConsolidationDisable': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'ssid_id'],
    'indexes': ['old_template_id', 'status'],
    'unique_constraints': [],
    'description': 'Old SSID disable results for SSID consolidation',
}
```

---

## State Transitions

### Phase Dependency Chain

```
Phase 1 (read-only audit)
    ↓ produces: cache.json + matrix report
Phase 2 (write site vars)
    ↓ requires: Phase 1 cache
    ↓ produces: phase2_results.json
Phase 3 (create/assign groups)
    ↓ requires: Phase 2 results
    ↓ produces: phase3_results.json
Phase 4 (create templates)
    ↓ requires: Phase 3 results
    ↓ produces: phase4_results.json
Phase 5 (disable old SSIDs)
    ↓ requires: Phase 4 results
    ↓ produces: phase5_results.json
```

### Site Status Flow

```
[discovered] → (Phase 1: classify)
  ├─ [psk_excluded] → skipped in all phases
  ├─ [anomaly] → skipped in phases 2-5
  └─ [eligible]
      → (Phase 2) → [vars_configured]
      → (Phase 3) → [group_assigned]
      → (Phase 4) → [template_created]
      → (Phase 5) → [old_ssid_disabled]
```

---

## Cache File Structures

### data/ssid_consolidation_cache.json

```json
{
  "target_ssid": "CorpSecure",
  "org_id": "uuid",
  "collected_at": "2026-04-08T12:00:00Z",
  "freshness_minutes": 60,
  "data": {
    "sites": [...],
    "wlan_templates": [...],
    "org_wlans": [...],
    "mxtunnels": [...],
    "sitegroups": [...]
  },
  "matrix": [...],
  "deviations": {...}
}
```

### data/ssid_consolidation_phase{N}_results.json

```json
{
  "phase": 2,
  "target_ssid": "CorpSecure",
  "started_at": "2026-04-08T12:05:00Z",
  "completed_at": "2026-04-08T12:10:00Z",
  "total_sites": 170,
  "processed": 170,
  "results": [
    {
      "site_id": "uuid",
      "site_name": "Site-A",
      "status": "written",
      "details": {...},
      "timestamp": "2026-04-08T12:05:01Z"
    }
  ]
}
```

---

## Validation Rules

1. **PSK detection**: `wlan.get("auth", {}).get("type", "")` in `("psk", "psk-tkip", "psk-wpa2-tkip")`
2. **Anomaly — SSID count**: `len(template_wlans) != 2` → anomaly
3. **Anomaly — no cluster**: `not wlan.get("mxtunnel_ids")` or ID not in mxtunnel_lookup → anomaly
4. **Anomaly — no template**: site has no `sitetemplate_id` → anomaly
5. **Pilot pattern**: `re.search(r'(?i)\b(pilot|test|lab)\b', site_name)` → pilot group
6. **Variable name convention**: `MISTHELPER_<PARAM>` (e.g., `MISTHELPER_VLAN_ID`)
7. **Template name convention**: `misthelper_<group>_<basename>`
8. **CONFIRM gate**: exact string match `"CONFIRM"`, case-sensitive
