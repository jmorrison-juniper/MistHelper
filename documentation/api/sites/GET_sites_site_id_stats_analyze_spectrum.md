# listSiteSpectrumAnalysis

> listSiteSpectrumAnalysis

## HTTP

`GET /api/v1/sites/{site_id}/stats/analyze_spectrum`

## Description

List the past spectrum analysis for a site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |

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
      "description": "End time of the spectrum analysis in epoch seconds",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "description": "Limit of the number of results returned",
      "contentEncoding": "int32"
    },
    "page": {
      "type": "integer",
      "description": "Page number of the results returned",
      "contentEncoding": "int32"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "response_past_spectrum_analysis_result",
        "type": "object",
        "properties": {
          "band": {
            "type": "string",
            "description": "Band on which the spectrum analysis was run (e.g., 24, 5, 6)"
          },
          "channel_usage": {
            "type": "array",
            "items": {
              "title": "response_past_spectrum_analysis_channel_usage",
              "type": "object",
              "properties": {
                "channel": {
                  "type": "integer",
                  "description": "Channel number",
                  "contentEncoding": "int32",
                  "examples": [
                    36
                  ]
                },
                "noise": {
                  "type": "number",
                  "description": "Noise level in dBm",
                  "examples": [
                    -90
                  ]
                },
                "non_wifi": {
                  "type": "number",
                  "description": "Percentage of channel usage by non-WiFi signals in the range [0, 1]",
                  "examples": [
                    0.87
                  ]
                },
                "wifi": {
                  "type": "number",
                  "description": "Percentage of channel usage by WiFi in the range [0, 1]",
                  "examples": [
                    0.13
                  ]
                }
              },
              "description": "Channel usage data for a specific channel"
            },
            "description": ""
          },
          "fft_samples": {
            "type": "array",
            "items": {
              "title": "response_past_spectrum_analysis_fft_sample",
              "type": "object",
              "properties": {
                "frequency": {
                  "type": "number",
                  "description": "Frequency in MHz",
                  "examples": [
                    2437
                  ]
                },
                "rssi": {
                  "type": "number",
                  "description": "RSSI in dBm",
                  "examples": [
                    -70
                  ]
                },
                "signal7": {
                  "type": "number",
                  "description": "RSSI in dBm",
                  "examples": [
                    -70
                  ]
                }
              },
              "description": "FFT sample data for a specific frequency"
            },
            "description": "List of FFT samples for the spectrum analysis"
          },
          "mac": {
            "type": "string",
            "description": "MAC Address of the AP that ran the spectrum analysis"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "timestamp": {
            "type": "integer",
            "description": "Timestamp when the spectrum analysis was run in epoch seconds",
            "contentEncoding": "int32"
          }
        },
        "description": "Result of a past spectrum analysis"
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "description": "Start time of the spectrum analysis in epoch seconds",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "description": "Total number of results available for the given time range",
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

`mistapi.api.v1.sites.spectrum_analysis.listSiteSpectrumAnalysis()`

## Usage Context

Retrieves spectrum analysis statistics for a site, including interference sources and channel utilization.

## Gotchas

- Requires APs with spectrum analysis capability (e.g., AP43/AP63).

## Related Endpoints

- [GET_sites_site_id_analyze_spectrum.md](GET_sites_site_id_analyze_spectrum.md) — Analyze spectrum
- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
