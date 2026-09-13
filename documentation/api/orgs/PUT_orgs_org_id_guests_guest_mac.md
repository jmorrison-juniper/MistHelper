# updateOrgGuestAuthorization

> updateOrgGuestAuthorization

## HTTP

`PUT /api/v1/orgs/{org_id}/guests/{guest_mac}`

## Description

Update Guest Authorization

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| guest_mac | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "access_code_email": {
      "type": "string",
      "description": "If `auth_method`==`email`, the email address where the authorization code has been sent to",
      "readOnly": true
    },
    "allow_wlan_id_roam": {
      "type": "boolean",
      "description": "Based on the WLAN portal configuration (field `allow_wlan_id_roam`), if the user is also authorized on other Guest WLANs of the same Org without reauthentication",
      "readOnly": true
    },
    "ap_mac": {
      "type": "string",
      "description": "MAC Address of the AP the guest was connected to during the registration process",
      "readOnly": true
    },
    "auth_method": {
      "type": "string",
      "description": "Type of guest authorization",
      "readOnly": true
    },
    "authorized": {
      "type": "boolean",
      "description": "Whether the guest is current authorized",
      "default": true
    },
    "authorized_expiring_time": {
      "type": "number",
      "description": "When the authorization would expire",
      "readOnly": true,
      "examples": [
        1480704955
      ]
    },
    "authorized_time": {
      "type": "number",
      "description": "When the guest was authorized",
      "readOnly": true,
      "examples": [
        1480704355
      ]
    },
    "company": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "examples": [
        "abc"
      ]
    },
    "cross_site": {
      "type": "boolean",
      "description": "Based on the WLAN portal configuration (field `cross_site`), if the user is also authorized on other sites (same `wlan.ssid`) of the same Org without reauthentication",
      "readOnly": true
    },
    "email": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "examples": [
        "john@abc.com"
      ]
    },
    "field1": {
      "type": "string",
      "description": "Optional, the info provided by user"
    },
    "field2": {
      "type": "string"
    },
    "field3": {
      "type": "string"
    },
    "field4": {
      "type": "string"
    },
    "mac": {
      "type": "string",
      "description": "MAC"
    },
    "minutes": {
      "maximum": 259200.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Authorization duration, in minutes. Default is 1440 minutes (1 day), maximum is 259200 (180 days)",
      "contentEncoding": "int32",
      "default": 1440
    },
    "name": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "examples": [
        "John Smith"
      ]
    },
    "random_mac": {
      "type": "boolean",
      "description": "If the client is using a randomized MAC Address to connect the SSID",
      "readOnly": true
    },
    "ssid": {
      "type": "string",
      "description": "Name of the SSID",
      "readOnly": true,
      "examples": [
        "Guest-SSID"
      ]
    },
    "wlan_id": {
      "type": "string",
      "description": "ID of the WLAN",
      "contentEncoding": "uuid",
      "examples": [
        "6748cfa6-4e12-11e6-9188-0242ac110007"
      ]
    }
  },
  "required": [
    "wlan_id"
  ],
  "description": "Guest"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "access_code_email": {
      "type": "string",
      "description": "If `auth_method`==`email`, the email address where the authorization code has been sent to",
      "readOnly": true
    },
    "ap_mac": {
      "type": "string",
      "description": "MAC Address of the AP the guest was connected to during the registration process",
      "readOnly": true
    },
    "auth_method": {
      "type": "string",
      "description": "Type of guest authorization",
      "readOnly": true
    },
    "authorized": {
      "type": "boolean",
      "description": "Whether the guest is current authorized",
      "default": true
    },
    "authorized_expiring_time": {
      "type": "number",
      "description": "When the authorization would expire",
      "readOnly": true,
      "examples": [
        1480704955
      ]
    },
    "authorized_time": {
      "type": "number",
      "description": "When the guest was authorized",
      "readOnly": true,
      "examples": [
        1480704355
      ]
    },
    "company": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "examples": [
        "abc"
      ]
    },
    "email": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "examples": [
        "john@abc.com"
      ]
    },
    "field1": {
      "type": "string",
      "description": "Optional, the info provided by user"
    },
    "field2": {
      "type": "string"
    },
    "field3": {
      "type": "string"
    },
    "field4": {
      "type": "string"
    },
    "mac": {
      "type": "string",
      "description": "MAC Address",
      "readOnly": true
    },
    "minutes": {
      "maximum": 259200.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Authorization duration, in minutes. Default is 1440 minutes (1 day), maximum is 259200 (180 days)",
      "contentEncoding": "int32",
      "default": 1440
    },
    "name": {
      "type": "string",
      "description": "Optional, the info provided by user",
      "readOnly": true,
      "examples": [
        "John Smith"
      ]
    },
    "random_mac": {
      "type": "boolean",
      "description": "If the client is using a randomized MAC Address to connect the SSID",
      "readOnly": true
    },
    "ssid": {
      "type": "string",
      "description": "Name of the SSID",
      "readOnly": true,
      "examples": [
        "Guest-SSID"
      ]
    },
    "wlan_id": {
      "type": "string",
      "description": "ID of the SSID",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "6748cfa6-4e12-11e6-9188-0242ac110007"
      ]
    }
  },
  "description": "Guest"
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

`mistapi.api.v1.orgs.guests.updateOrgGuestAuthorization()`

## Usage Context

Updates a guest authorization entry by MAC address.

## Gotchas

- The guest MAC is the identifier, not a UUID.

## Related Endpoints

- [GET_orgs_org_id_guests_search.md](GET_orgs_org_id_guests_search.md) — Search guests
- [DELETE_orgs_org_id_guests_guest_mac.md](DELETE_orgs_org_id_guests_guest_mac.md) — Delete guest

## MistHelper Notes

Not currently used by MistHelper directly.
