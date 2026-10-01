# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 292 | DESTRUCTIVE: Import PSKs, user MACs, and assets from CSV | src.inventory.csv_imports.operation | CsvImportOperation.run | destructive |  | True | False |

## OperationRegistry comment

One `# WHY:` paragraph for the registry entry, in the style of menu 269 and menu 270:

`# WHY: menu 292 imports PSKs, user MACs, and assets into Mist Cloud from CSV files under data/. It creates or updates cloud records, so it is destructive and must stay behind the exact IMPORT <row_count> confirmation and --dry-run support.`

## Primary key strategies

```python
"csv_import_log": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["import_type", "row_count", "dry_run", "status", "message"],
    "indexes": ["import_type", "status"],
},
```

The feature implementation writes `CsvImportLog.csv` directly under `data/`. If the integration pull request routes this audit log through `DataExporter`, use the strategy above.

## copilot-instructions category table

Add menu `292` to the `destructive` row. Increase the destructive count by one. Do not add the menu to `safe` or `interactive_safe` because it creates or updates Mist cloud records.

## Import line for MistHelper.py

`from src.inventory.csv_imports.operation import CsvImportOperation  # Menu 292 (issue #3572) -- destructive CSV imports for PSKs, user MACs, and assets.`

## Menu registration note

Register menu 292 with `handler=CsvImportOperation.run`, `category=OperationRegistry.skip_category("292")`, `destructive=True`, and `supports_fast=False`. The title must state `DESTRUCTIVE` and must mention CSV import. Keep the typed confirmation phrase `IMPORT <row_count>` in the menu description.

## Deferred generated files

The integration pull request must regenerate `documentation/menu_reference.md` and the wiki menu pages after menu 292 is wired. This feature branch must not edit those files.
