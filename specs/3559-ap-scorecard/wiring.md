# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 278 | Export the organization access point scorecard | `src.reports.ap_scorecard.operation` | `ApScorecard.run` | `safe` |  | `False` | `False` |

## OperationRegistry comment

`# WHY: Menu 278 is a read-only organization AP health export. It mirrors the Mist Access Points page tiles across all sites, writes operator evidence to data/ApScorecard.csv and data/ApScorecardBySite.csv, and uses the existing org device statistics pagination seam instead of a custom loop.`

## Primary key strategies

```python
"ap_scorecard": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id", "mac", "version", "status"],
    "indexes": ["org_id", "site_id", "mac", "model", "status"],
},
"ap_scorecard_by_site": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id"],
    "indexes": ["org_id", "site_id", "site"],
},
```

## copilot-instructions category table

Add menu `278` to the `safe` category row. Increase the `safe` count by `1`. Do not add menu `278` to `destructive`, `interactive`, `interactive_safe`, `resource_intensive`, `websocket`, or `continuous_loop`.

## Import line for MistHelper.py

`from src.reports.ap_scorecard.operation import ApScorecard  # Menu 278 (issue #3559) -- export AP scorecard tiles across all sites.`

## Menu registration note

Register menu `278` with the title `Export the organization access point scorecard`. Set the handler to `ApScorecard.run`. The handler takes no positional argument.

## README and generated documentation note

Add menu `278` to the safe operations documentation. Regenerate the menu reference and the menu API map in the integration pull request.

## Release note note

Create `changelog.d/issue-3559-ap-scorecard.md` during implementation, not during this plan step. Use one `### Added` heading and one bullet that names issue `#3559`.

## Integration validation note

After the integration pull request registers menu `278`, run `MistHelper.py --test` with the repository virtual environment. Confirm that menu `278` runs with no prompt and routes both exports through `data/ApScorecard.csv` and `data/ApScorecardBySite.csv`. The feature-owned tests prove the handler calls no direct `input()` prompt and passes both file names to `DataExporter`; the final `--test` and `data/` path proof needs the deferred menu registration.
