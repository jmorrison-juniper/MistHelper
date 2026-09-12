# showSiteSsrAndSrxSessions

> showSiteSsrAndSrxSessions

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_session`

## Description

Get active sessions passing through the Device.


The output will be available through websocket. As there can be multiple command
issued against the same device at the same time and the output all goes through
the same websocket stream, session is introduced for demux.



#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`


```json 
{ "subscribe": "/sites/{site_id}/devices/{device_id}/cmd" }
```


#### Example output from ws stream

```json 
{
      "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-xxxxxxxxxxxx/devices/00000000-0000-0000-1000-xxxxxxxxxxxx/cmd",
      "event": "data",
      "data": {
              "session": "f517bf29-1141-41ae-a084-17cacb0ccb57",
              "raw": "{\"status\":\"SUCCESS\",\"finished\":true,\"rows\":[{\"session_id\":\"a04b1cc7-dcc1-40a6-a010-0fe46ca38551\",\"direction\":\"forward\",\"service\":\"internet\",\"tenant\":\"SRV.PRD-Core\",\"device_interface\":\"ge-0/0/3\",\"network_interface\":\"ge-0/0/3.100\",\"protocol\":\"TCP\",\"source_ip\":\"10.3.20.101\",\"source_port\":45733,\"destination_ip\":\"13.38.46.35\",\"destination_port\":443,\"nat_ip\":\"192.168.1.115\",\"nat_port\":45256,\"payload_encrypted\":false,\"timeout\":1581,\"uptime\":319},{\"session_id\":\"a04b1cc7-dcc1-40a6-a010-0fe46ca38551\",\"direction\":\"reverse\",\"service\":\"internet\",\"tenant\":\"SRV.PRD-Core\",\"device_interface\":\"ge-0/0/0\",\"network_interface\":\"ge-0/0/0\",\"protocol\":\"TCP\",\"source_ip\":\"13.38.46.35\",\"source_port\":443,\"destination_ip\":\"192.168.1.115\",\"destination_port\":45256,\"nat_ip\":\"0.0.0.0\",\"nat_port\":0,\"payload_encrypted\":false,\"timeout\":1581,\"uptime\":319}]}\n"
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
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "service_name": {
      "type": "string",
      "description": "The exact service name for which to display the active sessions",
      "examples": [
        "any"
      ]
    },
    "session_id": {
      "type": "string",
      "description": "Show session details by session_id"
    }
  }
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session",
  "required": [
    "session"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ]
    }
  }
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

`mistapi.api.v1.utilities.wan.showSiteSsrAndSrxSessions()`

## Usage Context

Retrieves active session information from an SSR device. Shows session smart routing session state including source, destination, service, and tenant.

## Gotchas

- Only works on SSR devices.
- Session count can be very high on busy gateways.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_session.md](POST_sites_site_id_devices_device_id_clear_session.md) — Clear active sessions
- [POST_sites_site_id_devices_device_id_show_service_path.md](POST_sites_site_id_devices_device_id_show_service_path.md) — Service path table

## MistHelper Notes

Not currently used by MistHelper via REST API.
