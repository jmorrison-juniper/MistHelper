# searchSiteClientFingerprints

> searchSiteClientFingerprints

## HTTP

`GET /api/v1/sites/{site_id}/insights/fingerprints/search`

## Description

Search Client Fingerprints

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| family | string | No |  |  | Device Category of the client device |
| client_type | string | No |  |  | Filter results by client type. enum: `wireless`, `wired`, `vty` |
| model | string | No |  |  | Filter results by device model |
| mfg | string | No |  |  | Manufacturer name of the client device |
| os | string | No |  |  | Operating System name and version of the client device |
| os_type | string | No |  |  | Operating system name of the client device |
| mac | string | No |  |  | Filter results by MAC address |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
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
  "description": "Search response for client device fingerprint records",
  "properties": {
    "end": {
      "description": "Upper bound of the time range for the fingerprint search",
      "examples": [
        1711035686
      ],
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of fingerprint records returned in the response",
      "examples": [
        10
      ],
      "type": "integer"
    },
    "next": {
      "description": "Pagination URL for the next page of fingerprint search results",
      "type": "string"
    },
    "results": {
      "description": "Client device fingerprint records",
      "items": {
        "additionalProperties": false,
        "description": "Client device fingerprint record returned by NAC fingerprint insights",
        "properties": {
          "family": {
            "description": "Device family or category inferred from client fingerprinting",
            "readOnly": true,
            "type": "string"
          },
          "mac": {
            "description": "Client device MAC address for the fingerprint record",
            "readOnly": true,
            "type": "string"
          },
          "mfg": {
            "description": "Manufacturer name inferred from client fingerprinting",
            "readOnly": true,
            "type": "string"
          },
          "model": {
            "description": "Device model inferred from client fingerprinting",
            "readOnly": true,
            "type": "string"
          },
          "org_id": {
            "description": "Unique identifier of a Mist organization",
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ],
            "format": "uuid",
            "readOnly": true,
            "type": "string"
          },
          "os": {
            "description": "Operating system name and version inferred from client fingerprinting",
            "readOnly": true,
            "type": "string"
          },
          "os_type": {
            "description": "Operating system family inferred from client fingerprinting",
            "readOnly": true,
            "type": "string"
          },
          "random_mac": {
            "description": "Whether the client device uses a randomized MAC address",
            "readOnly": true,
            "type": "boolean"
          },
          "site_id": {
            "description": "Unique identifier of a Mist site",
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ],
            "format": "uuid",
            "readOnly": true,
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch timestamp, in seconds",
            "format": "double",
            "readOnly": true,
            "type": "number"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "start": {
      "description": "Lower bound of the time range for the fingerprint search",
      "examples": [
        1710949286
      ],
      "type": "integer"
    },
    "total": {
      "description": "Number of fingerprint records matching the search",
      "examples": [
        232
      ],
      "type": "integer"
    }
  },
  "required": [
    "start",
    "end",
    "limit",
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

`mistapi.api.v1.sites.insights.searchSiteClientFingerprints()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/sites/{site_id}/insights/fingerprints/search`.
Common use cases:

- Use it when you need to search Client Fingerprints.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `searchSiteClientFingerprints(mist_session: mistapi.__api_session.APISession, site_id: str, family: str | None = None, client_type: str | None = None, model: str | None = None, mfg: str | None = None, os: str | None = None, os_type: str | None = None, mac: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None, interval: str | None = None, sort: str | None = None, search_after: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- Query parameters include `family`, `client_type`, `model`, `mfg`, `os`. Keep filters narrow for repeatable results.
- Search results can be large. Set a time range and page through all required results.

## Related Endpoints

- [GET_sites_site_id_insights_fingerprints_search.md](../orgs/GET_sites_site_id_insights_fingerprints_search.md) -- searchOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/search`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.
- [GET_sites_site_id_insights_fingerprints_count.md](GET_sites_site_id_insights_fingerprints_count.md) -- countSiteClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

Menu Operation **261** offers this site-scoped simple read endpoint.
Verification source: `git grep -n "searchSiteClientFingerprints" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
