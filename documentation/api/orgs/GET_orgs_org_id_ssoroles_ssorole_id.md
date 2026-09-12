# getOrgSsoRole

> getOrgSsoRole

## HTTP

`GET /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}`

## Description

Get Org SSO Role Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| ssorole_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "60f6bfdb-2f45-4022-8e2a-e00d977953fe"
      ]
    },
    "privileges": {
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
      "description": ""
    }
  },
  "required": [
    "name",
    "privileges"
  ],
  "description": "SSO Role response"
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

`mistapi.api.v1.orgs.sso_roles.getOrgSsoRole()`

## Usage Context

Retrieves a specific SSO role by ID.

## Gotchas

- SSO roles map IdP group attributes to Mist RBAC privileges.

## Related Endpoints

- [GET_orgs_org_id_ssoroles.md](GET_orgs_org_id_ssoroles.md) — List roles
- [PUT_orgs_org_id_ssoroles_ssorole_id.md](PUT_orgs_org_id_ssoroles_ssorole_id.md) — Update role

## MistHelper Notes

Not currently used by MistHelper directly.
