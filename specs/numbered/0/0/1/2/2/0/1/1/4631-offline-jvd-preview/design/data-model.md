# Data Model: Offline Dynamic JVD Labs Preview

The feature stores no data. Each entity below exists in memory during one request. The feature writes no file and no table.

## Entities

| Entity | Fields | Natural key | Rules |
| - | - | - | - |
| RunNameSubmission | `run_name` (string, required), `csrf_token` (string, required) | None. One submission per request. | Exactly one `run_name` value. The value matches the run-name pattern. No other field appears (D-9, D-10). |
| ServerExample | `name` (string), `default_run_name` (string), `logical_devices` (list of device ids), `links` (list of endpoint pairs) | `name` | One constant in `planner.py`. The client cannot select it (D-11). All values are synthetic. |
| LogicalDevice | `id` (string), `label` (string) | `id` inside one plan | `id` matches `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`. `label` holds 1 to 80 printable ASCII characters. Duplicate ids reject the plan. |
| Link | `a_end` (device id), `z_end` (device id) | Ordered pair (`a_end`, `z_end`) inside one plan | Both ends name an existing logical device. A duplicate pair rejects the plan. Direction is kept. |
| PlanResult | `logical_devices` (list), `links` (list), `fingerprint` (string) | `fingerprint` | Input holds exactly the keys `logical_devices` and `links`. Output adds `fingerprint` (D-12, D-13). |
| PlannerOutcome | `state` (`available`, `absent`, or `failed`), `reason` (code or empty), `plan` (PlanResult or empty) | None | `absent` means the planner module is missing (D-15). `failed` means another import or call error (D-15). |
| CapabilityResponse | `feature`, `mode`, `planner`, `provider_access`, `deployment`, `execution_authority` | None | `provider_access`, `deployment`, and `execution_authority` always hold `disabled` (FR-003). |

## Fingerprint

The fingerprint is `sha256:` followed by the SHA-256 hex digest of this canonical JSON:

- Keys: `logical_devices` and `links` only.
- `logical_devices`: sorted by `id`. Each device holds `id` and `label` only.
- `links`: sorted by `a_end`, then by `z_end`. Each link holds `a_end` and `z_end` only.
- Encoding: ASCII, sorted object keys, and the separators `,` and `:` with no spaces.

The same content in another input order gives the same fingerprint (TU-08).

## Reason Codes

| Code | Meaning | Page result |
| - | - | - |
| `planner_absent` | The planner module is missing. | Unavailable state, HTTP 200 |
| `planner_failed` | The planner module fails to import or raises during the plan call. | Unavailable state, HTTP 200 |
| `unexpected_key` | The plan result holds a key other than `logical_devices` and `links`. | Unavailable state, HTTP 200 |
| `authority_claim` | The plan result names a key from the authority list in `plan-result.md`. | Unavailable state, HTTP 200 |
| `contract_violation` | A device id is duplicated, a link names an unknown device, or a value has the wrong type. | Unavailable state, HTTP 200 |

## State Transitions

Page state:

- `idle` to `ready`: the operator opens `GET /labs/`.
- `ready` to `rejected`: the plan route receives an invalid request. The response is HTTP 400.
- `ready` to `planned`: the plan route receives a valid request and the planner returns a valid plan result.
- `ready` to `unavailable`: the planner is absent, fails, or returns a result with a reason code. The response is HTTP 200.

Planner state:

- `absent` to `unavailable`: the gateway reports `planner_absent`.
- `available` to `planned`: the plan call returns a valid result.
- `available` to `failed`: the import or call raises. The gateway reports `planner_failed` and logs the error.

Plan result state:

- `received` to `accepted`: the projector applies the allow-list and the rules above.
- `received` to `violated`: the projector reports one reason code. The page shows no rows.

## Validation Order

The plan route checks in this order and returns at the first failure:

1. The CSRF token (shared answer, HTTP 400).
2. The field set (HTTP 400).
3. The repeated `run_name` rule (HTTP 400).
4. The run-name pattern (HTTP 400).
5. The planner outcome.
6. The plan result rules and reason codes.
