# listStates

> listStates

## HTTP

`GET /api/v1/const/states`

## Description

Get List of ISO States based on country code

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| country_code | string | Yes |  |  | Country code, in [two-character]($e/Constants%20Definitions/listCountryCodes) |

## Request Body

None.

## Response

### 200

List of Countries

```json
{
  "type": "array",
  "items": {
    "title": "const_state",
    "type": "object",
    "properties": {
      "iso_code": {
        "type": "string",
        "examples": [
          "AK"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Alaska"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "iso_code": "AK",
        "name": "Alaska"
      },
      {
        "iso_code": "AL",
        "name": "Alabama"
      },
      {
        "iso_code": "AS",
        "name": "American Samoa"
      },
      {
        "iso_code": "AZ",
        "name": "Arizona"
      },
      {
        "iso_code": "CA",
        "name": "California"
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

`mistapi.api.v1.constants.definitions.listStates()`

## Usage Context

Returns the list of US state codes used for site addressing and regional configuration. Use this when setting site location details that require state-level granularity.

## Gotchas

- This endpoint is US-specific. For other countries, the country code alone is typically sufficient.
- No known gotchas with the endpoint itself; the response is a small static reference list.

## Related Endpoints

- [GET_const_countries.md](GET_const_countries.md) — Country code list (parent level)
- [../orgs/GET_orgs_org_id_sites.md](../orgs/GET_orgs_org_id_sites.md) — Sites that include state in address fields

## MistHelper Notes

Not currently used by MistHelper directly.
