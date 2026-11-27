# Contract: Guest authorization portal routes

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Base path**: `/guest-authorizations`. The blueprint registers in `web_portal/app.py` (`_register_blueprints`, line 182).

## 1. Access Rules

- **Identity**: Each request needs the header `X-Forwarded-User` (D-4). The portal reads the header only when the socket peer is in `PORTAL_TRUSTED_PROXIES` (`web_portal/services/config.py` line 9). A missing or untrusted identity returns status 401 with category `identity_required`.
- **CSRF**: Each POST route requires the flask-wtf token. The app applies CSRF protection globally (`web_portal/services/config.py` line 297).
- **Organization**: The organization is the value `org_id` that `create_app` receives (`web_portal/app.py` line 37).
- **Session**: The Mist session comes from `app.config["APISESSION"]` (`web_portal/app.py` line 155). A missing session returns status 503 with category `unavailable`.
- **Writes**: Each write needs its exact typed word and the review digest from `POST /api/review`. A changed digest returns status 409 with category `stale`.

## 2. Response Envelope

Each JSON response has three fields:

| Field | Type | Rule |
| --- | --- | --- |
| `status` | string | One of `ok`, `invalid`, `forbidden`, `not_found`, `stale`, `unavailable`, `succeeded`, `failed`, `rejected`, `rate_limited`, `unknown`, `audit_failed`, or `not_attempted` |
| `message` | string | ASCII text for the operator. It holds no name, email, field value, MAC address in full, or token |
| `data` | object | Optional. Holds the fields listed for each route |

## 3. Routes

| Method | Path | Request | Data in a successful response | Status codes |
| --- | --- | --- | --- | --- |
| GET | `/guest-authorizations/` | None | HTML page with the controls in Section 5 | 200. Identity missing: 401 with the disabled page |
| GET | `/guest-authorizations/api/connection` | None | `session` value `connected` or `unavailable` | 200 |
| GET | `/guest-authorizations/api/sites` | None | `sites`: list of `site_id` and `name` | 200. Session missing: 503 |
| GET | `/guest-authorizations/api/sites/<site_id>/wlans` | None | `wlans`: list of `wlan_id` and `ssid` | 200. Unknown site: 404 |
| GET | `/guest-authorizations/api/sites/<site_id>/wlans/<wlan_id>/authorizations` | None | `records`: list of `masked_mac`, `authorized`, and `expires_at` | 200. Unknown site or WLAN: 404. Unavailable Mist call: 503 |
| GET | `/guest-authorizations/api/sites/<site_id>/clients` | Query `q` and `field` (`mac`, `hostname`, or `ip`) | `clients`: at most 200 rows with `masked_mac` and the fields that Mist returns (U05) | 200. Empty query: 400 |
| POST | `/guest-authorizations/api/review` | `action`, `site_id`, `wlan_id`, optional `guest_mac`, optional `minutes`, optional `fields` | `scope`, `masked_target`, `requested_change`, `required_word`, and `digest` | 200. Invalid input: 400 |
| POST | `/guest-authorizations/api/grant` | `site_id`, `wlan_id`, `guest_mac`, `minutes`, `confirmation`, `digest` | `operation_id` and `outcome` | 200 for each Mist outcome. Digest mismatch: 409. Invalid input: 400. Audit unavailable before dispatch: 503 |
| POST | `/guest-authorizations/api/update` | `site_id`, `wlan_id`, `guest_mac`, `fields`, `confirmation`, `digest` | `operation_id` and `outcome` | Same as grant |
| POST | `/guest-authorizations/api/extend` | `site_id`, `wlan_id`, `guest_mac`, `minutes`, `confirmation`, `digest` | Disabled until gate G5. Returns status `unavailable` with a reason | 503 while G5 is open |
| POST | `/guest-authorizations/api/revoke` | `site_id`, `wlan_id`, `guest_mac`, `confirmation`, `digest` | `operation_id`, `outcome`, and `verified` (true or false) | Same as grant |
| POST | `/guest-authorizations/api/import/preview` | Multipart file field `file` | `batch_id`, `file_sha256`, `byte_count`, `row_count`, `rows_sha256`, and `rows` | 400 for invalid rows or headers. 413 above 262144 bytes |
| POST | `/guest-authorizations/api/import/run` | `batch_id`, `rows_sha256`, `confirmation` | `rows` with `row_number` and `outcome`, and `stop_reason` when a stop occurs | 200. Digest mismatch: 409 |
| GET | `/guest-authorizations/api/audit` | Query `limit` (1 to 200) | `rows` with masked audit fields | 200 |

## 4. Outcome Values

| Value | Meaning | Route effect |
| --- | --- | --- |
| `succeeded` | Mist accepted the write (HTTP 2xx) | Continue. Revoke shows `verified` after read-back |
| `failed` | Mist refused the write for permission or input (HTTP 401 or 403) | Continue to the next row |
| `rejected` | Mist returned a client error for the input (HTTP 400, 404, 409, or 422) | Continue to the next row |
| `rate_limited` | HTTP 429 remained after the SDK retries | Stop the batch |
| `unknown` | Timeout, connection error, server error, or no response | Stop the batch. No retry |
| `audit_failed` | The outcome row failed after dispatch | Stop the batch |
| `not_attempted` | The row follows a stop | Do not send a call |

## 5. Stable Identifiers

The template holds these `data-testid` values. Each value is stable across releases.

- `nav-guest-authorizations` (navigation link in `base.html`)
- `guest-disabled-state`
- `guest-scope-site`
- `guest-scope-wlan`
- `guest-review-table`
- `guest-search-input`
- `guest-search-results`
- `guest-grant-minutes`
- `guest-grant-word`
- `guest-update-word`
- `guest-extend-state`
- `guest-revoke-word`
- `guest-import-file`
- `guest-import-preview`
- `guest-import-word`
- `guest-outcome-table`
- `guest-error-banner`

## 6. Logging Rules for Routes

- Each route logs an info line before the action and a debug line after the action.
- A log line holds the route name, the status, and a masked target. It holds no body and no header value.
- A log line holds no token and no password.
