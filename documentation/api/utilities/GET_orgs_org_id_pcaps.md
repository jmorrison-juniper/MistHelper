# listOrgPacketCaptures

> listOrgPacketCaptures

## HTTP

`GET /api/v1/orgs/{org_id}/pcaps`

## Description

Get List of Org  Packet Captures

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

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
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_pcap_search_item",
        "required": [
          "timestamp",
          "type",
          "url"
        ],
        "type": "object",
        "properties": {
          "ap_macs": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "aps": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "duration": {
            "type": "number",
            "examples": [
              600
            ]
          },
          "format": {
            "type": "string",
            "examples": [
              "stream"
            ]
          },
          "id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "max_num_packets": {
            "type": "number",
            "examples": [
              1024
            ]
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "pcap_aps": {
            "type": "object",
            "additionalProperties": {
              "title": "response_pcap_search_item_pcap_aps_item",
              "type": "object",
              "properties": {
                "band": {
                  "type": "string"
                },
                "bandwidth": {
                  "type": "string"
                },
                "channel": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "tcpdump_expression": {
                  "type": [
                    "string",
                    "null"
                  ]
                }
              }
            },
            "examples": [
              {
                "5c5b35000010": {
                  "band": "6",
                  "bandwidth": "20",
                  "channel": 133,
                  "tcpdump_expression": null
                }
              }
            ]
          },
          "pcap_url": {
            "type": "string"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "termination_reason": {
            "type": "string",
            "examples": [
              "default"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string"
          },
          "url": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.pcaps.listOrgPacketCaptures()`

## Usage Context

Lists all packet captures stored for an organization, including metadata such as capture duration, file size, device type, and download URLs. Use this to find and retrieve previously captured packet data for analysis.

## Gotchas

- Capture files have a retention period; older captures may be automatically deleted.
- Results are paginated; use pagination parameters for complete listings.

## Related Endpoints

- [POST_orgs_org_id_pcaps_capture.md](POST_orgs_org_id_pcaps_capture.md) — Start a new org-level capture
- [GET_orgs_org_id_pcaps_capture.md](GET_orgs_org_id_pcaps_capture.md) — Check active capture status
- [DELETE_orgs_org_id_pcaps_capture.md](DELETE_orgs_org_id_pcaps_capture.md) — Stop an active capture
- [GET_sites_site_id_pcaps.md](GET_sites_site_id_pcaps.md) — Site-level packet capture list

## MistHelper Notes

Used by Menu **10** (`PacketCaptureManager.start_org_packet_capture`) to list and manage org-level packet captures.
