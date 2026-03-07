# updateSiteWxTag

> updateSiteWxTag

## HTTP

`PUT /api/v1/sites/{site_id}/wxtags/{wxtag_id}`

## Description

Update Site WxTag

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| wxtag_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "last_ips": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "readOnly": true
    },
    "mac": {
      "type": [
        "string",
        "null"
      ],
      "description": "If `type`==`client`, Client MAC Address"
    },
    "match": {
      "type": "string",
      "description": "required if `type`==`match`. enum: `ap_id`, `app`, `asset_mac`, `client_mac`, `hostname`, `ip_range_subnet`, `port`, `psk_name`, `psk_role`, `radius_attr`, `radius_class`, `radius_group`, `radius_username`, `sdkclient_uuid`, `wlan_id`"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "The name"
    },
    "op": {
      "type": "string",
      "description": "required if `type`==`match`, type of tag (inclusive/exclusive). enum: `in`, `not_in`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "resource_mac": {
      "type": [
        "string",
        "null"
      ]
    },
    "services": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "specs": {
      "type": "array",
      "items": {
        "title": "wxlan_tag_spec",
        "type": "object",
        "properties": {
          "port_range": {
            "type": "string",
            "description": "Matched destination port, \"0\" means any",
            "default": "0"
          },
          "protocol": {
            "type": "string",
            "description": "tcp / udp / icmp / gre / any / \":protocol_number\", `protocol_number` is between 1-254",
            "default": "any"
          },
          "subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Matched destination subnets and/or IP Addresses",
            "default": [],
            "examples": [
              [
                "0.0.0.0/0"
              ]
            ]
          }
        }
      },
      "description": "If `type`==`spec`"
    },
    "subnet": {
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "enum: `client`, `match`, `resource`, `spec`, `subnet`, `vlan`"
    },
    "values": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required if `type`==`match` and\n  * `match`==`ap_id`: list of AP IDs\n  * `match`==`app`: list of Application Names\n  * `match`==`asset_mac`: list of Asset MAC Addresses\n  * `match`==`client_mac`: list of Client MAC Addresses\n  * `match`==`hostname`: list of Resources Hostnames\n  * `match`==`ip_range_subnet`: list of IP Addresses and/or CIDRs\n  * `match`==`psk_name`: list of PSK Names\n  * `match`==`psk_role`: list of PSK Roles\n  * `match`==`port`: list of Ports or Port Ranges\n  * `match`==`radius_attr`: list of RADIUS Attributes. The values are [ \"6=1\", \"26=10.2.3.4\" ], this support other RADIUS attributes where we know the type\n  * `match`==`radius_class`: list of RADIUS Classes. This matches the ATTR-Class(25)\n  * `match`==`radius_group`: list of RADIUS Groups. This is a smart tag that matches RADIUS-Filter-ID, Airespace-ACL-Name (VendorID=14179, VendorType=6) / Aruba-User-Role (VendorID=14823, VendorType=1)\n  * `match`==`radius_username`: list of RADIUS Usernames. This matches the ATTR-User-Name(1)\n  * `match`==`sdkclient_uuid`: list of SDK UUIDs\n  * `match`==`wlan_id`: list of WLAN IDs\n\n**Notes**:\nVariables are not allowed"
    },
    "vlan_id": {
      "type": "object",
      "description": "If `type`==`vlan_id`, VLAN ID or variable"
    }
  },
  "required": [
    "name",
    "type"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "last_ips": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "readOnly": true
    },
    "mac": {
      "type": [
        "string",
        "null"
      ],
      "description": "If `type`==`client`, Client MAC Address"
    },
    "match": {
      "type": "string",
      "description": "required if `type`==`match`. enum: `ap_id`, `app`, `asset_mac`, `client_mac`, `hostname`, `ip_range_subnet`, `port`, `psk_name`, `psk_role`, `radius_attr`, `radius_class`, `radius_group`, `radius_username`, `sdkclient_uuid`, `wlan_id`"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "The name"
    },
    "op": {
      "type": "string",
      "description": "required if `type`==`match`, type of tag (inclusive/exclusive). enum: `in`, `not_in`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "resource_mac": {
      "type": [
        "string",
        "null"
      ]
    },
    "services": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "specs": {
      "type": "array",
      "items": {
        "title": "wxlan_tag_spec",
        "type": "object",
        "properties": {
          "port_range": {
            "type": "string",
            "description": "Matched destination port, \"0\" means any",
            "default": "0"
          },
          "protocol": {
            "type": "string",
            "description": "tcp / udp / icmp / gre / any / \":protocol_number\", `protocol_number` is between 1-254",
            "default": "any"
          },
          "subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Matched destination subnets and/or IP Addresses",
            "default": [],
            "examples": [
              [
                "0.0.0.0/0"
              ]
            ]
          }
        }
      },
      "description": "If `type`==`spec`"
    },
    "subnet": {
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "enum: `client`, `match`, `resource`, `spec`, `subnet`, `vlan`"
    },
    "values": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required if `type`==`match` and\n  * `match`==`ap_id`: list of AP IDs\n  * `match`==`app`: list of Application Names\n  * `match`==`asset_mac`: list of Asset MAC Addresses\n  * `match`==`client_mac`: list of Client MAC Addresses\n  * `match`==`hostname`: list of Resources Hostnames\n  * `match`==`ip_range_subnet`: list of IP Addresses and/or CIDRs\n  * `match`==`psk_name`: list of PSK Names\n  * `match`==`psk_role`: list of PSK Roles\n  * `match`==`port`: list of Ports or Port Ranges\n  * `match`==`radius_attr`: list of RADIUS Attributes. The values are [ \"6=1\", \"26=10.2.3.4\" ], this support other RADIUS attributes where we know the type\n  * `match`==`radius_class`: list of RADIUS Classes. This matches the ATTR-Class(25)\n  * `match`==`radius_group`: list of RADIUS Groups. This is a smart tag that matches RADIUS-Filter-ID, Airespace-ACL-Name (VendorID=14179, VendorType=6) / Aruba-User-Role (VendorID=14823, VendorType=1)\n  * `match`==`radius_username`: list of RADIUS Usernames. This matches the ATTR-User-Name(1)\n  * `match`==`sdkclient_uuid`: list of SDK UUIDs\n  * `match`==`wlan_id`: list of WLAN IDs\n\n**Notes**:\nVariables are not allowed"
    },
    "vlan_id": {
      "type": "object",
      "description": "If `type`==`vlan_id`, VLAN ID or variable"
    }
  },
  "required": [
    "name",
    "type"
  ],
  "description": "WxLAN Tag\n  * type:\n    * client: created manually (e.g. on wireless client table, when they spot a device of interest, they can create a wxlan tag for it\n    * resource: created automatically when we discover a network resource\n    * subnet: create automatically when a subnet is discovered\n  * match:\n    * wlan_id, ap_id: values are a list of Wlan / Device ids\n    * client_mac: values are a list of MAC addresses\n  * radius_group: this is a smart tag that matches RADIUS-Filter-ID, Airespace-ACL-Name (VendorID=14179, VendorType=6) / Aruba-User-Role (VendorID=14823, VendorType=1)\n  * radius_username: this matches the ATTR-User-Name(1)\n  * radius_class: the matches the ATTR-Class(25)\n  * radius_attr: the values are [ \"6=1\" , \"26=10.2.3.4\" ], this support other RADIUS attributes where we know the type\n  * radius_vendor: the values are [ \"14179.10=1\" , \"14178.16=1.2.3.4\" ], this matches vendor attributes and will be dynamically evaluated"
}
```

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

`mistapi.api.v1.sites.wxtags.updateSiteWxTag()`

## Usage Context

Updates an existing WxLAN tag's properties.

## Gotchas

- Modifying tags used in active WxRules affects traffic matching immediately.

## Related Endpoints

- [GET_sites_site_id_wxtags_wxtag_id.md](GET_sites_site_id_wxtags_wxtag_id.md) — Tag details
- [GET_sites_site_id_wxtags.md](GET_sites_site_id_wxtags.md) — List tags

## MistHelper Notes

Not currently used by MistHelper directly.
