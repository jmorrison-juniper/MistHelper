# initiateSiteAnalyzeSpectrum

> initiateSiteAnalyzeSpectrum

## HTTP

`POST /api/v1/sites/{site_id}/analyze_spectrum`

## Description

Initiate a spectrum analysis for a site


The output will be available through websocket. As there can be multiple command
issued against the same device at the same time and the output all goes through
the same websocket stream, session is introduced for demux.



#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`


```json { "subscribe": "/sites/{site_id}/analyze_spectrum" } ```

#### Example output from ws stream

```json
{
  "event": "data",
  "channel": "/sites/4ac1dcf4-9d8b-7211-65c4-057819f0862b/analyze_spectrum",
  "data": {
      "session": "session_id",

      "fft_samples": [
          {
              "frequency": 2437.0,
              "rssi / signal ?": -93
          },
          ...
      ],

      "channel_usage": [
          {
              "channel": 36,
              "noise": -78,

              "wifi": 0.13,
              "non_wifi": 0.08
          },
          ...
      ]
  }
}     
```


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
    "band": {
      "type": "string",
      "description": "Band for spectrum analysis. enum: `24`, `5`, `6`"
    },
    "channels": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Optional list of channels to scan. If not specified, all supported channels will be scanned",
      "examples": [
        [
          "36",
          "40",
          "44",
          "48"
        ]
      ]
    },
    "device_id": {
      "type": "string",
      "description": "Device ID of the AP that is performing spectrum analysis",
      "contentEncoding": "uuid"
    },
    "duration": {
      "maximum": 600.0,
      "minimum": 60.0,
      "type": "integer",
      "description": "Duration of the spectrum analysis in seconds",
      "contentEncoding": "int32",
      "default": 300
    },
    "format": {
      "type": "string",
      "description": "Format of the spectrum analysis data. enum: `json`, `stream`"
    }
  },
  "required": [
    "band"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session",
  "required": [
    "session"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
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

`mistapi.api.v1.sites.spectrum_analysis.initiateSiteAnalyzeSpectrum()`

## Usage Context

Starts a spectrum analysis scan at a site. Triggers APs to begin collecting RF environment data.

## Gotchas

- Only supported on APs with spectrum analysis capability.
- Running analysis may temporarily affect AP performance.

## Related Endpoints

- [GET_sites_site_id_analyze_spectrum.md](GET_sites_site_id_analyze_spectrum.md) — Get spectrum data
- [GET_sites_site_id_stats_analyze_spectrum.md](GET_sites_site_id_stats_analyze_spectrum.md) — Spectrum stats

## MistHelper Notes

Not currently used by MistHelper directly.
