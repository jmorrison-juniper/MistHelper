# startOrgPacketCapture

> startOrgPacketCapture

## HTTP

`POST /api/v1/orgs/{org_id}/pcaps/capture`

## Description

Initiate a Packet Capture

**NOTE**: For packet captures of org level Mist Edges only. Use [Start Site Packet Capture]($e/Utilities%20PCAPs/startSitePacketCapture) for site level Mist Edges. 

The output will be available through websocket. As there can be multiple command issued against the same AP at the same time and the output all goes through the same websocket stream, session is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/pcaps"
}
```
#### Response (Wireless/RadioTap)
```json
{
  "event": "data"
  "channel": "/orgs/67970e46-4e12-11e6-9188-0242ac110007/pcaps"
  "data": {
      "capture_id": "f039b1b4-a23e-48b2-906a-0da40524de73", 
      "pcap_dict": {
          "dst_mac": "68:ec:c5:09:2e:87",
          "src_mac": "8c:3b:ad:e0:47:40", 
          "vlan": 1, 
          "src_ip": "34.224.147.117", 
          "dst_ip": "192.168.1.55",
          "dst_port": 51635, 
          "src_port": 443,
          "protocol": "TCP", 
          "mxedge_id": "00000000-0000-0000-1000-001122334455",
          "direction": "tx", 
          "timestamp": 1652247615, 
          "length": 159.0, 
          "interface": "port0",
          "info": "1652247616.007409 IP ec2-34-224-147-117.compute-1.amazonaws.com.https > ip-192-168-1-55.ec2.internal.51635: Flags [P.], seq 
                    2192123968:2192124057, ack 4035166782, win 12, options [nop,nop,TS val 597467050 ecr 740580660], length 89\\n",
          }, 
      "pcap_raw": "1MOyoQIABAAAAAAAAAAAAP//AAABAAAAQEx7YhMzAACfAAAAnwAAAGjsxQkuh4w7reBHQIEAAAEIAEUAAI1bLEAAKAZ/CiLgk3XAqAE3AbvJs4KpKEDwg8I+gBgADFf9AAABAQgKI5yfqiwkXTQXAwMAVKY5JopoKQrVEn0/3ld4YntctGEH/rTZuwtCvzSncFw71QJveJi9uxHs57KC8w9Apph3YvXJrmWg7M37+o+YV0KH/xmr626s5Bkhb3QhKOu+NoNEmA==\"
    }
}
```

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "ap_count": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "aps": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "client_mac": {
      "type": [
        "string",
        "null"
      ]
    },
    "duration": {
      "type": "number"
    },
    "enabled": {
      "type": "boolean"
    },
    "expiry": {
      "type": "number"
    },
    "format": {
      "type": "string"
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
    "include_mcast": {
      "type": "boolean"
    },
    "max_pkt_len": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_packets": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "raw": {
      "type": "boolean"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "ssid": {
      "type": [
        "string",
        "null"
      ]
    },
    "tcpdump_parser_expression": {
      "type": [
        "string",
        "null"
      ]
    },
    "timestamp": {
      "type": "number",
      "description": "Epoch (seconds)",
      "readOnly": true
    },
    "type": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "org_id",
    "site_id",
    "timestamp",
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

`mistapi.api.v1.utilities.pcaps.startOrgPacketCapture()`

## Usage Context

Starts a packet capture at the org level, targeting a specific device, client, or port. Supports wireless client captures, wired port captures (switches), and gateway captures with tcpdump filtering.

## Gotchas

- Only one capture can run per org at a time. Stop any active capture before starting a new one.
- Switch port captures require specifying the port ID and may need tcpdump filter syntax.
- Capture duration is limited; long captures will auto-stop.

## Related Endpoints

- [GET_orgs_org_id_pcaps_capture.md](GET_orgs_org_id_pcaps_capture.md) — Check if a capture is already running
- [DELETE_orgs_org_id_pcaps_capture.md](DELETE_orgs_org_id_pcaps_capture.md) — Stop the capture
- [GET_orgs_org_id_pcaps.md](GET_orgs_org_id_pcaps.md) — Retrieve completed captures
- [POST_sites_site_id_pcaps_capture.md](POST_sites_site_id_pcaps_capture.md) — Site-level capture (alternative scope)

## MistHelper Notes

Used by Menu **10** (`PacketCaptureManager.start_org_packet_capture`). Supports wireless client, wired client, gateway, and switch packet captures with full tcpdump filter support.
