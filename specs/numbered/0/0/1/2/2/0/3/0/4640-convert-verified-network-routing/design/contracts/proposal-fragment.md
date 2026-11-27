# Contract: Network Fragment Output

## Scope

This contract defines the output of `IOSNetworkConverter.convert`. Issue #4641 composes this output with the DNS output. This record defines no composed proposal.

## Shape

`NetworkFragment` is a `TypedDict` in `conversion/common/fragment.py`. It holds three keys.

| Key | Type | Presence |
| --- | --- | --- |
| `gateway_fields` | Object with the keys listed below | Always present. Empty keys are omitted. |
| `required_variables` | Sorted list of variable names | Always present. May be empty. |
| `unsupported_items` | List of `{line, command, reason}` objects | Always present. May be empty. |

The keys of `gateway_fields` are these. Each key appears only when the converter emits a value for it.

| Key | Value form | Mist path (see the register) |
| --- | --- | --- |
| `networks` | List of objects with `name`, and optional `vlan_id`, `subnet`, and `gateway` | `gateway_template.networks` |
| `port_config` | Object keyed by Mist port or aggregate list | `gateway_template.port_config` |
| `ip_configs` | Object keyed by network name | `gateway_template.ip_configs` |
| `dhcpd_config` | Object keyed by network name, with `type` set to `local` | `gateway_template.dhcpd_config` |
| `extra_routes` | Object keyed by destination CIDR | `gateway_template.extra_routes` |
| `vrf_instances` | Object keyed by VRF name | `gateway_template.vrf_instances` |
| `bgp_config` | Object keyed by session name | `gateway_template.bgp_config` |
| `ntp_servers` | List of IPv4 strings in input order | `gateway_template.ntp_servers` |

## Example

The example uses documentation address ranges from RFC 5737 and the reserved domain `example.test`. It holds no real value and no credential.

```json
{
  "gateway_fields": {
    "networks": [
      {"name": "VLAN10", "vlan_id": 10, "subnet": "192.0.2.0/24", "gateway": "192.0.2.1"}
    ],
    "port_config": {
      "ge-0/0/0": {"usage": "wan", "ip_config": {"ip": "198.51.100.10", "netmask": "/24"}},
      "ge-0/0/1": {"usage": "lan", "networks": ["VLAN10"], "port_network": "VLAN10"}
    },
    "ip_configs": {
      "VLAN10": {"type": "static", "ip": "192.0.2.1", "netmask": "/24"}
    },
    "dhcpd_config": {
      "VLAN10": {"type": "local", "ip_start": "192.0.2.11", "ip_end": "192.0.2.254", "gateway": "192.0.2.1", "dns_servers": ["203.0.113.53"], "dns_suffix": ["example.test"]}
    },
    "extra_routes": {
      "0.0.0.0/0": {"via": "198.51.100.1"}
    },
    "vrf_instances": {
      "BLUE": {"networks": ["VLAN10"]}
    },
    "bgp_config": {
      "BGP65001": {"via": "wan", "type": "external", "local_as": 65001, "neighbors": {"198.51.100.2": {"neighbor_as": 65002}}}
    },
    "ntp_servers": ["203.0.113.123"]
  },
  "required_variables": ["wan_ip"],
  "unsupported_items": [
    {"line": 14, "command": "switchport trunk native vlan [value omitted]", "reason": "The untagged network is verified for SRX only."}
  ]
}
```

## Merge Rules For Issue #4641

- Merge `gateway_fields` into the `gateway_template` object of the DNS proposal.
- Keep `dns_servers` and `dns_suffix` from the DNS path only.
- Stop the merge with an error when a key appears in both paths. The current design emits no such key.
- Compose the known-gap text in issue #4641. This fragment holds no known-gap text.

## Reason Catalog

The code stores the reason texts in one constant, `UNRESOLVED_REASONS`, in `conversion/common/fragment.py`. The code uses the key in the first column. The reason text appears in each `unsupported_items` entry.

| Key | Reason text |
| --- | --- |
| `PORT_MISSING` | No explicit port assignment exists for this interface. |
| `ROLE_MISSING` | No WAN or LAN role exists for this interface. |
| `ROLE_CONFLICT` | A source setting conflicts with the selected role. |
| `PORT_CONFLICT` | Two interfaces use the same Mist port. |
| `ADDRESS_INVALID` | The address or mask is not a valid IPv4 value. |
| `MASK_NONCONTIGUOUS` | The mask is not contiguous. |
| `DHCP_CLIENT` | DHCP client addressing has no verified mapping. |
| `VLAN_RANGE` | The VLAN ID is outside 1 to 4094 or the range is reversed. |
| `VLAN_VARIABLE` | A variable VLAN ID has no fixed network name. |
| `WAN_VLAN_MULTIPLE` | One port cannot carry two WAN VLANs. |
| `AGGREGATE_MEMBER` | An aggregate member has no matching assignment or role. |
| `AGGREGATE_MODE` | The channel group mode has no verified mapping. |
| `SHUTDOWN_MEANING` | The disabled field meaning is not verified. |
| `SPEED_FORMAT` | The speed or duplex value has no verified format. |
| `UNTAGGED_SRX_ONLY` | The untagged network is verified for SRX only. |
| `VARIABLE_FIELD` | A variable is not allowed in this field. |
| `DHCP_NO_NETWORK` | No converted network has this subnet. |
| `DHCP_MIDDLE_EXCLUSION` | An exclusion splits the pool. The range is not verified. |
| `DHCP_EXCLUSION_OUTSIDE` | An exclusion lies outside the usable range. |
| `DHCP_OVERLAP` | Two pool ranges overlap. |
| `DHCP_GATEWAY` | The gateway address lies inside the pool range. |
| `DHCP_LEASE` | The lease time is outside 3600 to 604800 seconds. |
| `DHCP_MASK` | The pool subnet has no usable range. |
| `ROUTE_FORM` | This route form has no verified field. |
| `ROUTE_HOST_BITS` | The route prefix has host bits set. |
| `ROUTE_DUPLICATE` | One destination has two next hops. |
| `VRF_DISTINGUISHER` | The route distinguisher has no verified field. The value is omitted. |
| `VRF_ROUTE` | A VRF route has no verified gateway field. |
| `VRF_MEMBER` | The VRF member has no converted network. |
| `BGP_TRANSPORT` | The neighbor lies outside every converted subnet. |
| `BGP_PREFIX` | Advertised prefixes have no verified field. |
| `BGP_CREDENTIAL` | The neighbor credential is omitted. |
| `BGP_COMMAND` | This BGP command has no verified field. |
| `NTP_HOSTNAME` | An NTP hostname is not verified. |
| `NTP_IPV6` | An IPv6 NTP server is not verified. |
| `NTP_OPTION` | An NTP option has no verified field. |
| `DOMAIN_INVALID` | The domain name is not valid. |
| `DOMAIN_CONFLICT` | Two domain names disagree. |
| `UNSUPPORTED` | Unsupported command or context. |

## Command Labels

A command label names the command family. A label never includes a value that follows the keyword.

- Use the form `<keyword phrase> [value omitted]` when the line carries a value. Example: `neighbor password [value omitted]`.
- Use the form `<keyword phrase>` when the line carries no value. Example: `router bgp`.
- Use `[unsupported source line]` when no known family applies.
