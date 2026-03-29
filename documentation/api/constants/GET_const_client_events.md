# listClientEventsDefinitions

> listClientEventsDefinitions

## HTTP

`GET /api/v1/const/client_events`

## Description

Get List of List of available Client Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Client Events definitions

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
        "display": "11r Association",
        "key": "CLIENT_AUTH_ASSOCIATION_11R"
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

`mistapi.api.v1.constants.events.listClientEventsDefinitions()`

## Usage Context

Returns definitions of all client event types (wireless and wired), including display names, descriptions, and example payloads. Use this to map raw event `type` values from client event queries into human-readable labels for reports or troubleshooting dashboards.

## Gotchas

- Client events cover both wireless (802.11) and wired (802.1X/MAB) event types — filter by relevant category if you only need one.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_events.md](GET_const_device_events.md) — Device-side event definitions (complements client-side view)
- [GET_const_nac_events.md](GET_const_nac_events.md) — NAC-specific event definitions
- [../sites/GET_sites_site_id_clients_events_search.md](../sites/GET_sites_site_id_clients_events_search.md) — Search actual client events at a site

## MistHelper Notes

Not currently used by MistHelper directly. Related event data is exported via Menu **2** (`OrgAlarmEventExporter.device_events`).
