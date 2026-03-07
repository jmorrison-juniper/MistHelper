# getSiteSiteRfdiagRecording

> getSiteSiteRfdiagRecording

## HTTP

`GET /api/v1/sites/{site_id}/rfdiags`

## Description

List RF Glass Recording

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
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
    "type": "array",
    "items": {
      "title": "rf_diag_info_item",
      "required": [
        "duration",
        "end_time",
        "frame_count",
        "map_id",
        "name",
        "raw_events",
        "ready",
        "start_time",
        "type",
        "url"
      ],
      "type": "object",
      "properties": {
        "asset_id": {
          "type": "string",
          "description": "If `type`==`asset`, id of the asset",
          "contentEncoding": "uuid"
        },
        "asset_name": {
          "type": "string",
          "description": "If `type`==`asset`, name of the asset"
        },
        "client_name": {
          "type": "string",
          "description": "If `type`==`client`, hostname of the client"
        },
        "duration": {
          "type": "integer",
          "description": "recording length in seconds, max is 120",
          "contentEncoding": "int32"
        },
        "end_time": {
          "type": "integer",
          "description": "Timestamp of end of recording",
          "contentEncoding": "int32"
        },
        "frame_count": {
          "type": "integer",
          "description": "Number of frames in the output",
          "contentEncoding": "int32"
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
        "mac": {
          "type": "string",
          "description": "If `type`==`client` or `asset`, mac of the device"
        },
        "map_id": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "name": {
          "type": "string"
        },
        "next": {
          "type": "string",
          "description": "Optional. id of the next recoding if present. Only valid for site survey."
        },
        "raw_events": {
          "type": "string",
          "description": "URL to a JSON file that contains array of raw location diag events"
        },
        "ready": {
          "type": "boolean",
          "description": "Whether it\u2019s ready for playback"
        },
        "sdkclient_id": {
          "type": "string",
          "description": "If `type`==`sdkclient`, sdkclient_id of this recording",
          "contentEncoding": "uuid"
        },
        "sdkclient_name": {
          "type": "string",
          "description": "If `type`==`sdkclient`, name of the sdkclient"
        },
        "sdkclient_uuid": {
          "type": "string",
          "description": "If `type`==`sdkclient`, device_id of sdkclient",
          "contentEncoding": "uuid"
        },
        "start_time": {
          "type": "integer",
          "description": "Timestamp of the recording (the start)",
          "contentEncoding": "int32"
        },
        "type": {
          "type": "string",
          "description": "enum: `asset`, `client`, `sdkclient`"
        },
        "url": {
          "type": "string",
          "description": "URL to a JSON file that contains an array of frames, each frame is the same format"
        }
      }
    }
  },
  "examples": [
    [
      [
        {
          "asset_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "asset_name": "string",
          "client_name": "string",
          "duration": 0,
          "end_time": 0,
          "frame_count": 0,
          "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "mac": "string",
          "map_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "name": "string",
          "next": "string",
          "raw_events": "string",
          "ready": true,
          "sdkclient_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "sdkclient_name": "string",
          "sdkclient_uuid": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "start_time": 0,
          "type": "sdkclient",
          "url": "string"
        }
      ]
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

`mistapi.api.v1.sites.rfdiags.getSiteSiteRfdiagRecording()`

## Usage Context

Lists RF diagnostics recordings at a site. Shows captures of radio environment data.

## Gotchas

- RF diag recordings consume storage and are typically time-limited.

## Related Endpoints

- [GET_sites_site_id_rfdiags_rfdiag_id.md](GET_sites_site_id_rfdiags_rfdiag_id.md) — Get specific recording
- [POST_sites_site_id_rfdiags.md](POST_sites_site_id_rfdiags.md) — Start new recording

## MistHelper Notes

Not currently used by MistHelper directly.
