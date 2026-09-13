# listOrgNacPortals

> listOrgNacPortals

## HTTP

`GET /api/v1/orgs/{org_id}/nacportals`

## Description

List Org NAC Portals

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

OK

```json
{
  "type": "array",
  "items": {
    "title": "nac_portal",
    "type": "object",
    "properties": {
      "access_type": {
        "type": "string",
        "description": "if `type`==`marvis_client`. enum: `wireless`, `wireless+wired`"
      },
      "additional_cacerts": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Optional list of additional CA certificates to be used",
        "examples": [
          [
            "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
          ]
        ]
      },
      "additional_nac_server_name": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Optional list of additional NAC server names",
        "examples": [
          [
            "nac1.corp.com",
            "nac2.corp.com"
          ]
        ]
      },
      "bg_image_url": {
        "type": "string",
        "description": "Background image"
      },
      "cert_expire_time": {
        "type": "integer",
        "description": "In days",
        "contentEncoding": "int32",
        "examples": [
          365
        ]
      },
      "eap_type": {
        "type": "string",
        "description": "enum: `wpa2`, `wpa3`"
      },
      "enable_telemetry": {
        "type": "boolean",
        "description": "Model, version, fingering, events (connecting, disconnect, roaming), which ap"
      },
      "expiry_notification_time": {
        "type": "integer",
        "description": "In days",
        "contentEncoding": "int32"
      },
      "name": {
        "type": "string",
        "examples": [
          "get-wifi"
        ]
      },
      "notify_expiry": {
        "type": "boolean",
        "description": "phase 2"
      },
      "portal": {
        "type": "object",
        "properties": {
          "auth": {
            "type": "string",
            "description": "Guest portal authentication type. enum: `external`, `multi`, `none`"
          },
          "expire": {
            "type": "integer",
            "description": "If `auth`==`none` or `auth`==`multi`, whether to expire the guest after a certain time",
            "contentEncoding": "int32",
            "examples": [
              1440
            ]
          },
          "external_portal_url": {
            "type": "string",
            "description": "If `auth`==`external`, the URL to redirect the user to for authentication",
            "examples": [
              "https://yourorg.com/external-guest-portal"
            ]
          },
          "force_reconnect": {
            "type": "boolean",
            "description": "Disconnect client (workaround for reauth issues)"
          },
          "forward": {
            "type": "boolean",
            "description": "If `auth`==`none` or `auth`==`multi`, whether to forward the user to the guest portal after authentication",
            "examples": [
              true
            ]
          },
          "forward_url": {
            "type": "string",
            "description": "If `auth`==`none` or `auth`==`multi`, URL to forward the user to after authentication",
            "examples": [
              "https://yourorg.com/guest-portal-redirect"
            ]
          },
          "max_num_devices": {
            "maximum": 100.0,
            "minimum": 0.0,
            "type": "integer",
            "description": "Maximum number of clients allowed per guest. 0 (default, unlimited), 1-100 range",
            "contentEncoding": "int32",
            "default": 0,
            "examples": [
              10
            ]
          },
          "privacy": {
            "type": "boolean",
            "description": "If `auth`==`none` or `auth`==`multi`, whether to show the privacy policy",
            "examples": [
              true
            ]
          }
        },
        "description": "Guest portal configuration when `type`==`guest_portal`. If \n  * `auth`==`none`, the user is presented with a terms of service and can click and continue.\n  * `auth`==`external`, the user is redirected to an external URL for authentication.\n  * `auth`==`multi`, the user is presented with a choice of authentication methods:\n    - social logins: facebook / google / amazon / microsoft / azure\n    - sponsor\n    - sms: supported provider: twillio\n    - email\n    - sso\n    - userpass: pre created guest list"
      },
      "portal_authorize_jwt_secret": {
        "type": "string",
        "description": "If `type`==`guest_portal` and `auth`==`external`, the `portal_authorize_jwt_secret` will be generated",
        "readOnly": true,
        "examples": [
          "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        ]
      },
      "portal_authorize_url": {
        "type": "string",
        "description": "If `type`==`guest_portal` and `auth`==`external`, the `portal_authorize_url` will be generated",
        "readOnly": true,
        "examples": [
          "https://guest-mistnac.mist.com/callback/be22bba7-8e22-e1cf-5185-b880816fe2cf/authorize"
        ]
      },
      "portal_sso_url": {
        "type": "string",
        "description": "If `type`==`guest_portal` or `type`==`guest_admin` and ans SSO is enabled, the `portal_sso_url` will be generated (which needs to be configured in your IDP",
        "readOnly": true,
        "examples": [
          "https://guest-mistnac.mist.com/callback/be22bba7-8e22-e1cf-5185-b880816fe2cf/acs"
        ]
      },
      "ssid": {
        "type": "string",
        "examples": [
          "Corp"
        ]
      },
      "sso": {
        "title": "nac_portal_sso",
        "type": "object",
        "properties": {
          "idp_cert": {
            "type": "string",
            "examples": [
              "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
            ]
          },
          "idp_sign_algo": {
            "type": "string",
            "description": "Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`."
          },
          "idp_sso_url": {
            "type": "string",
            "examples": [
              "https://yourorg.onelogin.com/trust/saml2/http-post/sso/138130"
            ]
          },
          "issuer": {
            "type": "string",
            "examples": [
              "https://app.onelogin.com/saml/metadata/138130"
            ]
          },
          "nameid_format": {
            "type": "string",
            "examples": [
              "email"
            ]
          },
          "sso_role_matching": {
            "type": "array",
            "items": {
              "title": "nac_portal_sso_role_matching",
              "type": "object",
              "properties": {
                "assigned": {
                  "type": "string",
                  "examples": [
                    "user"
                  ]
                },
                "match": {
                  "type": "string",
                  "examples": [
                    "Student"
                  ]
                }
              }
            },
            "description": ""
          },
          "use_sso_role_for_cert": {
            "type": "boolean",
            "description": "If it's desired to inject a role into Cert's Subject (so it can be used later on in policy)"
          }
        }
      },
      "template_url": {
        "type": "string"
      },
      "thumbnail_url": {
        "type": "string",
        "readOnly": true
      },
      "tos": {
        "type": "string"
      },
      "type": {
        "type": "string",
        "description": "enum: \n  * `guest_admin`: NAC-Based Portal Admin for Pre Created Guest Authentication\n  * `guest_portal`: NAC-Based Guest Portal\n  * `marvis_client`"
      },
      "ui_url": {
        "type": "string",
        "description": "If `auth`==`guest_admin`, the URL to the guest admin portal",
        "readOnly": true,
        "examples": [
          "https://guest-mistnac.mist.com/admin/51908ea7-dea7-4581-a578-f7320c4d5216/login"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "access_type": "wireless",
        "additional_cacerts": [
          "-----BEGIN CERTIFICATE-----\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\n-----END CERTIFICATE-----"
        ],
        "cert_expire_time": 365,
        "enable_telemetry": true,
        "expiry_notification_time": 2,
        "name": "get-wifi",
        "notify_expiry": true,
        "ssid": "Corp",
        "sso": {
          "idp_cert": "-----BEGIN CERTIFICATE-----\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\n-----END CERTIFICATE-----",
          "idp_sign_algo": "sha256",
          "idp_sso_url": "https://yourorg.onelogin.com/trust/saml2/http-post/sso/138130",
          "issuer": "https://app.onelogin.com/saml/metadata/138130",
          "nameid_format": "email",
          "sso_role_matching": [
            {
              "assigned": "user",
              "match": "Student"
            }
          ],
          "use_sso_role_for_cert": true
        }
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

`mistapi.api.v1.orgs.nac_portals.listOrgNacPortals()`

## Usage Context

Lists all NAC portals for the organization.

## Gotchas

- NAC portals define device onboarding and authentication workflows.

## Related Endpoints

- [GET_orgs_org_id_nacportals_nacportal_id.md](GET_orgs_org_id_nacportals_nacportal_id.md) — Get specific portal
- [POST_orgs_org_id_nacportals.md](POST_orgs_org_id_nacportals.md) — Create portal

## MistHelper Notes

Not currently used by MistHelper directly.
