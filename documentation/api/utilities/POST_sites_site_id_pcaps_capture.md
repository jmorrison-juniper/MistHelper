# startSitePacketCapture

> startSitePacketCapture

## HTTP

`POST /api/v1/sites/{site_id}/pcaps/capture`

## Description

Initiate a Site Packet Capture

The output will be available through websocket. As there can be multiple command issued against the same AP at the same time and the output all goes through the same websocket stream, session is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/pcaps"
}
```
#### Response (MxEdge)
```json
{
    "event": "data"
    "channel": "/sites/{site_id}/pcaps"
    "data": {
         "capture_id": "6b1be4fb-b239-44d9-9d3b-cb1ff3af1721",
     "lost_messages": 0
         "pcap_dict": {
             "channel_frequency": 2412,
             "channel": "1",
             "datarate": "1.0 Mbps",
             "rssi": -75, 
             "dst": "78:bd:bc:ca:0b:0a",
             "src": "18:b8:1f:4c:91:c0",
             "bssid": "18:b8:1f:4c:91:c0",
             "frame_type": "Management", 
             "frame_subtype": "Probe Response", 
         "proto": "802.11", 
             "ap_mac": "d4:20:b0:81:99:2e", 
             "direction": "tx", 
             "timestamp": 1652246543, 
             "length": 416.0,
             "interface": "radiotap",
             "info": "1652246544.467733 1683216786us tsft 1.0 Mb/s 2412 MHz 11g -75dBm signal -82dBm noise antenna 0 Probe Response (ATTKmsWiVS) [1.0* 2.0* 5.5* 11.0* 18.0 24.0 36.0 54.0 Mbit] CH: 2, PRIVACY\\n",
         }, 
        "pcap_raw": "1MOyoQIABAAAAAAAAAAAAP//AAABAAAAEEh7Yh5VBwCgAQAAoAEAAAAAKwBvCADAAQAAAIw7reCS2VNkAAAAABACbAmABLWuAAEAEBgAAwACAABQADoBeL28ygsKGLgfTJHAGLgfTJHAcIZ2WDlBJQAAAGQAERUACkFUVEttc1dpVlMBCIKEi5YkMEhsAwECBwZVUyABCx4gAQAjAhkAKgEEMgQMEhhgMBQBAAAPrAQBAAAPrAQBAAAPrAIMAAsFAQAbAABGBTIIAQAALRqtCR////8AAAAAAAAAAAAAAAAAAAAAAAAAAD0WAggVAAAAAAAAAAAAAAAAAAAAAAAAAH8IBAAIAAAAAEDdkwBQ8gQQSgABEBBEAAECEDsAAQMQRwAQn2481frn3KT+uGod2ERx+RAhAAtBcnJpcywgSW5jLhAjAApCR1cyMTAtNzAwECQACkJHVzIxMC03MDAQQgAKQkdXMjEwLTcwMBBUAAgABgBQ8gQAARARAA5BcnJpcyBXaXJlbGVzcxAIAAIgCBA8AAEBEEkABgA3KgABIN0JABAYAgEQHAAA3RgAUPICAQGEAAOkAAAnpAAAQkNeAGIyLwAzjakr"
}
```

#### Response (Wired)
```json
{
    "event": "data"
    "channel": "/sites/67970e46-4e12-11e6-9188-0242ac110007/pcaps"
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
             "proto": "TCP", 
             "ap_mac": "d4:20:b0:81:99:2e",
             "direction": "tx", 
             "timestamp": 1652247615, 
             "length": 159.0, 
             "interface": "wired",
             "info": "1652247616.007409 IP ec2-34-224-147-117.compute-1.amazonaws.com.https > ip-192-168-1-55.ec2.internal.51635: Flags [P.], seq 2192123968:2192124057, ack 4035166782, win 12, options [nop,nop,TS val 597467050 ecr 740580660], length 89\\n",
             }, 
        "pcap_raw": "1MOyoQIABAAAAAAAAAAAAP//AAABAAAAQEx7YhMzAACfAAAAnwAAAGjsxQkuh4w7reBHQIEAAAEIAEUAAI1bLEAAKAZ/CiLgk3XAqAE3AbvJs4KpKEDwg8I+gBgADFf9AAABAQgKI5yfqiwkXTQXAwMAVKY5JopoKQrVEn0/3ld4YntctGEH/rTZuwtCvzSncFw71QJveJi9uxHs57KC8w9Apph3YvXJrmWg7M37+o+YV0KH/xmr626s5Bkhb3QhKOu+NoNEmA=="

    }
}
```

#### Stop Response (Wired/Wireless)
```json
{
    "event": "data"
    "channel": "/sites/67970e46-4e12-11e6-9188-0242ac110007/pcaps"
    "data": {
      "capture_id": "a2f7374d-6a70-41fd-8a3f-71e42573baaf", 
      "lost_messages": 0,
      "pcap_dict": null
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

`mistapi.api.v1.utilities.pcaps.startSitePacketCapture()`

## Usage Context

Starts a packet capture at the site level, targeting a specific device, client, or switch port. Supports wireless client captures, wired port captures, new association captures, and scan radio captures.

## Gotchas

- Only one capture per site at a time. Check for and stop any active capture before starting.
- Switch port captures need the exact port identifier and support tcpdump filter syntax.
- Capture duration defaults are limited; specify `duration` for longer captures.

## Related Endpoints

- [GET_sites_site_id_pcaps_capture.md](GET_sites_site_id_pcaps_capture.md) — Check if a capture is running
- [DELETE_sites_site_id_pcaps_capture.md](DELETE_sites_site_id_pcaps_capture.md) — Stop the capture
- [GET_sites_site_id_pcaps.md](GET_sites_site_id_pcaps.md) — Retrieve completed captures
- [POST_orgs_org_id_pcaps_capture.md](POST_orgs_org_id_pcaps_capture.md) — Org-level capture (broader scope)

## MistHelper Notes

Used by Menu **9** (`PacketCaptureManager.start_site_packet_capture`). Supports wireless client, wired client, gateway, switch (port-specific with tcpdump), new association, and scan radio capture types.
