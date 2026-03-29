# listMxEdgeModels

> listMxEdgeModels

## HTTP

`GET /api/v1/const/mxedge_models`

## Description

Get List of available Mx Edge models

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of MxEdge Models

```json
{
  "type": "array",
  "items": {
    "title": "const_mxedge_model",
    "type": "object",
    "properties": {
      "custom_ports": {
        "type": "boolean"
      },
      "display": {
        "type": "string",
        "examples": [
          "X10"
        ]
      },
      "model": {
        "type": "string",
        "examples": [
          "ME-X10"
        ]
      },
      "ports": {
        "type": "object",
        "additionalProperties": {
          "title": "const_mxedge_model_port",
          "type": "object",
          "properties": {
            "display": {
              "type": "string",
              "examples": [
                "xe0"
              ]
            },
            "speed": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                10000
              ]
            }
          }
        }
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "X10",
        "model": "ME-X10",
        "ports": {
          "0": {
            "display": "xe0",
            "speed": 10000
          },
          "1": {
            "display": "xe1",
            "speed": 10000
          },
          "2": {
            "display": "xe2",
            "speed": 10000
          },
          "3": {
            "display": "xe3",
            "speed": 10000
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

`mistapi.api.v1.constants.models.listMxEdgeModels()`

## Usage Context

Returns the list of supported Mist Edge hardware models with specifications. Mist Edge appliances provide local tunnel termination, edge services, and failover capabilities. Use this to identify available hardware options for Mist Edge deployments.

## Gotchas

- Mist Edge models are separate from standard AP/switch/gateway models — use `GET /api/v1/const/device_models` for those.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_models.md](GET_const_device_models.md) — Standard device models (AP, switch, gateway)
- [GET_const_mxedge_events.md](GET_const_mxedge_events.md) — Mist Edge event type definitions
- [../orgs/GET_orgs_org_id_mxedges.md](../orgs/GET_orgs_org_id_mxedges.md) — List deployed Mist Edge appliances

## MistHelper Notes

Not currently used by MistHelper directly.
