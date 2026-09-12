# listOrgMarvisClientInvites

> listOrgMarvisClientInvites

## HTTP

`GET /api/v1/orgs/{org_id}/marvisinvites`

## Description

List Org Marvis Client Invites

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "marvis_client",
    "type": "object",
    "properties": {
      "disabled": {
        "type": "boolean",
        "default": false
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
      "name": {
        "type": "string",
        "examples": [
          "Handhelds"
        ]
      },
      "provision_url": {
        "type": "string",
        "description": "In MDM, add `--provision_url <provision_url>` to the install command",
        "readOnly": true,
        "examples": [
          "https://api.mist.com/path/to/url"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "id": "3a14098f-b995-7552-b0a4-b8ee39b337a6",
        "name": "Handhelds"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.marvis_invites.listOrgMarvisClientInvites()`

## Usage Context

Lists all Marvis invites for the organization.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_marvisinvites_marvisinvite_id.md](GET_orgs_org_id_marvisinvites_marvisinvite_id.md) — Get specific invite
- [POST_orgs_org_id_marvisinvites.md](POST_orgs_org_id_marvisinvites.md) — Create invite

## MistHelper Notes

Not currently used by MistHelper directly.
