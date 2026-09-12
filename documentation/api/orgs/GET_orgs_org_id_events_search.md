# searchOrgEvents

> searchOrgEvents

## HTTP

`GET /api/v1/orgs/{org_id}/events/search`

## Description

Search Org events


Supported Event Types:
- CRADLEPOINT_SYNC_FAILED
- ORG_CA_CERT_ADDED
- ORG_CA_CERT_REGENERATED

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
| type | string | No |  |  | Event type |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "title": "response_events_orgs_search",
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1688035193
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
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "org_event",
        "type": "object",
        "properties": {
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "text": {
            "type": "string",
            "examples": [
              "authentication failed, API key invalid"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "examples": [
              "CRADLEPOINT_SYNC_FAILED"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1687948793
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
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

`mistapi.api.v1.orgs.events.searchOrgEvents()`

## Usage Context

Searches device-level events across the organization.

## Gotchas

- Covers AP, switch, and gateway events.
- Time range defaults to last hour.

## Related Endpoints

- [GET_orgs_org_id_events_system_search.md](GET_orgs_org_id_events_system_search.md) — System events
- [GET_orgs_org_id_devices_events_search.md](GET_orgs_org_id_devices_events_search.md) — Device events

## MistHelper Notes

Not currently used by MistHelper directly.
