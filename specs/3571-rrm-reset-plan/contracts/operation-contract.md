# Operation Contract: menu 291

## Handler

```text
src.site.rrm_reset.operation.RrmResetOperation.run()
```

The handler takes no positional argument. It reads the active Mist API session from `SourceDependencyResolver.apisession`.

## Inputs

| Input | Source | Rule |
| - | - | - |
| Site | Shared site prompt | Required. |
| Action | Operator prompt | `OPTIMIZE` or `RESET`. |
| Confirmation | Operator prompt | Must equal the selected action. |
| Dry-run | Runtime argument or environment flag | True sends no Mist change request. |
| Settle time | `RRM_SETTLE_SECONDS` | Positive integer or default `300`. |

## Outputs

| File | Content |
| - | - |
| `RrmPlanBefore.csv` | Current plan before the destructive request. |
| `RrmPlanAfter.csv` | Current plan after the settle time. |
| `RrmPlanDiff.csv` | Radios whose channel, width, or power changed. |

## Mist API Contract

| Action | API |
| - | - |
| Read plan | `GET /api/v1/sites/{site_id}/rrm/current` |
| Optimize | `POST /api/v1/sites/{site_id}/rrm/optimize` |
| Reset | `POST /api/v1/sites/{site_id}/devices/reset_radio_config` |

## Safety Contract

- The before file must exist before any Mist change request starts.
- Dry-run mode must not send `optimizeSiteRrm` or reset requests.
- A wrong confirmation must not send a Mist change request.
- The pull request must state that the operation is destructive and needs human review.
