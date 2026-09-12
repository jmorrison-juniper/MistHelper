# Endpoint Contract: getOrgNacRule

**Feature**: 624-mist-get-org-nac-rule
**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Research**: [../research.md](../research.md)
**Data model**: [../data-model.md](../data-model.md)
**Enriched doc**: `documentation/api/orgs/GET_orgs_org_id_nacrules_nacrule_id.md`

This document is the sole authoritative contract for the HTTP interaction
between MistHelper and the Mist Cloud API for `getOrgNacRule`. Any drift
between this contract and the running code is a defect.

---

## HTTP contract

### Method

`GET`

### URL template

```
https://{MIST_HOST}/api/v1/orgs/{org_id}/nacrules/{nacrule_id}
```

`{MIST_HOST}` is one of: `api.mist.com`, `api.eu.mist.com`, `api.gc1.mist.com`,
`api.ac2.mist.com`, `api.gc2.mist.com`, `api.gc3.mist.com`, `api.gc4.mist.com`.
The host is loaded from the `MIST_HOST` environment variable at process
start by the existing `mistapi.APISession` constructor; MistHelper never
hardcodes it.

### Path parameters (both required)

| Name | Type | Format | Source | Description |
|------|------|--------|--------|-------------|
| `org_id` | string | UUID | Prompt (default from `.env MIST_ORG_ID`) | Owning Mist organization UUID |
| `nacrule_id` | string | UUID | Prompt | Unique NAC rule UUID |

Both are validated against the Mist UUID regex before the SDK call. On
validation failure the method logs `WARNING` and returns early.

### Query parameters

**None.** The endpoint is non-paginated and takes no filters.

### Request headers

Injected automatically by `mistapi.APISession`:

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `Token <MIST_API_TOKEN>` | From `.env`; never logged |
| `Content-Type` | `application/json` | Standard |
| `Accept` | `application/json` | Standard |
| `User-Agent` | `mistapi-python/<version>` | Set by SDK |

MistHelper adds no custom headers.

### Request body

**None.** GET request; body ignored by Mist API.

---

## Response 200 (success) schema

Single JSON object (`nac_rule` schema). Full schema reproduced from the
enriched doc:

```json
{
  "title": "nac_rule",
  "required": ["action", "name"],
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "description": "enum: `allow`, `block`"
    },
    "apply_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Optional. Injected into Access-Accept.",
      "examples": [["c049dfcd-0c73-5014-1c64-062e9903f1e5"]]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "enabled": {
      "type": "boolean",
      "description": "Enabled or not",
      "default": true
    },
    "guest_auth_state": {
      "type": "string",
      "description": "Guest portal authorization state. enum: `authorized`, `unknown`"
    },
    "id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["53f10664-3ce8-4c27-b382-0ef66432349f"]
    },
    "matching": {
      "title": "nac_rule_matching",
      "type": "object",
      "properties": {
        "auth_type":    { "type": "string",  "description": "enum: cert, device-auth, eap-teap, eap-tls, eap-ttls, idp, mab, eap-peap" },
        "family":       { "type": "array",   "items": { "type": "string" } },
        "mfg":          { "type": "array",   "items": { "type": "string" } },
        "model":        { "type": "array",   "items": { "type": "string" } },
        "nactags":      { "type": "array",   "items": { "type": "string" } },
        "os_type":      { "type": "array",   "items": { "type": "string" } },
        "port_types":   { "type": "array",   "items": { "type": "string", "enum": ["wired", "wireless"] } },
        "site_ids":     { "type": "array",   "items": { "type": "string", "contentEncoding": "uuid" } },
        "sitegroup_ids":{ "type": "array",   "items": { "type": "string", "contentEncoding": "uuid" } },
        "vendor":       { "type": "array",   "items": { "type": "string" } }
      }
    },
    "modified_time": {
      "type": "number",
      "description": "When last modified, in epoch",
      "readOnly": true
    },
    "name": { "type": "string" },
    "not_matching": {
      "title": "nac_rule_matching",
      "type": "object",
      "properties": {
        "auth_type":    { "type": "string" },
        "family":       { "type": "array",   "items": { "type": "string" } },
        "mfg":          { "type": "array",   "items": { "type": "string" } },
        "model":        { "type": "array",   "items": { "type": "string" } },
        "nactags":      { "type": "array",   "items": { "type": "string" } },
        "os_type":      { "type": "array",   "items": { "type": "string" } },
        "port_types":   { "type": "array",   "items": { "type": "string", "enum": ["wired", "wireless"] } },
        "site_ids":     { "type": "array",   "items": { "type": "string", "contentEncoding": "uuid" } },
        "sitegroup_ids":{ "type": "array",   "items": { "type": "string", "contentEncoding": "uuid" } },
        "vendor":       { "type": "array",   "items": { "type": "string" } }
      }
    },
    "order": {
      "type": "integer",
      "minimum": 0,
      "description": "Order of the rule; lower number = higher priority",
      "contentEncoding": "int32",
      "examples": [1]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"]
    }
  }
}
```

