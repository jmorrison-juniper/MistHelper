# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 273 | Admin and API Token Hygiene Report | src.mist.intelligence.reports.admin_token_hygiene.operation | AdminTokenHygieneReport.run | safe |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph for menu `273`: Admin and API token hygiene is read-only
and safe for automated tests because it reads administrator, organization token,
and organization setting metadata. It writes reports only under `data/`, and it
never prints or stores token key values.

## Primary key strategies

```python
"adminTokenHygieneAdmins": {
    "type": "natural_pk",
    "primary_key": ["row_id"],
    "indexes": ["email", "role_summary", "site_scope"],
},
"adminTokenHygieneTokens": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name", "created_by", "last_used"],
},
```

## copilot-instructions category table

The `safe` category gains menu number `273`. The safe count increases by one.

## Import line for MistHelper.py

`from src.mist.intelligence.reports.admin_token_hygiene.operation import AdminTokenHygieneReport  # Menu 273 (issue #3554) -- Export admin and API token hygiene reports.`

## Deferred integration notes

The integration pull request applies these source updates because this fleet
agent does not own the shared wiring files.

1. Add menu `273` to the menu registry with the title in this manifest.
2. Add operation `273` to the safe category.
3. Add the primary key strategy entries above.
4. Add the import line above to `MistHelper.py`.
5. Update the README menu table and safe operation count.
6. Regenerate the menu reference and the menu API map.
