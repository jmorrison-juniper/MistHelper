# Contract: getOrgGuestAuthorization

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_guests_guest_mac.md`
**Date**: 2026-06-30

## HTTP Contract

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/guests/{guest_mac}` |
| Auth header | `Authorization: Token {MIST_API_TOKEN}` (injected by `mistapi.APISession`) |
| Content-Type (request) | n/a (no body on GET) |
| Accept (request) | `application/json` |
| Idempotent | Yes (pure read) |
| Paginated | No (`Pagination: Not paginated` per source doc, line 163) |

### Required Path Parameters

| Name | Type | Format | Notes |
|------|------|--------|-------|
| `org_id` | string | UUID v4 | Validated by MistHelper before SDK call. |
| `guest_mac` | string | 12 hex chars (lower-case after normalization) | MistHelper strips separators and lowercases the user-supplied value before passing to the SDK. |

### Query Parameters

_None._

### Request Body

_None._ (HTTP GET.)

### Request Headers Set by `mistapi.APISession`

- `Authorization: Token <MIST_API_TOKEN>` (token loaded from `.env`)
- `User-Agent: mistapi-python/<version>`
- Standard `requests` library `Accept-Encoding` and `Connection` headers

## Response Contract

### 200 OK -- Success

**Content-Type**: `application/json`
**Body**: single JSON object (not a list, not paginated).

| Field | Type | readOnly | Notes |
|-------|------|----------|-------|
| `access_code_email` | string | yes | Email the access code was sent to (only when `auth_method`==`email`). PII. |
| `ap_mac` | string | yes | MAC of AP the guest registered through. |
| `auth_method` | string | yes | Authorization type: `email`, `sms`, `sponsor`, `passphrase`, etc. |
| `authorized` | boolean | no | Whether the guest is currently authorized. Default `true`. |
| `authorized_expiring_time` | number | yes | Epoch seconds when the authorization expires. Example: `1480704955`. |
| `authorized_time` | number | yes | Epoch seconds when the guest was authorized. Example: `1480704355`. |
| `company` | string | no | User-supplied company. PII. Example: `"abc"`. |
| `email` | string | no | User-supplied email. PII. Example: `"john@abc.com"`. |
| `field1` | string | no | Optional user-supplied free-text field. PII. |
| `field2` | string | no | Optional user-supplied free-text field. PII. |
| `field3` | string | no | Optional user-supplied free-text field. PII. |
| `field4` | string | no | Optional user-supplied free-text field. PII. |
| `mac` | string | yes | MAC of the guest client. |
| `minutes` | integer (int32) | no | Authorization duration in minutes. Min 0, max 259200 (180 days), default 1440 (1 day). |
| `name` | string | yes | User-supplied name. PII. Example: `"John Smith"`. |
| `random_mac` | boolean | yes | Whether the client is using a randomized MAC. |
| `ssid` | string | yes | SSID name used during registration. Example: `"Guest-SSID"`. |
| `wlan_id` | string (uuid) | yes | UUID of the WLAN. Example: `"6748cfa6-4e12-11e6-9188-0242ac110007"`. |

Example response body (synthesized from doc field examples):

```json
{
  "mac": "5684dae9ac8b",
  "authorized": true,
  "authorized_time": 1480704355,
  "authorized_expiring_time": 1480704955,
  "minutes": 1440,
  "auth_method": "email",
  "access_code_email": "john@abc.com",
  "ap_mac": "5c5b350e0001",
  "ssid": "Guest-SSID",
  "wlan_id": "6748cfa6-4e12-11e6-9188-0242ac110007",
  "random_mac": false,
  "name": "John Smith",
  "email": "john@abc.com",
  "company": "abc",
  "field1": null,
  "field2": null,
  "field3": null,
  "field4": null
}
```

### Error Responses and MistHelper Handling

| Status | Meaning (source doc) | MistHelper Handling |
|--------|----------------------|---------------------|
| `400` | Bad Syntax | Pre-call UUID + MAC validation makes this near-impossible. If it still occurs, `logging.warning("Bad request payload: %s", response.status_code)` and return without writing. No traceback shown to the user. |
| `401` | Unauthorized | `mistapi.APISession` surfaces this as an exception during the call. The method catches it via the global try/except in the menu dispatcher, logs `ERROR Unauthorized -- check MIST_API_TOKEN`, and the menu returns to the main prompt. Token value is never logged. |
| `403` | Permission Denied | Same handling as 401, with message `ERROR Permission denied -- token lacks read access to org %s`. |
| `404` | Not Found (endpoint or resource does not exist) | `logging.warning("No guest authorization found for org %s mac %s", org_id_short, mac)` and return without writing. No traceback. The CSV/SQLite output is unchanged on this branch. |
| `429` | Too Many Requests (5000-per-hour token cap exceeded) | The mistapi SDK's standard retry logic (governed by `delay_metrics.json` + `tuning_data.json`) handles back-off automatically. The method does nothing special. If retries are exhausted, the exception bubbles to the dispatcher and is logged at `ERROR`. |

## Exact `mistapi` Python Call Signature

```python
# Import path -- exactly as documented in
# documentation/api/orgs/GET_orgs_org_id_guests_guest_mac.md line 171
from mistapi.api.v1.orgs.guests import guests as mist_guests

# session is a mistapi.APISession constructed once at MistHelper startup
# from MIST_HOST and MIST_API_TOKEN
response = mist_guests.getOrgGuestAuthorization(
    session,                # mistapi.APISession
    org_id,                 # str -- UUID, validated before this call
    guest_mac,              # str -- 12 lower-case hex chars, normalized before this call
)

# response is a mistapi.models.response.Response-style object
record = response.data or {}   # dict matching the 200 OK schema; {} when API returns nothing
status_code = response.status_code   # int -- 200 on success
```

No keyword arguments are accepted beyond the three positional ones above (the
endpoint defines no query parameters per the source doc).

## Rate Limiting

Standard Mist API token cap: 5000 API calls per hour per token. This single GET
counts as one call regardless of response size. MistHelper's adaptive delay system
(`delay_metrics.json`, `tuning_data.json`) handles back-off transparently; no
endpoint-specific tuning is required.

## Related Endpoints (for cross-reference)

- `GET /api/v1/orgs/{org_id}/guests/search` -- list/search guests
  (`searchOrgGuestAuthorization`).
- `DELETE /api/v1/orgs/{org_id}/guests/{guest_mac}` -- delete guest
  (`deleteOrgGuestAuthorization`).
- `PUT /api/v1/orgs/{org_id}/guests/{guest_mac}` -- update guest
  (`updateOrgGuestAuthorization`).

This spec covers only the **GET**. Write operations are explicitly out of scope per
`spec.md` "Out of Scope".
