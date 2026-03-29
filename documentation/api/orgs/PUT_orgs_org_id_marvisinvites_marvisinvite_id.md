# updateOrgMarvisClientInvite

> updateOrgMarvisClientInvite

## HTTP

`PUT /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}`

## Description

Update Org Marvis Client Invite

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| marvisinvite_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
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
}
```

## Response

### 200

Example response

```json
{
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

`mistapi.api.v1.orgs.marvis_invites.updateOrgMarvisClientInvite()`

## Usage Context

Updates an existing Marvis AI invitation.

## Gotchas

- Marvis invitations grant Marvis Actions access.

## Related Endpoints

- [GET_orgs_org_id_marvisinvites.md](GET_orgs_org_id_marvisinvites.md) — List invitations
- [POST_orgs_org_id_marvisinvites.md](POST_orgs_org_id_marvisinvites.md) — Create invitation

## MistHelper Notes

Not currently used by MistHelper directly.
