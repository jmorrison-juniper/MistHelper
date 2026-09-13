# listSystemEventsDefinitions

> listSystemEventsDefinitions

## HTTP

`GET /api/v1/const/system_events`

## Description

Get List of List of available System Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of System Events definitions

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
        "display": "AP Disconnect",
        "group": "ap_health",
        "key": "ap_disconnected"
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

`mistapi.api.v1.constants.events.listSystemEventsDefinitions()`

## Usage Context

Returns definitions of system-level event types that cover platform-wide operations such as configuration changes, license events, and administrative actions. Use this to decode `type` values from audit logs and system event searches.

## Gotchas

- System events overlap with audit logs conceptually but have different schemas — system events are platform-generated, audit logs are user-action-generated.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_alarm_defs.md](GET_const_alarm_defs.md) — Alarm definitions (alarms may be triggered by system events)
- [GET_const_device_events.md](GET_const_device_events.md) — Device-specific event definitions
- [../orgs/GET_orgs_org_id_logs.md](../orgs/GET_orgs_org_id_logs.md) — Org audit logs (user-initiated actions)

## MistHelper Notes

Not currently used by MistHelper directly. Related audit log data is exported via Menu **3** (`OrgExportUtils.audit_logs`).
