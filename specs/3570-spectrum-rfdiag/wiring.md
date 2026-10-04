# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 290 | Run spectrum analysis and RF diagnostic recording | src.mist.intelligence.troubleshooting.rf_diagnostics.operation | RfDiagnosticsOperation.run | interactive |  | False | False |

## OperationRegistry comment
One `# WHY:` paragraph for the registry entry, in the style of the menu 269 and menu 270 entries:

`# WHY: Menu 290 starts bounded RF diagnostics only after an operator confirmation. The operation can run AP spectrum analysis or client RF diagnostic recording, and it stops a recording in a finally block so Ctrl+C does not leave cloud work running.`

## Primary key strategies
```python
"rf_diagnostics_runs": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["mode", "site_id", "target", "started_at"],
    "indexes": ["mode", "site_id", "target", "status", "started_at"],
}
```

## copilot-instructions category table
Add menu `290` to the `interactive` category row. Do not mark menu `290` as destructive.

## Import line for MistHelper.py
`from src.mist.intelligence.troubleshooting.rf_diagnostics.operation import RfDiagnosticsOperation  # Menu 290 (issue #3570) -- RF diagnostics spectrum and recording workflow.`

## Changelog ownership
The fleet contract allows this package pull request to add `changelog.d/issue-3570-spectrum-rfdiag.md`. The integration pull request must not duplicate that fragment.

## Deferred integration files
The integration pull request owns these files and generated references:

- `MistHelper.py` menu registration.
- `src/foundation/support/utils/operation_registry.py` registry metadata.
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py` primary-key strategy.
- `README.md` operation count and menu table.
- `documentation/menu_reference.md` and `documentation/wiki/**` generated menu reference output.
- `.github/copilot-instructions.md` category table.

## Endpoint catalog notes
Record these Mist API paths in the integration review:

- `POST /api/v1/sites/{site_id}/analyze_spectrum` uses operationId `initiateSiteAnalyzeSpectrum`.
- `GET /api/v1/sites/{site_id}/analyze_spectrum` uses operationId `getSiteRunningSprectrumAnalysis`.
- `POST /api/v1/sites/{site_id}/rfdiags` uses operationId `startSiteRecording`.
- `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}` uses operationId `getSiteRfdiagRecording`.
- `POST /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/stop` uses operationId `stopSiteRfdiagRecording`.
- `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download` uses operationId `downloadSiteRfdiagRecording`.
- `GET /api/v1/sites/{site_id}/rfdiags` uses operationId `getSiteSiteRfdiagRecording`. The assignment named `listSiteRfdiagRecording`, but OpenAPI and SDK expose `getSiteSiteRfdiagRecording`.

## Integration boundary
This core package pull request does not edit the deferred files. The fleet contract requires that this manifest carry the exact wiring values. The integration pull request copies the values from this file.