### Example response body

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "guest-vlan-block",
  "action": "block",
  "enabled": true,
  "order": 1,
  "apply_tags": ["c049dfcd-0c73-5014-1c64-062e9903f1e5"],
  "matching": {
    "port_types": ["wireless"],
    "site_ids":   ["bb19fc3e-4124-4b57-80d9-c3f6edce47c4"]
  },
  "not_matching": {
    "auth_type": "eap-tls"
  },
  "created_time":  1698765432.0,
  "modified_time": 1725432198.0
}
```

## Error responses and MistHelper handling

Every error is caught by the SDK and surfaced through `resp.status_code` and
`resp.data`. MistHelper's handling is defined by the existing central error
handler plus the additions below:

| Status | Meaning | MistHelper action |
|--------|---------|-------------------|
| **400** | Bad Syntax | `logging.warning("400 Bad Syntax on getOrgNacRule org=%s rule=%s", org_id, nacrule_id)`; return early; no CSV/DB write. |
| **401** | Unauthorized | `logging.error("401 Unauthorized -- check MIST_API_TOKEN in .env")`; return early; do NOT retry (invalid credential is not transient). |
| **403** | Permission Denied | `logging.warning("403 Permission Denied on org %s (token lacks scope)", org_id)`; return early; no write. |
| **404** | Rule not found | `logging.warning("404 -- NAC rule %s not found in org %s", nacrule_id, org_id)`; return early; no write. This is the "user typed the wrong id" case and is not an error condition. |
| **429** | Rate limit | Delegated to the SDK / adaptive delay system (`delay_metrics.json`, `tuning_data.json`); MistHelper retries with exponential back-off up to the retry cap; on final failure `logging.error("429 exhausted retries")` and return early. `--fast` mode raises the concurrency cap but still respects the 5000/hour ceiling. |
| **5xx** | Server error | Delegated to the SDK retry policy; on final failure `logging.exception("Unexpected server error on getOrgNacRule")` and return early. |

No error path raises to the top-level menu loop; the loop always sees a
clean return so the operator is returned to the menu without a traceback.

## Exact mistapi Python call signature

```python
import mistapi
import mistapi.api.v1.orgs.nac_rules as nac_rules_api

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

response = nac_rules_api.getOrgNacRule(
    apisession=apisession,          # required, first positional arg per SDK convention
    org_id=org_id,                  # required UUID string
    nacrule_id=nacrule_id,          # required UUID string
)

status_code = response.status_code  # int -- 200 on success
payload     = response.data         # dict -- the nac_rule object (or empty dict)
```

Notes:

- SDK module path is `mistapi.api.v1.orgs.nac_rules` (underscore in
  `nac_rules`), matching mistapi 0.59+ layout. The Mist API URL segment
  is still `nacrules` (no underscore) -- do not confuse the two.
- `apisession` is the singleton created once at MistHelper process start;
  do NOT construct a new session per menu invocation.
- `response.data` is the parsed JSON body; MistHelper never touches
  `response.raw_data` or the HTTP object directly.
- No custom kwargs (`timeout`, `verify`, etc.) are passed; SDK defaults
  are correct.

## Contract test hooks

- Positive: mock `nac_rules_api.getOrgNacRule` to return a `MistApiResponse`
  with `status_code=200` and `data={...example above...}`; assert
  `DataExporter.write_with_format_selection` receives exactly one row with
  `id="53f10664-..."` and `action="block"`.
- Negative 404: mock returns `status_code=404, data={}`; assert method
  returns early, no write occurs, one `WARNING` log line emitted.
- Negative 401: mock returns `status_code=401`; assert one `ERROR` log
  line, no retry, no write.
- Negative 429: mock returns `status_code=429` then `200`; assert one
  retry, one final write.
- EOF: patch `safe_input` to raise `EOFError`; assert `sys.exit(0)` and no
  traceback.

These hooks live under `tests/contract/test_get_org_nac_rule.py` (added
during Phase 2 / `tasks.md`; out of scope for this contract file).
