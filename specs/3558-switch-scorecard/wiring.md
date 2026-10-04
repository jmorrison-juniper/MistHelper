# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 277 | Export the organization switch scorecard | `src.mist.intelligence.reports.switch_scorecard.operation` | `SwitchScorecard.run` | `safe` |  | `False` | `False` |

## OperationRegistry comment

One `# WHY:` paragraph for the registry entry:

```python
# WHY: menu 277 gives NOC engineers one organization-wide switch scorecard without repeated site-page checks.
```

## Primary key strategies

```python
"switch_scorecard": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id", "switch_mac", "model", "version"],
    "indexes": ["org_id", "site_id", "model", "version_compliant", "config_success"],
},
"switch_scorecard_by_site": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["site_id", "site_name"],
    "indexes": ["site_id", "switch_count", "version_compliance_percent"],
},
```

## copilot-instructions category table

Add menu `277` to the `safe` category row. Increase the `safe` count by one.

## Import line for MistHelper.py

```python
from src.mist.intelligence.reports.switch_scorecard.operation import SwitchScorecard  # Menu 277 (issue #3558) -- organization switch scorecard report.
```

## Deferred integration notes

The feature branch does not edit `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `README.md`, or generated menu references. The integration pull request applies this manifest verbatim.
