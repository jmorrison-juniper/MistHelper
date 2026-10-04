# Wiring manifest

Menu 276 wiring is deferred to the integration pull request.

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
|------|-------|----------------|-------------------|----------|-------------|-------------|---------------|
| 276 | Export the organization security posture checklist | src.mist.intelligence.reports.org_security_posture.runner | OrgSecurityPostureChecklist.run | safe |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph for the registry entry:

```python
# WHY: menu 276 is a read-only organization settings audit that writes OrgSecurityPosture.csv and uses fixture data in --test.
```

## Primary key strategies

```python
"orgSecurityPostureChecklist": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["check id", "setting path", "recommended value"],
    "indexes": ["area", "verdict", "check id"],
},
```

## copilot-instructions category table

Add menu `276` to the `safe` category row.

## Import line for MistHelper.py

```python
from src.mist.intelligence.reports.org_security_posture.runner import OrgSecurityPostureChecklist  # Menu 276 (issue #3557) -- organization security posture checklist.
```

## Deferred integration files

The integration pull request owns these files:

- `MistHelper.py`
- `src/foundation/support/utils/operation_registry.py`
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
- `README.md`
- `documentation/menu_reference.md`
- generated menu reference artifacts
