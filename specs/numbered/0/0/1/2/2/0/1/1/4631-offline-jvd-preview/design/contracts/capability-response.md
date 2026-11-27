# Contract: Capability Response

## Route

- Method: `GET`
- Path: `/labs/capability`
- Endpoint: `labs.capability`
- Response: JSON, HTTP 200.
- CSRF: not required for `GET`.

## Body

| Field | Type | Values |
| - | - | - |
| `feature` | string | `labs-preview` |
| `mode` | string | `offline` |
| `planner` | string | `available`, `absent`, or `failed` |
| `provider_access` | string | `disabled` |
| `deployment` | string | `disabled` |
| `execution_authority` | string | `disabled` |

Example body for an absent planner:

```json
{
  "feature": "labs-preview",
  "mode": "offline",
  "planner": "absent",
  "provider_access": "disabled",
  "deployment": "disabled",
  "execution_authority": "disabled"
}
```

## Rules

- The three authority fields always hold `disabled` (FR-003).
- The `planner` field reports the outcome of the import check only. It does not run a plan.
- Query parameters are ignored.
- The route reads no request body.

## Evidence

- `test_capability_response_reports_disabled_authority` (TR-01).
- `test_capability_response_reports_absent_planner` (TR-02).
