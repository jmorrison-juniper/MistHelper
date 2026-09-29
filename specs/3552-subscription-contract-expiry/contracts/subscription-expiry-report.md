# Contract: Subscription Contract Expiry Report

## Run handler

The public run handler is:

```python
SubscriptionExpiryReport.run()
```

The handler accepts no positional argument. It resolves the active Mist context
with `SourceDependencyResolver`, matching the pattern used by menus 269 and 270.

## SDK client seam

`client.py` exposes a class that wraps only these Mist SDK calls:

| Method | SDK operation |
| - | - |
| `fetch_license_summary` | `mistapi.api.v1.orgs.licenses.getOrgLicensesSummary` |
| `fetch_license_usage_by_site` | `mistapi.api.v1.orgs.licenses.getOrgLicensesBySite` |
| `search_jsi_assets_and_contracts` | `mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts` |

The client converts SDK response wrappers into plain Python containers. The
client does not score rows and does not export files.

## Pure scoring seam

`model.py` holds dataclasses and scoring classes. It does not import Mist SDK
modules. It does not prompt the operator. It does not write files.

## Operation seam

`operation.py` prompts for or resolves the active organization context, calls
the client, calls the model scoring methods, exports both CSV files, and prints
the console summary.

## Output file: SubscriptionExpiry.csv

The file contains exactly one row per subscription type.

| Column | Required | Value rule |
| - | - | - |
| `subscription_type` | Yes | Source subscription type. |
| `entitled` | Yes | Entitled count or missing value marker. |
| `usage` | Yes | Usage count or missing value marker. |
| `status` | Yes | `Active`, `Expired`, `Exceeded`, or `Inactive`. |
| `end_date` | Yes | ISO date or missing value marker. |
| `days_remaining` | Yes | Integer days or missing value marker. |
| `band` | Yes | `expired`, `0-30 days`, `31-90 days`, `more than 90 days`, or missing value marker. |

## Output file: ContractExpiry.csv

The file contains exactly one row per device.

| Column | Required | Value rule |
| - | - | - |
| `serial` | Yes | Device serial or missing value marker. |
| `model` | Yes | Device model or missing value marker. |
| `contract_status` | Yes | Mist contract status or visible source value. |
| `contract_state` | Yes | `Supported` or `Unsupported`. |
| `end_date` | Yes | ISO date or missing value marker. |
| `bucket` | Yes | `Expired`, `0-3 months`, `0-12 months`, `more than 12 months`, or missing value marker. |

## Console summary

The console summary prints every subscription band and every contract bucket.
Counts with no rows print as zero.

Required subscription bands:

- `expired`
- `0-30 days`
- `31-90 days`
- `more than 90 days`

Required contract buckets:

- `Expired`
- `0-3 months`
- `0-12 months`
- `more than 12 months`

## Error behavior

- If subscription data is empty, the report still creates
  `SubscriptionExpiry.csv` and prints zero subscription counts.
- If contract data is empty, the report still creates `ContractExpiry.csv` and
  prints zero contract counts.
- If the JSI endpoint returns `400` because no Juniper account is linked, the
  operation reports the condition clearly and continues with an empty contract
  report when repository error-handling standards allow that behavior.
- If an SDK call fails for another reason, the operation surfaces the error and
  does not create a success-shaped result.
