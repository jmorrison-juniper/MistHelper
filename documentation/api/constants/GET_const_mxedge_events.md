# listMxEdgeEventsDefinitions

> listMxEdgeEventsDefinitions

## HTTP

`GET /api/v1/const/mxedge_events`

## Description

Get List of available MX Edge Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of MxEdge Events definitions

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
        "description": "Config change on ME was triggered as a result of change made by user",
        "display": "ME Config changed by user",
        "example": {
          "audit_id": "e9a88814-fa81-5bdc-34b0-84e8735420e5",
          "mxcluster_id": "ed4665ed-c9ad-4835-8ca5-dda642765ad3",
          "mxedge_id": "387804a7-3474-85ce-15a2-f9a9684c9c9",
          "org_id": "2818e386-8dec-2562-9ede-5b8a0fbbdc71",
          "service": "mxagent",
          "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
          "timestamp": 1552408871,
          "type": "ME_CONFIG_CHANGED_BY_USER"
        },
        "key": "ME_CONFIG_CHANGED_BY_USER"
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

`mistapi.api.v1.constants.events.listMxEdgeEventsDefinitions()`

## Usage Context

Returns definitions of all Mist Edge (mxedge) event types, including display names and example payloads. Use this to interpret event data from Mist Edge appliances deployed for tunnel termination, edge computing, or local breakout.

## Gotchas

- Mist Edge events are separate from standard device events — do not assume the same `type` values.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_events.md](GET_const_device_events.md) — Standard device event definitions
- [GET_const_mxedge_models.md](GET_const_mxedge_models.md) — Mist Edge hardware model definitions
- [../orgs/GET_orgs_org_id_mxedges.md](../orgs/GET_orgs_org_id_mxedges.md) — List Mist Edge appliances in an org

## MistHelper Notes

Not currently used by MistHelper directly.
