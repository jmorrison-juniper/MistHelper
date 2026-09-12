# Research: Bulk RADIUS WLAN Configuration

**Feature**: 001-radius-wlan-config  
**Date**: 2026-03-03

## Research Tasks

### 1. Mist API: How to update WLAN authentication settings

**Decision**: Use existing patterns from `WLANRadiusTimerManager`

**Rationale**: MistHelper already has working implementations for three WLAN update scenarios:
- `mistapi.api.v1.sites.wlans.updateSiteWlan(apisession, site_id, wlan_id, payload)` - for site-level WLANs
- `mistapi.api.v1.orgs.wlans.updateOrgWlan(apisession, org_id, wlan_id, payload)` - for org-level WLANs
- `mistapi.api.v1.orgs.sitetemplates.updateOrgSiteTemplate(...)` - for template-managed WLANs

**Alternatives considered**: None - existing pattern is proven and working

### 2. .env Configuration: Best practices for MistHelper

**Decision**: Follow existing `os.getenv()` pattern with defaults

**Rationale**: MistHelper consistently uses this pattern for all configurable values:
```python
RADIUS_AUTH_TIMEOUT = int(os.getenv("RADIUS_AUTH_TIMEOUT", "3"))
RADIUS_AUTH_RETRIES = int(os.getenv("RADIUS_AUTH_RETRIES", "2"))
RADIUS_FAST_DOT1X = os.getenv("RADIUS_FAST_DOT1X", "true").lower() == "true"
```

**Alternatives considered**: 
- Hardcoded values - Rejected: Less flexible for different enterprise requirements
- Interactive prompts - Rejected: Slower for bulk operations

### 3. Selection Input Parsing: Range and comma-separated parsing

**Decision**: Reuse existing `_parse_selection_input()` method from MSP multi-org firmware upgrade feature (line ~37313)

**Rationale**: Well-tested implementation already exists:
```python
def _parse_selection_input(self, user_input: str, max_count: int) -> list:
    """
    Parse user selection input into list of 0-based indices.
    
    Supports:
    - Single index: "1" -> [0]
    - Comma-separated: "1,3,5" -> [0, 2, 4]
    - Dash range: "1-5" -> [0, 1, 2, 3, 4]
    - 'through' range: "1 through 5" -> [0, 1, 2, 3, 4]
    - Mixed: "1-3, 5, 7 through 10" -> [0, 1, 2, 4, 6, 7, 8, 9]
    """
```

For "all" keyword, check before calling parser:
```python
if selection.lower() == "all":
    selected_indices = list(range(len(wlans)))
else:
    selected_indices = self._parse_selection_input(selection, len(wlans))
```

**Alternatives considered**:
- External library (e.g., `parse-range`) - Rejected: No additional dependencies constraint
- Simple comma-only - Rejected: Ranges improve UX for bulk selection

### 4. RADIUS Detection: How to identify RADIUS/RadSec WLANs

**Decision**: Reuse existing `_uses_radius_auth()` logic from `WLANRadiusTimerManager`

**Rationale**: Already proven detection logic (line ~45627):
```python
def _uses_radius_auth(wlan: Dict[str, Any]) -> bool:
    has_auth_servers = bool(wlan.get('auth_servers'))
    radsec_config = wlan.get('radsec', {})
    has_radsec = radsec_config.get('enabled', False) if isinstance(radsec_config, dict) else False
    auth_config = wlan.get('auth', {})
    uses_eap = auth_config.get('type', '') in ['eap', 'eap192'] if isinstance(auth_config, dict) else False
    return has_auth_servers or has_radsec or uses_eap
```

**Alternatives considered**: None - existing logic is comprehensive

### 5. CSV Export: Audit trail format

**Decision**: Use existing `DataExporter` pattern to `data/` directory

**Rationale**: MistHelper uses `DataExporter.write_with_format_selection()` for all exports. For audit trail, use timestamped filename: `RadiusWLANBulkConfig_YYYYMMDD_HHMMSS.csv`

**Columns**:
- wlan_id, ssid, site_name, inheritance_level
- before_timeout, after_timeout
- before_retries, after_retries
- before_fast_dot1x, after_fast_dot1x
- status (success/skipped/failed), error_message, timestamp

**Alternatives considered**: 
- SQLite - Already supported via existing dual-output infrastructure, but CSV provides simpler audit sharing

### 6. Menu Number Assignment

**Decision**: Use menu number **116** (next available in advanced operations range)

**Rationale**: 
- Menu 102 already exists for site-level RADIUS timer management
- Numbers 103-115 are taken by other operations
- 116 is next sequential available number

**Alternatives considered**:
- Extend menu 102 - Rejected: Different use case (site-level vs org-level bulk)

## Resolved Clarifications

All NEEDS CLARIFICATION items resolved in spec.md - no outstanding research gaps.
