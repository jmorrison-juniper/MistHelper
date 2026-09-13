# listDeviceEventsDefinitions

> listDeviceEventsDefinitions

## HTTP

`GET /api/v1/const/device_events`

## Description

Get list of available Device Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Device Events Definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_event",
    "required": [
      "display",
      "key"
    ],
    "type": "object",
    "properties": {
      "description": {
        "type": "string"
      },
      "display": {
        "type": "string"
      },
      "example": {
        "type": "object"
      },
      "group": {
        "type": "string"
      },
      "key": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "description": "AP was assigned to a site",
        "display": "AP Assigned",
        "example": {
          "ap": "5c5b35000001",
          "audit_id": "e9a88814-fa81-5bdc-34b0-84e8735420e5",
          "org_id": "2818e386-8dec-2562-9ede-5b8a0fbbdc71",
          "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
          "timestamp": 1552408871,
          "type": "AP_ASSIGNED"
        },
        "key": "AP_ASSIGNED"
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

`mistapi.api.v1.constants.events.listDeviceEventsDefinitions()`

## Usage Context

Returns definitions of all device event types (AP, switch, gateway), including display text, descriptions, and example payloads. Use this to decode raw `type` fields from device event searches into meaningful labels for dashboards and reports.

## Gotchas

- The list includes event types for all device categories (AP, switch, gateway) in one response — filter by device type context when displaying.
- Event definitions may include device-type-specific fields that are absent for other device types.

## Related Endpoints

- [GET_const_alarm_defs.md](GET_const_alarm_defs.md) — Alarm definitions (alarms are a subset of events with severity)
- [GET_const_client_events.md](GET_const_client_events.md) — Client-side event definitions
- [GET_const_mxedge_events.md](GET_const_mxedge_events.md) — Mist Edge event definitions
- [../orgs/POST_orgs_org_id_devices_events_search.md](../orgs/GET_orgs_org_id_devices_events_search.md) — Search actual device events

## MistHelper Notes

Not currently used by MistHelper as a constants lookup. Menu **2** (`OrgAlarmEventExporter.device_events`) exports device events whose `type` values correspond to definitions returned here.
