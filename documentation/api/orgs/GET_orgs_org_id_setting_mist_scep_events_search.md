# searchOrgScepEvents

> searchOrgScepEvents

## HTTP

`GET /api/v1/orgs/{org_id}/setting/mist_scep/events/search`

## Description

Search Mist SCEP PKI operation events for the organization. Use this to audit certificate issuance errors and diagnose client onboarding problems.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | Filter by event type. enum: `failure`, `success` |
| cert_provider | string | No |  |  | Filter by the MDM or certificate provider that triggered the operation |
| common_name | string | No |  |  | Partial match against the certificate common name, such as a user UPN |
| device_id | string | No |  |  | Filter by the device identifier associated with the SCEP operation |
| text | string | No |  |  | Keyword search within the event reason text |
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
  "description": "Paginated Mist SCEP PKI operation event search response",
  "properties": {
    "end": {
      "description": "End of the SCEP event search window, in epoch seconds",
      "examples": [
        1748314800
      ],
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of SCEP events returned per page",
      "examples": [
        100
      ],
      "type": "integer"
    },
    "page": {
      "description": "Current page of SCEP event search results",
      "examples": [
        1
      ],
      "type": "integer"
    },
    "results": {
      "description": "SCEP PKI operation events returned by a search",
      "items": {
        "additionalProperties": false,
        "description": "Mist SCEP PKI operation event reported for an organization",
        "properties": {
          "cert_provider": {
            "description": "MDM or certificate provider that triggered the SCEP operation",
            "examples": [
              "jamf"
            ],
            "type": "string"
          },
          "common_name": {
            "description": "Common name presented in the SCEP certificate request",
            "examples": [
              "name@company.net bb08e3c5-a1d9-5f21-a3b7-cd0821eab8f6"
            ],
            "type": "string"
          },
          "device_id": {
            "description": "Device identifier associated with the SCEP operation. Empty when the SCEP request did not include a device ID",
            "examples": [
              "bb08e3c5-a1d9-5f21-a3b7-cd0821eab8f6"
            ],
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
          "text": {
            "description": "Reason text describing the outcome of the SCEP operation",
            "examples": [
              "invalid challenge/expired"
            ],
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch timestamp, in seconds",
            "format": "double",
            "readOnly": true,
            "type": "number"
          },
          "type": {
            "description": "enum: `SCEP_PKI_OPERATION_FAILURE`, `SCEP_PKI_OPERATION_SUCCESS`",
            "enum": [
              "SCEP_PKI_OPERATION_FAILURE",
              "SCEP_PKI_OPERATION_SUCCESS"
            ],
            "examples": [
              "SCEP_PKI_OPERATION_FAILURE"
            ],
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "start": {
      "description": "Start of the SCEP event search window, in epoch seconds",
      "examples": [
        1748228400
      ],
      "type": "integer"
    },
    "total": {
      "description": "Number of SCEP events matching the search",
      "examples": [
        3
      ],
      "type": "integer"
    }
  },
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

`mistapi.api.v1.orgs.scep.searchOrgScepEvents()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
