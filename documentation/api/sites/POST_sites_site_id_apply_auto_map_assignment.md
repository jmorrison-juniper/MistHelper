# applySiteAutoMapAssignment

> applySiteAutoMapAssignment

## HTTP

`POST /api/v1/sites/{site_id}/apply_auto_map_assignment`

## Description

Apply (accept) auto map assignment results for a site. Devices are associated with their assigned maps. Omit `map_ids` or provide an empty list to accept all pending assignments; provide specific `map_ids` for a partial accept.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body for accepting or clearing pending map assignments",
  "properties": {
    "map_ids": {
      "description": "Optional list of specific map IDs to apply/clear. If not provided or empty, all pending map assignments are accepted/rejected.",
      "items": {
        "format": "uuid",
        "type": "string"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Result returned after applying accepted auto map assignments",
  "properties": {
    "accepted_maps": {
      "description": "List of map IDs that were successfully accepted",
      "items": {
        "format": "uuid",
        "type": "string"
      },
      "type": "array"
    },
    "message": {
      "description": "Human-readable description of the operation result",
      "type": "string"
    }
  },
  "required": [
    "accepted_maps",
    "message"
  ],
  "type": "object"
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

`mistapi.api.v1.sites.apply_auto_map_assignment.applySiteAutoMapAssignment()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/apply_auto_map_assignment`.
Common use cases:

- Use it when you need to apply (accept) auto map assignment results for a site.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `applySiteAutoMapAssignment(mist_session: mistapi.__api_session.APISession, site_id: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.
- [GET_sites_site_id_insights_fingerprints_search.md](../orgs/GET_sites_site_id_insights_fingerprints_search.md) -- searchOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/search`.
- [DELETE_sites_site_id.md](DELETE_sites_site_id.md) -- deleteSite uses `DELETE /api/v1/sites/{site_id}`.

## MistHelper Notes

MistHelper does not currently call `applySiteAutoMapAssignment`.
Verification source: `git grep -n "applySiteAutoMapAssignment" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
