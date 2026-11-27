# SDK and schema contract

This contract covers each mistapi call the future migration may use. It states the request fields, the response classes, and the evidence limits. It does not approve live use. Evidence IDs resolve in [research](../research.md). Decision IDs refer to the [decision register](../research.md#7-decision-register).

## Pinned evidence

- Source pin: `mistapi==0.64.0` (S08 L2).
- Target pin: `mistapi==0.64.1` (T10 L129). The installed package reports 0.64.1 (R71).
- Checked-in schema: `documentation/mist-api-openapi31json.json`, version `2609.1.0` (T11). The YAML twin holds the same paths (T12).
- Future calls must use a mistapi method. Direct HTTP to a Mist REST endpoint is not permitted (constitution T18 L274 to L279).

## Method contracts

| Contract | Installed signature and URI | Use in migration | Test |
| --- | --- | --- | --- |
| CT-01 List site guests | `listSiteAllGuestAuthorizations(mist_session, site_id, wlan_id=None)`. GET `/api/v1/sites/{site_id}/guests` (def L17, call L43 to L47). | Read the exact site and WLAN scope. Pass the WLAN ID by name. | TEST-003, TEST-005 |
| CT-02 Count site guests | `countSiteGuestAuthorizations`. GET `/api/v1/sites/{site_id}/guests/count` (def L51, call L91 to L103). | Not used. Any future use needs a contract test. | TEST-005 |
| CT-03 Derived site guests | `listSiteAllGuestAuthorizationsDerived(mist_session, site_id, wlan_id=None, cross_site=None)`. GET `/api/v1/sites/{site_id}/guests/derived` (def L107, call L138 to L144). | Not used. Do not set `cross_site`. A cross-site view needs a separate decision. | TEST-003 |
| CT-04 Search site guests | `searchSiteGuestAuthorization`. GET `/api/v1/sites/{site_id}/guests/search` (def L148, call L200 to L220). | Not used by the source. Any future use needs a contract test. | TEST-005 |
| CT-05 Read one site guest | `getSiteGuestAuthorization(mist_session, site_id, guest_mac)`. GET `/api/v1/sites/{site_id}/guests/{guest_mac}` (def L224, call L246 to L248). | Reconcile after each write. | TEST-022 |
| CT-06 Update one site guest | `updateSiteGuestAuthorization(mist_session, site_id, guest_mac, body)`. PUT `/api/v1/sites/{site_id}/guests/{guest_mac}` (def L280, call L307 to L308). | Grant, edit, and extension use this method after D-7, D-8, D-9, and D-14. | TEST-009, TEST-012, TEST-013, TEST-022 |
| CT-07 Delete one site guest | `deleteSiteGuestAuthorization(mist_session, site_id, guest_mac)`. DELETE `/api/v1/sites/{site_id}/guests/{guest_mac}` (def L252, call L274 to L276). | Not enabled. Revoke waits for D-8 evidence. | TEST-014 |
| CT-08 Organization guest functions | Six functions at organization defs L17, L42, L98, L169, L197, and L225. | Not used. An organization fallback for a site request is forbidden (P058). | TEST-022 |

Note: CT-08 covers the organization functions only as a boundary. The target uses none of them.

## Request body rules

- The MAC is a path parameter. It is never a body field.
- Permitted writable body fields are `authorized`, `minutes`, `company`, `email`, `field1`, `field2`, `field3`, and `field4`. The schema marks each one writable (T11).
- `authorized` defaults to true in the schema. A grant sends `authorized` true explicitly.
- `minutes` is an integer from 0 to 259200. The default for a new grant is 1440 (D-7).
- A value of 0 in `minutes` is schema-valid. It is not proof of revocation (D-8).
- Read-only fields are never sent: `name`, `mac` in the body, `wlan_id`, `ssid`, `auth_method`, `random_mac`, `access_code_email`, `ap_mac`, `authorized_time`, and `authorized_expiring_time` (D-9).
- The field `notify` is never sent (D-10).
- The field `field4` is never filled from the API token name. The migration uses the approved actor reference instead (P025, D-6).

## Response classes

| Class | Rule | Result shown to the operator |
| --- | --- | --- |
| Verified success | A 2xx response, followed by an exact-scope read that matches the requested state. | Success with the observed record. |
| Unknown | A 2xx response without a matching read, a timeout after dispatch, or a 5xx response after dispatch. | Unknown. No automatic repeat. |
| Rejected | A 4xx response. The response body is not echoed. | Rejected with a reason category. |
| Rate limited | A 429 response. | Rate limited. Reads may retry with bounded backoff. Writes do not retry automatically. |
| Unavailable | Missing credentials, no permitted scope, or a failed lookup. | Unavailable with the cause. |

Warning: a write that reaches Mist and returns no response can change device access. Show unknown, and keep the record for review.

## Retry and transport

- The migration must follow AGENTS.md. Use bounded concurrency and exponential backoff for external calls.
- The installed SDK retry behavior is not verified in this run. T003 inspects it before the first write.
- The owned WebSocket transport is not required. No plan step uses one (research section 6).

## Evidence limits

- The schema describes request shape. It does not prove cloud behavior.
- This run did not call the live API. Live behavior for revoke, extension origin, name editing, and zero-minute expiry is UNVERIFIED (research U04).
- The source guide and the source code disagree about revocation (S09 L238 and S02 L649 to L652).
- Official HPE pages were not fetched in this run (research L35).
