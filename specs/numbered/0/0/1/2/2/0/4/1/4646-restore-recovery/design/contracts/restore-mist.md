# Contract: Restore Mist Gateway

## Module and imports

- Module: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/gateway.py`.
- Class: `MistRestoreGateway`. It holds one `mist_session` attribute and four methods.
- Import path: `mistapi.api.v1.orgs.networks`, `mistapi.api.v1.orgs.services`, and `mistapi.api.v1.orgs.servicepolicies`.
- Every call passes the arguments by name. The module does not forward `*args` or `**kwargs`.

## Family mapping

| Family | List | Read | Create | Update | OpenAPI paths | Remote checks |
| --- | --- | --- | --- | --- | --- | --- |
| `network` | `listOrgNetworks` | `getOrgNetwork` | `createOrgNetwork` | `updateOrgNetwork` | `/api/v1/orgs/{org_id}/networks` and `/api/v1/orgs/{org_id}/networks/{network_id}` | 75 to 78 |
| `service` | `listOrgServices` | `getOrgService` | `createOrgService` | `updateOrgService` | `/api/v1/orgs/{org_id}/services` and `/api/v1/orgs/{org_id}/services/{service_id}` | 79 to 82 |
| `service-policy` | `listOrgServicePolicies` | `getOrgServicePolicy` | `createOrgServicePolicy` | `updateOrgServicePolicy` | `/api/v1/orgs/{org_id}/servicepolicies` and `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | 83 to 86 |

The installed module defines each function at lines 17, 58, 89, 117, and 145 (remote checks 97 to 99). Task T002 confirms the argument names for the service functions against the installed module.

## Arguments

- List: `(mist_session, org_id, limit, page)`. The gateway passes `limit` as 100 and counts `page` from 1.
- Read: `(mist_session, org_id, object_id)`.
- Create: `(mist_session, org_id, body)`.
- Update: `(mist_session, org_id, object_id, body)`.

## Pagination

The gateway reads pages in order until a page returns fewer items than `limit`. A page that is not a list, or that returns a non-2xx status, ends the listing with a lookup error. The gateway never uses a partial listing.

## Body normalization

Before a write, the gateway removes these fields from the body: `id`, `org_id`, `created_time`, and `modified_time`. Task T002 may remove more fields, but only fields that the OpenAPI marks `readOnly` (remote checks 91 to 94).

## Status mapping for reads

| Status | Result |
| --- | --- |
| 2xx with a dictionary | Present |
| 404 | Absent. The decision rules treat absence as a confirmed not-found only for this result. |
| Any other status, or no status | Lookup failed |

## Status mapping for writes

| Status or event | Outcome |
| --- | --- |
| 2xx with the object body and, for create, a new natural ID | Verified after read-back |
| 2xx without a new natural ID on create | Indeterminate |
| 400, 401, 403, 404, 409, or 422 | Failed. The write did not apply. |
| 429 after the SDK internal retries | Indeterminate (decision D-17) |
| 5xx | Indeterminate |
| No status, which the SDK returns for a connection or proxy failure | Indeterminate |
| Worker wait longer than 60 seconds | Indeterminate (decision D-16) |

The SDK repeats a write after HTTP 429 up to three times. The waits are 5, 10, and 20 seconds, unless the response has a `Retry-After` header. The gateway treats the sequence as one attempt. Remote checks 100 and 101 record the retry behavior.

## Read-back

After each successful write, the executor reads the object by its natural ID and compares the normalized digest with `target_digest`. A mismatch is a partial outcome. The mismatch means that the write applied but the object differs from the target.

## Logging

- Before each call, the gateway writes one info line. The line names the method, the family, and the natural ID.
- After each call, the gateway writes one debug line. The line names the status and the item count when the call lists objects.
- The gateway never logs a body, a token, or a session value.

## Unverified payload rules

These rules stay unverified until issue 4634 records payload evidence:

- Whether an update replaces or merges the body (unverified item U-2).
- Whether a create returns a new natural ID for the normalized body (unverified item U-3).
- Whether an HTTP 429 response means the request was not processed (unverified item U-4).
- The meaning of the `services` and `tenants` strings (unverified item U-1).
- The maximum page size (unverified item U-8).
