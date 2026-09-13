# listSiteAllGuestAuthorizationsDerived

> listSiteAllGuestAuthorizationsDerived

## HTTP

`GET /api/v1/sites/{site_id}/guests/derived`

## Description

Get the list of derived Guest Authorizations for a site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| wlan_id | string | No |  |  | UUID of single or multiple (Comma separated) WLAN under Site `site_id` (to filter by WLAN) |
| cross_site | boolean | No | False |  | Whether to get org level guests, default is false i.e get site level guests |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "guest",
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
  },
  "description": "",
  "examples": [
    "[{\"authorized\":true,\"authorized_expiring_time\":0,\"authorized_time\":0,\"company\":\"string\",\"email\":\"user@example.com\",\"field1\":\"string\",\"field2\":\"string\",\"field3\":\"string\",\"field4\":\"string\",\"mac\":\"string\",\"minutes\":0,\"name\":\"string\"}]",
    "[{\"authorized\":true,\"authorized_expiring_time\":1480704955,\"authorized_time\":1480704355,\"company\":\"abc\",\"email\":\"john@abc.com\",\"field1\":\"xxx\",\"mac\":\"5684dae9ac8b\",\"name\":\"John Smith\"}]"
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

`mistapi.api.v1.sites.guests.listSiteAllGuestAuthorizationsDerived()`

## Usage Context

Retrieves the derived guest authorization list for a site, including guests authorized via org-level policies and templates.

## Gotchas

- Includes guests from all authorization sources (site + org + WLAN portal).

## Related Endpoints

- [GET_sites_site_id_guests_search.md](GET_sites_site_id_guests_search.md) — Search guests
- [GET_sites_site_id_guests_count.md](GET_sites_site_id_guests_count.md) — Count guests

## MistHelper Notes

Not currently used by MistHelper directly.
