# createOrgSso

> createOrgSso

## HTTP

`POST /api/v1/orgs/{org_id}/ssos`

## Description

Create Org SSO Configuration

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
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "custom_logout_url": {
      "type": "string",
      "description": "If `idp_type`==`saml`, a URL we will redirect the user after user logout from Mist (for some IdP which supports a custom logout URL that is different from SP-initiated SLO process)"
    },
    "default_role": {
      "type": "string",
      "description": "If `idp_type`==`saml`, default role to assign if there\u2019s no match. By default, an assertion is treated as invalid when there\u2019s no role matched"
    },
    "domain": {
      "type": "string",
      "description": "Random string generated during the SSO creation and used to generate the SAML URLs:\n  * ACS URL = `/api/v1/saml/{domain}/login` (e.g. `https://api.mist.com/api/v1/saml/s4t5vwv8/login`)\n  * Single Logout URL = `/api/v1/saml/{domain}/logout` (e.g. `https://api.mist.com/api/v1/saml/s4t5vwv8/logout`)",
      "readOnly": true
    },
    "group_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`, LDAP filter that will identify the type of group"
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
    "idp_cert": {
      "type": "string",
      "description": "If `idp_type`==`saml`. IDP Cert (used to verify the signed response)"
    },
    "idp_sign_algo": {
      "type": "string",
      "description": "Required if `idp_type`==`saml`, Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`"
    },
    "idp_sso_url": {
      "type": "string",
      "description": "Required if `idp_type`==`saml`, IDP Single-Sign-On URL"
    },
    "idp_type": {
      "type": "string",
      "description": "SSO IDP Type:\n  * For Admin SSO, enum: `saml`\n  * For NAC SSO, enum: `ldap`, `mxedge_proxy`, `oauth`, `openroaming`"
    },
    "ignore_unmatched_roles": {
      "type": "boolean",
      "description": "If `idp_type`==`saml`, ignore any unmatched roles provided in assertion. By default, an assertion is treated as invalid for any unmatched role"
    },
    "issuer": {
      "type": "string",
      "description": "If `idp_type`==`saml`. IDP issuer URL"
    },
    "ldap_base_dn": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, whole domain or a specific organization unit (container) in Search base to specify where users and groups are found in the LDAP tree",
      "examples": [
        "DC=abc,DC=com"
      ]
    },
    "ldap_bind_dn": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, the account used to authenticate against the LDAP",
      "examples": [
        "CN=nas,CN=users,DC=abc,DC=com"
      ]
    },
    "ldap_bind_password": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, the password used to authenticate against the LDAP",
      "examples": [
        "secret"
      ]
    },
    "ldap_cacerts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required if `idp_type`==`ldap`, list of CA certificates to validate the LDAP certificate",
      "examples": [
        [
          "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----",
          "-----BEGIN CERTIFICATE-----\\nBhMCRVMxFDASBgNVBAoMC1N0YXJ0Q29tIENBMSwwKgYDVn-----END CERTIFICATE-----"
        ]
      ]
    },
    "ldap_client_cert": {
      "type": "string",
      "description": "If `idp_type`==`ldap`, LDAPS Client certificate",
      "examples": [
        "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
      ]
    },
    "ldap_client_key": {
      "type": "string",
      "description": "If `idp_type`==`ldap`, Key for the `ldap_client_cert`",
      "examples": [
        "-----BEGIN PRI..."
      ]
    },
    "ldap_group_attr": {
      "type": "string",
      "description": "If `ldap_type`==`custom`",
      "default": "memberOf"
    },
    "ldap_group_dn": {
      "type": "string",
      "description": "If `ldap_type`==`custom`",
      "default": "base_dn"
    },
    "ldap_resolve_groups": {
      "type": "boolean",
      "description": "If `idp_type`==`ldap`, whether to recursively resolve LDAP groups",
      "default": false
    },
    "ldap_server_hosts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "If `idp_type`==`ldap`, list of LDAP/LDAPS server IP Addresses or Hostnames",
      "examples": [
        [
          "hostname",
          "63.1.3.5"
        ]
      ]
    },
    "ldap_type": {
      "type": "string",
      "description": "if `idp_type`==`ldap`. enum: `azure`, `custom`, `google`, `okta`, `ping_identity`"
    },
    "ldap_user_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`, LDAP filter that will identify the type of user",
      "examples": [
        "(mail=%s)"
      ]
    },
    "member_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`,LDAP filter that will identify the type of member",
      "examples": [
        "(CN=%s)"
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
    "mxedge_proxy": {
      "type": "object",
      "properties": {
        "acct_servers": {
          "type": "array",
          "items": {
            "title": "sso_mxedge_proxy_acct_server",
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "port": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 1813
              },
              "secret": {
                "type": "string",
                "examples": [
                  "testing123"
                ]
              }
            }
          },
          "description": ""
        },
        "auth_servers": {
          "type": "array",
          "items": {
            "title": "sso_mxedge_proxy_auth_server",
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "port": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 1812
              },
              "require_message_authenticator": {
                "type": "boolean",
                "description": "Whether to require Message-Authenticator in requests",
                "default": false
              },
              "retry": {
                "type": "integer",
                "description": "Authentication request retry",
                "contentEncoding": "int32",
                "default": 2
              },
              "secret": {
                "type": "string",
                "examples": [
                  "testing123"
                ]
              },
              "timeout": {
                "type": "integer",
                "description": "Authentication request timeout, in seconds",
                "contentEncoding": "int32",
                "default": 5
              }
            }
          },
          "description": ""
        },
        "mxcluster_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "examples": [
            "572586b7-f97b-a22b-526c-8b97a3f609c4"
          ]
        },
        "operator_name": {
          "type": "string",
          "description": "Operator name as Radius attribute while proxying"
        },
        "proxy_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Public hostname/IPs",
          "examples": [
            [
              "mxedge1.corp.com",
              "63.1.3.5"
            ]
          ]
        },
        "ssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "SSIDs that support eduroam",
          "examples": [
            [
              "eduroam_test, eduroam_main"
            ]
          ]
        }
      },
      "description": "If `idp_type`==`mxedge_proxy`, this requires `mist_nac` to be enabled on the mxcluster"
    },
    "name": {
      "type": "string",
      "description": "Name"
    },
    "nameid_format": {
      "type": "string",
      "description": "if `idp_type`==`saml`. enum: `email`, `unspecified`"
    },
    "oauth_cc_client_id": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, Client Credentials",
      "examples": [
        "e60da615-7def-4c5a-8196-43675f45e174"
      ]
    },
    "oauth_cc_client_secret": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, oauth_cc_client_secret is RSA private key, of the form \"-----BEGIN RSA PRIVATE KEY--....\"",
      "examples": [
        "akL8Q~5kWFMVFYl4TFZ3fi~7cMdyDONi6cj01cpH"
      ]
    },
    "oauth_discovery_url": {
      "type": "string",
      "description": "If `idp_type`==`oauth`"
    },
    "oauth_ping_identity_region": {
      "type": "string",
      "description": "enum: `us` (United States, default), `ca` (Canada), `eu` (Europe), `asia` (Asia), `au` (Australia)"
    },
    "oauth_provider_domain": {
      "type": "string",
      "description": "If `oauth_type`==`okta`, specifies the region-specific OAuth provider domain. enum: `okta.com`, `oktapreview.com`, `okta-emea.com`, `okta-gov.com`, `okta.mil`, `mtls.okta.com`"
    },
    "oauth_ropc_client_id": {
      "type": "string",
      "description": "If `idp_type`==`oauth`, ropc = Resource Owner Password Credentials",
      "examples": [
        "9ce04c97-b5b1-4ec8-af17-f5ed42d2daf7"
      ]
    },
    "oauth_ropc_client_secret": {
      "type": "string",
      "description": "If `oauth_type`==`azure` or `oauth_type`==`azure-gov`. oauth_ropc_client_secret can be empty",
      "examples": [
        "blM9R~6kWFMVFYl4TFZ3fi~8cMdyDONi6cj01dqI"
      ]
    },
    "oauth_tenant_id": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, oauth_tenant_id",
      "examples": [
        "dev-88336535"
      ]
    },
    "oauth_type": {
      "type": "string",
      "description": "if `idp_type`==`oauth`. enum: `azure`, `azure-gov`, `okta`, `ping_identity`"
    },
    "openroaming": {
      "type": "object",
      "properties": {
        "ssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "SSIDs that support OpenRoaming",
          "examples": [
            [
              "ssid_name1",
              "ssid_name2"
            ]
          ]
        },
        "wba_cert": {
          "type": "string",
          "description": "Optional WBA-issued certificate. If not provided, the default WBA-issued certificate for Juniper will be used.",
          "examples": [
            "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
          ]
        }
      },
      "required": [
        "ssids"
      ],
      "description": "if `idp_type`==`openroaming`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "role_attr_extraction": {
      "type": "string",
      "description": "If `idp_type`==`saml`, custom role attribute parsing scheme. Supported Role Parsing Schemes <table><tr><th>Name</th><th>Scheme</th></tr><tr><td>`cn`</td><td><ul><li>The expected role attribute format in SAML Assertion is \"CN=cn,OU=ou1,OU=ou2,\u2026\"</li><li>CN (the key) is case-insensitive and exactly 1 CN is expected (or the entire entry will be ignored)</li></ul>E.g. if role attribute is \"CN=cn,OU=ou1,OU=ou2\" then parsed role value is \"cn\"</td></tr></table>"
    },
    "role_attr_from": {
      "type": "string",
      "description": "If `idp_type`==`saml`, name of the attribute in SAML Assertion to extract role from",
      "default": "Role"
    },
    "scim_enabled": {
      "type": "boolean",
      "description": "If `idp_type`==`oauth`, indicates if SCIM provisioning is enabled for the OAuth IDP",
      "default": false
    },
    "scim_secret_token": {
      "type": "string",
      "description": "If `idp_type`==`oauth`, scim_secret_token (auto-generated when not provided by caller and `scim_enabled`==`true`, empty string when `scim_enabled`==`false`) is used as the Bearer token in the Authorization header of SCIM provisioning requests by the IDP",
      "examples": [
        "FBitbKPE1aecSloPGBuqqPxDUrFeZyZk"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
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
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "custom_logout_url": {
      "type": "string",
      "description": "If `idp_type`==`saml`, a URL we will redirect the user after user logout from Mist (for some IdP which supports a custom logout URL that is different from SP-initiated SLO process)"
    },
    "default_role": {
      "type": "string",
      "description": "If `idp_type`==`saml`, default role to assign if there\u2019s no match. By default, an assertion is treated as invalid when there\u2019s no role matched"
    },
    "domain": {
      "type": "string",
      "description": "Random string generated during the SSO creation and used to generate the SAML URLs:\n  * ACS URL = `/api/v1/saml/{domain}/login` (e.g. `https://api.mist.com/api/v1/saml/s4t5vwv8/login`)\n  * Single Logout URL = `/api/v1/saml/{domain}/logout` (e.g. `https://api.mist.com/api/v1/saml/s4t5vwv8/logout`)",
      "readOnly": true
    },
    "group_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`, LDAP filter that will identify the type of group"
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
    "idp_cert": {
      "type": "string",
      "description": "If `idp_type`==`saml`. IDP Cert (used to verify the signed response)"
    },
    "idp_sign_algo": {
      "type": "string",
      "description": "Required if `idp_type`==`saml`, Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`"
    },
    "idp_sso_url": {
      "type": "string",
      "description": "Required if `idp_type`==`saml`, IDP Single-Sign-On URL"
    },
    "idp_type": {
      "type": "string",
      "description": "SSO IDP Type:\n  * For Admin SSO, enum: `saml`\n  * For NAC SSO, enum: `ldap`, `mxedge_proxy`, `oauth`, `openroaming`"
    },
    "ignore_unmatched_roles": {
      "type": "boolean",
      "description": "If `idp_type`==`saml`, ignore any unmatched roles provided in assertion. By default, an assertion is treated as invalid for any unmatched role"
    },
    "issuer": {
      "type": "string",
      "description": "If `idp_type`==`saml`. IDP issuer URL"
    },
    "ldap_base_dn": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, whole domain or a specific organization unit (container) in Search base to specify where users and groups are found in the LDAP tree",
      "examples": [
        "DC=abc,DC=com"
      ]
    },
    "ldap_bind_dn": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, the account used to authenticate against the LDAP",
      "examples": [
        "CN=nas,CN=users,DC=abc,DC=com"
      ]
    },
    "ldap_bind_password": {
      "type": "string",
      "description": "Required if `idp_type`==`ldap`, the password used to authenticate against the LDAP",
      "examples": [
        "secret"
      ]
    },
    "ldap_cacerts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required if `idp_type`==`ldap`, list of CA certificates to validate the LDAP certificate",
      "examples": [
        [
          "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----",
          "-----BEGIN CERTIFICATE-----\\nBhMCRVMxFDASBgNVBAoMC1N0YXJ0Q29tIENBMSwwKgYDVn-----END CERTIFICATE-----"
        ]
      ]
    },
    "ldap_client_cert": {
      "type": "string",
      "description": "If `idp_type`==`ldap`, LDAPS Client certificate",
      "examples": [
        "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
      ]
    },
    "ldap_client_key": {
      "type": "string",
      "description": "If `idp_type`==`ldap`, Key for the `ldap_client_cert`",
      "examples": [
        "-----BEGIN PRI..."
      ]
    },
    "ldap_group_attr": {
      "type": "string",
      "description": "If `ldap_type`==`custom`",
      "default": "memberOf"
    },
    "ldap_group_dn": {
      "type": "string",
      "description": "If `ldap_type`==`custom`",
      "default": "base_dn"
    },
    "ldap_resolve_groups": {
      "type": "boolean",
      "description": "If `idp_type`==`ldap`, whether to recursively resolve LDAP groups",
      "default": false
    },
    "ldap_server_hosts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "If `idp_type`==`ldap`, list of LDAP/LDAPS server IP Addresses or Hostnames",
      "examples": [
        [
          "hostname",
          "63.1.3.5"
        ]
      ]
    },
    "ldap_type": {
      "type": "string",
      "description": "if `idp_type`==`ldap`. enum: `azure`, `custom`, `google`, `okta`, `ping_identity`"
    },
    "ldap_user_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`, LDAP filter that will identify the type of user",
      "examples": [
        "(mail=%s)"
      ]
    },
    "member_filter": {
      "type": "string",
      "description": "Required if `ldap_type`==`custom`,LDAP filter that will identify the type of member",
      "examples": [
        "(CN=%s)"
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
    "mxedge_proxy": {
      "type": "object",
      "properties": {
        "acct_servers": {
          "type": "array",
          "items": {
            "title": "sso_mxedge_proxy_acct_server",
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "port": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 1813
              },
              "secret": {
                "type": "string",
                "examples": [
                  "testing123"
                ]
              }
            }
          },
          "description": ""
        },
        "auth_servers": {
          "type": "array",
          "items": {
            "title": "sso_mxedge_proxy_auth_server",
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "port": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 1812
              },
              "require_message_authenticator": {
                "type": "boolean",
                "description": "Whether to require Message-Authenticator in requests",
                "default": false
              },
              "retry": {
                "type": "integer",
                "description": "Authentication request retry",
                "contentEncoding": "int32",
                "default": 2
              },
              "secret": {
                "type": "string",
                "examples": [
                  "testing123"
                ]
              },
              "timeout": {
                "type": "integer",
                "description": "Authentication request timeout, in seconds",
                "contentEncoding": "int32",
                "default": 5
              }
            }
          },
          "description": ""
        },
        "mxcluster_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "examples": [
            "572586b7-f97b-a22b-526c-8b97a3f609c4"
          ]
        },
        "operator_name": {
          "type": "string",
          "description": "Operator name as Radius attribute while proxying"
        },
        "proxy_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Public hostname/IPs",
          "examples": [
            [
              "mxedge1.corp.com",
              "63.1.3.5"
            ]
          ]
        },
        "ssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "SSIDs that support eduroam",
          "examples": [
            [
              "eduroam_test, eduroam_main"
            ]
          ]
        }
      },
      "description": "If `idp_type`==`mxedge_proxy`, this requires `mist_nac` to be enabled on the mxcluster"
    },
    "name": {
      "type": "string",
      "description": "Name"
    },
    "nameid_format": {
      "type": "string",
      "description": "if `idp_type`==`saml`. enum: `email`, `unspecified`"
    },
    "oauth_cc_client_id": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, Client Credentials",
      "examples": [
        "e60da615-7def-4c5a-8196-43675f45e174"
      ]
    },
    "oauth_cc_client_secret": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, oauth_cc_client_secret is RSA private key, of the form \"-----BEGIN RSA PRIVATE KEY--....\"",
      "examples": [
        "akL8Q~5kWFMVFYl4TFZ3fi~7cMdyDONi6cj01cpH"
      ]
    },
    "oauth_discovery_url": {
      "type": "string",
      "description": "If `idp_type`==`oauth`"
    },
    "oauth_ping_identity_region": {
      "type": "string",
      "description": "enum: `us` (United States, default), `ca` (Canada), `eu` (Europe), `asia` (Asia), `au` (Australia)"
    },
    "oauth_provider_domain": {
      "type": "string",
      "description": "If `oauth_type`==`okta`, specifies the region-specific OAuth provider domain. enum: `okta.com`, `oktapreview.com`, `okta-emea.com`, `okta-gov.com`, `okta.mil`, `mtls.okta.com`"
    },
    "oauth_ropc_client_id": {
      "type": "string",
      "description": "If `idp_type`==`oauth`, ropc = Resource Owner Password Credentials",
      "examples": [
        "9ce04c97-b5b1-4ec8-af17-f5ed42d2daf7"
      ]
    },
    "oauth_ropc_client_secret": {
      "type": "string",
      "description": "If `oauth_type`==`azure` or `oauth_type`==`azure-gov`. oauth_ropc_client_secret can be empty",
      "examples": [
        "blM9R~6kWFMVFYl4TFZ3fi~8cMdyDONi6cj01dqI"
      ]
    },
    "oauth_tenant_id": {
      "type": "string",
      "description": "Required if `idp_type`==`oauth`, oauth_tenant_id",
      "examples": [
        "dev-88336535"
      ]
    },
    "oauth_type": {
      "type": "string",
      "description": "if `idp_type`==`oauth`. enum: `azure`, `azure-gov`, `okta`, `ping_identity`"
    },
    "openroaming": {
      "type": "object",
      "properties": {
        "ssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "SSIDs that support OpenRoaming",
          "examples": [
            [
              "ssid_name1",
              "ssid_name2"
            ]
          ]
        },
        "wba_cert": {
          "type": "string",
          "description": "Optional WBA-issued certificate. If not provided, the default WBA-issued certificate for Juniper will be used.",
          "examples": [
            "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
          ]
        }
      },
      "required": [
        "ssids"
      ],
      "description": "if `idp_type`==`openroaming`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "role_attr_extraction": {
      "type": "string",
      "description": "If `idp_type`==`saml`, custom role attribute parsing scheme. Supported Role Parsing Schemes <table><tr><th>Name</th><th>Scheme</th></tr><tr><td>`cn`</td><td><ul><li>The expected role attribute format in SAML Assertion is \"CN=cn,OU=ou1,OU=ou2,\u2026\"</li><li>CN (the key) is case-insensitive and exactly 1 CN is expected (or the entire entry will be ignored)</li></ul>E.g. if role attribute is \"CN=cn,OU=ou1,OU=ou2\" then parsed role value is \"cn\"</td></tr></table>"
    },
    "role_attr_from": {
      "type": "string",
      "description": "If `idp_type`==`saml`, name of the attribute in SAML Assertion to extract role from",
      "default": "Role"
    },
    "scim_enabled": {
      "type": "boolean",
      "description": "If `idp_type`==`oauth`, indicates if SCIM provisioning is enabled for the OAuth IDP",
      "default": false
    },
    "scim_secret_token": {
      "type": "string",
      "description": "If `idp_type`==`oauth`, scim_secret_token (auto-generated when not provided by caller and `scim_enabled`==`true`, empty string when `scim_enabled`==`false`) is used as the Bearer token in the Authorization header of SCIM provisioning requests by the IDP",
      "examples": [
        "FBitbKPE1aecSloPGBuqqPxDUrFeZyZk"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "SSO"
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

`mistapi.api.v1.orgs.sso.createOrgSso()`

## Usage Context

Creates a new SSO (Single Sign-On) configuration for the organization.

## Gotchas

- Requires SAML IdP metadata or manual configuration.
- Test SSO before enforcing to avoid lockout.

## Related Endpoints

- [GET_orgs_org_id_ssos.md](GET_orgs_org_id_ssos.md) — List SSO configs
- [POST_orgs_org_id_ssoroles.md](POST_orgs_org_id_ssoroles.md) — Create SSO role

## MistHelper Notes

SSO listing uses Menu 57 (`listOrgSsos`). Creation is not used directly.
