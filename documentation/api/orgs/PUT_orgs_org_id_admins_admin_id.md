# updateOrgAdmin

> updateOrgAdmin

## HTTP

`PUT /api/v1/orgs/{org_id}/admins/{admin_id}`

## Description

Invite Org Admin

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| admin_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "admin_id": {
      "type": "string",
      "description": "ID of the administrator",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "456b7016-a916-a4b1-78dd-72b947c152b7"
      ]
    },
    "compliance_status": {
      "type": "string",
      "description": "trade compliance status. enum: `blocked`, `restricted`"
    },
    "email": {
      "type": "string",
      "description": "If admin account is not an Org API Token",
      "examples": [
        "jsnow@abc.com"
      ]
    },
    "enable_two_factor": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token",
      "readOnly": true
    },
    "expire_time": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "first_name": {
      "type": "string",
      "description": "If admin account is not an Org API Token. For an invite, this is the original first name used",
      "examples": [
        "John"
      ]
    },
    "hours": {
      "maximum": 168.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "If admin account is not an Org API Token, how long the invite should be valid",
      "contentEncoding": "int32",
      "default": 24
    },
    "last_name": {
      "type": "string",
      "description": "If admin account is not an Org API Token. For an invite, this is the original last name used",
      "examples": [
        "Sno"
      ]
    },
    "name": {
      "type": "string",
      "description": "For Org API Token Only"
    },
    "no_tracking": {
      "type": [
        "boolean",
        "null"
      ],
      "description": "Optional, whether to store privacy-consent information. When it doesn\u2019t exist, it\u2019s assumed true on EU (i.e. no tracking, the user has to opt-in); otherwise, the user would have to opt-out"
    },
    "oauth_google": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token",
      "readOnly": true
    },
    "password_modified_time": {
      "type": "number",
      "description": "Password last modified time, in epoch"
    },
    "phone": {
      "type": "string",
      "description": "If admin account is not an Org API Token. Phone number (numbers only, including country code)"
    },
    "phone2": {
      "type": "string",
      "description": "If admin account is not an Org API Token. Secondary phone number (numbers only, including country code)"
    },
    "privileges": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "admin_privilege",
        "required": [
          "role",
          "scope"
        ],
        "type": "object",
        "properties": {
          "msp_id": {
            "type": "string",
            "description": "Required if `scope`==`msp`",
            "contentEncoding": "uuid",
            "examples": [
              "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
            ]
          },
          "msp_logo_url": {
            "type": "string",
            "description": "Logo of the MSP (if the MSP belongs to an Advanced tier)",
            "readOnly": true
          },
          "msp_name": {
            "type": [
              "string",
              "null"
            ],
            "description": "Name of the MSP (if the org belongs to an MSP)",
            "readOnly": true
          },
          "msp_url": {
            "type": "string",
            "description": "Custom url of the MSP (if the MSP belongs to an Advanced tier)",
            "readOnly": true
          },
          "name": {
            "type": "string",
            "description": "Name of the org/site/MSP depending on object scope",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "description": "Required if `scope`==`org`",
            "contentEncoding": "uuid",
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "org_name": {
            "type": "string",
            "description": "Name of the org (for a site belonging to org)",
            "readOnly": true
          },
          "orggroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "If `scope`==`orggroup`"
          },
          "role": {
            "type": "string",
            "description": "access permissions. enum: `admin`, `helpdesk`, `installer`, `read`, `write`"
          },
          "scope": {
            "type": "string",
            "description": "enum: `msp`, `org`, `orggroup`, `site`, `sitegroup`"
          },
          "site_id": {
            "type": "string",
            "description": "Required if `scope`==`site`",
            "contentEncoding": "uuid",
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "sitegroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": ""
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
        "description": "Privilieges settings"
      },
      "description": "List of privileges the admin has"
    },
    "session_expiry": {
      "maximum": 20160.0,
      "minimum": 10.0,
      "type": "integer",
      "contentEncoding": "int64",
      "readOnly": true,
      "examples": [
        1440
      ]
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "readOnly": true
    },
    "two_factor_verified": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token. Two factor status",
      "readOnly": true
    },
    "via_sso": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token, an admin login via_sso is more restircted. (password and email cannot be changed)",
      "readOnly": true
    }
  },
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
    "admin_id": {
      "type": "string",
      "description": "ID of the administrator",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "456b7016-a916-a4b1-78dd-72b947c152b7"
      ]
    },
    "compliance_status": {
      "type": "string",
      "description": "trade compliance status. enum: `blocked`, `restricted`"
    },
    "email": {
      "type": "string",
      "description": "If admin account is not an Org API Token",
      "examples": [
        "jsnow@abc.com"
      ]
    },
    "enable_two_factor": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token",
      "readOnly": true
    },
    "expire_time": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "first_name": {
      "type": "string",
      "description": "If admin account is not an Org API Token. For an invite, this is the original first name used",
      "examples": [
        "John"
      ]
    },
    "hours": {
      "maximum": 168.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "If admin account is not an Org API Token, how long the invite should be valid",
      "contentEncoding": "int32",
      "default": 24
    },
    "last_name": {
      "type": "string",
      "description": "If admin account is not an Org API Token. For an invite, this is the original last name used",
      "examples": [
        "Sno"
      ]
    },
    "name": {
      "type": "string",
      "description": "For Org API Token Only"
    },
    "no_tracking": {
      "type": [
        "boolean",
        "null"
      ],
      "description": "Optional, whether to store privacy-consent information. When it doesn\u2019t exist, it\u2019s assumed true on EU (i.e. no tracking, the user has to opt-in); otherwise, the user would have to opt-out"
    },
    "oauth_google": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token",
      "readOnly": true
    },
    "password_modified_time": {
      "type": "number",
      "description": "Password last modified time, in epoch"
    },
    "phone": {
      "type": "string",
      "description": "If admin account is not an Org API Token. Phone number (numbers only, including country code)"
    },
    "phone2": {
      "type": "string",
      "description": "If admin account is not an Org API Token. Secondary phone number (numbers only, including country code)"
    },
    "privileges": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "admin_privilege",
        "required": [
          "role",
          "scope"
        ],
        "type": "object",
        "properties": {
          "msp_id": {
            "type": "string",
            "description": "Required if `scope`==`msp`",
            "contentEncoding": "uuid",
            "examples": [
              "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
            ]
          },
          "msp_logo_url": {
            "type": "string",
            "description": "Logo of the MSP (if the MSP belongs to an Advanced tier)",
            "readOnly": true
          },
          "msp_name": {
            "type": [
              "string",
              "null"
            ],
            "description": "Name of the MSP (if the org belongs to an MSP)",
            "readOnly": true
          },
          "msp_url": {
            "type": "string",
            "description": "Custom url of the MSP (if the MSP belongs to an Advanced tier)",
            "readOnly": true
          },
          "name": {
            "type": "string",
            "description": "Name of the org/site/MSP depending on object scope",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "description": "Required if `scope`==`org`",
            "contentEncoding": "uuid",
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "org_name": {
            "type": "string",
            "description": "Name of the org (for a site belonging to org)",
            "readOnly": true
          },
          "orggroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "If `scope`==`orggroup`"
          },
          "role": {
            "type": "string",
            "description": "access permissions. enum: `admin`, `helpdesk`, `installer`, `read`, `write`"
          },
          "scope": {
            "type": "string",
            "description": "enum: `msp`, `org`, `orggroup`, `site`, `sitegroup`"
          },
          "site_id": {
            "type": "string",
            "description": "Required if `scope`==`site`",
            "contentEncoding": "uuid",
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "sitegroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": ""
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
        "description": "Privilieges settings"
      },
      "description": "List of privileges the admin has"
    },
    "session_expiry": {
      "maximum": 20160.0,
      "minimum": 10.0,
      "type": "integer",
      "contentEncoding": "int64",
      "readOnly": true,
      "examples": [
        1440
      ]
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "readOnly": true
    },
    "two_factor_verified": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token. Two factor status",
      "readOnly": true
    },
    "via_sso": {
      "type": "boolean",
      "description": "If admin account is not an Org API Token, an admin login via_sso is more restircted. (password and email cannot be changed)",
      "readOnly": true
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

`mistapi.api.v1.orgs.admins.updateOrgAdmin()`

## Usage Context

Updates an org admin's role or privileges.

## Gotchas

- Cannot change your own role. Another admin must do it.

## Related Endpoints

- [GET_orgs_org_id_admins.md](GET_orgs_org_id_admins.md) — List admins
- [DELETE_orgs_org_id_admins_admin_id.md](DELETE_orgs_org_id_admins_admin_id.md) — Revoke admin

## MistHelper Notes

Not currently used by MistHelper directly.
