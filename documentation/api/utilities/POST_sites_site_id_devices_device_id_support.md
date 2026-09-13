# uploadSiteDeviceSupportFile

> uploadSiteDeviceSupportFile

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/support`

## Description

Support / Upload device support files

#### Info Param
| Name | Type | Description |
| --- | --- | --- |
| process | string | Upload 1 file with output of show system processes extensive |
| outbound-ssh | string | Upload 1 file that concatenates all /var/log/outbound-ssh.log* files |
| messages | string | Upload 1 to 10 /var/log/messages* files |
| core-dumps | string | Upload all core dump files, if any |
| full | string | Upload 1 file with output of request support information, 1 file that concatenates all /var/log/outbound-ssh.log files, all core dump files, the 3 most recent /var/log/messages files, and Mist agent logs (for Junos devices running the Mist agent) |
| var-logs | string | Upload all non-empty files in the /var/log/ directory |
| jma-logs | string | Upload Mist agent logs (for Junos devices running the Mist agent only) |
"

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "info": {
      "type": "string",
      "description": "Optional, enum: \n    * `code-dumps`: Upload all core dump files, if any found\n    * `full`: Upload 1 file with output of `request support information`, 1 file that concatenates all `/var/log/outbound-ssh.log*` files, all core dump files, the 5 most recent `/var/log/messages*` files, and Mist agent logs\n    * `messages`: Upload 1 to 10 `/var/log/messages*` files\n    * `outbound-ssh`: Upload 1 file that concatenates all `/var/log/outbound-ssh.log*` files\n    * `process`: Upload 1 file with output of show `system processes extensive``\n    * `var-logs`: Upload all non-empty files in the `/var/log/` directory"
    },
    "node": {
      "type": "string",
      "description": "optional: for SSR, if node is not present, both nodes support files are uploaded"
    },
    "num_messages_files": {
      "maximum": 10.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "optional: number of most recent messages files to upload.",
      "contentEncoding": "int32",
      "default": 1
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Device not online |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.common.uploadSiteDeviceSupportFile()`

## Usage Context

Generates and uploads a support file (tech-support/request support information) from a device. Used when working with Juniper TAC or JTAC for issue investigation.

## Gotchas

- Support file generation can take several minutes depending on device state.
- The generated file may be large and stored temporarily.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_shell.md](POST_sites_site_id_devices_device_id_shell.md) — Interactive shell for manual diagnostics
- [POST_sites_site_id_devices_device_id_snapshot.md](POST_sites_site_id_devices_device_id_snapshot.md) — Configuration snapshot

## MistHelper Notes

Not currently used by MistHelper via REST API.
