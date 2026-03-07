# getSiteCapturingStatus

> getSiteCapturingStatus

## HTTP

`GET /api/v1/sites/{site_id}/pcaps/capture`

## Description

Get Capturing status

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
    "ap_mac": {
      "type": [
        "string",
        "null"
      ]
    },
    "aps": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of target APs to capture packets"
    },
    "client_mac": {
      "type": [
        "string",
        "null"
      ],
      "examples": [
        "60a10a773412"
      ]
    },
    "duration": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        300
      ]
    },
    "failed": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of APs where configuration attempt failed"
    },
    "format": {
      "type": "string",
      "description": "PCAP format. enum: \n    * `stream`: to Mist cloud\n    * `tzsp`: stream packets (over UDP as TZSP packets) to a remote host (typically running Wireshark)"
    },
    "gateways": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Information on gateways to capture packets on if a gateway capture type is specified"
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
    "includes_mcast": {
      "type": "boolean"
    },
    "max_num_packets": {
      "type": "integer",
      "description": "Max number of packets configured by user",
      "contentEncoding": "int32",
      "examples": [
        1000
      ]
    },
    "max_pkt_len": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        128
      ]
    },
    "mxedges": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Information on mxedges to capture packets on if a mxedge capture type is specified"
    },
    "num_packets": {
      "type": "integer",
      "description": "total number of packets captured by all AP, not applicable for type [client, new_assoc]",
      "contentEncoding": "int32"
    },
    "ok": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of target APs successfully configured to capture packets"
    },
    "pcap_aps": {
      "type": "object",
      "additionalProperties": {
        "title": "response_pcap_ap",
        "type": "object",
        "properties": {
          "band": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "bandwidth": {
            "type": "integer",
            "contentEncoding": "int32"
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
            "band": 6,
            "bandwidth": 20,
            "channel": 133,
            "tcpdump_expression": null
          }
        }
      ]
    },
    "radiotap_tcpdump_expression": {
      "type": "string",
      "description": "When `type`==`radiotap`, radiotap_tcpdump_expression expression provided by the user"
    },
    "scan_tcpdump_expression": {
      "type": "string",
      "description": "When `type`==`scan`, scan_tcpdump_expression provided by the user"
    },
    "ssid": {
      "type": [
        "string",
        "null"
      ]
    },
    "started_time": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1435080709
      ]
    },
    "switches": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Information on switches to capture packets on if a switch capture type is specified. irb port interface is automatically added to capture as needed to ensure all desired packets are captured."
    },
    "tcpdump_expression": {
      "type": "string",
      "description": "tcpdump expression provided by the user (common)"
    },
    "type": {
      "type": "string",
      "description": "enum: `client`, `gateway`, `new_assoc`, `radiotap`, `radiotap,wired`, `wired`, `wireless`"
    },
    "tzsp_host": {
      "type": "string",
      "description": "Required if `format`==`tzsp`. Remote host accessible to mxedges over the network for receiving the captured packets.",
      "examples": [
        "192.168.1.2"
      ]
    },
    "tzsp_port": {
      "maximum": 65535.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "If `format`==`tzsp`. Port on remote host for receiving the captured packets",
      "contentEncoding": "int32"
    },
    "wired_tcpdump_expression": {
      "type": "string",
      "description": "When `type`==`wired`, wired_tcpdump_expression provided by the user"
    },
    "wireless_tcpdump_expression": {
      "type": "string",
      "description": "When `type`==`\u2018wireless\u2019`, wireless_tcpdump_expression provided by the user"
    }
  },
  "required": [
    "id",
    "type"
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

`mistapi.api.v1.utilities.pcaps.getSiteCapturingStatus()`

## Usage Context

Checks the status of an active site-level packet capture, including running state, target device, and elapsed time.

## Gotchas

- Returns 404 if no capture is currently active at the site.

## Related Endpoints

- [POST_sites_site_id_pcaps_capture.md](POST_sites_site_id_pcaps_capture.md) — Start a site capture
- [DELETE_sites_site_id_pcaps_capture.md](DELETE_sites_site_id_pcaps_capture.md) — Stop the active capture
- [GET_sites_site_id_pcaps.md](GET_sites_site_id_pcaps.md) — List completed captures

## MistHelper Notes

Used by Menu **9** (`PacketCaptureManager.start_site_packet_capture`) to check capture status.
