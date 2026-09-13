# Endpoint Contract: getOrgMxEdgeCluster

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_mxclusters_mxcluster_id.md`

This contract is the binding HTTP + SDK reference the MistHelper menu item
implements. It is the source of truth for tests, the flatten helper, and
the DataExporter PK strategy.

---

## 1. HTTP Contract

| Property | Value |
|---|---|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}` |
| Auth | `Authorization: Token <MIST_API_TOKEN>` header (set by `mistapi.APISession`) |
| Request body | None |
| Pagination | Not paginated -- single object response |
| Idempotent | Yes (safe to retry) |

### Path Parameters (both required)

| Name | Type | Required | Validation | Source |
|---|---|---|---|---|
| `org_id` | UUID string | Yes | Mist UUID shape `[0-9a-fA-F-]{36}` | `.env` `MIST_ORG_ID` or user prompt |
| `mxcluster_id` | UUID string | Yes | Mist UUID shape `[0-9a-fA-F-]{36}` | User prompt only (no env default) |

### Query Parameters

None.

### Required Headers

Set automatically by `mistapi.APISession`. MistHelper does **not** add
custom headers.

- `Authorization: Token <MIST_API_TOKEN>` -- from `.env`, never logged.
- `Accept: application/json` -- default.
- `User-Agent: mistapi/<version>` -- default.

---

## 2. Success Response (200)

Content-Type: `application/json`. Body is a single `MxCluster` object.

### Top-level fields (selected)

| Field | Type | Description |
|---|---|---|
| `id` | string (UUID) | Cluster UUID, readOnly, primary key. |
| `org_id` | string (UUID) | Parent org UUID, readOnly. |
| `site_id` | string (UUID, nullable) | Owning site UUID when `for_site`. |
| `for_site` | boolean | True if cluster is site-scoped. readOnly. |
| `name` | string | Human-readable cluster name. |
| `created_time` | number | Epoch seconds, readOnly. |
| `modified_time` | number | Epoch seconds, readOnly. |

### Nested objects (JSON-encoded into single columns by the flattener)

| Field | Description |
|---|---|
| `mist_das` | Cloud-assisted dynamic authorization: `enabled` flag plus an array of CoA servers (each with `host`, `port`, `secret`, `enabled`, etc.). |
| `mist_nac` | Mist NAC config: `acct_server_port`, `auth_server_port`, `enabled`, `secret`, and a `client_ips` map keyed by RADIUS client IP/subnet. |
| `mxedge_mgmt` | Management config: `config_auto_revert`, `fips_enabled`, `mist_password`, `oob_ip_type`, `oob_ip_type6`, `root_password`. |
| `proxy` | Proxy config: `disabled` flag and `url`. |
| `radsec` | RadSec config: arrays `auth_servers` and `acct_servers`, plus `enabled`, `match_ssid`, `nas_ip_source`, `proxy_hosts`, `server_selection`, `src_ip_source`. |
| `radsec_tls` | TLS config: `keypair` reference. |
| `tunterm_dhcpd_config` | DHCP server/relay config keyed by VLAN id. |
| `tunterm_extra_routes` | Extra routes keyed by CIDR. |
| `tunterm_monitoring` | Array-of-arrays of monitoring probes (each entry has `host`, `port`, `protocol`, `src_vlan_id`, `timeout`). |

### Array fields (also JSON-encoded by the flattener)

| Field | Description |
|---|---|
| `tunterm_ap_subnets` | List of subnets where APs may establish Mist Tunnels. |
| `tunterm_hosts` | Hostnames/IPs used as tunnel peers. |
| `tunterm_hosts_order` | Integer indexes into `tunterm_hosts`. |
| `tunterm_monitoring_disabled` | Boolean. |

### Scalar enum

- `tunterm_hosts_selection`: one of `shuffle`, `shuffle-by-site`, `ordered`.

The full schema is reproduced verbatim in
`documentation/api/orgs/GET_orgs_org_id_mxclusters_mxcluster_id.md`; this
contract is the operational subset MistHelper persists.

---

## 3. Error Responses

| Status | Mist meaning | MistHelper handling |
|---|---|---|
| **400** Bad Syntax | Malformed request | Should not occur because both IDs are pre-validated locally; if it does, log `ERROR` via `logging.exception` and return 0 without raising. |
| **401** Unauthorized | Token missing or invalid | Log `ERROR` "Mist API token rejected (401). Check MIST_API_TOKEN in .env."; return 0. Never log the token value. |
| **403** Permission Denied | Token lacks org scope | Log `ERROR` "Permission denied (403) on cluster %s. Token may lack org-read scope."; return 0. |
| **404** Not Found | Wrong `org_id` or `mxcluster_id`, or cluster deleted | Log `WARNING` "MxCluster %s not found in org %s (404). No row written."; return 0 (no traceback). |
| **429** Too Many Requests | 5000 calls/hour reached | Adaptive delay system in `delay_metrics.json` triggers; menu retries automatically per existing rate-limit logic. No special handling required in the new method. |

All error paths exit with code 0 and emit a single ASCII log line. No
secret values (API token, RADIUS shared secrets, `mist_password`,
`root_password`) appear in any error log.

---

## 4. mistapi SDK Call

### Signature

```python
mistapi.api.v1.orgs.mxclusters.getOrgMxEdgeCluster(
    mist_session: mistapi.APISession,
    org_id: str,
    mxcluster_id: str,
) -> mistapi.APIResponse
```

### Usage (MistHelper canonical form)

```python
import mistapi                                                              # Already imported at module top.
import mistapi.api.v1.orgs.mxclusters                                       # Sub-module for this endpoint.

response = mistapi.api.v1.orgs.mxclusters.getOrgMxEdgeCluster(              # The single GET.
    apisession,                                                             # Shared module-level APISession.
    org_id=org_id,                                                          # UUID from prompt or .env.
    mxcluster_id=mxcluster_id,                                              # UUID from prompt.
)
record: dict = response.data or {}                                          # .data is dict (not list).
```

### Return shape

- `response.status_code` -- HTTP status code (200 on success).
- `response.data` -- decoded JSON object (a `dict`). May be an empty dict
  on 404; MistHelper treats `not record` as "no row to write" and exits
  cleanly.
- `response.next` -- not used (endpoint is not paginated).

### Threading / concurrency

The SDK call is synchronous and re-entrant. MistHelper's existing rate
limiter and adaptive delay apply transparently via the shared
`apisession`; no per-call concurrency knobs are required for this menu
item.

---

## 5. Contract Test Hooks

For implementation phase, the contract surface to test is:

1. **Happy path**: mock `response.data = {"id": "<uuid>", "name": "x",
   "org_id": "<uuid>"}` -> verify one row written to
   `OrgMxEdgeCluster.csv` and SQLite `org_mx_edge_cluster` upserts by
   `id`.
2. **Empty payload**: mock `response.data = {}` -> verify zero rows
   written, `WARNING` log emitted, exit code 0.
3. **404 path**: mock `response.status_code = 404` -> verify
   `WARNING` "not found" log line and clean exit.
4. **UUID validation**: invoke method with `org_id = "not-a-uuid"` ->
   verify the SDK is NOT called and a `WARNING` is logged.
5. **Secret redaction**: mock `response.data` containing
   `radsec.auth_servers[0].secret = "supersecret"` -> verify the
   DEBUG log line does NOT contain the literal `"supersecret"`.

These tests are out of scope for `/speckit.plan`; they are tracked for
`/speckit.tasks`.
