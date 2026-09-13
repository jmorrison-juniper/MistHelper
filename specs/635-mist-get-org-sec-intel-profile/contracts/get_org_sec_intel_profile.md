# Contract: getOrgSecIntelProfile

Authoritative endpoint contract for Phase 1. Source:
`documentation/api/orgs/GET_orgs_org_id_secintelprofiles_secintelprofile_id.md`
plus the Mist OpenAPI spec under `documentation/mist-api-openapi3*`.

## HTTP Contract

- **Method**: `GET`
- **URL template**: `https://{MIST_HOST}/api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}`
- **Tag**: `Orgs SecIntel Profiles`
- **operationId**: `getOrgSecIntelProfile`
- **Paginated**: No
- **Idempotent**: Yes (read-only)

### Path Parameters (both required)

| Name                 | Type   | Required | Description                                                    |
|----------------------|--------|----------|----------------------------------------------------------------|
| `org_id`             | string (UUID) | Yes | Owning organization UUID.                                    |
| `secintelprofile_id` | string (UUID) | Yes | UUID of the target Security Intelligence profile.            |

### Query Parameters

None.

### Request Headers

| Header          | Value                          | Notes                                                       |
|-----------------|--------------------------------|-------------------------------------------------------------|
| `Authorization` | `Token {MIST_API_TOKEN}`       | Managed by `mistapi.APISession`; never logged by MistHelper.|
| `Accept`        | `application/json`             | Set by SDK.                                                 |
| `User-Agent`    | `mistapi/<version>` + MistHelper suffix | Set by SDK; harmless in logs.                      |

### Request Body

None. (GET request.)

## Response

### 200 OK -- Success (JSON object)

Full schema per the enriched endpoint doc:

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "examples": ["secintel-custom"]
    },
    "profiles": {
      "type": "array",
      "items": {
        "title": "secintel_profile_profile",
        "type": "object",
        "properties": {
          "action":   { "type": "string", "description": "enum: default, standard, strict" },
          "category": { "type": "string", "description": "enum: CC, IH (Infected Host), DNS" }
        }
      },
      "description": ""
    }
  }
}
```

Notes:
- Neither `name` nor `profiles` is declared `required` in the source schema;
  MistHelper defends with `payload.get("name")` and `payload.get("profiles") or []`.
- `id` is not returned in the body; MistHelper uses the path parameter
  `secintelprofile_id` as the natural PK column when persisting.
- `org_id` is likewise supplied by the caller and denormalized onto every
  row for downstream filtering.

### Error Responses

| Status | Description                                                            | MistHelper handling                                                                                          |
|--------|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                             | `logging.warning("Menu 89: 400 Bad Request for org=%s profile=%s", ...)`; return without writing rows.       |
| 401    | Unauthorized (missing / invalid token)                                 | Surface via `mistapi` exception; `logging.error(...)`; exit menu handler cleanly. Token is never echoed.     |
| 403    | Permission Denied                                                      | `logging.warning("Menu 89: 403 Forbidden -- token lacks org read scope"); return.                            |
| 404    | Not found (org or profile UUID unknown)                                | `logging.warning("Menu 89: 404 Not Found for profile %s"); return without writing rows.                      |
| 429    | Too Many Requests (5000 calls/hr threshold)                            | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) increases back-off; SDK retries per policy.|

Any unexpected exception is caught at the menu-dispatch layer and logged
with `logging.exception(...)` so the traceback lands in
`data/script.log` without crashing the interactive session.

## mistapi Python Call Signature

Per the enriched endpoint doc:

```python
import mistapi
import mistapi.api.v1.orgs.secintel_profiles as secintel_profiles_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],           # From .env
    apitoken=os.environ["MIST_API_TOKEN"],  # From .env; never logged
)

# The SDK call (only permitted Mist interface per Constitution)
response = secintel_profiles_module.getOrgSecIntelProfile(
    apisession,                             # Auth + rate-limit session
    org_id,                                 # Path parameter 1 (UUID string)
    secintelprofile_id,                     # Path parameter 2 (UUID string)
)

# Usage
payload = response.data or {}               # Defensive default on empty body
name = payload.get("name")                  # Optional string
rules = payload.get("profiles") or []       # Optional list of {category, action}
```

`response.data` is a Python dict for this endpoint (single object, no
pagination). `response.status_code` carries the HTTP status; the SDK raises
on transport errors and adheres to the shared retry/backoff policy driven
by `delay_metrics.json`.
