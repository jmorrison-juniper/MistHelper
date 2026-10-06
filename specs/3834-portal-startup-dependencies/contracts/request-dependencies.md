# Contract: Request Dependencies and Failure Responses

## Factory boundary

`create_app()` remains callable with no arguments.
It installs production dependency construction before registering routes.
It must not require `MIST_CLIENT` or `DB_ROUTER` injection.
It must not resolve an operator outside a request or construct services with missing required collaborators.

`create_app(overrides=complete_overrides)` preserves the existing complete E2E boundary.
Validate overrides first. Install each exact object, then return from production wiring before any external setup.
Keep the existing E2E response owner header.
Do not add required fields to `E2EFactoryOverrides`.

## Provider boundary

The provider resolves the authenticated operator through `identity.current_session()`.
It constructs one graph per request and reuses that graph only within that request.
It never updates shared service instances with a request session.
It never forwards credentials, session contents, or driver exception messages to the browser.

Use `DatabaseConfig.from_env()` and `DatabaseRouter(config, strategies)`.
Verify configured addresses agree with portal settings.
Treat standalone mode and unavailable ArangoDB as storage unavailable.
Redis lock failures remain separate and retain their existing refusal.

The router write contract is `write(data, api_function_name) -> WriteResult`.
The router does not provide document-query or run/comparison methods.
Use explicit document-store operations at existing service and route owners.
Bind AQL parameters. Never place `run_id` directly inside query text.

The audit dependency provides the existing `AuditLogger.log_operation` contract.
Align its arguments and persistence call sites. A stdlib logger is not an audit service.
Verify real SDK and driver signatures with strict doubles or signature-bound tests.
An unrestricted `MagicMock` does not prove compatibility.

## Current route consumers

| Consumer | Resolution requirement | Existing success shape |
| - | - | - |
| `POST /api/runs/<run_id>/capture/start` | Current operator, storage, capture service | 202 with `capture_id`, `status`, `devices_count`, and `run_id`. |
| `POST /api/runs/<run_id>/upgrade/start` | Current operator, storage, upgrade service, existing mutation guards | 202 with current upgrade identifier and options. |
| Existing upgrade status owner | Valid request scope and storage | Existing progress response. Add no second public status rule. |
| `POST /api/runs/<run_id>/upgrade/cancel` | Current operator, storage, upgrade service, existing cancellation guards | Current cancellation response only after verified success. |
| `GET /api/runs/<run_id>/comparison/results` | Authenticated scope, storage, comparison availability | 200 with current stored comparison fields. This read does not start comparison work. |
| `POST /api/runs/<run_id>/comparison/approve` | Authenticated scope, storage, existing approval controls | Current approval envelope only after both required writes succeed. |

Settle and comparison computation keep their current service interfaces.
Test them through the provider inside authenticated request contexts. Add no new endpoint.
Preserve explicit service injections used by current route tests.
A supplied service wins without constructing an unused production replacement.
The complete E2E branch is stronger than an individual injected service and must bypass all production resolution.

## Failure contract

| Condition | Response or result | Forbidden work |
| - | - | - |
| Missing owner, stale registry, or mismatched browser | Existing JSON 401 `not_authenticated`, or existing browser sign-in redirect | No storage or Mist call. |
| Owner record has no usable cloud session | Same authentication refusal for Mist-dependent work | No Mist call or mutation. |
| Missing, invalid, standalone, or unavailable required storage | HTTP 503 with the established portal error envelope and `service_unavailable` code | No service write or Mist operation. |
| Storage fails after valid construction | Visible operation failure using the current operation code | No later cloud mutation or completion response. |
| Required settle evidence is unavailable or fails | Failed settle/comparison result | No assumed successful settle or comparison. |
| Comparison persistence or approval update fails | Visible comparison/approval failure | No success identifier or completed run response. |
| Cancellation fails | Current cancellation failure shape | No claim that devices were cancelled or rolled back. |

Malformed input keeps current 400 behavior. Missing records keep current 404 behavior.
Organization refusals, lock conflicts, CSRF refusals, and write gates retain their current status and codes.
Validate those guards through registered routes. Do not bypass decorators in acceptance tests.
Use safe fixed error text and structured error types. Do not include `str(driver_error)` or dependency representations.

## Isolation and lifecycle proof

Two concurrent requests must resolve distinct fake sessions from two real registry records.
Use separate Flask clients and a barrier that overlaps service work.
Each SDK call must receive only its request's session.
Each request must own its router and graph.
Closing one request must not close the other router or either registry-owned session.

Test failures during resolution and operation, then send another authenticated request.
The new request must not inherit a previous service instance, session, database handle, or failed dependency state.
Test incomplete and complete E2E overrides with production constructor and connector traps.
All external traps must record zero production calls.
