# Contract: getOrgMxEdge

**Feature**: 615-mist-get-org-mx-edge | **Date**: 2026-06-30
**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source**: `documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id.md` (Mist OpenAPI 3)

This document is the authoritative HTTP + SDK contract that MistHelper must implement
for menu item 235.

---

## 1. HTTP Contract

| Attribute | Value |
|-----------|-------|
| **Method** | `GET` |
| **URL template** | `https://{MIST_HOST}/api/v1/orgs/{org_id}/mxedges/{mxedge_id}` |
| **Tag** | `Orgs MxEdges` |
| **operationId** | `getOrgMxEdge` |
| **Paginated** | No |
| **Idempotent** | Yes (safe read; no side effects) |

### Required Path Parameters

| Name | Type | Description |
|------|------|-------------|
| `org_id` | string (UUID) | Owning Mist organization. |
| `mxedge_id` | string (UUID) | Target MxEdge appliance. |

### Query Parameters

_None._ The endpoint accepts no query string parameters. MistHelper must not append
any.

### Request Headers

| Header | Value |
|--------|-------|
| `Authorization` | `Token {MIST_API_TOKEN}` (loaded from `.env`; never logged) |
| `Accept` | `application/json` |
| `User-Agent` | mistapi default (no override) |

Cookie-based auth (`X-CSRFToken`) is supported by the API but not used by MistHelper.

### Request Body

_None._ GET request.

---

## 2. Successful Response (`200 OK`)

A single JSON object describing one MxEdge. Top-level shape (full schema in
`documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id.md`):

```jsonc
{
  "id":                  "53f10664-3ce8-4c27-b382-0ef66432349f",   // UUID, readOnly, PK
  "org_id":              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",   // UUID, readOnly
  "site_id":             "441a1214-6928-442a-8e92-e1d34b8ec6a6",   // UUID, readOnly, nullable
  "mxcluster_id":        "572586b7-f97b-a22b-526c-8b97a3f609c4",   // UUID
  "for_site":            false,                                    // bool, readOnly
  "name":                "Guest",                                  // REQUIRED by schema
  "model":               "ME-100",                                 // REQUIRED by schema
  "mac":                 "0200009fbe65",                           // readOnly
  "magic":               "L-NpT5gi-...",                           // readOnly; REDACT before log/store
  "created_time":        1719600000.0,                             // epoch seconds
  "modified_time":       1719700000.0,                             // epoch seconds
  "mxagent_registered":  true,                                     // readOnly
  "tunterm_registered":  true,                                     // readOnly
  "note":                "note for mxedge",
  "services":            ["tunterm"],                              // strings
  "ntp_servers":         ["10.0.0.1"],                             // unique strings
  "versions": {
    "mxagent":           "1.2.3",                                  // readOnly
    "tunterm":           "4.5.6"                                   // readOnly
  },
  "mxedge_mgmt": {
    "fips_enabled":         false,
    "config_auto_revert":   false,
    "oob_ip_type":          "static",         // enum: dhcp | disabled | static
    "oob_ip_type6":         "disabled",       // enum: autoconf | dhcp | disabled | static
    "mist_password":        "MIST_PASSWORD",  // REDACT
    "root_password":        "ROOT_PASSWORD"   // REDACT
  },
  "oob_ip_config": {
    "type":          "static",                // enum: dhcp | static
    "ip":            "10.2.1.2",
    "netmask":       "255.255.255.0",
    "gateway":       "10.2.1.254",
    "dns":           ["8.8.8.8", "8.8.4.4"],
    "type6":         "static",
    "ip6":           "2601:1700:43c0:dc0:20c:29ff:fea7:93bc",
    "netmask6":      "/64",
    "gateway6":      "2601:1700:43c0:dc0::1",
    "dhcp6":         true,
    "autoconf6":     true
  },
  "proxy": {
    "disabled":      true,
    "url":           "https://proxy.corp.com:8080/"
  },
  "tunterm_ip_config": {                       // required keys: gateway, ip, netmask
    "ip":            "10.2.1.1",
    "netmask":       "255.255.255.0",
    "gateway":       "10.2.1.254",
    "ip6":           "2001:1010:1010:1010::2",
    "netmask6":      "/64",
    "gateway6":      "2001:1010:1010:1010::1"
  },
  "tunterm_port_config": {
    "separate_upstream_downstream": false,
    "upstream_ports":              ["0", "1"],
    "downstream_ports":            ["2", "3"],
    "upstream_port_vlan_id":       { /* opaque object */ }
  },
  "tunterm_switch_config":        { "enabled": true },
  "tunterm_dhcpd_config":         { /* per-VLAN object, key is VLAN id */ },
  "tunterm_extra_routes":         { /* keyed by CIDR */ },
  "tunterm_igmp_snooping_config": { "enabled": true, "querier": { /* ... */ }, "vlan_ids": [10,20] },
  "tunterm_multicast_config":     { "mdns": { /* ... */ }, "ssdp": { /* ... */ } },
  "tunterm_other_ip_configs":     { /* keyed by VLAN id */ },
  "tunterm_monitoring":           [ [ { "host": "10.2.8.15", "protocol": "ping", "timeout": 300 } ] ]
}
```

