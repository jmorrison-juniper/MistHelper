# verifyOrgCustomBucket

> verifyOrgCustomBucket

## HTTP

`POST /api/v1/orgs/{org_id}/setting/pcap_bucket/verify`

## Description

Verify Customer PCAP Bucket

**Note**: If successful, a "VERIFIED" file will be created in the bucket

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
    "bucket": {
      "type": "string",
      "examples": [
        "company-private-pcap"
      ]
    },
    "verify_token": {
      "type": "string",
      "examples": [
        "eyJhbGciOiJIUzI1J9.eyJzdWIiOiIxMjM0joiMjgxOG5MDIyfQ.2rzcRvMA3Eg09NnjCAC-1EWMRtxAnFDM"
      ]
    }
  },
  "required": [
    "bucket",
    "verify_token"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.setting.verifyOrgCustomBucket()`

## Usage Context

Verifies connectivity to the configured packet capture storage bucket.

## Gotchas

- Run after `pcap_bucket_setup` to confirm the bucket is reachable.

## Related Endpoints

- [POST_orgs_org_id_setting_pcap_bucket_setup.md](POST_orgs_org_id_setting_pcap_bucket_setup.md) — Setup bucket
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings

## MistHelper Notes

Not currently used by MistHelper directly.
