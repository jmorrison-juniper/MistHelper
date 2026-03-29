# listSiteCurrentRrmNeighbors

> listSiteCurrentRrmNeighbors

## HTTP

`GET /api/v1/sites/{site_id}/rrm/neighbors/band/{band}`

## Description

List Current RRM observed neighbors

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| band | string | Yes | 802.11 Band |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string",
      "description": "Link to query next set of results. value is null if no next page exists."
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "rrm_neighbors",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "5c5b35000001"
            ]
          },
          "neighbors": {
            "type": "array",
            "items": {
              "title": "rrm_neighbors_neighbor",
              "type": "object",
              "properties": {
                "mac": {
                  "type": "string",
                  "examples": [
                    "5c5b35000311"
                  ]
                },
                "rssi": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    -66
                  ]
                }
              }
            },
            "description": ""
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.rrm.listSiteCurrentRrmNeighbors()`

## Usage Context

Retrieves RF neighbor relationships between APs for a specific band (2.4GHz/5GHz/6GHz). Shows which APs can hear each other.

## Gotchas

- The `band` path parameter must be one of: `24`, `5`, `6`.
- Neighbor data is critical for RRM optimization and co-channel interference analysis.

## Related Endpoints

- [GET_sites_site_id_rrm_current.md](GET_sites_site_id_rrm_current.md) — Current RRM assignments
- [GET_sites_site_id_rrm_events.md](GET_sites_site_id_rrm_events.md) — RRM events

## MistHelper Notes

Not currently used by MistHelper directly.
