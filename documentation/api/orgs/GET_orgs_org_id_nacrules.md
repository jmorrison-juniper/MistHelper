# listOrgNacRules

> listOrgNacRules

## HTTP

`GET /api/v1/orgs/{org_id}/nacrules`

## Description

Get List of Org NAC Rules

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
    "title": "nac_rule",
    "required": [
      "action",
      "name"
    ],
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "enum: `allow`, `block`"
      },
      "apply_tags": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "All optional, this goes into Access-Accept",
        "examples": [
          [
            "c049dfcd-0c73-5014-1c64-062e9903f1e5"
          ]
        ]
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "enabled": {
        "type": "boolean",
        "description": "Enabled or not",
        "default": true
      },
      "guest_auth_state": {
        "type": "string",
        "description": "Guest portal authorization state. enum: `authorized`, `unknown`"
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
      "matching": {
        "title": "nac_rule_matching",
        "type": "object",
        "properties": {
          "auth_type": {
            "type": "string",
            "description": "enum: `cert`, `device-auth`, `eap-teap`, `eap-tls`, `eap-ttls`, `idp`, `mab`, `eap-peap`"
          },
          "family": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device families to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed family values"
          },
          "mfg": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device models to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed model values"
          },
          "model": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device manufacturers to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed mfg values"
          },
          "nactags": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "041d5d36-716c-4cfb-4988-3857c6aa14a2",
                "a809a97f-d599-f812-eb8c-c3f84aabf6ba"
              ]
            ]
          },
          "os_type": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device os types to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed os_type values"
          },
          "port_types": {
            "type": "array",
            "items": {
              "title": "nac_rule_matching_port_type",
              "enum": [
                "wired",
                "wireless"
              ],
              "type": "string",
              "description": "enum: `wired`, `wireless`"
            },
            "description": "",
            "examples": [
              [
                "wired"
              ]
            ]
          },
          "site_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of site ids to match",
            "examples": [
              [
                "bb19fc3e-4124-4b57-80d9-c3f6edce47c4",
                "bb19fc3e-6564-4b57-80d9-c3f6edce47c1"
              ]
            ]
          },
          "sitegroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of sitegroup ids to match",
            "examples": [
              [
                "bb19fc3e-4124-4b57-80d9-c3f6edce47c4",
                "bb19fc3e-6564-4b57-80d9-c3f6edce47c1"
              ]
            ]
          },
          "vendor": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of vendors to match"
          }
        }
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string"
      },
      "not_matching": {
        "title": "nac_rule_matching",
        "type": "object",
        "properties": {
          "auth_type": {
            "type": "string",
            "description": "enum: `cert`, `device-auth`, `eap-teap`, `eap-tls`, `eap-ttls`, `idp`, `mab`, `eap-peap`"
          },
          "family": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device families to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed family values"
          },
          "mfg": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device models to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed model values"
          },
          "model": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device manufacturers to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed mfg values"
          },
          "nactags": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "041d5d36-716c-4cfb-4988-3857c6aa14a2",
                "a809a97f-d599-f812-eb8c-c3f84aabf6ba"
              ]
            ]
          },
          "os_type": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of client device os types to match. Refer to [List Fingerprint Types]]($e/Constants%20Definitions/listFingerprintTypes) for allowed os_type values"
          },
          "port_types": {
            "type": "array",
            "items": {
              "title": "nac_rule_matching_port_type",
              "enum": [
                "wired",
                "wireless"
              ],
              "type": "string",
              "description": "enum: `wired`, `wireless`"
            },
            "description": "",
            "examples": [
              [
                "wired"
              ]
            ]
          },
          "site_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of site ids to match",
            "examples": [
              [
                "bb19fc3e-4124-4b57-80d9-c3f6edce47c4",
                "bb19fc3e-6564-4b57-80d9-c3f6edce47c1"
              ]
            ]
          },
          "sitegroup_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of sitegroup ids to match",
            "examples": [
              [
                "bb19fc3e-4124-4b57-80d9-c3f6edce47c4",
                "bb19fc3e-6564-4b57-80d9-c3f6edce47c1"
              ]
            ]
          },
          "vendor": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of vendors to match"
          }
        }
      },
      "order": {
        "minimum": 0.0,
        "type": "integer",
        "description": "Order of the rule, lower value implies higher priority",
        "contentEncoding": "int32",
        "examples": [
          1
        ]
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "action": "allow",
        "apply_tags": [
          "string"
        ],
        "created_time": 0,
        "id": "455f6eca-6276-4993-bfeb-53cbbbba6208",
        "matching": {
          "auth_type": "eap-tls",
          "nactags": [
            "string"
          ],
          "port_types": [
            "wireless"
          ],
          "site_ids": [
            "454f6eca-6276-4993-bfeb-53cbbbba6308"
          ],
          "sitegroup_ids": [
            "453f6eca-6276-4993-bfeb-53cbbbba6408"
          ]
        },
        "modified_time": 0,
        "name": "string",
        "not_matching": {
          "auth_type": "eap-tls",
          "nactags": [
            "string"
          ],
          "port_types": [
            "wireless"
          ],
          "site_ids": [
            "452f6eca-6276-4993-bfeb-53cbbbba6508"
          ],
          "sitegroup_ids": [
            "451f6eca-6276-4993-bfeb-53cbbbba6608"
          ]
        },
        "order": 1,
        "org_id": "a40f5d1f-d889-42e9-94ea-b9b33585fc6b"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.nac_rules.listOrgNacRules()`

## Usage Context

Lists all NAC rules for the organization.

## Gotchas

- Rules are evaluated in order; priority matters.

## Related Endpoints

- [GET_orgs_org_id_nacrules_nacrule_id.md](GET_orgs_org_id_nacrules_nacrule_id.md) — Get specific rule
- [POST_orgs_org_id_nacrules.md](POST_orgs_org_id_nacrules.md) — Create rule

## MistHelper Notes

Used by MistHelper via `listOrgNacRules` in Menu 43.