**Required fields (per OpenAPI schema)**: `model`, `name`. All other top-level fields
are optional and may be absent.

**Redaction**: Before logging or persistence, MistHelper replaces the values of
`magic`, `mxedge_mgmt.mist_password`, and `mxedge_mgmt.root_password` with the literal
string `<redacted>`. See [../data-model.md](../data-model.md) section "Redaction Rules".

---

## 3. Error Responses

| Status | Meaning (per OpenAPI) | MistHelper handling |
|--------|------------------------|---------------------|
| `400`  | Bad Syntax | `logging.warning("getOrgMxEdge 400: %s", reason)`; return early. Should not happen if UUID regex validation passes. |
| `401`  | Unauthorized | `logging.error("getOrgMxEdge 401: token invalid or expired")`; return early. The shared `mistapi.APISession` is the same one used by other menu items, so a 401 here is a hard environmental error -- no retry. |
| `403`  | Permission Denied | `logging.error("getOrgMxEdge 403: insufficient privileges for org %s", org_id)`; return early. No retry. |
| `404`  | Not found (endpoint missing or resource missing) | `logging.warning("getOrgMxEdge 404: mxedge %s not found in org %s", mxedge_id, org_id)`; return early with exit 0. This is the most likely operator-facing error and must NOT raise a traceback. |
| `429`  | Too Many Requests (5000/hour limit) | Adaptive delay system (existing `delay_metrics.json` + `tuning_data.json`) handles retry transparently. The menu method does not branch on 429 -- mistapi + the shared retry wrapper handle it. |

Any unexpected exception is caught at the top of the menu method and routed through
`logging.exception("Unexpected error in get_org_mxedge_detail")`, which preserves the
traceback in the per-host log without leaking the API token.

---

## 4. mistapi Python SDK Call

### Import

```python
import mistapi
import mistapi.api.v1.orgs.mxedges                                  # the SDK module
```

### Exact call signature

```python
response: mistapi.APIResponse = mistapi.api.v1.orgs.mxedges.getOrgMxEdge(
    apisession,                # mistapi.APISession (shared MistHelper singleton)
    org_id=org_id,             # str, UUID (required path param)
    mxedge_id=mxedge_id,       # str, UUID (required path param)
)
record: dict = response.data   # dict on 200; empty/None on 404
```

### Field reference

- `response.status_code` -- HTTP status (200 / 4xx).
- `response.data` -- decoded JSON body (`dict` for this endpoint).
- `response.headers` -- response headers including rate-limit telemetry consumed by
  the adaptive delay system.
- `response.next` -- always `None` for this endpoint (not paginated).

### Pagination

Not applicable. The SDK returns the full record in a single call; the menu method
does NOT iterate or call `mistapi.get_next()`.

### Rate Limiting

Standard Mist API limits (5000 calls / hour per token). The shared adaptive delay
system handles back-off without per-menu logic. A 429 results in transparent retry by
mistapi + the shared wrapper.

---

## 5. Test Expectations

When `python MistHelper.py --test` invokes menu 235 with the env fixtures from
[../quickstart.md](../quickstart.md):

1. Exit code is 0.
2. `data/OrgMxEdgeDetail.csv` exists and contains exactly 1 data row (plus header).
3. `data/mist_data.db` table `org_mxedge_detail` contains exactly 1 row keyed by the
   test MxEdge id.
4. Re-running the same invocation produces a row count of still exactly 1 (upsert
   verified).
5. The log file contains exactly one `INFO` "Fetching MxEdge detail" line per run.
6. The log file contains zero occurrences of the literal token value, `magic` value,
   `mist_password` value, or `root_password` value.

When the env fixtures are not set, menu 235 logs a `WARNING` and returns with exit
code 0 (test sweep is not failed).

---

## 6. Related Contracts

- `listOrgMxEdges` -- bulk listing already cataloged at line ~4685 of `MistHelper.py`.
- `getOrgMxEdgeStats` -- runtime stats sibling (line ~5210). Out of scope for this
  spec.
- `PUT /api/v1/orgs/{org_id}/mxedges/{mxedge_id}` -- write counterpart. Explicitly
  out of scope per `spec.md` "Out of Scope" section.
