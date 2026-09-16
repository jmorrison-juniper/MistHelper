# listMarvisClientEventsDefinitions

> listMarvisClientEventsDefinitions

## HTTP

`GET /api/v1/const/marvisclient_events`

## Description

Return Marvis Client event type definitions used by the Marvis Client event search and count APIs.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Marvis Client event type definitions

```json
{
  "description": "Marvis Client event type definitions returned by the constants API",
  "items": {
    "additionalProperties": false,
    "description": "A Marvis Client event type definition",
    "properties": {
      "display": {
        "description": "Human-readable name for this Marvis Client event type",
        "examples": [
          "Marvis Client Roamed"
        ],
        "type": "string"
      },
      "key": {
        "description": "Event type key used in Marvis Client event search and count APIs",
        "examples": [
          "MARVISCLIENT_ROAMED"
        ],
        "type": "string"
      }
    },
    "type": "object"
  },
  "type": "array"
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

`mistapi.api.v1.const.marvisclient_events.listMarvisClientEventsDefinitions()`

## Usage Context

Use this endpoint to read the resource at `/api/v1/const/marvisclient_events`.
Common use cases:

- Use it when you need to return Marvis Client event type definitions used by the Marvis Client event search and count APIs.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `listMarvisClientEventsDefinitions(mist_session: mistapi.__api_session.APISession) -> mistapi.__api_response.APIResponse`.

## Gotchas

- No known gotchas beyond Mist API authentication and rate limits.

## Related Endpoints

- [GET_const_alarm_defs.md](GET_const_alarm_defs.md) -- listAlarmDefinitions uses `GET /api/v1/const/alarm_defs`.
- [GET_const_applications.md](GET_const_applications.md) -- listApplications uses `GET /api/v1/const/applications`.
- [GET_const_app_categories.md](GET_const_app_categories.md) -- listAppCategoryDefinitions uses `GET /api/v1/const/app_categories`.

## MistHelper Notes

MistHelper does not currently call `listMarvisClientEventsDefinitions`.
Verification source: `git grep -n "listMarvisClientEventsDefinitions" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
