# getSiteDefaultPlfForModels

> getSiteDefaultPlfForModels

## HTTP

`GET /api/v1/sites/{site_id}/location/ml/defaults`

## Description

Get Default PLF for Models

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "type": "object"
  },
  "description": "",
  "examples": [
    [
      {
        "current": {
          "Android": {
            "completed": 36,
            "int": -6,
            "level": 3,
            "ple": -3,
            "quality": "4",
            "src": "device",
            "timestamp": 1442854794
          },
          "iOS": {
            "completed": 16,
            "int": -6,
            "level": 6,
            "ple": -3,
            "quality": "2",
            "src": "default",
            "timestamp": 1442854704
          },
          "iPod": {
            "int": -10,
            "overwrite": true,
            "ple": -5,
            "src": "overwrite"
          }
        },
        "device_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
      },
      {
        "beacon_id": "7913f032-aab4-c3ae-e83e-5a2756ef4d40",
        "current": {
          "iOS": {
            "completed": 16,
            "int": -6,
            "level": 6,
            "ple": -3,
            "quality": "last",
            "src": "device",
            "timestamp": 1442854704
          }
        }
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

`mistapi.api.v1.sites.location.getSiteDefaultPlfForModels()`

## Usage Context

Retrieves the default ML parameters for location services at a site. Shows baseline configuration before customization.

## Gotchas

- Defaults are a starting point. Site-specific tuning via calibration overrides these values.

## Related Endpoints

- [GET_sites_site_id_location_ml_current.md](GET_sites_site_id_location_ml_current.md) — Current ML state
- [GET_sites_site_id_location_coverage.md](GET_sites_site_id_location_coverage.md) — Coverage data

## MistHelper Notes

Not currently used by MistHelper directly.
