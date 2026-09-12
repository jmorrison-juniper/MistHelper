# getOrgOtherDevice

> getOrgOtherDevice

## HTTP

`GET /api/v1/orgs/{org_id}/otherdevices/{device_mac}`

## Description

Get Org other device (3rd party device)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "device_mac": {
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
    "mac": {
      "type": "string"
    },
    "model": {
      "type": "string"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "serial": {
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
    "state": {
      "type": "string"
    },
    "vendor": {
      "type": "string"
    },
    "vendor_api_id": {
      "type": "string"
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

`mistapi.api.v1.orgs.devices_-_others.getOrgOtherDevice()`

## Usage Context

Retrieves details for a specific non-Juniper device by MAC address.

## Gotchas

- Other devices include third-party switches and routers managed via Mist.

## Related Endpoints

- [GET_orgs_org_id_otherdevices.md](GET_orgs_org_id_otherdevices.md) — List other devices
- [GET_orgs_org_id_otherdevices_events_search.md](GET_orgs_org_id_otherdevices_events_search.md) — Events

## MistHelper Notes

Not currently used by MistHelper directly.
