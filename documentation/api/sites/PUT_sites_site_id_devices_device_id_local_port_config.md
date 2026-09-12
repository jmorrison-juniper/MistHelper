# updateSiteLocalSwitchPortConfig

> updateSiteLocalSwitchPortConfig

## HTTP

`PUT /api/v1/sites/{site_id}/devices/{device_id}/local_port_config`

## Description

API Calls to add port config local overrides. This can be used by Switch Port Operators or Helpdesk administrators
to change a Switch Port configuration without having to change the switch configuration.


The local overrides configured for the switchports with `no_local_overwrite`==`true` won't be applied to the switch configuration. 


> NOTE:
>
> When using the API Call, it is required to put send all overrides in the PUT request Payload, even the existing once. 
>
> The current overrides can be retrieved with the API Call [Get Site Device]($e/Sites%20Devices/getSiteDevice). The local overrides will show up separately from the `port_config` in the `local_port_config` so it can be easily identified (and cleared)

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
  "additionalProperties": {
    "title": "junos_local_port_config",
    "required": [
      "usage"
    ],
    "type": "object",
    "properties": {
      "all_networks": {
        "type": "boolean",
        "description": "Only if `mode`==`trunk` whether to trunk all network/vlans",
        "default": false
      },
      "allow_dhcpd": {
        "type": "boolean",
        "description": "Controls whether DHCP server traffic is allowed on ports using this configuration if DHCP snooping is enabled. This is a tri-state setting; `true`: ports become trusted ports allowing DHCP server traffic, `false`: ports become untrusted blocking DHCP server traffic, undefined: use system defaults (access ports default to untrusted, trunk ports default to trusted)."
      },
      "allow_multiple_supplicants": {
        "type": "boolean",
        "default": false
      },
      "bypass_auth_when_server_down": {
        "type": "boolean",
        "description": "Only if `port_auth`==`dot1x` bypass auth for known clients if set to true when RADIUS server is down",
        "default": false
      },
      "bypass_auth_when_server_down_for_unknown_client": {
        "type": "boolean",
        "description": "Only if `port_auth`=`dot1x` bypass auth for all (including unknown clients) if set to true when RADIUS server is down",
        "default": false
      },
      "description": {
        "type": "string"
      },
      "disable_autoneg": {
        "type": "boolean",
        "description": "Only if `mode`!=`dynamic` if speed and duplex are specified, whether to disable autonegotiation",
        "default": false
      },
      "disabled": {
        "type": "boolean",
        "description": "Whether the port is disabled",
        "default": false
      },
      "duplex": {
        "type": "string",
        "description": "link connection mode. enum: `auto`, `full`, `half`"
      },
      "dynamic_vlan_networks": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Only if `port_auth`==`dot1x`, if dynamic vlan is used, specify the possible networks/vlans RADIUS can return",
        "examples": [
          [
            "corp",
            "user"
          ]
        ]
      },
      "enable_mac_auth": {
        "type": "boolean",
        "description": "Only if `port_auth`==`dot1x` whether to enable MAC Auth",
        "default": false
      },
      "enable_qos": {
        "type": "boolean",
        "default": false
      },
      "guest_network": {
        "type": [
          "string",
          "null"
        ],
        "description": "Only if `port_auth`==`dot1x` which network to put the device into if the device cannot do dot1x. default is null (i.e. not allowed)"
      },
      "inter_switch_link": {
        "type": "boolean",
        "description": "inter_switch_link is used together with \"isolation\" under networks. NOTE: inter_switch_link works only between Juniper devices. This has to be applied to both ports connected together",
        "default": false
      },
      "mac_auth_only": {
        "type": "boolean",
        "description": "Only if `enable_mac_auth`==`true`"
      },
      "mac_auth_preferred": {
        "type": "boolean",
        "description": "Only if `enable_mac_auth`==`true` + `mac_auth_only`==`false`, dot1x will be given priority then mac_auth. Enable this to prefer mac_auth over dot1x."
      },
      "mac_auth_protocol": {
        "type": "string",
        "description": "Only if `enable_mac_auth` ==`true`. This type is ignored if mist_nac is enabled. enum: `eap-md5`, `eap-peap`, `pap`"
      },
      "mac_limit": {
        "minimum": 0.0,
        "type": "integer",
        "description": "Max number of mac addresses, default is 0 for unlimited, otherwise range is 1 or higher, with upper bound constrained by platform",
        "contentEncoding": "int32",
        "default": 0
      },
      "mode": {
        "type": "string",
        "description": "enum: `access`, `inet`, `trunk`"
      },
      "mtu": {
        "type": "integer",
        "description": "Media maximum transmission unit (MTU) is the largest data unit that can be forwarded without fragmentation. The default value is 1514.",
        "contentEncoding": "int32"
      },
      "networks": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Only if `mode`==`trunk`, the list of network/vlans"
      },
      "note": {
        "type": "string",
        "description": "Additional note for the port config override",
        "examples": [
          "force 100M for camera"
        ]
      },
      "persist_mac": {
        "type": "boolean",
        "description": "Only if `mode`==`access` and `port_auth`!=`dot1x` whether the port should retain dynamically learned MAC addresses",
        "default": false
      },
      "poe_disabled": {
        "type": "boolean",
        "description": "Whether PoE capabilities are disabled for a port",
        "default": false
      },
      "port_auth": {
        "type": "object",
        "description": "if dot1x is desired, set to dot1x. enum: `dot1x`"
      },
      "port_network": {
        "type": "string",
        "description": "Native network/vlan for untagged traffic"
      },
      "reauth_interval": {
        "type": "object",
        "description": "Only if `mode`!=`dynamic` and `port_auth`=`dot1x` reauthentication interval range (min: 10, max: 65535, default: 3600)"
      },
      "server_fail_network": {
        "type": [
          "string",
          "null"
        ],
        "description": "Only if `port_auth`==`dot1x` sets server fail fallback vlan"
      },
      "server_reject_network": {
        "type": [
          "string",
          "null"
        ],
        "description": "Only if `port_auth`==`dot1x` when radius server reject / fails"
      },
      "speed": {
        "type": "string",
        "description": "enum: `100m`, `10m`, `1g`, `2.5g`, `5g`, `10g`, `25g`, `40g`, `100g`,`auto`"
      },
      "storm_control": {
        "type": "object",
        "properties": {
          "disable_port": {
            "type": "boolean",
            "description": "Whether to disable the port when storm control is triggered",
            "default": false
          },
          "no_broadcast": {
            "type": "boolean",
            "description": "Whether to disable storm control on broadcast traffic",
            "default": false
          },
          "no_multicast": {
            "type": "boolean",
            "description": "Whether to disable storm control on multicast traffic",
            "default": false
          },
          "no_registered_multicast": {
            "type": "boolean",
            "description": "Whether to disable storm control on registered multicast traffic",
            "default": false
          },
          "no_unknown_unicast": {
            "type": "boolean",
            "description": "Whether to disable storm control on unknown unicast traffic",
            "default": false
          },
          "percentage": {
            "maximum": 100.0,
            "minimum": 0.0,
            "type": "integer",
            "description": "Bandwidth-percentage, configures the storm control level as a percentage of the available bandwidth",
            "contentEncoding": "int32",
            "default": 80
          }
        },
        "description": "Switch storm control"
      },
      "stp_edge": {
        "type": "boolean",
        "description": "When enabled, the port is not expected to receive BPDU frames",
        "default": false
      },
      "stp_no_root_port": {
        "type": "boolean",
        "default": false
      },
      "stp_p2p": {
        "type": "boolean",
        "default": false
      },
      "usage": {
        "type": "string",
        "description": "Port usage name."
      },
      "use_vstp": {
        "type": "boolean",
        "description": "If this is connected to a vstp network",
        "default": false
      },
      "voip_network": {
        "type": "string",
        "description": "Network/vlan for voip traffic, must also set port_network. to authenticate device, set port_auth"
      }
    },
    "description": "Switch port config"
  },
  "examples": [
    {
      "ge-0/0/0-1": {
        "poe_disabled": true,
        "usage": "iot"
      }
    }
  ]
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

`mistapi.api.v1.sites.devices_-_wired.updateSiteLocalSwitchPortConfig()`

## Usage Context

Updates the local port configuration for a device. Controls Ethernet port settings on APs.

## Gotchas

- Changes may disrupt clients connected via the AP Ethernet port during application.

## Related Endpoints

- [PUT_sites_site_id_devices_device_id.md](PUT_sites_site_id_devices_device_id.md) — Update device
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device details

## MistHelper Notes

Not currently used by MistHelper directly.
