# Endpoint Contract: getMspSamlMetadata

**Feature**: `586-mist-get-msp-saml-metadata`
**Date**: 2026-06-29
**Source**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.md`

## HTTP Contract

| Item                  | Value                                                                  |
|-----------------------|------------------------------------------------------------------------|
| **Method**            | `GET`                                                                  |
| **URL template**      | `https://{MIST_HOST}/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata`      |
| **operationId**       | `getMspSamlMetadata`                                                   |
| **Tag**               | `MSPs SSO`                                                             |
| **Pagination**        | None (single object response)                                          |
| **Idempotent**        | Yes (HTTP GET, no side effects)                                        |
| **Rate limiting**     | Standard Mist 5000 calls/hour per token                                |

### Path Parameters

| Name      | Type   | Required | Validation                              | Source                                  |
|-----------|--------|----------|-----------------------------------------|------------------------------------------|
| `msp_id`  | string | Yes      | UUID v4 shape (`xxxxxxxx-xxxx-...`)     | `safe_input(context="msp_saml_metadata:msp_id")` |
| `sso_id`  | string | Yes      | UUID v4 shape                           | `safe_input(context="msp_saml_metadata:sso_id")` |

### Query Parameters

None.

### Request Headers

| Header           | Value                              | Source                                          |
|------------------|------------------------------------|--------------------------------------------------|
| `Authorization`  | `Token {api_token}`                | `mistapi.APISession` (loaded from `.env`)       |
| `Accept`         | `application/json`                 | Default by SDK                                  |
| `User-Agent`     | `mistapi-python/{version}`         | SDK default                                     |

### Request Body

None (GET).

## Response Contract -- 200 OK

Returns a single JSON object (not an array). All properties are read-only and optional;
presence depends on the underlying SSO configuration's `idp_type`.

### Schema (from OpenAPI)

```json
{
  "type": "object",
  "properties": {
    "acs_url": {
      "type": "string",
      "description": "If idp_type==saml",
      "readOnly": true,
      "examples": ["https://api.mist.com/api/v1/saml/llDfa13f/login"]
    },
    "entity_id": {
      "type": "string",
      "description": "If idp_type==saml",
      "readOnly": true,
      "examples": ["https://api.mist.com/api/v1/saml/llDfa13f/login"]
    },
    "logout_url": {
      "type": "string",
      "description": "If idp_type==saml",
      "readOnly": true,
      "examples": ["https://api.mist.com/api/v1/saml/llDfa13f/logout"]
    },
    "metadata": {
      "type": "string",
      "description": "Raw XML SAML metadata document. If idp_type==saml",
      "readOnly": true,
      "examples": [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><md:EntityDescriptor xmlns:md=\"urn:oasis:names:tc:SAML:2.0:metadata\" entityID=\"https://api.mist.com/api/v1/saml/llDfa13f/login\" ...>...</md:EntityDescriptor>"
      ]
    },
    "scim_base_url": {
      "type": "string",
      "description": "If idp_type==oauth and scim_enabled==true",
      "examples": [
        "https://scim.nac-staging.mistsys.com/S_41b2525a-e8b8-4809-8168-f1d8dcbe9735/azure/4d72b1dc-7503-4717-81ea-80d0125b886e"
      ]
    }
  }
}
```

### Field-by-field handling

| Field           | Type   | When present                            | MistHelper handling                                                    |
|-----------------|--------|------------------------------------------|------------------------------------------------------------------------|
| `acs_url`       | string | `idp_type == saml`                       | Stored verbatim in `acs_url` column; `None` otherwise.                  |
| `entity_id`     | string | `idp_type == saml`                       | Stored verbatim; `None` otherwise.                                      |
| `logout_url`    | string | `idp_type == saml`                       | Stored verbatim; `None` otherwise.                                      |
| `metadata`      | string | `idp_type == saml`                       | Stored verbatim as raw XML -- never parsed, never re-encoded. Logged only at DEBUG and only by byte length. |
| `scim_base_url` | string | `idp_type == oauth` AND `scim_enabled`   | Stored verbatim; `None` otherwise.                                      |

## Error Responses

| Status | Mist description                                                       | MistHelper handling                                                       |
|--------|------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 400    | Bad Syntax                                                             | `logging.warning("Bad request for msp %s sso %s", ...)`; return early.    |
| 401    | Unauthorized                                                           | `logging.error("Auth failed -- check MIST_API_TOKEN")`; return early. Do not log the token. |
| 403    | Permission Denied                                                      | `logging.warning("Permission denied for msp %s sso %s", ...)`; return early. |
| 404    | Not found -- endpoint or resource does not exist                       | `logging.warning("MSP SSO %s/%s not found -- no data returned", ...)`; return early without writing. |
| 429    | Too Many Requests (5000/hour token threshold)                          | Adaptive delay system in `delay_metrics.json` + `tuning_data.json` handles back-off automatically. No manual intervention required; `--fast` mode caps retries. |

All non-2xx responses are caught by `mistapi.APISession`'s built-in exception handling
plus a `try/except` in the menu method that emits `logging.exception(...)` for unknown
errors and returns 0 from the menu (no traceback, no crash). The menu item exits cleanly
in every documented error case.

## mistapi Python Call Signature

```python
import mistapi
import mistapi.api.v1.msps.ssos.metadata as msp_saml_metadata_api

apisession = mistapi.APISession()                                # Loads .env automatically
apisession.login()                                               # No-op when token is set
response = msp_saml_metadata_api.getMspSamlMetadata(             # SDK function
    apisession,                                                  # Session is always first positional arg
    msp_id,                                                      # Path param 1
    sso_id,                                                      # Path param 2
)
payload = response.data                                          # dict, or None on empty body
```

### SDK module path note

The enriched documentation file lists the SDK path as
`mistapi.api.v1.msps.sso.getMspSamlMetadata()`, while the OpenAPI URL path
(`/api/v1/msps/{msp_id}/ssos/{sso_id}/metadata`) and the project spec.md both indicate
`mistapi.api.v1.msps.ssos.metadata` as the conventional module. The implementer must
resolve this at task generation time by inspecting the installed `mistapi` 0.59+
package -- e.g.:

```powershell
python -c "import mistapi.api.v1.msps.ssos.metadata as m; print(dir(m))"
python -c "import mistapi.api.v1.msps.sso as m; print(dir(m))"
```

Whichever module exposes `getMspSamlMetadata` is the correct import path. Both possible
imports appear in this contract so the implementer has the full menu of choices; only
one survives into MistHelper.py.

## Example Response (200, idp_type=saml)

```json
{
  "acs_url": "https://api.mist.com/api/v1/saml/llDfa13f/login",
  "entity_id": "https://api.mist.com/api/v1/saml/llDfa13f/login",
  "logout_url": "https://api.mist.com/api/v1/saml/llDfa13f/logout",
  "metadata": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><md:EntityDescriptor ...>...</md:EntityDescriptor>"
}
```

## Example Response (200, idp_type=oauth+scim)

```json
{
  "scim_base_url": "https://scim.nac-staging.mistsys.com/S_41b2525a-e8b8-4809-8168-f1d8dcbe9735/azure/4d72b1dc-7503-4717-81ea-80d0125b886e"
}
```

Both shapes flatten cleanly into the single `msp_saml_metadata` row defined in
`data-model.md`; the absent fields are stored as `NULL` in SQLite or empty cells in CSV.
