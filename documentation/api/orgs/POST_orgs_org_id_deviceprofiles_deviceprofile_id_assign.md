# assignOrgDeviceProfile

> assignOrgDeviceProfile

## HTTP

`POST /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign`

## Description

Assign Org Device Profile to Devices

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| deviceprofile_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK - list only devices that has deviceprofile_id changed

```json
{
  "type": "object",
  "properties": {
    "success": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "success"
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

`mistapi.api.v1.orgs.device_profiles.assignOrgDeviceProfile()`

## Usage Context

Assigns a device profile to specific devices.

## Gotchas

- Devices inherit all settings from the assigned profile.
- Assigning a new profile replaces the previous one.

## Related Endpoints

- [POST_orgs_org_id_deviceprofiles_deviceprofile_id_unassign.md](POST_orgs_org_id_deviceprofiles_deviceprofile_id_unassign.md) — Unassign profile
- [GET_orgs_org_id_deviceprofiles.md](GET_orgs_org_id_deviceprofiles.md) — List profiles

## MistHelper Notes

Not currently used by MistHelper directly.
