# Contract: getOrgEvpnTopology

Source reference: `documentation/api/orgs/GET_orgs_org_id_evpn_topologies_evpn_topology_id.md`

## HTTP

- **Method**: `GET`
- **URL template**: `https://{MIST_HOST}/api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}`
- **Default host**: `api.mist.com` (regional clouds: `api.eu.mist.com`, `api.gc1.mist.com`, etc.)

### Path parameters (required)

| Name               | Type   | Format | Description                                  |
|--------------------|--------|--------|----------------------------------------------|
| `org_id`           | string | UUID   | Mist organization identifier.                |
| `evpn_topology_id` | string | UUID   | Mist EVPN topology identifier within the org.|

### Query parameters

_None._ Endpoint is not paginated.

### Request headers

| Header           | Value                                  | Notes                                |
|------------------|----------------------------------------|--------------------------------------|
| `Authorization`  | `Token {MIST_API_TOKEN}`               | Loaded from `.env`; never logged.    |
| `Accept`         | `application/json`                     | Implicit via `mistapi.APISession`.   |
| `User-Agent`     | `mistapi/<version> python/<version>`   | Set by the SDK.                      |

### Request body

_None._

## Response 200 (success)

Single JSON object. Top-level fields (full schema in
`documentation/api/orgs/GET_orgs_org_id_evpn_topologies_evpn_topology_id.md`
lines 36-1450):

| Field             | Type         | Notes                                                                  |
|-------------------|--------------|------------------------------------------------------------------------|
| `id`              | string(UUID) | Topology identifier. Required (used as natural PK).                    |
| `name`            | string       | Human label.                                                           |
| `org_id`          | string(UUID) | Read-only, echoes path parameter.                                      |
| `site_id`         | string(UUID) | Read-only; nullable for org-scope topologies.                          |
| `created_time`    | number       | Epoch seconds; read-only.                                              |
| `modified_time`   | number       | Epoch seconds; read-only.                                              |
| `overwrite`       | boolean      | Whether this topology overrides org-level templates.                   |
| `evpn_options`    | object       | Embedded overlay/underlay BGP config; see schema for full sub-fields.  |
| `pod_names`       | map<int,str> | Free-form per-pod labels keyed by pod number.                          |
| `switch_configs`  | map<mac,obj> | Per-MAC overrides (`switch_network` + `dhcpd_config`).                 |
| `switches`        | array<obj>   | **Required.** Per-switch role / pod / `evpn_id` / `mac` records.       |

Required at the top level: `switches`.

### `switches[]` element fields

Documented at lines 1320-1450 of the enriched reference. Key fields used by the
data-model detail row:

- `mac` (string) -- 12-char lowercase hex device MAC.
- `role` (string) -- enum: `core`, `distribution`, `access`, `esilag-access`, etc.
- `pod` (integer) -- pod assignment for distribution / access / esilag-access.
- `pods` (array<int>) -- limits which pods a core switch services.
- `evpn_id` (integer) -- VxLAN EVPN identifier.
- `site_id` (string, UUID) -- optional per-switch site override.

## Error responses and MistHelper handling

| Status | Mist meaning                                              | MistHelper handling                                                                                   |
|--------|-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (e.g. malformed UUID)                          | UUID shape is validated client-side BEFORE the call; if 400 still arrives, log `WARNING` with status. |
| 401    | Unauthorized (invalid / expired API token)                | Log `ERROR` "API token rejected; check MIST_API_TOKEN"; exit method without exporting empty files.    |
| 403    | Permission Denied (token lacks org read scope)            | Log `ERROR` "Insufficient privilege for org %s"; exit method without exporting empty files.           |
| 404    | Not Found (endpoint or resource missing)                  | Log `WARNING` "EVPN topology %s not found in org %s"; exit method without exporting empty files.      |
| 429    | Rate limited (5000 calls/hour)                            | Handled by the existing adaptive delay subsystem (`delay_metrics.json`, `tuning_data.json`); retried. |

In all error cases the method returns control to the menu loop with no
traceback. Operators see a single ASCII log line; no API token, full URL, or
raw response body is ever logged.

## Pagination

Not paginated. Single request, single object response.

## Rate limiting

Standard Mist API limits (5000 calls/hour per token). The MistHelper adaptive
delay system applies without endpoint-specific tuning; in `--fast` mode the
existing concurrency and retry caps apply unchanged.

## Exact mistapi Python call signature

```python
import mistapi
import mistapi.api.v1.orgs.evpn_topologies as evpn

session: mistapi.APISession = mistapi.APISession(env_file=".env")
session.login()  # No-op for token auth; preserved for SDK API consistency.

response: mistapi.APIResponse = evpn.getOrgEvpnTopology(
    session,                                       # APISession instance
    "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",        # org_id
    "9c8d0e2a-1f4b-4d5e-aabb-001122334455",        # evpn_topology_id
)

topology: dict = response.data or {}               # Single JSON object on 200; {} on 404.
switches: list = topology.get("switches", [])      # Required field, but defensive default.
```

### Notes

- `mistapi.APISession` reads `MIST_HOST` and `MIST_API_TOKEN` from `.env` at
  construction. MistHelper already wraps this in `_get_session()`.
- The SDK function name is `getOrgEvpnTopology` (camelCase). MistHelper passes
  the same string as the `api_function_name=` keyword to
  `DataExporter.write_with_format_selection()` so the dispatch picks up the
  registered PK strategy from `ENDPOINT_PRIMARY_KEY_STRATEGIES`. The synthetic
  sibling `getOrgEvpnTopology_switches` is used for the per-switch detail file.
- `response.status_code` is checked implicitly by the SDK; 4xx / 5xx raise no
  exception by default but yield `response.data is None` -- the method treats
  that as "empty payload" and logs a warning.
