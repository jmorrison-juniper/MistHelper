# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 283 | Trigger a synthetic test on demand | src.mist.intelligence.troubleshooting.synthetic_test_trigger.operation | SyntheticTestTrigger.run | interactive | Requires a site, an optional device, and a y/N confirmation | False | False |

## OperationRegistry comment
One `# WHY:` paragraph: `# WHY: menu 283 starts one Mist synthetic test only after an explicit y/N confirmation. It is interactive because it prompts for a site, scope, optional device, and test parameters. The operation masks RADIUS secrets and writes only a safe request summary and result.`

## Primary key strategies
```python
"SyntheticTestTrigger": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["site_id", "device_id", "scope", "test_type", "triggered_at"],
    "indexes": ["site_id", "device_id", "scope", "test_type", "status"],
},
```

## copilot-instructions category table
Add menu `283` to the `interactive` category row.

## Import line for MistHelper.py
`from src.mist.intelligence.troubleshooting.synthetic_test_trigger.operation import SyntheticTestTrigger  # Menu 283 (issue #3563) -- trigger one synthetic test on demand.`
