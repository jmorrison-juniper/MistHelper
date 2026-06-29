# Endpoint Contract: getInstallerDeviceVirtualChassis

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Authoritative reference**: `documentation/api/installer/GET_installer_orgs_org_id_devices_fpc0_mac_vc.md`

## HTTP Contract

| Aspect | Value |
|--------|-------|
| **Method** | `GET` |
| **URL template** | `/api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc` |
| **Full URL example** | `https://api.mist.com/api/v1/installer/orgs/a97c1b22-a4e9-411e-9bfd-d8695a0f9e61/devices/fc3342123456/vc` |
| **Authentication** | `Authorization: Token <api_token>` header **or** `X-CSRFToken` cookie. MistHelper uses the header form supplied by `mistapi.APISession`. |
| **Content-Type (request)** | N/A (no body) |
| **Content-Type (response)** | `application/json` |
| **Pagination** | None. Single non-paginated JSON object. |
| **Rate limit** | Standard Mist API limit (5000 calls/hour per token). 429 triggers MistHelper's adaptive delay system. |

### Path Parameters

| Name | Type | Required | Description | MistHelper source |
|------|------|----------|-------------|-------------------|
| `org_id` | string (UUID) | yes | Target organization UUID. | `safe_input("Enter org_id [...]: ", context="installer_vc:org_id")` with `MIST_ORG_ID` default from `.env`. |
| `fpc0_mac` | string (12-hex MAC) | yes | MAC address of the FPC0 (master/primary) switch in the VC. | `safe_input("Enter FPC0 MAC (any notation): ", context="installer_vc:fpc0_mac")`, normalized via `re.sub(r"[^0-9a-fA-F]", "", value).lower()` before the SDK call. |

### Query Parameters

None.

### Request Headers (supplied by mistapi.APISession)

```http
Authorization: Token <MIST_API_TOKEN>
Accept: application/json
User-Agent: mistapi/<version> python/<version>
```

### Request Body

None.

## 200 Success Response Schema

The endpoint returns a single JSON object (the VC). Top-level fields:

| Field | Type | readOnly | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | yes | Mist-assigned unique chassis ID. **Used as the natural PK for `installer_device_vc_summary`.** |
| `org_id` | string (UUID) | yes | Parent org. |
| `site_id` | string (UUID) | yes | Parent site. |
| `vc_mac` | string | yes | Canonical VC MAC. |
| `mac` | string | no | Chassis-level MAC. |
| `model` | string | yes | Chassis model. |
| `serial` | string | yes | Chassis serial. |
| `type` | string | no | Device type. |
| `config_type` | string | yes | API-supplied config type. |
| `status` | string | yes | Chassis status. |
| `num_routing_engines` | integer (int32) | no | RE count. |
| `locating` | boolean | yes | Locating LED flag. |
| `members` | array | no | One entry per stack member. `minItems: 1, uniqueItems: true`. See below. |

### `members[]` element schema (`stats_switch_module_stat_item`)

Each element represents one switch in the VC:

| Field | Type | readOnly | Description |
|-------|------|----------|-------------|
| `fpc_idx` | integer (int32) | yes | Slot index within the VC. **Used with parent `id` as composite PK for `installer_device_vc_members`.** |
| `mac` | string | no | Member MAC (e.g. `fc3342123456`). |
| `serial` | string | yes | Member serial (e.g. `PX8716230021`). |
| `model` | string | yes | Member model (e.g. `EX4300-48P`). |
| `status` | string | yes | Member status. |
| `type` | string | yes | Member type. |
| `vc_role` | string | yes | Enum: `master`, `backup`, `linecard`. |
| `vc_state` | string | yes | Member VC state. |
| `vc_mode` | string | yes | Member VC mode. |
| `version` | string | yes | Running Junos version. |
| `backup_version` | string\|null | yes | Backup-partition version. |
| `pending_version` | string\|null | yes | Staged-upgrade version. |
| `recovery_version` | string\|null | yes | Recovery-image version. |
| `bios_version` | string\|null | yes | BIOS version. |
| `uboot_version` | string\|null | yes | U-Boot version. |
| `fpga_version` | string\|null | yes | Main FPGA version. |
| `re_fpga_version` | string\|null | yes | RE FPGA version. |
| `tmc_fpga_version` | string\|null | yes | TMC FPGA version. |
| `cpld_version` | string\|null | yes | CPLD version. |
| `optics_cpld_version` | string\|null | yes | Optics CPLD version. |
| `power_cpld_version` | string\|null | yes | Power CPLD version. |
| `poe_version` | string\|null | yes | PoE controller version. |
| `boot_partition` | string | no | Currently booted partition. |
| `last_seen` | number\|null | yes | Unix-ts last contact. |
| `uptime` | integer (int32)\|null | yes | Uptime seconds. |
| `locating` | boolean | no | Per-member locating LED flag. |
| `cpu_stat` | object | -- | `idle`, `system`, `user`, `interrupt`, `usage` percents; `load_avg` array of 1/5/15 min. |
| `memory_stat` | object | -- | `usage` (master-RE memory). `usage` required. |
| `poe` | object | -- | `max_power`, `power_draw`, `status`. |
| `fans` | array | -- | Items: `{name, rpm, status, airflow}`. uniqueItems. |
| `psus` | array | -- | Items: `{name, status}`. uniqueItems. |
| `temperatures` | array | -- | Items: `{name, celsius, status}`. uniqueItems. |
| `vc_links` | array | -- | Items: `{port_id, neighbor_module_idx, neighbor_port_id}`. uniqueItems. |
| `pics` | array | -- | Items: `{index, model_number, port_groups[]}` where each port_group is `{count, type}`. |
| `errors` | array | -- | Items: `{type, since, feature?, reason?, minimum_version?}`. `type` and `since` required. |

