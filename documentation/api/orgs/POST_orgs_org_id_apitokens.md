# createOrgApiToken

> createOrgApiToken

## HTTP

`POST /api/v1/orgs/{org_id}/apitokens`

## Description

Create Org API Token
Note that the token key is only available during creation time.

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
  "title": "org_apitoken",
  "required": [
    "name"
  ],
  "type": "object",
  "properties": {
    "created_by": {
      "type": [
        "string",
        "null"
      ],
      "description": "email of the token creator / null if creator is deleted",
      "readOnly": true,
      "examples": [
        "user@mycorp.com"
      ]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
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
    "key": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "1qkb...QQCL"
      ]
    },
    "last_used": {
      "type": [
        "number",
        "null"
      ],
      "readOnly": true,
      "examples": [
        1690115110
      ]
    },
    "name": {
      "type": "string",
      "description": "Name of the token",
      "examples": [
        "org_token_xyz"
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
    "privileges": {
      "maxItems": 10,
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "privilege_org",
        "required": [
          "role",
          "scope"
        ],
        "type": "object",
        "properties": {
          "org_id": {
            "type": "string",
            "description": "If `scope`==`org`",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "role": {
            "type": "string",
            "description": "access permissions. enum: `admin`, `helpdesk`, `installer`, `read`, `write`"
          },
          "scope": {
            "type": "string",
            "description": "enum: `org`, `site`, `sitegroup`, `orgsites`"
          },
          "site_id": {
            "type": "string",
            "description": "If `scope`==`site`",
            "contentEncoding": "uuid"
          },
          "sitegroup_id": {
            "type": "string",
            "description": "If `scope`==`sitegroup`",
            "contentEncoding": "uuid"
          },
          "view": {
            "type": "string",
            "description": "Used for backward compatibility. Use `views` instead.",
            "deprecated": true
          },
          "views": {
            "type": "array",
            "items": {
              "title": "admin_privilege_view",
              "enum": [
                "lobby_admin",
                "location",
                "marketing",
                "mxedge_admin",
                "reporting",
                "security",
                "super_observer",
                "switch_admin"
              ],
              "type": "string"
            },
            "description": "Custom roles restrict Org users to specific UI views. This is useful for limiting UI access of Org users. Custom roles restrict Org users to specific UI views. This is useful for limiting UI access of Org users.  \nYou can define custom roles by adding the `views` attribute along with `role` when assigning privileges.  \nBelow are the list of supported UI views. Note that this is UI only feature.  \n\n  | UI View | Required Role | Description |\n  | --- | --- | --- |\n  | `reporting` | `read` | full access to all analytics tools |\n  | `marketing` | `read` | can view analytics and location maps |\n  | `super_observer` | `read` | can view all the organization except the subscription page |\n  | `location` | `write` | can view and manage location maps, can view analytics |\n  | `security` | `write` | can view and manage site labels, policies and security |\n  | `switch_admin` | `helpdesk` | can view and manage Switch ports, can view wired clients |\n  | `mxedge_admin` | `admin` | can view and manage Mist edges and Mist tunnels |\n  | `lobby_admin` | `admin` | full access to Org and Site Pre-shared keys |"
          }
        },
        "description": "Privileges settings"
      },
      "description": "List of privileges the token has on the orgs/sites",
      "examples": [
        [
          {
            "role": "admin",
            "scope": "org"
          }
        ]
      ]
    },
    "src_ips": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of allowed IP addresses from where the token can be used from. At most 10 IP addresses can be specified, cannot be changed once the API Token is created.",
      "examples": [
        [
          "63.3.56.0/24",
          "63.3.55.4"
        ]
      ]
    }
  },
  "description": "Org API Token\n\n**Note:**\n`privilege` field is required to create the object, but may not be \nreturned in the POST API Response (only in the afterward GET)"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_by": {
      "type": [
        "string",
        "null"
      ],
      "description": "email of the token creator / null if creator is deleted",
      "readOnly": true,
      "examples": [
        "user@mycorp.com"
      ]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
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
    "key": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "1qkb...QQCL"
      ]
    },
    "last_used": {
      "type": [
        "number",
        "null"
      ],
      "readOnly": true,
      "examples": [
        1690115110
      ]
    },
    "name": {
      "type": "string",
      "description": "Name of the token",
      "examples": [
        "org_token_xyz"
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
    "privileges": {
      "maxItems": 10,
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "privilege_org",
        "required": [
          "role",
          "scope"
        ],
        "type": "object",
        "properties": {
          "org_id": {
            "type": "string",
            "description": "If `scope`==`org`",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "role": {
            "type": "string",
            "description": "access permissions. enum: `admin`, `helpdesk`, `installer`, `read`, `write`"
          },
          "scope": {
            "type": "string",
            "description": "enum: `org`, `site`, `sitegroup`, `orgsites`"
          },
          "site_id": {
            "type": "string",
            "description": "If `scope`==`site`",
            "contentEncoding": "uuid"
          },
          "sitegroup_id": {
            "type": "string",
            "description": "If `scope`==`sitegroup`",
            "contentEncoding": "uuid"
          },
          "view": {
            "type": "string",
            "description": "Used for backward compatibility. Use `views` instead.",
            "deprecated": true
          },
          "views": {
            "type": "array",
            "items": {
              "title": "admin_privilege_view",
              "enum": [
                "lobby_admin",
                "location",
                "marketing",
                "mxedge_admin",
                "reporting",
                "security",
                "super_observer",
                "switch_admin"
              ],
              "type": "string"
            },
            "description": "Custom roles restrict Org users to specific UI views. This is useful for limiting UI access of Org users. Custom roles restrict Org users to specific UI views. This is useful for limiting UI access of Org users.  \nYou can define custom roles by adding the `views` attribute along with `role` when assigning privileges.  \nBelow are the list of supported UI views. Note that this is UI only feature.  \n\n  | UI View | Required Role | Description |\n  | --- | --- | --- |\n  | `reporting` | `read` | full access to all analytics tools |\n  | `marketing` | `read` | can view analytics and location maps |\n  | `super_observer` | `read` | can view all the organization except the subscription page |\n  | `location` | `write` | can view and manage location maps, can view analytics |\n  | `security` | `write` | can view and manage site labels, policies and security |\n  | `switch_admin` | `helpdesk` | can view and manage Switch ports, can view wired clients |\n  | `mxedge_admin` | `admin` | can view and manage Mist edges and Mist tunnels |\n  | `lobby_admin` | `admin` | full access to Org and Site Pre-shared keys |"
          }
        },
        "description": "Privileges settings"
      },
      "description": "List of privileges the token has on the orgs/sites",
      "examples": [
        [
          {
            "role": "admin",
            "scope": "org"
          }
        ]
      ]
    },
    "src_ips": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of allowed IP addresses from where the token can be used from. At most 10 IP addresses can be specified, cannot be changed once the API Token is created.",
      "examples": [
        [
          "63.3.56.0/24",
          "63.3.55.4"
        ]
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Org API Token\n\n**Note:**\n`privilege` field is required to create the object, but may not be \nreturned in the POST API Response (only in the afterward GET)"
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

`mistapi.api.v1.orgs.api_tokens.createOrgApiToken()`

## Usage Context

Creates a new API token for the organization.

## Gotchas

- The token value is only returned once at creation time. Store it securely.
- Tokens have configurable privileges and expiry.

## Related Endpoints

- [GET_orgs_org_id_apitokens.md](GET_orgs_org_id_apitokens.md) — List tokens
- [PUT_orgs_org_id_apitokens_apitoken_id.md](PUT_orgs_org_id_apitokens_apitoken_id.md) — Update token

## MistHelper Notes

Not currently used by MistHelper directly.
