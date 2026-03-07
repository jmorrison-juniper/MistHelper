# listMspOrgGroups

> listMspOrgGroups

## HTTP

`GET /api/v1/msps/{msp_id}/orggroups`

## Description

Get List of MSP Org Groups

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "orggroup",
    "required": [
      "name"
    ],
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
    "description": "Organizations Group"
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 0,
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "modified_time": 0,
        "msp_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "name": "string",
        "org_ids": [
          "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
        ]
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

`mistapi.api.v1.msps.org_groups.listMspOrgGroups()`

## Usage Context

Lists all organization groups defined within an MSP. Org groups allow MSP administrators to logically group managed organizations for batch operations, reporting, and policy application (e.g., by region, customer tier, or business unit).

## Gotchas

- Org groups are an MSP-level construct — they are separate from site groups within individual organizations.
- No known gotchas with the endpoint itself.

## Related Endpoints

- [GET_msps_msp_id_orggroups_orggroup_id.md](GET_msps_msp_id_orggroups_orggroup_id.md) — Get specific org group details
- [GET_msps_msp_id_search.md](GET_msps_msp_id_search.md) — Search org groups
- [POST_msps_msp_id_orggroups.md](POST_msps_msp_id_orggroups.md) — Create a new org group
- [PUT_msps_msp_id_orggroups_orggroup_id.md](PUT_msps_msp_id_orggroups_orggroup_id.md) — Update an org group

## MistHelper Notes

Not currently used by MistHelper directly.
