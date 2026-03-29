# getSiteRunningSpectrumAnalysis

> getSiteRunningSpectrumAnalysis

## HTTP

`GET /api/v1/sites/{site_id}/analyze_spectrum`

## Description

Get the running spectrum analysis for a site

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
  "type": "object",
  "properties": {
    "band": {
      "type": "string",
      "description": "Band on which the spectrum analysis is running (e.g., 24, 5, 6)"
    },
    "device_id": {
      "type": "string",
      "description": "Device ID of the AP that is running spectrum analysis",
      "contentEncoding": "uuid"
    },
    "duration": {
      "type": "integer",
      "description": "Duration of the spectrum analysis in seconds",
      "contentEncoding": "int32"
    },
    "format": {
      "type": "string",
      "description": "Format of the spectrum analysis data (e.g., json, stream)"
    },
    "started_time": {
      "type": "integer",
      "description": "Time when the spectrum analysis was started",
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.spectrum_analysis.getSiteRunningSpectrumAnalysis()`

## Usage Context

Retrieves spectrum analysis data for a site. Shows RF environment including interference sources and channel utilization.

## Gotchas

- Requires APs with spectrum analysis capability (AP43/AP45/AP63 series or newer).
- Data is sampled; high-resolution analysis may require dedicated scanning radios.

## Related Endpoints

- [GET_sites_site_id_rrm_current.md](GET_sites_site_id_rrm_current.md) — Current RRM state
- [GET_sites_site_id_rfdiags.md](GET_sites_site_id_rfdiags.md) — RF diagnostics recordings

## MistHelper Notes

Not currently used by MistHelper directly.
