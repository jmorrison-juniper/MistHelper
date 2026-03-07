# listFingerprintTypes

> listFingerprintTypes

## HTTP

`GET /api/v1/const/fingerprint_types`

## Description

Get List of supported fingerprint attribute values
* family
* model
* mfg
* os_type

This information can be used in the [Mist NAC Rules]($h/Orgs%20NAC%20Rules/_overview) `matching` attribute.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Fingerprint Types

```json
{
  "type": "object",
  "properties": {
    "family": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "mfg": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "model": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "os": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
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

`mistapi.api.v1.constants.definitions.listFingerprintTypes()`

## Usage Context

Returns the list of device fingerprinting types used by the Mist platform to identify client device manufacturers, operating systems, and device classes via DHCP, HTTP, and other network signatures. Use this to understand how clients are classified in analytics and policy enforcement.

## Gotchas

- Fingerprinting accuracy varies by client type and network visibility — clients behind NAT or using randomized MACs may not be accurately fingerprinted.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [../orgs/POST_orgs_org_id_clients_search.md](../orgs/POST_orgs_org_id_clients_search.md) — Search clients with fingerprint data
- [../sites/GET_sites_site_id_clients.md](../sites/GET_sites_site_id_clients.md) — Site client list with fingerprint info

## MistHelper Notes

Not currently used by MistHelper directly.
