# getOrgOtherDeviceStats

> getOrgOtherDeviceStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/otherdevices/{device_mac}`

## Description

Get Otherdevice Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "cached_stats": {
      "type": "boolean"
    },
    "config_status": {
      "type": "string",
      "examples": [
        "synced"
      ]
    },
    "connected_devices": {
      "type": "object",
      "additionalProperties": {
        "title": "stats_device_other_connected_device",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "020001abcdef"
            ]
          },
          "name": {
            "type": "string",
            "examples": [
              "DNT-NTR-GWE"
            ]
          },
          "port_id": {
            "type": "string",
            "examples": [
              "ge-0/0/1"
            ]
          },
          "type": {
            "type": "string",
            "examples": [
              "gateway"
            ]
          }
        }
      },
      "description": "Property key is the connected device MAC Address"
    },
    "interfaces": {
      "type": "object",
      "additionalProperties": {
        "title": "stats_device_other_interface",
        "type": "object",
        "properties": {
          "bytes_in": {
            "type": "integer",
            "contentEncoding": "int64",
            "examples": [
              5623096929
            ]
          },
          "bytes_out": {
            "type": "integer",
            "contentEncoding": "int64",
            "examples": [
              12372750366
            ]
          },
          "carrier": {
            "type": "string",
            "examples": [
              "Orange"
            ]
          },
          "imei": {
            "type": "string",
            "examples": [
              "866401234567893"
            ]
          },
          "imsi": {
            "type": "string",
            "examples": [
              "2080101234567893"
            ]
          },
          "ip": {
            "type": "string",
            "examples": [
              "10.134.237.57"
            ]
          },
          "link": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "mode": {
            "type": "string",
            "examples": [
              "wan"
            ]
          },
          "mtu": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              1500
            ]
          },
          "rsrp": {
            "type": "number",
            "examples": [
              -108
            ]
          },
          "rsrq": {
            "type": "number",
            "examples": [
              -14
            ]
          },
          "rssi": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              -74
            ]
          },
          "service_mode": {
            "type": "string",
            "examples": [
              "5G NSA"
            ]
          },
          "sinr": {
            "type": "number",
            "examples": [
              -1.2
            ]
          },
          "state": {
            "type": "string",
            "examples": [
              "READY"
            ]
          },
          "type": {
            "type": "string",
            "examples": [
              "mdm"
            ]
          },
          "uptime": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              2095779
            ]
          }
        }
      },
      "description": "Property key is the interface name"
    },
    "last_config": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1675392788
      ]
    },
    "last_seen": {
      "type": [
        "number",
        "null"
      ],
      "description": "Last seen timestamp",
      "readOnly": true,
      "examples": [
        1470417522
      ]
    },
    "lldp_enabled": {
      "type": "boolean"
    },
    "mac": {
      "type": "string",
      "examples": [
        "5c5b35000018"
      ]
    },
    "status": {
      "type": "string",
      "examples": [
        "online"
      ]
    },
    "uptime": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        20296
      ]
    },
    "vendor": {
      "type": "string",
      "examples": [
        "cradlepoint"
      ]
    },
    "vendor_specific": {
      "type": "object",
      "properties": {
        "interfaces": {
          "type": "object",
          "additionalProperties": {
            "title": "stats_device_other_vendor_specific_port",
            "type": "object",
            "properties": {
              "bytes_in": {
                "type": "integer",
                "contentEncoding": "int64",
                "examples": [
                  5623096929
                ]
              },
              "bytes_out": {
                "type": "integer",
                "contentEncoding": "int64",
                "examples": [
                  12372750366
                ]
              },
              "carrier": {
                "type": "string",
                "examples": [
                  "Orange"
                ]
              },
              "display_name": {
                "type": "string",
                "examples": [
                  "mdm-4d0e073b"
                ]
              },
              "imei": {
                "type": "string",
                "examples": [
                  "866401234567893"
                ]
              },
              "imsi": {
                "type": "string",
                "examples": [
                  "2080101234567893"
                ]
              },
              "ip": {
                "type": "string",
                "examples": [
                  "10.134.237.57"
                ]
              },
              "link": {
                "type": "boolean",
                "examples": [
                  true
                ]
              },
              "mode": {
                "type": "string",
                "examples": [
                  "wan"
                ]
              },
              "mtu": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1500
                ]
              },
              "port_parent": {
                "type": "string",
                "examples": [
                  "mdm"
                ]
              },
              "rsrp": {
                "type": "number",
                "examples": [
                  -108
                ]
              },
              "rsrq": {
                "type": "number",
                "examples": [
                  -14
                ]
              },
              "rssi": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  -74
                ]
              },
              "service_mode": {
                "type": "string",
                "examples": [
                  "5G NSA"
                ]
              },
              "sinr": {
                "type": "number",
                "examples": [
                  -1.2
                ]
              },
              "state": {
                "type": "string",
                "examples": [
                  "READY"
                ]
              },
              "type": {
                "type": "string",
                "examples": [
                  "mdm"
                ]
              },
              "uptime": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  2095779
                ]
              }
            }
          },
          "examples": [
            {
              "mdm-4d0e073b": {
                "bytes_in": 5623096929,
                "bytes_out": 12372750366,
                "carrier": "Orange",
                "imei": "866401234567893",
                "imsi": "2080101234567893",
                "ip": "10.134.237.57",
                "link": true,
                "mode": "wan",
                "rsrp": -108,
                "rsrq": -14,
                "rssi": -74,
                "service_mode": "5G NSA",
                "sinr": -1.2,
                "state": "READY",
                "type": "mdm",
                "uptime": 2095779
              }
            }
          ]
        },
        "target_version": {
          "type": "string",
          "examples": [
            "7.23.40"
          ]
        }
      },
      "description": "When `vendor`==`cradlepoint`"
    },
    "version": {
      "type": "string",
      "examples": [
        "7.22.70"
      ]
    }
  }
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

`mistapi.api.v1.orgs.stats_-_other_devices.getOrgOtherDeviceStats()`

## Usage Context

Retrieves statistics for a specific non-Juniper device by MAC address.

## Gotchas

- Other devices are third-party devices discovered on the network.

## Related Endpoints

- [GET_orgs_org_id_otherdevices.md](GET_orgs_org_id_otherdevices.md) — List other devices
- [GET_orgs_org_id_stats_devices.md](GET_orgs_org_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
