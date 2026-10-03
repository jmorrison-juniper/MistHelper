# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 293 | Run the Mist Edge lifecycle operation | src.mist.resources.org.mxedge_lifecycle.operation | MxEdgeLifecycleOperation.run | destructive | Mist Edge lifecycle actions change organization inventory, site assignment, tunnel data ports, and firmware state; requires typed confirmation and a live Mist tenant. | True | False |

## OperationRegistry comment

One `# WHY:` paragraph for the registry entry:

```python
# WHY: Menu 293 changes Mist Edge organization inventory, site assignment, tunnel data ports, and firmware state. It is destructive, so the operator must use the sub-menu typed confirmation words and dry-run mode before any live request.
```

## Primary key strategies

```python
"mxedge_lifecycle_log": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["timestamp_utc", "org_id", "step", "target"],
    "indexes": ["org_id", "step", "status", "dry_run"],
},
```

## copilot-instructions category table

Add menu `293` to the `destructive` category row. The row count increases by `1`.

## Import line for MistHelper.py

```python
from src.mist.resources.org.mxedge_lifecycle.operation import MxEdgeLifecycleOperation  # Menu 293 (issue #3573) -- destructive Mist Edge lifecycle operation.
```
