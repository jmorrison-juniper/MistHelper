# updateSiteVirtualChassisMember

> updateSiteVirtualChassisMember

## HTTP

`PUT /api/v1/sites/{site_id}/devices/{device_id}/vc`

## Description

The VC creation and adding member switch API will update the device' s virtual chassis config which is applied after VC is formed to create JUNOS pre-provisioned virtual chassis configuration.

**Note:** Update Device's VC config can achieve similar purpose by directly modifying current virtual_chassis config. However, it cannot fulfill requests to enabling vc_ports on new members that are yet to belong to current VC.


## Change to use preprovisioned VC
To switch the VC to use preprovisioned VC, enable preprovisioned in virtual_chassis config. Both vc_role master and backup will be matched to routing-engine role in Junos preprovisioned VC config.

In this config, fpc0 has to be the same as the mac of device_id. Use renumber if you want to replace fpc0 which involves device_id change.

**Notice:** to configure preprovisioned VC, every member of the VC must be in the inventory.

## Add new members
For models (e.g. EX4300 and up) having dedicated VC ports, it is easier to add new member switches into a VC by just connecting cables with the dedicated VC ports. Cloud will detect the new members and update the inventory.

For EX2300 VC, adding new members requires to follow the procedures below:
1. Powering on the new member switches and ensuring cables are not connected to any VC ports.
2. Claim or adopt all new member switches under the VC's organization Inventory
3. Assign all new member switches to the same Site as the VC
4. Invoke vc command to add switches to the VC.
5. Connect the cables to the VC ports for these switches
6. After a while, the Org's Inventory shows that new switches has been added into the VC.

## Removing member switch
To remove a member switch from the VC, following the procedures below:

1. Ensuring the VC is connected to the cloud first
2. Unplug the cable from the VC port of the switch
3. Waiting for the VC state (vc_state) of this switch is changed to not-present
4. Invoke update_vc with remove to remove this switch from the VC
5. The Org's Inventory shows the switch is removed.

Please notice that member ID 0 (fpc0) cannot be removed. When a VC has two switches left, unplugging the cable may result in the situation that fpc0 becomes a line card (LC). When this situation is happening, please re-plug in the cable, wait for both switches becoming present (show virtual-chassis) and then removing the cable again.

## Renumber a member switch
When a member switch doesn' t work properly and needed to be replaced, the renumber API could be used. The following two types of renumber are supported:

1. Replace a non-fpc0 member switch
2. Replace fpc0. When fpc0 is replaced, PAPI device config and JUNOS config will be both updated.

For renumber to work, the following procedures are needed: 
1. Ensuring the VC is connected to the cloud and the state of the member switch to be replaced must be non present. 
2. Adding the new member switch to the VC 
3. Waiting for the VC state (vc_state) of this VC to be updated to API server 
4. Invoke vc with renumber to replace\ the new member switch from fpc X to

## Perprovision VC members
By specifying "preprovision" op, you can convert the current VC to pre-provisioned mode, update VC members as well as specify vc_ports when adding new members for device models without dedicated vc ports. Use renumber for fpc0 replacement which involves device_id change.

Note: 
1. vc_ports is used for adding new members and not needed if 
  * the device model has dedicated vc ports, or 
  * no new member is added 
2. New VC members to be added should exist in the same Site as the VC

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "member": {
      "type": "integer",
      "description": "Only if `op`==`renumber`",
      "contentEncoding": "int32"
    },
    "members": {
      "type": "array",
      "items": {
        "title": "virtual_chassis_member_update",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "description": "Required if `op`==`add` or `op`==`preprovision`."
          },
          "member": {
            "type": "integer",
            "description": "Required if `op`==`remove`",
            "contentEncoding": "int32"
          },
          "member_id": {
            "type": "integer",
            "description": "Required if `op`==`preprovision`. Optional if `op`==`add`",
            "contentEncoding": "int32"
          },
          "vc_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Required if `op`==`add` or `op`==`preprovision`"
          },
          "vc_role": {
            "type": "string",
            "description": "Required if `op`==`add` or `op`==`preprovision`. enum: `backup`, `linecard`, `master`"
          }
        }
      },
      "description": ""
    },
    "new-member": {
      "type": "integer",
      "description": "Only if `op`==`renumber`",
      "contentEncoding": "int32"
    },
    "op": {
      "type": "string",
      "description": "enum: `add`, `preprovision`, `remove`, `renumber`"
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.updateSiteVirtualChassisMember()`

## Usage Context

Updates the Virtual Chassis configuration for a switch device.

## Gotchas

- VC changes may cause a device reboot. Execute during maintenance windows.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — VC operations
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device details

## MistHelper Notes

Used by MistHelper for Virtual Chassis operations in Menus 94, 95, 96.
