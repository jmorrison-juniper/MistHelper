# Endpoint Contract: countOrgJsiPbn

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_jsi_pbn_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                            |
|-----------------|------------------------------------------------------------------|
| **Method**      | `GET`                                                            |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/jsi/pbn/count`         |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs JSI`                                                       |
| **operationId** | `countOrgJsiPbn`                                                 |
| **Description** | Get count of PBN (Proactive Bug Notification) advisories grouped by a specified field |

### Path Parameters

| Name     | Type          | Required | Description |
|----------|---------------|----------|-------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name       | Type    | Required | Default | Enum                                                | Description |
|------------|---------|----------|---------|-----------------------------------------------------|-------------|
| `distinct` | string  | Yes      | (none)  | `versions`, `models`, `customer_risk`, `bug_type`   | Field to group advisory counts by. Validated client-side against this enum before the call. |
| `limit`    | integer | No       | `100`   | --                                                  | Maximum result rows the server returns. The server may clamp lower and echo the value in the response envelope. |
| `start`    | string  | No       | (server picks) | --                                          | Window start. Accepts epoch seconds (e.g. `1719676800`) or relative strings (e.g. `-1d`, `-1w`). Pass-through to mistapi. |
| `end`      | string  | No       | (server picks) | --                                          | Window end. Accepts epoch seconds or relative strings (e.g. `-2h`, `now`). |

### Request Headers

| Header          | Value                  | Notes |
|-----------------|------------------------|-------|
| `Authorization` | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`     | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Schema (200 OK)

Content-Type: `application/json`. Schema title: `response_count`.

Required top-level keys: `distinct`, `end`, `limit`, `results`, `start`, `total`.

```json
{
  "distinct": "versions",
  "start": 1719072000,
  "end": 1719676800,
  "limit": 100,
  "total": 42,
  "results": [
    { "count": 12, "versions": "23.4R1" },
    { "count": 9,  "versions": "23.2R2" },
    { "count": 21, "versions": "22.4R3" }
  ]
}
```

### Field semantics

| Field      | Type   | Notes |
|------------|--------|-------|
| `distinct` | string | Echoes the request `distinct` grouping field. |
| `start`    | int32  | Epoch seconds the server honored as the window start. |
| `end`      | int32  | Epoch seconds the server honored as the window end. |
| `limit`    | int32  | Maximum rows the server honored (may be clamped). |
| `total`    | int32  | Total advisories matching the filter across all groups in the window. |
| `results`  | array of object | `uniqueItems: true`. Each element has a required integer `count` plus exactly one additional property whose key equals `distinct` (string) and whose value is the per-group label. |

`additionalProperties: {type: string}` on each result element means the per-group
label is always a string -- even when grouping by a numeric-looking field such as
`models`.

## Error Responses & MistHelper Handling

| Status | Description                                                                 | MistHelper handling |
|--------|-----------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax (e.g. unknown `distinct` value)                                  | Logged as `WARNING`; method returns early without writing. Client-side enum validation makes this rare. |
| 401    | Unauthorized (missing / invalid token)                                      | Logged as `ERROR`; raises in the dispatcher so the operator sees the failure immediately. Token never logged. |
| 403    | Permission Denied (token scope insufficient or org lacks JSI subscription)  | Logged as `WARNING`; method returns early. |
| 404    | Org not found or endpoint not provisioned                                   | Logged as `WARNING`; method returns early without writing. |
| 429    | Rate limited (5000 calls/hour per token)                                    | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) increases back-off automatically; mistapi retries per its built-in policy; no operator intervention required. |
| 5xx    | Upstream Mist Cloud error                                                   | Logged as `ERROR` with `logging.exception` (full traceback); method returns early. Retried by mistapi internal policy first. |

All error log lines are ASCII-only and never include the API token, full URL with
query string, or any field marked sensitive in the constitution.

## mistapi Python call signature

```python
from mistapi.api.v1.orgs.jsi import countOrgJsiPbn   # SDK module path per enriched doc
# ...
response = countOrgJsiPbn(                            # one-shot GET; no pagination loop needed
    self.apisession,                                  # mistapi.APISession bearing the token
    org_id,                                           # path param (UUID string)
    distinct=distinct,                                # required query enum
    limit=100,                                        # optional, default 100
    start=None,                                       # optional epoch / relative string
    end=None,                                         # optional epoch / relative string
)                                                     # returns mistapi.APIResponse
body = response.data or {}                            # parsed JSON dict
results = body.get("results", [])                     # list[dict]
```

The SDK function signature is verified at implementation time with:

```powershell
python -c "from mistapi.api.v1.orgs.jsi import countOrgJsiPbn; help(countOrgJsiPbn)"
```

If the actual SDK module path differs (e.g. `mistapi.api.v1.orgs.jsi.pbn.count`),
the implementation updates the import line accordingly; everything else in this
contract (URL, params, response schema, error handling) remains binding.

## Pagination

Documented as "supports pagination via `limit` and `page`", but `page` is not
exposed by the OpenAPI parameter list for this endpoint and `total` is the count
of advisories (not groups). MistHelper therefore makes one GET per invocation and
trusts the server-side `limit` (default 100) to bound the result set. If the
endpoint later adds a `page` query parameter, the implementation extends the
method with a paginate loop using the existing helper pattern.

## Rate Limiting

Standard Mist API rate limits apply: 5000 calls/hour per API token. The adaptive
delay system handles 429s automatically; no per-endpoint tuning is required for
this lightweight count endpoint.
