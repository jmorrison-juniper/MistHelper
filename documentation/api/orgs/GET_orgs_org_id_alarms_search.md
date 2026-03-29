# searchOrgAlarms

> searchOrgAlarms

## HTTP

`GET /api/v1/orgs/{org_id}/alarms/search`

## Description

Search Org Alarms

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| site_id | string | No |  |  | Site ID |
| group | string | No |  |  | Alarm group. enum: `infrastructure`, `marvis`, `security`.  The `marvis` group is used to retrieve AI-driven network issue detections.  Known Marvis alarm types include: `bad_cable`, `bad_wan_uplink`, `dns_failure`,  `arp_failure`, `auth_failure`, `dhcp_failure`, `missing_vlan`,  `negotiation_mismatch`, `port_flap`. Results include resolution status  (`status`, `resolved_time`) and affected entity details." |
| severity | string | No |  |  | Severity of the alarm. enum: `critical`, `info`, `warn` |
| type | string | No |  |  | Type of the alarm. Accepts multiple values separated by comma. Use [List Alarm Definitions](/#operations/listAlarmDefinitions) to get the list of possible alarm types. |
| ack_admin_name | string | No |  |  | Name of the admins who have acked the alarms; accepts multiple values separated by comma |
| acked | boolean | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "alarm_search_result",
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
  ],
  "type": "object",
  "properties": {
    "component": {
      "type": "string",
      "description": "Component of the alarm"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1711035686
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string",
      "examples": [
        "/api/v1/orgs/b3b9f5e6-67b1-4112-9b4c-6824c565eaeb/alarms/search?end=1711035686&limit=10&search_after=%5B1711031354000%2C+%2256bfa7af-b2db-43ee-a4c8-9b820bbba0e1%22%5D&start=1710949286"
      ]
    },
    "page": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "results": {
      "type": "array",
      "items": {
        "title": "alarm",
        "required": [
          "count",
          "group",
          "id",
          "last_seen",
          "severity",
          "timestamp",
          "type"
        ],
        "type": "object",
        "properties": {
          "ack_admin_id": {
            "type": "string",
            "description": "UUID of the admin who acked the alarm",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "456b7016-a916-a4b1-78dd-72b947c152b7"
            ]
          },
          "ack_admin_name": {
            "type": "string",
            "description": "Name & Email ID of the admin who acked the alarm",
            "examples": [
              "Joe"
            ]
          },
          "acked": {
            "type": "boolean",
            "description": "Whether the alarm is acked or not",
            "examples": [
              true
            ]
          },
          "acked_time": {
            "type": "integer",
            "description": "Epoch (seconds) when the alarm was acked",
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              1711031352
            ]
          },
          "aps": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "additional information: List of MACs of the APs",
            "examples": [
              [
                "ffeeddccbbaa",
                "ffeeddccbbab"
              ]
            ]
          },
          "bssids": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of BSSIDs"
          },
          "count": {
            "type": "integer",
            "description": "Number of incident within an alarm window",
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              2
            ]
          },
          "gateways": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "additional information: List of MACs of the gateways",
            "examples": [
              [
                "ffeeddccbbaa",
                "ffeeddccbbab"
              ]
            ]
          },
          "group": {
            "type": "string",
            "description": "Group of the alarm",
            "examples": [
              "security"
            ]
          },
          "hostnames": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "additional information: List of Hostnames of the devices (AP/Switch/Gateway)",
            "examples": [
              [
                "MC_DavidL",
                "MCM_AP_33_Nishant"
              ]
            ]
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
          "last_seen": {
            "type": "number",
            "description": "Epoch (seconds) of the last incident/alarm within an alarm window",
            "readOnly": true,
            "examples": [
              1711031774
            ]
          },
          "note": {
            "type": "string",
            "description": "Text describing the alarm"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "resolved_time": {
            "type": "integer",
            "description": "Epoch (seconds) of the resolved_time for the alarm",
            "contentEncoding": "int32"
          },
          "severity": {
            "type": "string",
            "description": "Severity of the alarm",
            "examples": [
              "critical"
            ]
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "ssids": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of SSIDs"
          },
          "status": {
            "type": "string",
            "description": "enum: `open`, `resolved`"
          },
          "switches": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "additional information: List of MACs of the switches",
            "examples": [
              [
                "ffeeddccbbaa",
                "ffeeddccbbab"
              ]
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Key-name of the alarm type",
            "readOnly": true,
            "examples": [
              "rogue_client"
            ]
          }
        },
        "description": "Additional information per alarm type"
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1710949286
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        232
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.alarms.searchOrgAlarms()`

## Usage Context

Searches organization alarms with filtering on type, severity, time range, and more.

## Gotchas

- Time range defaults to last hour if not specified.
- Large orgs may hit rate limits with broad searches.

## Related Endpoints

- [GET_orgs_org_id_alarms_count.md](GET_orgs_org_id_alarms_count.md) — Count alarms
- [POST_orgs_org_id_alarms_ack.md](POST_orgs_org_id_alarms_ack.md) — Acknowledge alarms

## MistHelper Notes

Used by MistHelper via `searchOrgAlarms` in Menu 1 (Search Org Alarms).
