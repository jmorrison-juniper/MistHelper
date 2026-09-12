# Endpoint Contract: countOrgAuditLogs

## HTTP Contract

| Field          | Value                                              |
|----------------|----------------------------------------------------|
| Method         | `GET`                                              |
| URL Template   | `https://{host}/api/v1/orgs/{org_id}/logs/count`   |
| Auth Header    | `Authorization: Token {MIST_API_TOKEN}`            |
| Accept Header  | `application/json`                                 |
| Content-Type   | (none -- no request body)                          |

### Path Parameters

| Name     | Type          | Required | Description                                |
|----------|---------------|----------|--------------------------------------------|
| `org_id` | string (UUID) | Yes      | Mist Cloud organization identifier.        |

### Query Parameters

| Name         | Type    | Required | Default | Notes                                                                                          |
|--------------|---------|----------|---------|------------------------------------------------------------------------------------------------|
| `distinct`   | string  | No       | (none)  | Grouping field. Per related-endpoint convention: `admin_id`, `admin_name`, `message`, `site_id`. MistHelper defaults to `admin_name`. |
| `admin_id`   | string  | No       | (none)  | Server-side filter -- limit to actions by this admin UUID.                                     |
| `admin_name` | string  | No       | (none)  | Server-side filter -- limit to actions by this admin display name.                             |
| `site_id`    | string  | No       | (none)  | Server-side filter -- limit to actions scoped to a single site.                                |
| `message`    | string  | No       | (none)  | Server-side text filter on the audit-log `message` field.                                      |
| `start`      | string  | No       | (none)  | Window start. Epoch seconds or relative (`-1d`, `-1w`).                                        |
| `end`        | string  | No       | (none)  | Window end. Epoch seconds or relative (`now`, `-1h`).                                          |
| `duration`   | string  | No       | `1d`    | Convenience window length (`7d`, `2w`, etc.) -- mutually compatible with `end`.                |
| `limit`      | integer | No       | `100`   | Maximum number of distinct buckets returned.                                                   |

### Request Body

None.

## Response Schema (200 OK)

Per `documentation/api/orgs/GET_orgs_org_id_logs_count.md`:

```json
{
  "type": "object",
  "properties": {
    "distinct": { "type": "string" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "start":    { "type": "integer", "contentEncoding": "int32" },
    "total":    { "type": "integer", "contentEncoding": "int32" },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": ["count"],
        "type": "object",
        "properties": {
          "count": { "type": "integer", "contentEncoding": "int32" }
        },
        "additionalProperties": { "type": "string" }
      }
    }
  },
  "required": ["distinct", "end", "limit", "results", "start", "total"]
}
```

Each `results[i]` entry is a 2-key object: the required `count` integer plus exactly one
additional string key whose **name matches the value of `distinct`** and whose value is
the bucket label. Example with `distinct=admin_name`:

```json
{
  "distinct": "admin_name",
  "start": 1719012345,
  "end":   1719617145,
  "limit": 100,
  "total": 1342,
  "results": [
    { "count": 412, "admin_name": "alice@example.com" },
    { "count": 305, "admin_name": "bob@example.com"   },
    { "count": 198, "admin_name": "ops-bot@example.com" }
  ]
}
```

## Error Responses

| Status | Meaning              | MistHelper Handling                                                                                         |
|--------|----------------------|-------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax           | Log `WARNING` with the offending parameters; return without writing output.                                 |
| 401    | Unauthorized         | Log `ERROR` ("API token rejected -- check `.env`"); return without writing output. Do **not** log the token. |
| 403    | Permission Denied    | Log `ERROR` ("Token lacks permission for org %s"); return without writing output.                           |
| 404    | Not Found            | Log `WARNING` ("Org %s not found"); return without writing output.                                          |
| 429    | Too Many Requests    | Adaptive delay system in `delay_metrics.json` / `tuning_data.json` back-offs and retries automatically. No menu-level handling required. |

All error paths exit with code 0 in interactive mode (no traceback bubbles up to the
TTY) and with a non-zero exit only when `--test` is in effect, per the project's
test-mode convention.

## mistapi SDK Call Signature

```python
import mistapi
import mistapi.api.v1.orgs.logs

# self.apisession is the existing mistapi.APISession constructed from .env
response = mistapi.api.v1.orgs.logs.countOrgAuditLogs(
    self.apisession,                  # Authenticated session -- carries MIST_HOST + MIST_API_TOKEN
    org_id,                           # Path parameter -- validated UUID string
    distinct=distinct,                # Query: grouping field (default "admin_name")
    admin_id=None,                    # Query: optional admin UUID filter (v1 menu does not prompt)
    admin_name=None,                  # Query: optional admin name filter (v1 menu does not prompt)
    site_id=None,                     # Query: optional site filter (v1 menu does not prompt)
    message=None,                     # Query: optional text filter (v1 menu does not prompt)
    start=None,                       # Query: optional explicit window start
    end=None,                         # Query: optional explicit window end
    duration=duration,                # Query: convenience window length (default "1d")
    limit=limit,                      # Query: bucket cap (default 100)
)
payload = response.data               # dict matching the 200 schema above
```

The SDK is the sole permitted interface to the Mist Cloud -- direct `requests` calls
are prohibited by project convention. The call is invoked exactly once per menu run;
pagination, retry, and rate-limit handling are delegated to the existing MistHelper
adaptive-delay framework.

## Idempotency & Caching

The endpoint is naturally idempotent: repeated GETs with the same query string yield
the same aggregate (subject to new audit-log entries arriving server-side). MistHelper
upserts results by composite primary key (see `data-model.md`) so two runs in quick
succession produce one summary row + N bucket rows, not duplicates.
