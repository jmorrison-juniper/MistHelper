# Contract: Mist Gateway Template Request

**Scope**: The first cloud write that the converter can make. The write creates an organization gateway template. The other Mist families belong to child records. Child 4634 reports 22 write rows, including `deleteOrgServicePolicy`, and 18 read rows (U-10).

## Operation

| Item | Value | Evidence |
|---|---|---|
| HTTP method and path | `POST /api/v1/orgs/{org_id}/gatewaytemplates` | R-73 (OpenAPI line 9727) |
| OpenAPI operation | `createOrgGatewayTemplate` | R-29 (line 9764) |
| SDK module | `mistapi.api.v1.orgs.gatewaytemplates` | R-80 (module defines the functions) |
| SDK signature | `createOrgGatewayTemplate(mist_session, org_id, body)`. The body type is a dict or a list. | R-28 (line 58) |
| Request schema | `gateway_template` | R-77 (line 9887) |
| Installed package | mistapi 0.64.1 | R-78 |
| Same-family functions | `listOrgGatewayTemplates`, `getOrgGatewayTemplate`, `updateOrgGatewayTemplate`, `deleteOrgGatewayTemplate` | R-80 (listed at line 17 of the module) and the module definitions |

## Request Fields

| Field | Rule | Evidence |
|---|---|---|
| `name` | Required. The converter limits the name to 1 to 120 visible characters. | R-30 (line 80782), R-37 |
| `type` | `standalone` or `spoke`. No other value is accepted. | R-75 (line 80789) |
| `dns_servers` | Optional array of strings. Each value is an IPv4 address from a supported Cisco `ip name-server` line. | R-31 (line 78038), R-76 (line 80678), R-40 |

Hub is not a template type. The converter refuses any other type before the SDK call (R-75).

## Verification Before the Call

1. The converter validates the body against the local allowlist above before the SDK call.
2. The converter checks the write family and the approval record (D-3, D-5).
3. The converter checks that the review digest matches the current proposal (R-39).
4. The converter starts the write only after each check passes.

The SDK does not validate the body schema. Its signature accepts `dict | list` (R-28). The local allowlist is the only schema check in this flow.

## Responses

| Status | Meaning | Outcome for an apply run |
|---|---|---|
| 200 | The template exists in Mist | Success |
| 400, 401, 403, 404 | Documented client errors (OpenAPI operation block, R-77) | Failed. The run stops. |
| 429 | The SDK retried three times and the final response is still 429 (R-79) | Indeterminate. No retry runs. |
| 5xx, timeout, or a missing create identifier | No safe conclusion | Indeterminate. No retry runs. |

## Retry and Timeout Rules

- mistapi retries HTTP 429 up to three times (R-79, `_MAX_429_RETRIES` at line 59). The converter adds no retry for a write (D-6).
- The converter bounds each write at 90 seconds and each run at 10 minutes (child 4644).
- After an indeterminate result, the run stops. The operator reviews the object in Mist before a new run.

## Redaction

- The converter stores no request body in a log. It logs the object name, the status, and the operation identifier only (FR-028, R-58).
- This rule holds even when a library logs a request body at DEBUG level. The library behavior is unverified (U-03).
- The converter never sends a credential inside the body. The credential comes from the existing settings (R-55).

## Gating

- The write runs only when the gateway template family is enabled. Gates G2, G4, and G5 must pass for the current run (plan gate table).
- Enabling the family needs the decision in D-15. The record does not enable it.

Warning: a successful create call adds a gateway template to a production organization. A code revert does not remove it. The operator must remove the template in Mist through a reviewed change.
