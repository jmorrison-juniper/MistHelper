# Implementation Plan: AP Localization Acceptance (Menu 204)

**Branch**: `204-ap-localization-acceptance` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/204-ap-localization-acceptance/spec.md`

## Summary

Add menu operation 204 to accept or reject pending AP localization data
(placement and/or orientation) for a site map, via
`POST /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values`
(`mistapi.api.v1.sites.maps.confirmSiteApLocalizationData`). Follows the
destructive-operation safety model: validate inputs, display elevated
warning, require typed confirmation, execute single API call, export
audit record for every attempt (executed and cancelled).

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: mistapi 0.63.0+ (`mistapi.api.v1.sites.maps.confirmSiteApLocalizationData`)  
**Storage**: CSV / SQLite via `DataExporter.write_with_format_selection`  
**Testing**: pytest (unit tests in `tests/unit/test_menu_204_ap_localization.py`)  
**Target Platform**: Linux container (SSH) and local Windows dev  
**Project Type**: CLI / interactive menu (single-file extension of MistHelper.py)  
**Performance Goals**: Single API call, interactive; no throughput target  
**Constraints**: EOF-safe input via `safe_input()`, ASCII-only logs, max 25 lines/function, max 5 params  
**Scale/Scope**: +1 class, +1 menu dispatch entry, +1 test file within the existing 28K-line codebase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | `ApLocalizationManager` has 4 methods; each ≤25 lines, ≤5 params |
| II. Class-Based Architecture | PASS | `ApLocalizationManager` class; no standalone wrapper functions |
| III. Safety-First | PASS | `safe_input()` wraps all prompts; typed confirmation gate before API call; validate-early pattern |
| IV. Full Deployment Pipeline | PASS | `py_compile`, commit, push, CI wait, pull, restart mandatory |
| V. Observability & Logging | PASS | ASCII-only logs; `logging.info` before / `logging.debug` after every action |
| VI. Inline Comments | PASS | Every executable line of generated code gets same-line comment explaining why |
| VII. Action Logging | PASS | `logging.info` before, `logging.debug` after every meaningful action |

*Post-design re-check: no violations introduced by Phase 1 design.*

## Project Structure

### Documentation (this feature)

```text
specs/204-ap-localization-acceptance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── confirmSiteApLocalizationData.md   # API contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
MistHelper.py           # +ApLocalizationManager class (~80 lines), +dispatch entry '204'
README.md               # Operation count 203→204; new row in Destructive section
CHANGELOG.md            # New entry: version YY.MM.DD.HH.MM - add menu 204 AP localization acceptance
tests/
└── unit/
    └── test_menu_204_ap_localization.py   # New: validation + call-wiring unit tests
```

**Structure Decision**: Single-file extension (Option 1 equivalent). All new code
appended to `MistHelper.py` after Menu 203 `send_site_nac_client_coa` (~line 28155).
New class `ApLocalizationManager` contains all logic; public entry point
`confirm_site_ap_localization_data()` added to menu dispatch dict.

## Implementation Design

### Class: `ApLocalizationManager`

```text
ApLocalizationManager
├── confirm_site_ap_localization()   # Entry: prompt → validate → warn → confirm → call → audit
├── _prompt_inputs()                 # Collect site_id, map_id, for_type, accept_flag, macs
├── _validate_inputs()               # Guard: non-empty UUIDs, for_type in allowed set
└── _export_audit_record()           # Build and write audit dict via DataExporter
```

*Note: typed confirmation is handled inline in `confirm_site_ap_localization()` to keep*
*method count at 4 and avoid a 1-line dedicated method.*

### API Contract

- **Endpoint**: `POST /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values`
- **SDK call**: `mistapi.api.v1.sites.maps.confirmSiteApLocalizationData(apisession, site_id, map_id, body)`
- **Body fields**:
  - `accept` (bool, required): `true` = accept, `false` = reject
  - `for` (str, required): `"placement"` or `"orientation"`
  - `macs` (list[str], optional): AP MAC addresses; omit for full-map scope
- **Success response**: HTTP 200, empty body
- **Error responses**: 400, 401, 403, 404, 429

### Typed Confirmation Phrases

| Action | Required phrase |
|--------|----------------|
| Accept | `ACCEPT-LOCALIZATION` |
| Reject | `REJECT-LOCALIZATION` |

### Audit Record Fields

| Field | Source |
|-------|--------|
| `timestamp` | `datetime.utcnow().isoformat()` |
| `menu_operation` | `"204"` |
| `site_id` | user input |
| `map_id` | user input |
| `for_type` | user input |
| `action` | `"accept"` or `"reject"` |
| `macs_scope` | comma-joined macs or `"full_map"` |
| `http_status` | response status code or `"n/a"` |
| `outcome` | `"executed"` or `"cancelled"` |
| `cancel_reason` | `"confirmation_failed"` / `"validation_failed"` / `""` |

### Primary Key Strategy

```python
'confirmSiteApLocalizationData': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_constraints': ['timestamp', 'site_id', 'map_id', 'for_type', 'action'],
    'description': 'AP localization acceptance audit records - action-level, no stable UUID from API'
}
```

### Test-Mode Guard

```python
if getattr(globals(), 'TEST_MODE', False):  # Skip real call during automated --test run
    print('[TEST MODE] Skipping confirmSiteApLocalizationData call')
    return
```

## Complexity Tracking

No constitution violations. No justification required.
