# Contract: getOrgDeviceUpgrade

**Feature**: 605-mist-get-org-device-upgrade
**Date**: 2026-06-30
**Source**: `documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md`

## HTTP

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` |
| Tag | `Utilities Upgrade` |
| operationId | `getOrgDeviceUpgrade` |
| Pagination | None (single object response) |
| Rate limit | Standard Mist API (5000 req/hr per token) |

### Path parameters (both required)

| Name | Type | Format | Source | Description |
|------|------|--------|--------|-------------|
| `org_id` | string | UUID | `MIST_ORG_ID` env var (default) or `safe_input()` | Target organization |
| `upgrade_id` | string | UUID | `safe_input()` (no default) | Upgrade job UUID returned by `listOrgDeviceUpgrades` |

### Query parameters

_None._

### Request headers

| Header | Value | Source |
|--------|-------|--------|
| `Authorization` | `Token <MIST_API_TOKEN>` | `.env` via `mistapi.APISession` |
| `Accept` | `application/json` | `mistapi` SDK default |
| `User-Agent` | `mistapi/<version>` | `mistapi` SDK default |

### Request body

_None._ This is a `GET`.

## Response: 200 OK

Single JSON object (not an array). Schema reproduced from
`documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md`:

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "target_version": "0.14.29411",
  "strategy": "canary",
  "enable_p2p": true,
  "force": false,
  "upgrades": [
    {
      "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
      "upgrade": {
        "id": "6c8e1a90-...",
        "start_time": 1717658765,
        "status": "upgrading",
        "targets": {
          "total": 12,
          "download_requested": ["5c5b35000001"],
          "downloading": ["5c5b35000002"],
          "downloaded": ["5c5b35000003", "5c5b35000004"],
          "scheduled": [],
          "reboot_in_progress": ["5c5b35000005"],
          "rebooted": ["5c5b35000006"],
          "upgraded": ["5c5b35000007", "5c5b35000008"],
          "failed": ["5c5b35000009"],
          "skipped": []
        }
      }
    }
  ]
}
```

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID, read-only) | Unique upgrade job UUID. Stable across polls. |
| `target_version` | string | Firmware version requested, e.g. `0.14.29411`. |
| `strategy` | string (enum) | One of `big_bang`, `canary`, `rrm`, `serial`. |
| `enable_p2p` | boolean | Whether AP-to-AP local firmware copy is allowed. |
| `force` | boolean | Force upgrade when current == target version. |
| `upgrades` | array | Zero or more per-site sub-records (see below). |

### Per-site sub-record (`upgrades[]`)

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | string (UUID) | Site this sub-record applies to. |
| `upgrade.id` | string (UUID) | Per-site sub-upgrade UUID. |
| `upgrade.start_time` | integer (epoch seconds) | When the upgrade kicked off at this site. |
| `upgrade.status` | string (enum) | One of `cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`, `upgrading`, `queued`. |
| `upgrade.targets.total` | integer | Devices in scope at this site. |
| `upgrade.targets.download_requested` | array<string> | MAC addresses cloud has asked to download firmware. |
| `upgrade.targets.downloading` | array<string> | MAC addresses currently downloading. |
| `upgrade.targets.downloaded` | array<string> | MAC addresses with firmware downloaded. |
| `upgrade.targets.scheduled` | array<string> | MAC addresses with a scheduled upgrade. |
| `upgrade.targets.reboot_in_progress` | array<string> | MAC addresses currently rebooting. |
| `upgrade.targets.rebooted` | array<string> | MAC addresses that rebooted successfully. |
| `upgrade.targets.upgraded` | array<string> | MAC addresses that completed upgrade successfully. |
| `upgrade.targets.failed` | array<string> | MAC addresses that failed to upgrade. |
| `upgrade.targets.skipped` | array<string> | MAC addresses skipped because running == target version. |

## Error responses

| Status | Meaning | MistHelper handling |
|--------|---------|---------------------|
| 400 | Bad syntax (malformed UUID) | UUID regex validation upstream catches this; if it still surfaces, log `WARNING` with sanitized message and return early. |
| 401 | Unauthorized -- token missing, expired, or revoked | Log `ERROR` "API token rejected by Mist (401). Check MIST_API_TOKEN in .env." Do NOT log the token value. Return early. |
| 403 | Permission denied -- token lacks org read scope | Log `ERROR` "Token lacks read permission on org %s (403)." Return early. |
| 404 | Upgrade UUID not found in this org | Log `WARNING` "Upgrade %s not found in org %s (404)." Return early -- no traceback per Principle III. |
| 429 | Rate limited (>5000 req/hr) | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) kicks in automatically. MistHelper retries per the standard backoff policy; no manual intervention required. Log `INFO` "Rate limited -- backoff engaged." |
| 5xx | Mist cloud transient failure | `mistapi` SDK retries per its built-in policy; on exhaustion MistHelper logs `ERROR` with `logging.exception` and returns early. |

## mistapi Python call signature

```python
import mistapi
import mistapi.api.v1.orgs.devices.upgrade  # Path-derived module

# apisession is the existing mistapi.APISession built from .env
response = mistapi.api.v1.orgs.devices.upgrade.getOrgDeviceUpgrade(
    apisession,        # mistapi.APISession -- loaded once at startup
    org_id,            # str -- Mist org UUID, validated before this call
    upgrade_id,        # str -- upgrade job UUID, validated before this call
)

# response is mistapi.APIResponse
# response.status_code -- int (200 on success)
# response.data -- dict (single object per the schema above)
# response.headers -- dict (includes rate-limit headers used by the adaptive delay system)
```

### Smoke verification (pre-implementation)

A one-line import check confirms the module path before menu wiring:

```powershell
python -c "import mistapi.api.v1.orgs.devices.upgrade as m; print(m.getOrgDeviceUpgrade)"
```

If this fails (module path drift between mistapi releases), the
implementation falls back to discovering the correct path via:

```powershell
python -c "import mistapi, pkgutil; [print(m.name) for m in pkgutil.walk_packages(mistapi.__path__, 'mistapi.') if 'upgrade' in m.name]"
```

and the task list is updated accordingly before code is written.

## Idempotency and polling guidance

This endpoint is fully idempotent. Polling the same `upgrade_id` returns
the same `id` field; status fields evolve over the upgrade lifecycle. The
MistHelper PK strategy (`composite_pk` on `(org_id, id)`) guarantees that
repeated polls upsert in place rather than accumulating duplicate rows.

The enriched doc explicitly warns: *"The upgrade may take significant
time for large device fleets; poll periodically rather than
continuously."* MistHelper does NOT implement an auto-poll loop in this
menu item. Users seeking continuous monitoring should re-invoke the menu
on their own cadence (or run it inside an external scheduler).
