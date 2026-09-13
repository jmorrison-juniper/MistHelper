# listTrafficTypes

> listTrafficTypes

## HTTP

`GET /api/v1/const/traffic_types`

## Description

Get List of identified traffic

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Traffic Types

```json
{
  "type": "array",
  "items": {
    "title": "const_traffic_type",
    "type": "object",
    "properties": {
      "display": {
        "type": "string",
        "examples": [
          "VoIP Video"
        ]
      },
      "dscp": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          32
        ]
      },
      "failover_policy": {
        "type": "string",
        "examples": [
          "non_revertible"
        ]
      },
      "max_jitter": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          250
        ]
      },
      "max_latency": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          1500
        ]
      },
      "max_loss": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          35
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "voip_video"
        ]
      },
      "traffic_class": {
        "type": "string",
        "examples": [
          "medium"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "VoIP Video",
        "dscp": 32,
        "failover_policy": "non_revertible",
        "max_jitter": 250,
        "max_latency": 1500,
        "max_loss": 35,
        "name": "voip_video",
        "traffic_class": "medium"
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

`mistapi.api.v1.constants.definitions.listTrafficTypes()`

## Usage Context

Returns the list of traffic type classifications used for application-aware routing and QoS policies on gateway devices. Traffic types define how different application categories are prioritized across WAN links.

## Gotchas

- Traffic types are primarily relevant for WAN/SD-WAN configurations on SRX/SSR gateways.
- No known gotchas with the endpoint itself; the response is a small static reference list.

## Related Endpoints

- [GET_const_applications.md](GET_const_applications.md) — Applications that are classified into traffic types
- [GET_const_gateway_applications.md](GET_const_gateway_applications.md) — Gateway-specific application definitions
- [../orgs/GET_orgs_org_id_servicepolicies.md](../orgs/GET_orgs_org_id_servicepolicies.md) — Service policies that use traffic types

## MistHelper Notes

Not currently used by MistHelper directly.
