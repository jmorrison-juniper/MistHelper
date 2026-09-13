# getMspDetails

> getMspDetails

## HTTP

`GET /api/v1/msps/{msp_id}`

## Description

Get MSP Detail

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
  "type": "object",
  "properties": {
    "allow_mist": {
      "type": "boolean"
    },
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
    "logo_url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "tier": {
      "type": "string",
      "description": "enum: `advanced`, `base`"
    },
    "url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
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

`mistapi.api.v1.msps.msps.getMspDetails()`

## Usage Context

Retrieves the details of a specific MSP including name, settings, and associated metadata. Use this to verify MSP configuration or display MSP information in management dashboards.

## Gotchas

- The `msp_id` must be a valid UUID for an MSP the authenticated admin has access to.
- No known gotchas with the endpoint itself.

## Related Endpoints

- [PUT_msps_msp_id.md](PUT_msps_msp_id.md) — Update MSP settings
- [DELETE_msps_msp_id.md](DELETE_msps_msp_id.md) — Delete the MSP
- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — List organizations under this MSP

## MistHelper Notes

Not currently used by MistHelper directly. Menu **56** (`OrgConfigExporter.msp`) exports MSP-related configurations at the org level.
