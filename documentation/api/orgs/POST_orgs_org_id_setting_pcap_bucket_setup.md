# setOrgCustomBucket

> setOrgCustomBucket

## HTTP

`POST /api/v1/orgs/{org_id}/setting/pcap_bucket/setup`

## Description

Provide Customer Bucket Name

Setting up Custom PCAP Bucket Involves the following:
* provide the bucket name
* we’ll attempt to write a file MIST_TOKEN
* you have to verify the ownership of the bucket by providing the content of the MIST_TOKEN

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
    }
  },
  "required": [
    "bucket"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "bucket": {
      "type": "string"
    },
    "detail": {
      "type": "string"
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

`mistapi.api.v1.orgs.setting.setOrgCustomBucket()`

## Usage Context

Configures the cloud storage bucket for packet captures.

## Gotchas

- Bucket must be accessible from the Mist cloud.
- Use the verify endpoint after setup to confirm connectivity.

## Related Endpoints

- [POST_orgs_org_id_setting_pcap_bucket_verify.md](POST_orgs_org_id_setting_pcap_bucket_verify.md) — Verify bucket
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings

## MistHelper Notes

Not currently used by MistHelper directly.
