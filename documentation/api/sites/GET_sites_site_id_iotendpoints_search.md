# searchSiteIotEndpoints

> searchSiteIotEndpoints

## HTTP

`GET /api/v1/sites/{site_id}/iotendpoints/search`

## Description

Search IoT Endpoints

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| ap_mac | string | No |  |  | Filter results by AP MAC address |
| mac | string | No |  |  | Filter results by MAC address |
| type | string | No |  |  | IoT endpoint type. enum: `zigbee` |
| mfg | string | No |  |  | Filter results by manufacturer |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Time-bounded response for IoT endpoint search results",
  "properties": {
    "end": {
      "description": "Epoch timestamp, in seconds, for the end of the IoT endpoint search window",
      "type": "number"
    },
    "results": {
      "description": "IoT endpoint statistics returned by a search response",
      "items": {
        "additionalProperties": false,
        "description": "IoT endpoint statistics returned by a search response",
        "properties": {
          "ap_mac": {
            "description": "MAC address of the AP the endpoint was seen on",
            "examples": [
              "5c5b350e0001"
            ],
            "type": "string"
          },
          "id": {
            "description": "Unique identifier for the IoT endpoint",
            "examples": [
              "63f9e299182b63f9"
            ],
            "type": "string"
          },
          "lqi": {
            "description": "Link Quality Indicator (0\u2013255)",
            "maximum": 255,
            "minimum": 0,
            "type": "integer"
          },
          "mac": {
            "description": "Endpoint MAC address reported in IoT statistics",
            "examples": [
              "63f9e299182b63f9"
            ],
            "type": "string"
          },
          "mfg": {
            "description": "Manufacturer name reported for the IoT endpoint",
            "examples": [
              "Assa Abloy"
            ],
            "type": "string"
          },
          "model": {
            "description": "Device model reported for the IoT endpoint",
            "examples": [
              "Assa Abloy"
            ],
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch timestamp of the last observation, in seconds",
            "type": "number"
          },
          "type": {
            "description": "IoT endpoint type. enum: `zigbee`",
            "examples": [
              "zigbee"
            ],
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp, in seconds, for the start of the IoT endpoint search window",
      "type": "number"
    },
    "total": {
      "description": "Number of IoT endpoint records matching the search filters",
      "type": "integer"
    }
  },
  "required": [
    "start",
    "end",
    "total",
    "results"
  ],
  "type": "object"
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

`mistapi.api.v1.sites.iotendpoints.searchSiteIotEndpoints()`

## Usage Context

Use this endpoint to read the resource at `/api/v1/sites/{site_id}/iotendpoints/search`.
Common use cases:

- Use it when you need to search IoT Endpoints.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `searchSiteIotEndpoints(mist_session: mistapi.__api_session.APISession, site_id: str, ap_mac: str | None = None, mac: str | None = None, type: str | None = None, mfg: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- Query parameters include `ap_mac`, `mac`, `type`, `mfg`, `limit`. Keep filters narrow for repeatable results.
- Search results can be large. Set a time range and page through all required results.

## Related Endpoints

- [GET_sites_site_id_iotendpoints_count.md](GET_sites_site_id_iotendpoints_count.md) -- countSiteIotEndpoints uses `GET /api/v1/sites/{site_id}/iotendpoints/count`.
- [POST_sites_site_id_iotendpoints_id_zigbee_rejoin.md](POST_sites_site_id_iotendpoints_id_zigbee_rejoin.md) -- rejoinSiteIotEndpointZigbee uses `POST /api/v1/sites/{site_id}/iotendpoints/{id}/zigbee_rejoin`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

MistHelper does not currently call `searchSiteIotEndpoints`.
Verification source: `git grep -n "searchSiteIotEndpoints" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
