# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 289 | Export the client fingerprint census for a site | src.reports.client_fingerprint_census.operation | ClientFingerprintCensus.run | interactive_safe | Requires a site prompt and a distinct-field prompt. | False | False |

## OperationRegistry comment
One `# WHY:` paragraph for the registry entry, in the style of the menu 269 and menu 270 entries:

```python
# WHY: A NOC engineer needs a site-scoped client fingerprint census before NAC policy design and capacity planning. The operation prompts for one site and one OpenAPI distinct field, then exports a read-only count report.
```

## Primary key strategies
```python
"countOrgClientFingerprints": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["site_id", "distinct", "value"],
    "indexes": ["site_id", "site_name", "distinct", "value"],
},
```

## copilot-instructions category table
Add menu `289` to the `interactive_safe` row. Increase the `interactive_safe` count by one. Increase the full menu range upper bound as needed after integration.

## Import line for MistHelper.py
`from src.reports.client_fingerprint_census.operation import ClientFingerprintCensus  # Menu 289 (issue #3569) -- export a site client fingerprint census.`

## Deferred shared-file changes
The integration pull request must add menu `289` to `MistHelper.py`, `src/utils/operation_registry.py`, generated menu references, and `src/refactors/endpoint_primary_key_strategies.py`. This feature branch must not edit those shared files.
