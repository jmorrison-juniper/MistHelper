# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 287 | Replace a Mist inventory device for RMA | src.inventory.device_replace.operation | DeviceReplaceOperation.run | destructive |  | True | False |

## OperationRegistry comment
One `# WHY:` paragraph for the registry entry, in the style of menu 269 and menu 270 entries:

`# WHY: Menu 287 moves an existing Mist device configuration to an unassigned replacement during an RMA. It is destructive because the Mist cloud changes inventory assignment and configuration ownership. The operation requires the typed word REPLACE, writes a backup under data/rma_backups/ before the request, and supports --dry-run so an operator can prove the path without changing Mist.`

## Primary key strategies
```python
"replaceOrgDevices": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["timestamp", "org_id", "old_mac", "new_mac", "result"],
    "indexes": ["org_id", "old_mac", "new_mac", "result"],
},
```

## copilot-instructions category table
Add menu `287` to the `destructive` category row. Increase the destructive count by one. Do not add this menu to any safe or interactive category.

## Import line for MistHelper.py
`from src.inventory.device_replace.operation import DeviceReplaceOperation  # Menu 287 (issue #3567) -- Replace a Mist inventory device for an RMA.`

## Deferred integration changes
The integration pull request owns these edits:

1. Add the menu row to `MistHelper.py` and call `DeviceReplaceOperation.run`.
2. Add the operation metadata to `src/utils/operation_registry.py` as destructive with typed `REPLACE` and dry-run support.
3. Add the primary key strategy above to `src/refactors/endpoint_primary_key_strategies.py` if the CSV log is exported to a database backend.
4. Update `README.md`, `.github/copilot-instructions.md`, `documentation/menu_reference.md`, and generated wiki pages.
5. Run generated reference commands after the menu registration exists.