## Example 200 Response (abbreviated)

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "vc_mac": "fc3342000001",
  "mac": "fc3342000001",
  "model": "EX4300-48P",
  "serial": "PX8716230020",
  "type": "switch",
  "config_type": "vc",
  "status": "connected",
  "num_routing_engines": 1,
  "locating": false,
  "members": [
    {
      "fpc_idx": 0,
      "mac": "fc3342000001",
      "serial": "PX8716230020",
      "model": "EX4300-48P",
      "status": "connected",
      "vc_role": "master",
      "vc_state": "Prsnt",
      "version": "21.4R3-S5.4",
      "last_seen": 1719600000,
      "uptime": 864000,
      "cpu_stat": {"idle": 92.1, "system": 4.3, "user": 3.4, "interrupt": 0.2, "usage": 7.9, "load_avg": [0.21, 0.18, 0.15]},
      "memory_stat": {"usage": 38.4},
      "poe": {"max_power": 740, "power_draw": 312.5, "status": "ok"},
      "fans": [{"name": "Fan 0", "rpm": 4800, "status": "ok", "airflow": "out"}],
      "psus": [{"name": "Power Supply 0", "status": "ok"}],
      "temperatures": [{"name": "CPU", "celsius": 45, "status": "ok"}],
      "vc_links": [{"port_id": "vcp-255/1/0", "neighbor_module_idx": 1, "neighbor_port_id": "vcp-255/1/0"}],
      "pics": [{"index": 0, "model_number": "EX4300-48P", "port_groups": [{"count": 48, "type": "1000BASE-T"}]}],
      "errors": []
    }
  ]
}
```

## Error Responses & MistHelper Handling

| Status | Mist meaning | MistHelper behavior |
|--------|--------------|---------------------|
| **400** | Bad Syntax | `mistapi` raises; caught by the menu's try/except, `logging.warning("Bad request for org %s fpc0 %s", org_id, fpc0_mac_normalized)`, return code 1. Most often triggered by an unnormalized MAC -- preventive validation in the menu method should make this rare. |
| **401** | Unauthorized | `logging.error("Auth failed -- check MIST_API_TOKEN in .env")` then `sys.exit(2)` (consistent with adjacent menu items). Token is never logged. |
| **403** | Permission Denied | `logging.warning("Token lacks Installer scope on org %s", org_id)`, return code 1. The user is prompted to retry with a token that includes Installer permissions. |
| **404** | Not found (org or fpc0_mac does not exist, or the device is not a VC) | `logging.warning("VC not found for org %s fpc0 %s (standalone switch or unknown device?)", org_id, fpc0_mac_normalized)`, return code 0 -- a 404 here is a legitimate "no data" answer, not a failure. |
| **429** | Too Many Requests | Handled transparently by the adaptive delay system in `delay_metrics.json` + `tuning_data.json`. The menu method does not need explicit handling; mistapi back-off + retry covers it. |

All error paths route through `logging.exception(...)` for unexpected exceptions so the
full traceback lands in `data/script.log` for post-mortem analysis.

## mistapi SDK Python Call Signature

**Primary (path-aligned) module** -- the import path declared in spec.md and used by
MistHelper for all 580+ catalogued endpoints:

```python
import mistapi
import mistapi.api.v1.installer.orgs.devices.vc

apisession = mistapi.APISession(env_file=".env")  # loads MIST_HOST + MIST_API_TOKEN
apisession.login()                                # establishes the session

response = mistapi.api.v1.installer.orgs.devices.vc.getInstallerDeviceVirtualChassis(
    apisession,        # mistapi.APISession instance
    org_id,            # str -- target org UUID (path param)
    fpc0_mac,          # str -- normalized 12-hex FPC0 MAC (path param)
)

payload = response.data          # dict | None -- the VC JSON object
status_code = response.status_code  # int -- HTTP status from Mist
url_called = response.url           # str -- for debug logging (do NOT log token)
```

**Return type**: `mistapi.APIResponse` with:

- `.data` -- `dict` matching the schema above, or `None` on empty body.
- `.status_code` -- `int` HTTP code (200 on success).
- `.url` -- `str` request URL (safe to log; token is in the header, not the URL).
- `.headers` -- `dict` of response headers including `X-Page-Limit` etc. (not used by
  this endpoint since it is non-paginated).

**Tag-grouped alias** (also valid, for cross-reference with the enriched doc):
`mistapi.api.v1.installer.installer.getInstallerDeviceVirtualChassis()`.
MistHelper standardizes on the path-aligned form above; the tag-grouped form is not
used.

## Contract Test Plan

A future `/speckit.tasks` artifact will translate the rows below into concrete test
tasks. They are listed here so the contract is verifiable end-to-end:

1. **Happy path**: known org + known FPC0 MAC -> 200 + non-empty `members` -> two CSV
   files written, two SQLite tables populated with the expected row counts.
2. **Re-run idempotency**: invoke twice in succession -> SQLite row counts unchanged,
   `fetched_at` advanced, no duplicate (id) or (vc_id, fpc_idx) rows.
3. **Bad MAC**: input `not-a-mac` -> validation rejects with WARNING, exit code 1, no
   API call made.
4. **Unknown FPC0**: valid-shape MAC that does not exist -> 404 -> WARNING, exit code
   0, no rows written.
5. **EOF on prompt**: simulate Ctrl-D / SSH disconnect during `safe_input()` -> clean
   `sys.exit(0)`, no traceback.
6. **--fast mode**: pass `--fast` flag -> retry cap reduced, concurrency raised, but
   the single GET still completes successfully.
