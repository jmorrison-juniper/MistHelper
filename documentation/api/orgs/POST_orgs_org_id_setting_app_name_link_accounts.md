# addOrgOauthAppAccounts

> addOrgOauthAppAccounts

## HTTP

`POST /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts`

## Description

Add Jamf, VMware Authorization With Mist Portal

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| app_name | string | Yes | OAuth application name |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "accounts": {
      "type": "array",
      "items": {
        "title": "account_oauth_info_account",
        "type": "object",
        "properties": {
          "account_id": {
            "type": "string",
            "description": "Linked app account id",
            "readOnly": true,
            "examples": [
              "iojzXIJWEuiD73ZvydOfg"
            ]
          },
          "auto_probe_subnet": {
            "type": "string",
            "description": "For Prisma accounts only, tunnel auto probe subnet",
            "readOnly": true,
            "examples": [
              "11.0.0.0/8"
            ]
          },
          "client_id": {
            "type": "string",
            "description": "Customer account Client ID",
            "readOnly": true
          },
          "cloud_name": {
            "type": "string",
            "description": "Name of the company whose account mist has subscribed to",
            "readOnly": true,
            "examples": [
              "Tapi.sase.paloaltonetworks.com"
            ]
          },
          "company": {
            "type": "string",
            "description": "Name of the company whose account mist has subscribed to",
            "readOnly": true,
            "examples": [
              "Test Company1 Ltd"
            ]
          },
          "enable_probe": {
            "type": "boolean",
            "description": "For Prisma accounts only, tunnel probe enable/disable",
            "readOnly": true,
            "examples": [
              false
            ]
          },
          "error": {
            "type": "string",
            "description": "This error is provided when the account fails to fetch token/data",
            "readOnly": true,
            "examples": [
              "OAuth token refresh failed, please re-link your account"
            ]
          },
          "errors": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "OAuth token refresh failed, please re-link your account",
                "API daily rate limit reached for your account"
              ]
            ]
          },
          "instance_url": {
            "type": "string",
            "description": "Customer account instance URL",
            "readOnly": true
          },
          "key_id": {
            "type": "string",
            "description": "For ZDX Account only, Customer account API key ID",
            "examples": [
              "L72frZcK3JvrZc"
            ]
          },
          "last_status": {
            "type": "string",
            "description": "Is the last data pull for account is successful or not",
            "readOnly": true,
            "examples": [
              "failed"
            ]
          },
          "last_sync": {
            "type": "integer",
            "description": "Last data pull timestamp, background jobs that pull account data",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              1665465339000
            ]
          },
          "linked_by": {
            "type": "string",
            "description": "First name of the user who linked the account",
            "readOnly": true,
            "examples": [
              "Testname1"
            ]
          },
          "linked_timestamp": {
            "type": "number",
            "readOnly": true,
            "examples": [
              1665465339000
            ]
          },
          "max_daily_api_requests": {
            "type": "integer",
            "description": "Zoom daily api request quota, https://developers.zoom.us/docs/api/rest/rate-limits/",
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              5000
            ]
          },
          "name": {
            "type": "string",
            "description": "Name of the company whose account mist has subscribed to",
            "readOnly": true,
            "examples": [
              "Test Compay1 Ltd"
            ]
          },
          "password": {
            "type": "string",
            "description": "Customer account password instance URL",
            "readOnly": true
          },
          "region": {
            "type": "string",
            "description": "For Prisma accounts only",
            "readOnly": true,
            "examples": [
              "americas"
            ]
          },
          "regions": {
            "type": "object",
            "additionalProperties": {
              "title": "account_oauth_info_account_region",
              "type": "object",
              "properties": {
                "aggregate_region": {
                  "type": "string",
                  "description": "Bandwidth Aggregate region for this region",
                  "examples": [
                    "us-southwest"
                  ]
                },
                "allocated_bandwidth": {
                  "type": "integer",
                  "description": "Allocated bandwidth for the region, in Mbps",
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    1000
                  ]
                },
                "name": {
                  "type": "string",
                  "description": "Display name for this region",
                  "examples": [
                    "US West"
                  ]
                }
              }
            },
            "description": "For Prisma accounts only, property key is the region name. Regions with allocated bandwidth"
          },
          "service_account_name": {
            "type": "string",
            "description": "For Prisma accounts only",
            "readOnly": true,
            "examples": [
              "Corp SA"
            ]
          },
          "service_connections": {
            "type": "object",
            "additionalProperties": {
              "title": "account_oauth_info_account_service_connection",
              "type": "object",
              "properties": {
                "region": {
                  "type": "string",
                  "description": "Region of the service connection",
                  "examples": [
                    "us-southwest"
                  ]
                }
              }
            },
            "description": "For Prisma accounts only, property key is the service connection name"
          },
          "smartgroup_name": {
            "type": "string",
            "description": "Smart group membership for determining compliance status",
            "readOnly": true,
            "examples": [
              "CompliantGroup1"
            ]
          },
          "tsg_id": {
            "type": "string",
            "description": "For Prisma accounts only, Prisma Tenant Service Group id",
            "readOnly": true,
            "examples": [
              "189953456"
            ]
          },
          "username": {
            "type": "string",
            "description": "Customer account username",
            "readOnly": true
          },
          "webhook_auth_type": {
            "type": "string",
            "description": "For Crowdstrike, JAMF, SentinelOne and VMWare accounts only",
            "examples": [
              "Basic",
              "Bearer"
            ]
          },
          "webhook_enabled": {
            "type": "boolean",
            "description": "For Crowdstrike, JAMF, SentinelOne and VMWare accounts only"
          },
          "webhook_password": {
            "type": "string",
            "description": "For VMWare accounts only",
            "examples": [
              "password_1234"
            ]
          },
          "webhook_secret": {
            "type": "string",
            "description": "For Crowdstrike accounts only",
            "examples": [
              "secret-value"
            ]
          },
          "webhook_token": {
            "type": "string",
            "description": "For JAMF and SentinelOne accounts only",
            "examples": [
              "token-value"
            ]
          },
          "webhook_url": {
            "type": "string",
            "description": "For Crowdstrike, JAMF, SentinelOne and VMWare accounts only",
            "examples": [
              "https://websync.nac-staging.mistsys.com/v1/S_org-8dcbe9005/ae9dee49-69e7-4710-a114-5b827a777738/crowdstrike/edr",
              "https://websync.nac-staging.mistsys.com/v1/S_org-8dcbe9005/ae9dee49-69e7-4710-a114-5b827a777738/jamf/mdm",
              "https://websync.nac-staging.mistsys.com/v1/S_org-8dcbe9005/00fd8b39-cf92-4b43-a2ff-a461b48e7059/sentinelone/edr",
              "https://websync.nac-staging.mistsys.com/v1/S_41b2525af1d8dcbe9005/f43ea4c48f22/vmware/mdm"
            ]
          },
          "webhook_username": {
            "type": "string",
            "description": "For VMWare accounts only",
            "examples": [
              "username_1234"
            ]
          },
          "zdx_org_id": {
            "type": "string",
            "description": "For ZDX Account only, ZDX organization id",
            "examples": [
              "123456"
            ]
          }
        },
        "description": "OAuth linked apps account info"
      },
      "description": "List of linked account details"
    },
    "authorization_url": {
      "type": "string",
      "readOnly": true
    },
    "linked": {
      "type": "boolean",
      "readOnly": true
    }
  },
  "required": [
    "accounts",
    "linked"
  ]
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Unsuccessful |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.linked_applications.addOrgOauthAppAccounts()`

## Usage Context

Links third-party application accounts to the org settings.

## Gotchas

- The `app_name` path parameter specifies which integration (e.g., "crowdstrike").

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings
- [DELETE_orgs_org_id_setting_app_name_link_accounts.md](DELETE_orgs_org_id_setting_app_name_link_accounts_account_id.md) — Unlink

## MistHelper Notes

Not currently used by MistHelper directly.
