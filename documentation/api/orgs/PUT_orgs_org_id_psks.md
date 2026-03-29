# updateOrgMultiplePsks

> updateOrgMultiplePsks

## HTTP

`PUT /api/v1/orgs/{org_id}/psks`

## Description

Update Multiple PSKs

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
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "psk",
    "required": [
      "name",
      "passphrase",
      "ssid"
    ],
    "type": "object",
    "properties": {
      "admin_sso_id": {
        "type": "string",
        "description": "sso id for psk created from psk portal",
        "readOnly": true
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "email": {
        "type": "string",
        "description": "email to send psk expiring notifications to"
      },
      "expire_time": {
        "type": [
          "integer",
          "null"
        ],
        "description": "Expire time for this PSK key (epoch time in seconds). Default `null` (as no expiration)",
        "contentEncoding": "int32",
        "examples": [
          1614990263
        ]
      },
      "expiry_notification_time": {
        "type": "integer",
        "description": "Number of days before psk is expired. Used as to when to start sending reminder notification when the psk is about to expire",
        "contentEncoding": "int32"
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
        "type": "string",
        "description": "If `usage`==`single`, the mac that this PSK ties to, empty if `auto-binding`"
      },
      "macs": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `usage`==`macs`, this list contains N number of client mac addresses or mac patterns(1122*) or both. This list is capped at 5000",
        "examples": [
          [
            "112233abcedf",
            "aabbcc*"
          ]
        ]
      },
      "max_usage": {
        "type": "integer",
        "description": "For Org PSK Only. Max concurrent users for this PSK key. Default is 0 (unlimited)",
        "contentEncoding": "int32",
        "default": 0
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string"
      },
      "note": {
        "type": "string"
      },
      "notify_expiry": {
        "type": "boolean",
        "description": "If set to true, reminder notification will be sent when psk is about to expire",
        "default": false
      },
      "notify_on_create_or_edit": {
        "type": "boolean",
        "description": "If set to true, notification will be sent when psk is created or edited"
      },
      "old_passphrase": {
        "type": "string",
        "description": "previous passphrase of the PSK if it has been rotated"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "passphrase": {
        "maxLength": 64,
        "minLength": 8,
        "type": "string",
        "description": "passphrase of the PSK (8-63 character or 64 in hex)"
      },
      "role": {
        "maxLength": 32,
        "minLength": 0,
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
      "ssid": {
        "type": "string",
        "description": "SSID this PSK should be applicable to"
      },
      "usage": {
        "type": "string",
        "description": "enum: `macs`, `multi`, `single`"
      },
      "vlan_id": {
        "type": "object",
        "description": "VLAN for this PSK key"
      }
    },
    "description": "PSK"
  },
  "description": "",
  "examples": [
    [
      {
        "expire_time": 1614990263,
        "mac": "string",
        "max_usage": 0,
        "name": "string",
        "passphrase": "secretpsk",
        "ssid": "string",
        "usage": "multi",
        "vlan_id": 10
      }
    ]
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "psk",
    "required": [
      "name",
      "passphrase",
      "ssid"
    ],
    "type": "object",
    "properties": {
      "admin_sso_id": {
        "type": "string",
        "description": "sso id for psk created from psk portal",
        "readOnly": true
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "email": {
        "type": "string",
        "description": "email to send psk expiring notifications to"
      },
      "expire_time": {
        "type": [
          "integer",
          "null"
        ],
        "description": "Expire time for this PSK key (epoch time in seconds). Default `null` (as no expiration)",
        "contentEncoding": "int32",
        "examples": [
          1614990263
        ]
      },
      "expiry_notification_time": {
        "type": "integer",
        "description": "Number of days before psk is expired. Used as to when to start sending reminder notification when the psk is about to expire",
        "contentEncoding": "int32"
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
        "type": "string",
        "description": "If `usage`==`single`, the mac that this PSK ties to, empty if `auto-binding`"
      },
      "macs": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `usage`==`macs`, this list contains N number of client mac addresses or mac patterns(1122*) or both. This list is capped at 5000",
        "examples": [
          [
            "112233abcedf",
            "aabbcc*"
          ]
        ]
      },
      "max_usage": {
        "type": "integer",
        "description": "For Org PSK Only. Max concurrent users for this PSK key. Default is 0 (unlimited)",
        "contentEncoding": "int32",
        "default": 0
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string"
      },
      "note": {
        "type": "string"
      },
      "notify_expiry": {
        "type": "boolean",
        "description": "If set to true, reminder notification will be sent when psk is about to expire",
        "default": false
      },
      "notify_on_create_or_edit": {
        "type": "boolean",
        "description": "If set to true, notification will be sent when psk is created or edited"
      },
      "old_passphrase": {
        "type": "string",
        "description": "previous passphrase of the PSK if it has been rotated"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "passphrase": {
        "maxLength": 64,
        "minLength": 8,
        "type": "string",
        "description": "passphrase of the PSK (8-63 character or 64 in hex)"
      },
      "role": {
        "maxLength": 32,
        "minLength": 0,
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
      "ssid": {
        "type": "string",
        "description": "SSID this PSK should be applicable to"
      },
      "usage": {
        "type": "string",
        "description": "enum: `macs`, `multi`, `single`"
      },
      "vlan_id": {
        "type": "object",
        "description": "VLAN for this PSK key"
      }
    },
    "description": "PSK"
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 0,
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "mac": "string",
        "modified_time": 0,
        "name": "string",
        "org_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "passphrase": "secretpsk",
        "site_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "ssid": "string",
        "usage": "multi",
        "vlan_id": 1
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

`mistapi.api.v1.orgs.psks.updateOrgMultiplePsks()`

## Usage Context

Bulk-updates multiple PSKs in the organization.

## Gotchas

- Accepts an array of PSK objects with their IDs for batch modification.

## Related Endpoints

- [GET_orgs_org_id_psks.md](GET_orgs_org_id_psks.md) — List PSKs
- [PUT_orgs_org_id_psks_psk_id.md](PUT_orgs_org_id_psks_psk_id.md) — Update single PSK

## MistHelper Notes

PSK listing uses Menu 46 (`listOrgPsks`). Bulk update is not used directly.
