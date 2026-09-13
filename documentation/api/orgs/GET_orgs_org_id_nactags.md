# listOrgNacTags

> listOrgNacTags

## HTTP

`GET /api/v1/orgs/{org_id}/nactags`

## Description

Get List of Org NAC Tags

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | Type of NAC Tag. enum: `egress_vlan_names`, `gbp_tag`, `match`, `radius_attrs`, `radius_group`, `radius_vendor_attrs`, `session_timeout`, `username_attr`, `vlan` |
| name | string | No |  |  | Name of NAC Tag |
| match | string | No |  |  | if `type`==`match`, Type of NAC Tag. enum: `cert_cn`, `cert_eku`, `cert_issuer`, `cert_san`, `cert_serial`, `cert_sub`, `cert_template`, `client_mac`, `edr_status`, `gbp_tag`, `hostname`, `idp_role`, `ingress_vlan`, `mdm_status`, `nas_ip`, `radius_group`, `realm`, `ssid`, `user_name`, `usermac_label` |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "nac_tag",
    "required": [
      "name",
      "type"
    ],
    "type": "object",
    "properties": {
      "allow_usermac_override": {
        "type": "boolean",
        "description": "Can be set to true to allow the override by usermac result",
        "default": false
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "egress_vlan_names": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`egress_vlan_names`, list of egress vlans to return",
        "examples": [
          [
            "1vlan-30",
            "1vlan-20",
            "2-vlan10"
          ]
        ]
      },
      "gbp_tag": {
        "type": "object",
        "description": "If `type`==`gbp_tag`"
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
      "match": {
        "type": "string",
        "description": "if `type`==`match`. enum: `cert_cn`, `cert_eku`, `cert_issuer`, `cert_san`, `cert_serial`, `cert_sub`, `cert_template`, `client_mac`, `edr_status`, `gbp_tag`, `hostname`, `idp_role`, `ingress_vlan`, `mdm_status`, `nas_ip`, `radius_group`, `realm`, `ssid`, `user_name`, `usermac_label`"
      },
      "match_all": {
        "type": "boolean",
        "description": "This field is applicable only when `type`==`match`\n  * `false`: means it is sufficient to match any of the values (i.e., match-any behavior)\n  * `true`: means all values should be matched (i.e., match-all behavior)\n\n\nCurrently it makes sense to set this field to `true` only if the `match`==`idp_role`, `match`==`usermac_label` and `edr_status`",
        "default": false
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "nacportal_id": {
        "type": "string",
        "description": "If `type`==`redirect_nacportal_id`, the ID of the NAC portal to redirect to",
        "contentEncoding": "uuid",
        "examples": [
          "1e970fec-0a7a-4d73-a472-3ef3b6a456aa"
        ]
      },
      "name": {
        "minLength": 1,
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
      "radius_attrs": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`radius_attrs`, user can specify a list of one or more standard attributes in the field \"radius_attrs\". \nIt is the responsibility of the user to provide a syntactically correct string, otherwise it may not work as expected.\nNote that it is allowed to have more than one radius_attrs in the result of a given rule.",
        "examples": [
          [
            "Idle-Timeout=600",
            "Termination-Action=RADIUS-Request"
          ]
        ]
      },
      "radius_group": {
        "type": "string",
        "description": "If `type`==`radius_group`"
      },
      "radius_vendor_attrs": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`radius_vendor_attrs`, user can specify a list of one or more vendor-specific attributes in the field \"radius_vendor_attrs\". \nIt is the responsibility of the user to provide a syntactically correct string, otherwise it may not work as expected.\nNote that it is allowed to have more than one radius_vendor_attrs in the result of a given rule.",
        "examples": [
          [
            "PaloAlto-Admin-Role=superuser",
            "PaloAlto-Panorama-Admin-Role=administrator"
          ]
        ]
      },
      "session_timeout": {
        "type": "integer",
        "description": "If `type`==`session_timeout, in seconds",
        "contentEncoding": "int32",
        "examples": [
          86000
        ]
      },
      "type": {
        "type": "string",
        "description": "enum: `egress_vlan_names`, `gbp_tag`, `match`, `radius_attrs`, `radius_group`, `radius_vendor_attrs`, `redirect_nacportal_id`, `session_timeout`, `username_attr`, `vlan`"
      },
      "username_attr": {
        "type": "string",
        "description": "enum: `automatic`, `cn`, `dns`, `email`, `upn`"
      },
      "values": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`match`"
      },
      "vlan": {
        "type": "string",
        "description": "If `type`==`vlan`"
      }
    }
  },
  "description": ""
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.nac_tags.listOrgNacTags()`

## Usage Context

Lists all NAC tags for the organization.

## Gotchas

- Tags define matching criteria used in NAC rules.

## Related Endpoints

- [GET_orgs_org_id_nactags_nactag_id.md](GET_orgs_org_id_nactags_nactag_id.md) — Get specific tag
- [POST_orgs_org_id_nactags.md](POST_orgs_org_id_nactags.md) — Create tag

## MistHelper Notes

Used by MistHelper via `listOrgNacTags` in Menu 44.
