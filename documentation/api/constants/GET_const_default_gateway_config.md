# getGatewayDefaultConfig

> getGatewayDefaultConfig

## HTTP

`GET /api/v1/const/default_gateway_config`

## Description

Generate Default Gateway Config

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| model | string | Yes |  |  | Model the default gateway config is intended (as the default LAN/WAN port can differ) |
| ha | string | No |  |  | Whether the config is intended for HA |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "examples": [
    {
      "dhcpd_config": {
        "lan": {
          "ip_end": "192.168.1.254",
          "ip_start": "192.168.1.2"
        }
      },
      "ip_configs": {
        "lan": {
          "ip": "192.168.1.1",
          "type": "static"
        }
      },
      "networks": {
        "lan": {
          "name": "lan",
          "subnet": "192.168.1.0/24",
          "vlan_id": 1
        }
      },
      "path_preferences": {
        "wan": {
          "paths": [
            {
              "name": "wan",
              "type": "wan"
            }
          ]
        }
      },
      "port_config": {
        "cl-1/0/0": {
          "ip_config": {
            "type": "dhcp"
          },
          "name": "lte",
          "usage": "wan",
          "wan_type": "lte"
        },
        "ge-0/0/0,ge-0/0/7": {
          "ip_config": {
            "type": "dhcp"
          },
          "name": "wan",
          "usage": "wan"
        },
        "ge-0/0/1-6": {
          "port_network": "lan",
          "usage": "lan"
        }
      },
      "service_policies": [
        {
          "action": "allow",
          "name": "Internet",
          "path_preference": "wan",
          "services": [
            "any"
          ],
          "tenants": [
            "lan"
          ]
        }
      ]
    }
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

`mistapi.api.v1.constants.models.getGatewayDefaultConfig()`

## Usage Context

Returns the default configuration template for Juniper gateway devices (SRX/SSR). This provides the baseline config that gateways receive when first adopted, including default security policies, routing settings, and management parameters. Use this to understand what settings are pre-configured before customization.

## Gotchas

- The default config serves as a starting point — site-level and device-level overrides take precedence.
- Gateway type (SRX vs SSR) may affect which default settings are applicable.
- This is a reference endpoint; modifying gateway defaults requires gateway templates.

## Related Endpoints

- [../orgs/GET_orgs_org_id_gatewaytemplates.md](../orgs/GET_orgs_org_id_gatewaytemplates.md) — Custom gateway templates that override defaults
- [GET_const_device_models.md](GET_const_device_models.md) — Gateway hardware models
- [../orgs/GET_orgs_org_id_servicepolicies.md](../orgs/GET_orgs_org_id_servicepolicies.md) — Service/firewall policies

## MistHelper Notes

Not currently used by MistHelper directly. Menu **26** (`GatewayExportUtils.templates`) exports gateway templates that build upon these defaults.
