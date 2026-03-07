# updateOrgPskPortal

> updateOrgPskPortal

## HTTP

`PUT /api/v1/orgs/{org_id}/pskportals/{pskportal_id}`

## Description

Update Org Psk Portal

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| pskportal_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "auth": {
      "type": "string",
      "description": "enum: `sponsor`, `sso`"
    },
    "bg_image_url": {
      "type": "string"
    },
    "cleanup_psk": {
      "type": "boolean",
      "description": "Used to cleanup exited psk when portal delete or ssid changed",
      "default": false
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "expire_time": {
      "type": "integer",
      "description": "unit min",
      "contentEncoding": "int32"
    },
    "expiry_notification_time": {
      "type": "integer",
      "description": "Number of days before psk is expired. Used as to when to start sending reminder notification when the psk is about to expire",
      "contentEncoding": "int32"
    },
    "hide_psks_created_by_other_admins": {
      "type": "boolean",
      "description": "Only if `type`==`admin`",
      "default": false
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
    "max_usage": {
      "type": "integer",
      "description": "`max_usage`==`0` means unlimited",
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
    "notification_renew_url": {
      "type": "string",
      "description": "Optional, will include the link in the notification email the customer can either provide their own url or use the one generate from mist, or do a url shorterner against either",
      "examples": [
        "https://custom-sso/url"
      ]
    },
    "notify_expiry": {
      "type": "boolean",
      "description": "If set to true, reminder notification will be sent when psk is about to expire"
    },
    "notify_on_create_or_edit": {
      "type": "boolean",
      "default": false
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "passphrase_rules": {
      "title": "psk_portal_passphrase_rules",
      "type": "object",
      "properties": {
        "alphabets_enabled": {
          "type": "boolean",
          "default": true
        },
        "length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "contentEncoding": "int32"
        },
        "max_length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "description": "For valid `max_length` and `min_length`, passphrase size is set randomly from that range.\n  - if `max_length` and/or `min_length` are invalid, passphrase size is equal to `length` parameter\n  - if `length` is not set or is invalid, default passphrase size is 8.\n  - valid `max_length`, `min_length`, `length` should be an integer between 8 to 63. Also, `max_length` > `min_length`",
          "contentEncoding": "int32"
        },
        "min_length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "description": "Ror valid `max_length` and `min_length`, passphrase size is set randomly from that range.\n  - if `max_length` and/or `min_length` are invalid, passphrase size is equal to `length` parameter\n  - if `length` is not set or is invalid, default passphrase size is 8.\n  - valid `max_length`, `min_length`, `length` should be an integer between 8 to 63. Also, `max_length` > `min_length`",
          "contentEncoding": "int32"
        },
        "numerics_enabled": {
          "type": "boolean",
          "default": true
        },
        "symbols": {
          "type": "string",
          "examples": [
            "()[]{}_%@#&$"
          ]
        },
        "symbols_enabled": {
          "type": "boolean",
          "default": true
        }
      }
    },
    "required_fields": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "what information to ask for (email is required by default)"
    },
    "role": {
      "type": "string"
    },
    "ssid": {
      "type": "string",
      "description": "intended SSID"
    },
    "sso": {
      "type": "object",
      "properties": {
        "allowed_roles": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Allowed roles for accessing psk portal, if none, any role is permitted"
        },
        "idp_cert": {
          "type": "string"
        },
        "idp_sign_algo": {
          "type": "string",
          "description": "Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`. enum: `sha1`, `sha256`, `sha384`, `sha512`"
        },
        "idp_sso_url": {
          "type": "string"
        },
        "issuer": {
          "type": "string"
        },
        "nameid_format": {
          "type": "string"
        },
        "role_mapping": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Property key is the role name, property value is the SSO Attribute"
        },
        "use_sso_role_for_psk_role": {
          "type": "boolean",
          "description": "If enabled, the `role` above will be ignored"
        }
      },
      "description": "If `auth`==`sso`"
    },
    "template_url": {
      "type": "string",
      "description": "UI customization"
    },
    "thumbnail_url": {
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "for personal psk portal. enum: `admin`, `byod`"
    },
    "ui_url": {
      "type": "string"
    },
    "vlan_id": {
      "type": "object"
    }
  },
  "required": [
    "name",
    "ssid"
  ]
}
```

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "auth": {
      "type": "string",
      "description": "enum: `sponsor`, `sso`"
    },
    "bg_image_url": {
      "type": "string"
    },
    "cleanup_psk": {
      "type": "boolean",
      "description": "Used to cleanup exited psk when portal delete or ssid changed",
      "default": false
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "expire_time": {
      "type": "integer",
      "description": "unit min",
      "contentEncoding": "int32"
    },
    "expiry_notification_time": {
      "type": "integer",
      "description": "Number of days before psk is expired. Used as to when to start sending reminder notification when the psk is about to expire",
      "contentEncoding": "int32"
    },
    "hide_psks_created_by_other_admins": {
      "type": "boolean",
      "description": "Only if `type`==`admin`",
      "default": false
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
    "max_usage": {
      "type": "integer",
      "description": "`max_usage`==`0` means unlimited",
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
    "notification_renew_url": {
      "type": "string",
      "description": "Optional, will include the link in the notification email the customer can either provide their own url or use the one generate from mist, or do a url shorterner against either",
      "examples": [
        "https://custom-sso/url"
      ]
    },
    "notify_expiry": {
      "type": "boolean",
      "description": "If set to true, reminder notification will be sent when psk is about to expire"
    },
    "notify_on_create_or_edit": {
      "type": "boolean",
      "default": false
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "passphrase_rules": {
      "title": "psk_portal_passphrase_rules",
      "type": "object",
      "properties": {
        "alphabets_enabled": {
          "type": "boolean",
          "default": true
        },
        "length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "contentEncoding": "int32"
        },
        "max_length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "description": "For valid `max_length` and `min_length`, passphrase size is set randomly from that range.\n  - if `max_length` and/or `min_length` are invalid, passphrase size is equal to `length` parameter\n  - if `length` is not set or is invalid, default passphrase size is 8.\n  - valid `max_length`, `min_length`, `length` should be an integer between 8 to 63. Also, `max_length` > `min_length`",
          "contentEncoding": "int32"
        },
        "min_length": {
          "maximum": 63.0,
          "minimum": 8.0,
          "type": "integer",
          "description": "Ror valid `max_length` and `min_length`, passphrase size is set randomly from that range.\n  - if `max_length` and/or `min_length` are invalid, passphrase size is equal to `length` parameter\n  - if `length` is not set or is invalid, default passphrase size is 8.\n  - valid `max_length`, `min_length`, `length` should be an integer between 8 to 63. Also, `max_length` > `min_length`",
          "contentEncoding": "int32"
        },
        "numerics_enabled": {
          "type": "boolean",
          "default": true
        },
        "symbols": {
          "type": "string",
          "examples": [
            "()[]{}_%@#&$"
          ]
        },
        "symbols_enabled": {
          "type": "boolean",
          "default": true
        }
      }
    },
    "required_fields": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "what information to ask for (email is required by default)"
    },
    "role": {
      "type": "string"
    },
    "ssid": {
      "type": "string",
      "description": "intended SSID"
    },
    "sso": {
      "type": "object",
      "properties": {
        "allowed_roles": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Allowed roles for accessing psk portal, if none, any role is permitted"
        },
        "idp_cert": {
          "type": "string"
        },
        "idp_sign_algo": {
          "type": "string",
          "description": "Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`. enum: `sha1`, `sha256`, `sha384`, `sha512`"
        },
        "idp_sso_url": {
          "type": "string"
        },
        "issuer": {
          "type": "string"
        },
        "nameid_format": {
          "type": "string"
        },
        "role_mapping": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Property key is the role name, property value is the SSO Attribute"
        },
        "use_sso_role_for_psk_role": {
          "type": "boolean",
          "description": "If enabled, the `role` above will be ignored"
        }
      },
      "description": "If `auth`==`sso`"
    },
    "template_url": {
      "type": "string",
      "description": "UI customization"
    },
    "thumbnail_url": {
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "for personal psk portal. enum: `admin`, `byod`"
    },
    "ui_url": {
      "type": "string"
    },
    "vlan_id": {
      "type": "object"
    }
  },
  "required": [
    "name",
    "ssid"
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

`mistapi.api.v1.orgs.psk_portals.updateOrgPskPortal()`

## Usage Context

Updates an existing PSK portal configuration.

## Gotchas

- Changes affect the self-service PSK provisioning experience.

## Related Endpoints

- [GET_orgs_org_id_pskportals_pskportal_id.md](GET_orgs_org_id_pskportals_pskportal_id.md) — Get PSK portal
- [POST_orgs_org_id_pskportals.md](POST_orgs_org_id_pskportals.md) — Create PSK portal

## MistHelper Notes

Not currently used by MistHelper directly.
