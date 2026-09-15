# searchSiteDeviceFlowRecords

> searchSiteDeviceFlowRecords

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/flow_records/search`

## Description

Search network flow records for a specific device within a site.
Note: Only supported for switch devices. The device must be manageable. The `device_mac` is automatically scoped to the device in the URL path and cannot be overridden by query parameter.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
| src_ip | string | No |  |  | Source IP address |
| dst_ip | string | No |  |  | Destination IP address |
| src_port | string | No |  |  | Source port |
| dst_port | string | No |  |  | Destination port |
| protocol | string | No |  |  | Protocol (e.g. `tcp`, `udp`, `icmp`) |
| state | string | No |  |  | Flow state |
| direction | string | No |  |  | Flow direction |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Paginated response for device flow record search results",
  "properties": {
    "end": {
      "description": "Epoch timestamp, in seconds, for the end of the flow record search window",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of flow records returned in this page",
      "type": "integer"
    },
    "results": {
      "description": "Flow records matching the search filters",
      "items": {
        "additionalProperties": false,
        "description": "Network flow record reported by a switch device",
        "properties": {
          "device_mac": {
            "description": "MAC address of the device",
            "type": "string"
          },
          "direction": {
            "description": "Flow direction. enum: `egress`, `ingress`",
            "enum": [
              "egress",
              "ingress"
            ],
            "type": "string"
          },
          "dst_ip": {
            "description": "Destination IP address",
            "type": "string"
          },
          "dst_port": {
            "description": "Destination port number",
            "type": "integer"
          },
          "duration": {
            "description": "Flow duration in seconds",
            "format": "int64",
            "type": "integer"
          },
          "end_time": {
            "description": "Flow end time in epoch seconds",
            "format": "int64",
            "type": "integer"
          },
          "flow_id": {
            "description": "Unique flow identifier",
            "format": "int64",
            "type": "integer"
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
          "protocol": {
            "description": "Protocol (e.g. `tcp`, `udp`, `icmp`)",
            "type": "string"
          },
          "sampling_percentage": {
            "description": "Percentage of packets sampled (e.g. `0.1` means 0.1% of packets are captured via sFlow; `100.0` means all packets are captured via FBT)",
            "format": "float",
            "type": "number"
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
          "src_ip": {
            "description": "Source IP address",
            "type": "string"
          },
          "src_port": {
            "description": "Source port number",
            "type": "integer"
          },
          "start_time": {
            "description": "Flow start time in epoch seconds",
            "format": "int64",
            "type": "integer"
          },
          "state": {
            "description": "Flow state. enum: `active`, `aged-out`",
            "enum": [
              "active",
              "aged-out"
            ],
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch time (in seconds) when the flow record was last updated or completed",
            "format": "int64",
            "type": "integer"
          },
          "total_bytes": {
            "description": "Total number of bytes in the flow",
            "format": "int64",
            "type": "integer"
          },
          "total_pkts": {
            "description": "Total number of packets in the flow",
            "format": "int64",
            "type": "integer"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "search_after": {
      "description": "Cursor token for retrieving the next page of flow records",
      "type": "string"
    },
    "start": {
      "description": "Epoch timestamp, in seconds, for the start of the flow record search window",
      "type": "integer"
    },
    "total": {
      "description": "Number of flow records matching the search filters",
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

`mistapi.api.v1.utilities.lan.searchSiteDeviceFlowRecords()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
