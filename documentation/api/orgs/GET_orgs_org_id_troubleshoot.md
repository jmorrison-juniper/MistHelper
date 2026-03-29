# troubleshootOrg

> troubleshootOrg

## HTTP

`GET /api/v1/orgs/{org_id}/troubleshoot`

## Description

Troubleshoot sites, devices, clients, and wired clients for maximum of last 7 days from current time. See search APIs for device information:
- [search Device]($e/Orgs%20Devices/searchOrgDevices)
- [search Wireless Client]($e/Orgs%20Clients%20-%20Wireless/searchOrgWirelessClients)
- [search Wired Client]($e/Orgs%20Clients%20-%20Wired/searchOrgWiredClients)
- [search Wan Client]($e/Orgs%20Clients%20-%20Wan/searchOrgWanClients)

**NOTE**: requires Marvis subscription license

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  | **required** when troubleshooting device or a client |
| site_id | string | No |  |  | **required** when troubleshooting site |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| type | string | No |  |  | When troubleshooting site, type of network to troubleshoot |

## Request Body

None.

## Response

### 200

Troubleshoot Response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1655151856
      ]
    },
    "results": {
      "type": "array",
      "items": {
        "title": "response_troubleshoot_item",
        "type": "object",
        "properties": {
          "category": {
            "type": "string",
            "examples": [
              "client"
            ]
          },
          "reason": {
            "type": "string",
            "examples": [
              "slow association"
            ]
          },
          "recommendation": {
            "type": "string",
            "examples": [
              "Ensure the IP helper-address is configured on the VLAN interface."
            ]
          },
          "text": {
            "type": "string",
            "examples": [
              "Clients of the AP had slow association 8% of the time on Bhavabhi and 5 GHz. ..."
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1655065456
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

`mistapi.api.v1.orgs.marvis.troubleshootOrg()`

## Usage Context

Retrieves troubleshooting session results for the organization.

## Gotchas

- Troubleshoot sessions are initiated via Marvis or the dashboard.

## Related Endpoints

- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices
- [GET_orgs_org_id_events_search.md](GET_orgs_org_id_events_search.md) — Search events

## MistHelper Notes

Not currently used by MistHelper directly.
