# updateOrgServicePolicy

> updateOrgServicePolicy

## HTTP

`PUT /api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}`

## Description

Update Org Service Policy

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| servicepolicy_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "aamw": {
      "type": "object",
      "properties": {
        "aamwprofile_id": {
          "type": "string",
          "description": "org-level Advanced Advance Anti Malware Profile (SkyAtp) Profile can be used, this takes precedence over 'profile'",
          "contentEncoding": "uuid"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "enum: `docsonly`, `executables`, `standard`"
        }
      },
      "description": "SRX only"
    },
    "action": {
      "type": "string",
      "description": "enum: `allow`, `deny`"
    },
    "antivirus": {
      "type": "object",
      "properties": {
        "avprofile_id": {
          "type": "string",
          "description": "org-level AV Profile can be used, this takes precedence over 'profile'",
          "contentEncoding": "uuid"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "Default / noftp / httponly / or keys from av_profiles"
        }
      },
      "description": "For SRX-only"
    },
    "appqoe": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "SRX only"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "ewf": {
      "type": "array",
      "items": {
        "title": "service_policy_ewf_rule",
        "type": "object",
        "properties": {
          "alert_only": {
            "type": "boolean"
          },
          "block_message": {
            "type": "string",
            "examples": [
              "Access to this URL Category has been blocked"
            ]
          },
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "profile": {
            "type": "string",
            "description": "enum: `critical`, `standard`, `strict`"
          }
        }
      },
      "description": ""
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
    "idp": {
      "title": "idp_config",
      "type": "object",
      "properties": {
        "alert_only": {
          "type": "boolean"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "idpprofile_id": {
          "type": "string",
          "description": "org_level IDP Profile can be used, this takes precedence over `profile`",
          "contentEncoding": "uuid",
          "examples": [
            "89b9d208-84a4-fa8f-af57-78f92c639cf2"
          ]
        },
        "profile": {
          "type": "string",
          "description": "enum: `Custom`, `strict` (default), `standard` or keys from idp_profiles",
          "default": "strict"
        }
      }
    },
    "local_routing": {
      "type": "boolean",
      "description": "access within the same VRF"
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
    "path_preference": {
      "type": "string",
      "description": "By default, we derive all paths available and use them, optionally, you can customize by using `path_preference`"
    },
    "secintel": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "enum: `default`, `standard`, `strict`"
        },
        "secintelprofile_id": {
          "type": "string",
          "description": "org-level secintel Profile can be used, this takes precedence over 'profile'"
        }
      },
      "description": "SRX only"
    },
    "services": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "ssl_proxy": {
      "type": "object",
      "properties": {
        "ciphers_category": {
          "type": "string",
          "description": "enum: `medium`, `strong`, `weak`"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "For SRX-only"
    },
    "tenants": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  }
}
```

## Response

### 200

Example response

```json
{
  "title": "org_service_policy",
  "type": "object",
  "properties": {
    "aamw": {
      "type": "object",
      "properties": {
        "aamwprofile_id": {
          "type": "string",
          "description": "org-level Advanced Advance Anti Malware Profile (SkyAtp) Profile can be used, this takes precedence over 'profile'",
          "contentEncoding": "uuid"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "enum: `docsonly`, `executables`, `standard`"
        }
      },
      "description": "SRX only"
    },
    "action": {
      "type": "string",
      "description": "enum: `allow`, `deny`"
    },
    "antivirus": {
      "type": "object",
      "properties": {
        "avprofile_id": {
          "type": "string",
          "description": "org-level AV Profile can be used, this takes precedence over 'profile'",
          "contentEncoding": "uuid"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "Default / noftp / httponly / or keys from av_profiles"
        }
      },
      "description": "For SRX-only"
    },
    "appqoe": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "SRX only"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "ewf": {
      "type": "array",
      "items": {
        "title": "service_policy_ewf_rule",
        "type": "object",
        "properties": {
          "alert_only": {
            "type": "boolean"
          },
          "block_message": {
            "type": "string",
            "examples": [
              "Access to this URL Category has been blocked"
            ]
          },
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "profile": {
            "type": "string",
            "description": "enum: `critical`, `standard`, `strict`"
          }
        }
      },
      "description": ""
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
    "idp": {
      "title": "idp_config",
      "type": "object",
      "properties": {
        "alert_only": {
          "type": "boolean"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "idpprofile_id": {
          "type": "string",
          "description": "org_level IDP Profile can be used, this takes precedence over `profile`",
          "contentEncoding": "uuid",
          "examples": [
            "89b9d208-84a4-fa8f-af57-78f92c639cf2"
          ]
        },
        "profile": {
          "type": "string",
          "description": "enum: `Custom`, `strict` (default), `standard` or keys from idp_profiles",
          "default": "strict"
        }
      }
    },
    "local_routing": {
      "type": "boolean",
      "description": "access within the same VRF"
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
    "path_preference": {
      "type": "string",
      "description": "By default, we derive all paths available and use them, optionally, you can customize by using `path_preference`"
    },
    "secintel": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "profile": {
          "type": "string",
          "description": "enum: `default`, `standard`, `strict`"
        },
        "secintelprofile_id": {
          "type": "string",
          "description": "org-level secintel Profile can be used, this takes precedence over 'profile'"
        }
      },
      "description": "SRX only"
    },
    "services": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "ssl_proxy": {
      "type": "object",
      "properties": {
        "ciphers_category": {
          "type": "string",
          "description": "enum: `medium`, `strong`, `weak`"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "For SRX-only"
    },
    "tenants": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
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

`mistapi.api.v1.orgs.service_policies.updateOrgServicePolicy()`

## Usage Context

Updates an existing service policy.

## Gotchas

- Service policies define traffic handling rules for applications.

## Related Endpoints

- [GET_orgs_org_id_servicepolicies_servicepolicy_id.md](GET_orgs_org_id_servicepolicies_servicepolicy_id.md) — Get policy
- [POST_orgs_org_id_servicepolicies.md](POST_orgs_org_id_servicepolicies.md) — Create policy

## MistHelper Notes

Service policy listing uses Menu 4 (`listOrgServicePolicies`). Update is not used directly.
