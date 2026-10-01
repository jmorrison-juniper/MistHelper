# Operation Contract: RMA Device Replacement

## Menu contract

- Menu number: `287`.
- Category: `destructive`.
- Handler: `src.inventory.device_replace.operation.DeviceReplaceOperation.run`.
- Confirmation word: `REPLACE`.
- Dry-run flag: `--dry-run` in process arguments.

## Mist API contract

### Inventory read

`GET /api/v1/orgs/{org_id}/inventory`

The client calls `mistapi.api.v1.orgs.inventory.getOrgInventory(apisession, org_id, limit=1000)`.

### Device backup read

`GET /api/v1/sites/{site_id}/devices/{device_id}`

The client calls `mistapi.api.v1.sites.devices.getSiteDevice(apisession, site_id, device_id)`.

### Replacement request

`POST /api/v1/orgs/{org_id}/inventory/replace`

The client calls `mistapi.api.v1.orgs.inventory.replaceOrgDevices(apisession, org_id, body)`.

Required body shape:

```json
{
  "site_id": "site-id",
  "mac": "old-device-mac",
  "inventory_mac": "new-device-mac",
  "discard": []
}
```

## File contract

- Backups are JSON files under `data/rma_backups/`.
- The operation log is `data/DeviceReplaceLog.csv`.
- The log row includes old MAC, new MAC, and result.

## Safety contract

The operation must not call `replaceOrgDevices` unless all conditions are true:

1. The old device has a `site_id` and a device `id`.
2. The replacement device is unassigned.
3. The old and new device types match.
4. The old configuration backup file exists.
5. The operator typed `REPLACE`.
6. `--dry-run` is not active.
