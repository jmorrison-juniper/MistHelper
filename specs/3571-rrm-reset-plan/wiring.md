# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 291 | Optimize or reset site RRM with before and after plan capture | src.site.rrm_reset.operation | RrmResetOperation.run | destructive |  | True | False |

## OperationRegistry comment

One `# WHY:` paragraph for menu `291`: `# WHY: this destructive site RRM action must capture the current plan before it changes channels or power, and typed confirmation keeps accidental optimize or reset requests from reaching Mist.`

## Primary key strategies

```python
"rrm_reset_plan_diff": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["site_id", "ap", "band", "change_type"],
    "indexes": ["site_id", "ap", "band", "change_type"],
},
```

## copilot-instructions category table

Add menu `291` to the `destructive` row.

## Import line for MistHelper.py

`from src.site.rrm_reset.operation import RrmResetOperation  # Menu 291 (issue #3571) -- capture RRM before and after optimize or reset.`

## Deferred registration

The integration pull request registers menu `291` in `MistHelper.py` and `src/utils/operation_registry.py`. This feature branch does not edit those files.

## Environment documentation

Add `RRM_SETTLE_SECONDS=300` to `deploy/.env.example` if the integration pull request owns environment documentation. This feature branch cannot edit that file under the fleet contract.
