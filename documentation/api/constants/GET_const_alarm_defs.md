# listAlarmDefinitions

> listAlarmDefinitions

## HTTP

`GET /api/v1/const/alarm_defs`

## Description

Get List of brief definitions of all the supported alarm types. The example field contains an example payload as you would receive in the alarm webhook output.
HA cluster node names will be specified in the `node` field, if applicable.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Alarm Definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_alarm_definition",
    "required": [
      "display",
      "fields",
      "group",
      "key",
      "severity"
    ],
    "type": "object",
    "properties": {
      "display": {
        "type": "string",
        "description": "Description of the alarm type",
        "examples": [
          "Device offline"
        ]
      },
      "example": {
        "type": "object",
        "examples": [
          {
            "aps": [
              "d420b02000fa"
            ],
            "count": 1,
            "group": "infrastructure",
            "hostnames": [
              "Vendor_AP2"
            ],
            "id": "f70c308f-7007-4866-9ecd-0d01842979ea",
            "last_seen": 1629753888,
            "org_id": "09dac91f-6e73-4100-89f7-698e0fafbb1b",
            "severity": "warn",
            "site_id": "dcfb31a1-d615-4361-8c95-b9dde05aa704",
            "timestamp": 1629753888,
            "type": "device_down"
          }
        ]
      },
      "fields": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of fields available in an alarm details payload (in REST APIs & Webhooks); e.g. `aps`, `switches`, `gateways`, `hostnames`, `ssids`, `bssids`",
        "examples": [
          [
            "aps",
            "hostnames"
          ]
        ]
      },
      "group": {
        "type": "string",
        "description": "Group to which the alarm belongs",
        "examples": [
          "infrastructure"
        ]
      },
      "key": {
        "type": "string",
        "description": "Key name of the alarm type",
        "examples": [
          "device_down"
        ]
      },
      "marvis_suggestion_category": {
        "type": "string",
        "description": "Marvis defined category to which the alarm belongs"
      },
      "severity": {
        "type": "string",
        "description": "Severity of the alarm",
        "examples": [
          "warn"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "Device offline",
        "example": {
          "aps": [
            "d420b02000fa"
          ],
          "count": 1,
          "group": "infrastructure",
          "hostnames": [
            "Vendor_AP2"
          ],
          "id": "e70c308f-7007-4866-9ecd-0d01842979ea",
          "last_seen": 1629753888,
          "org_id": "09dac91f-6e73-4100-89f7-698e0fafbb1b",
          "severity": "warn",
          "site_id": "dcfb31a1-d615-4361-8c95-b9dde05aa704",
          "timestamp": 1629753888,
          "type": "device_down"
        },
        "fields": [
          "aps",
          "hostnames"
        ],
        "group": "infrastructure",
        "key": "device_down",
        "marvis_suggestion_category": "string",
        "severity": "warn"
      }
    ]
  ]
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

`mistapi.api.v1.constants.events.listAlarmDefinitions()`

## Usage Context

Returns the master list of all alarm types the Mist platform can generate, including display names, severity levels, required fields, and example webhook payloads. Use this to build alarm dashboards, map alarm `key` values to human-readable labels, or validate incoming webhook payloads against known alarm types.

## Gotchas

- The response is a flat array (not paginated), but can be large as it covers all alarm types across device categories.
- HA cluster alarms include a `node` field that non-HA alarms omit — do not assume uniform schema.
- Alarm `key` values are stable identifiers, but `display` text may change between API versions.

## Related Endpoints

- [GET_const_device_events.md](GET_const_device_events.md) — Device event type definitions (events vs alarms)
- [GET_const_client_events.md](GET_const_client_events.md) — Client event type definitions
- [GET_const_system_events.md](GET_const_system_events.md) — System-level event definitions
- [../orgs/GET_orgs_org_id_alarmtemplates.md](../orgs/GET_orgs_org_id_alarmtemplates.md) — Alarm rule templates that reference these definitions

## MistHelper Notes

Not currently used by MistHelper directly. However, Menu **1** (`OrgAlarmEventExporter.alarms`) exports live alarms whose `type` fields correspond to the `key` values returned here.
