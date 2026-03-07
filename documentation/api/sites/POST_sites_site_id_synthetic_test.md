# triggerSiteSyntheticTest

> triggerSiteSyntheticTest

## HTTP

`POST /api/v1/sites/{site_id}/synthetic_test`

## Description

Trigger Synthetic Testing

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "email": {
      "type": "string",
      "examples": [
        "test@mist.com"
      ]
    }
  }
}
```

## Response

### 200

Synthetic Test Started

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "message": {
      "type": "string",
      "examples": [
        "Successfully queued synthetic test for the site."
      ]
    },
    "status": {
      "type": "string",
      "examples": [
        "success"
      ]
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.synthetic_tests.triggerSiteSyntheticTest()`

## Usage Context

Triggers a synthetic network test from a site device. Tests include connectivity, throughput, and latency checks.

## Gotchas

- Test execution is asynchronous. Poll for results after triggering.

## Related Endpoints

- [GET_sites_site_id_synthetic_test.md](GET_sites_site_id_synthetic_test.md) — Get test results
- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
