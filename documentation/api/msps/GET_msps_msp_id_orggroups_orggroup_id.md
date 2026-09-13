# getMspOrgGroup

> getMspOrgGroup

## HTTP

`GET /api/v1/msps/{msp_id}/orggroups/{orggroup_id}`

## Description

Get MSP Org Group Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| orggroup_id | string | Yes |  |

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
    "org_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    }
  },
  "required": [
    "name"
  ],
  "description": "Organizations Group"
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

`mistapi.api.v1.msps.org_groups.getMspOrgGroup()`

## Usage Context

Retrieves the details of a specific MSP organization group, including its name, member organizations, and configuration metadata.

## Gotchas

- No known gotchas; standard GET by ID pattern.

## Related Endpoints

- [GET_msps_msp_id_orggroups.md](GET_msps_msp_id_orggroups.md) — List all org groups
- [PUT_msps_msp_id_orggroups_orggroup_id.md](PUT_msps_msp_id_orggroups_orggroup_id.md) — Update this org group
- [DELETE_msps_msp_id_orggroups_orggroup_id.md](DELETE_msps_msp_id_orggroups_orggroup_id.md) — Delete this org group

## MistHelper Notes

Not currently used by MistHelper directly.
