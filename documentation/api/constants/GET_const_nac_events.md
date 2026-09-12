# listNacEventsDefinitions

> listNacEventsDefinitions

## HTTP

`GET /api/v1/const/nac_events`

## Description

Get List of List of available NAC Client Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "const_nac_event",
    "type": "object",
    "properties": {
      "ap": {
        "type": "string",
        "examples": [
          "5c5b355008c0"
        ]
      },
      "bssid": {
        "type": "string",
        "examples": [
          "5c5b35548892"
        ]
      },
      "cert_cn": {
        "type": "string",
        "examples": [
          "suriyas"
        ]
      },
      "cert_expiry": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          1711557441
        ]
      },
      "cert_issuer": {
        "type": "string",
        "examples": [
          "/DC=net/DC=jnpr/CN=Juniper Networks Issuing AWS1 CA"
        ]
      },
      "cert_san_upn": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "suriyas@juniper.net"
          ]
        ]
      },
      "cert_serial": {
        "type": "string",
        "examples": [
          "1300103d29e56ef083797bedc2000100103d29"
        ]
      },
      "cert_subject": {
        "type": "string",
        "examples": [
          "/CN=suriyas/emailAddress=suriyas@juniper.net"
        ]
      },
      "eap_type": {
        "type": "string",
        "examples": [
          "EAP-TLS"
        ]
      },
      "nas_vendor": {
        "type": "string",
        "examples": [
          "Mist"
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
      "random_mac": {
        "type": "boolean",
        "examples": [
          true
        ]
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
        "type": "string",
        "examples": [
          "Test_Suriya-SSID"
        ]
      },
      "timestamp": {
        "type": "number",
        "description": "Epoch (seconds)",
        "readOnly": true
      },
      "type": {
        "type": "string",
        "examples": [
          "NAC_CLIENT_CERT_CHECK_SUCCESS"
        ]
      },
      "username": {
        "type": "string",
        "examples": [
          "suriyas@juniper.net"
        ]
      },
      "wcid": {
        "type": "string",
        "contentEncoding": "uuid",
        "examples": [
          "b43637b0-f0d9-0a1d-1ec2-73c394a9f679"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "ap": "5c5b355008c0",
        "bssid": "5c5b35548892",
        "cert_cn": "suriyas",
        "cert_expiry": 1711557441,
        "cert_issuer": "/DC=net/DC=jnpr/CN=Juniper Networks Issuing AWS1 CA",
        "cert_san_upn": [
          "suriyas@juniper.net"
        ],
        "cert_serial": "1300103d29e56ef083797bedc2000100103d29",
        "cert_subject": "/CN=suriyas/emailAddress=suriyas@juniper.net",
        "eap_type": "EAP-TLS",
        "nas_vendor": "Mist",
        "org_id": "94de66e8-556a-4d56-8780-a114620a5c42",
        "random_mac": true,
        "site_id": "b5a005ab-47d4-41f7-97bf-733f9cc252dd",
        "ssid": "Test_Suriya-SSID",
        "timestamp": 1685658478.438995,
        "type": "NAC_CLIENT_CERT_CHECK_SUCCESS",
        "username": "suriyas@juniper.net",
        "wcid": "b43637b0-f0d9-0a1d-1ec2-73c394a9f679"
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

`mistapi.api.v1.constants.events.listNacEventsDefinitions()`

## Usage Context

Returns definitions of all Network Access Control (NAC) event types, including authentication successes, failures, and policy enforcement outcomes. Use this to decode `type` values in NAC event search results for 802.1X and RADIUS troubleshooting.

## Gotchas

- NAC events are distinct from client events — NAC events focus on authentication/authorization, while client events cover connectivity lifecycle.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_client_events.md](GET_const_client_events.md) — Client event definitions (connectivity lifecycle)
- [../orgs/GET_orgs_org_id_nactags.md](../orgs/GET_orgs_org_id_nactags.md) — NAC tags for access control rules
- [../orgs/GET_orgs_org_id_nacrules.md](../orgs/GET_orgs_org_id_nacrules.md) — NAC rules configuration

## MistHelper Notes

Not currently used by MistHelper directly.
