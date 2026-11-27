# Contract: Mist Field Register

## Purpose

This register holds one row for each key that the network converter emits. Decision D-13 says the converter emits no key without a row. Test 35 reads this register and fails when a key lacks a row. The source is `documentation\mist-api-openapi31yaml.yaml`, whose blob SHA on GitHub `main` is `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`.

The status column has three values.

- `verified`: The schema names the key, and its description or type states the value form.
- `verified, representation open`: The schema names the key, but the value form has an open point. The register names the point (UV-2, UV-4, or UV-5 in `research.md`). The converter emits the key with the stated form.

## Emitted Keys

The path uses `gateway_template` as the object name. Issue #4638 selects the Hub target, which uses the `deviceprofile_gateway` object with the same property names at lines 77255 to 77363.

| Mist path | Source family | OpenAPI pointer (line) | Value form and evidence | Status | Test |
| --- | --- | --- | --- | --- | --- |
| `networks[].name` | Network name | `network` at 88200, `name` at 88242, `networks` at 88706 | String. Required by the schema. | verified | 8, 13 |
| `networks[].subnet` | SVI subnet | `subnet` at 88252 | IPv4 CIDR for this network. | verified | 2, 8 |
| `networks[].gateway` | SVI address | `gateway` at 88212 | IPv4 gateway address for this network. | verified | 2 |
| `networks[].vlan_id` | VLAN ID | `vlan_id` at 88265, `vlan_id_with_variable` at 117762 | Integer from 1 to 4094, or a variable string. | verified | 8, 9, 16 |
| `port_config[<port>].usage` | WAN or LAN role | `gateway_port_config` at 80080, `usage` at 80227, `gateway_port_usage` at 80464 | Enum: `ha_control`, `ha_data`, `lan`, `wan`. The converter uses `lan` and `wan`. | verified | 1, 5, 6 |
| `port_config[<port>].ip_config.ip` | WAN address | `ip_config` at 80138, `gateway_port_config_ip_config` at 80287, `ip` at 80312 | IPv4 address for the port, or a variable. | verified | 1, 16 |
| `port_config[<port>].ip_config.netmask` | WAN prefix length | `netmask` at 80326 | Prefix such as `/24`, or a variable. Used when the network has no subnet. | verified | 1, 3, 16 |
| `port_config[<port>].networks` | LAN network membership | `networks` at 80164, `gateway_port_networks` at 80449 | List of network names. Used only when usage is `lan`. | verified | 8 |
| `port_config[<port>].port_network` | Untagged LAN network | `port_network` at 80178 | Network name. The schema says SRX only and usage `lan`. | verified | 8, 13 |
| `port_config[<port>].vlan_id` | VLAN on a WAN port | `vlan_id` at 80231, `gateway_port_vlan_id_with_variable` at 80472 | Integer from 1 to 4094, or a variable string. | verified | 9, 10 |
| `port_config[<aggregate list>]` | Aggregate member list | `port_config` at 80739, key description at 80742 | Comma list of ports. The schema allows a list only for aggregated ports. | verified | 11 |
| `port_config[<port>].aggregated` | Aggregate flag | `aggregated` at 80103 | Boolean. True for each aggregate key. | verified | 11 |
| `port_config[<port>].ae_idx` | Aggregate index | `ae_idx` at 80089 | Type is string or null. The description gives an integer from 0 to 127. The converter emits a string. | verified, representation open (UV-4) | 11 |
| `port_config[<port>].ae_disable_lacp` | LACP mode | `ae_disable_lacp` at 80084 | Boolean. The description applies when aggregated is true. Mode `on` maps to true. | verified | 11 |
| `ip_configs[<network>].ip` | LAN address | `gateway_ip_configs` at 79704, `gateway_ip_config_property` at 79657, `ip` at 79661 | IPv4 address for the network interface. | verified | 2 |
| `ip_configs[<network>].netmask` | LAN prefix length | `netmask` at 79671 | Prefix such as `/24`. | verified | 2, 3 |
| `ip_configs[<network>].type` | Static address mode | `type` at 79687, enum at 79690, `ip_type` at 82623 | Enum `dhcp` or `static`. The converter uses `static`. | verified | 2 |
| `dhcpd_config[<network>].type` | Local DHCP pool | `dhcpd_config` at 77579, `dhcpd_config_property` at 77667, `type` at 77736, enum at 77738 | Enum `local`, `none`, or `relay`. The converter uses `local`. | verified | 18 |
| `dhcpd_config[<network>].ip_start` | Pool start | `ip_start` at 77706 | IPv4 start address of the lease pool. The converter emits a range only when the gateway lies outside it. | verified | 18 |
| `dhcpd_config[<network>].ip_end` | Pool end | `ip_end` at 77700 | IPv4 end address of the lease pool. The converter emits a range only when the gateway lies outside it. | verified | 18 |
| `dhcpd_config[<network>].gateway` | Default router | `gateway` at 77683 | IPv4 address. The schema uses the pool IP when this value is absent. | verified | 18 |
| `dhcpd_config[<network>].dns_servers` | Pool DNS servers | `dns_servers` at 77671, `dhcpd_config_dns_servers` at 77589 | List of IPv4 strings. Used when the type is `local`. | verified | 18 |
| `dhcpd_config[<network>].dns_suffix` | Pool DNS suffix | `dns_suffix` at 77675, `dhcpd_config_dns_suffix` at 77599 | List of strings. Used when the type is `local`. | verified | 18 |
| `dhcpd_config[<network>].lease_time` | Lease time | `lease_time` at 77712 | Integer from 3600 to 604800. The schema default is 86400. | verified | 21 |
| `extra_routes[<cidr>].via` | Static route next hop | `gateway_extra_routes` at 79627, `gateway_extra_route` at 79609, `via` at 79613 | IPv4 next-hop address. The key is a destination CIDR or a variable. | verified | 25, 26, 16 |
| `vrf_instances[<name>].networks` | VRF members | `gateway_vrf_instances` at 80833, `gateway_vrf_instance` at 80821 | List of network names in the VRF instance. | verified | 28 |
| `bgp_config[<session>].via` | BGP transport | `bgp_config` at 71719, `via` at 71820, `bgp_config_via` at 71884 | Enum `lan`, `tunnel`, `vpn`, or `wan`. The converter uses `lan` or `wan`. | verified | 30, 32 |
| `bgp_config[<session>].type` | BGP session type | `type` at 71816, `bgp_config_type` at 71876, enum at 71879 | Enum `external` or `internal`. | verified | 30 |
| `bgp_config[<session>].local_as` | Local AS | `local_as` at 71784, `bgp_local_as` at 71893 | Integer. The schema minimum is 1. | verified | 30 |
| `bgp_config[<session>].neighbors[<address>].neighbor_as` | Remote AS | `neighbors` at 71792, `bgp_config_neighbors` at 71834, `neighbor_as` at 71860 | Type is the `bgp_as` schema at 71709. The converter emits an integer. | verified, representation open (UV-5) | 30 |
| `ntp_servers[]` | NTP servers | `ntp_servers` at 80725 and 88742 | Array of strings. The converter emits IPv4 strings only. | verified | 22 |
| `dns_servers[]` | DNS servers | `dns_servers` at 80678 and 78038 | Array of strings. Existing key from the DNS path. | verified | 33 |
| `dns_suffix[]` | DNS suffix | `dns_suffix` at 80681 and 78044 | Array of strings. | verified | 24, 33 |
| `type` | Gateway template role | `type` at 80766, enum at 80768 | Enum `spoke` or `standalone`. Existing key from the DNS path. | verified | 33 |

## Variable Fields

The converter keeps a variable token only in these verified fields. A variable token in any other field produces the reason `VARIABLE_FIELD`.

| Field | Evidence | Test |
| --- | --- | --- |
| Port key | Key form includes a variable at 80742 | 16 |
| Port IP address | `ip` description allows a variable at 80312 | 16 |
| Port netmask | `netmask` description allows a variable at 80326 | 16 |
| Port gateway | `gateway` description allows a variable at 80299 | 16 |
| Port VLAN ID | VLAN ID accepts a variable at 80472 and 117762 | 9 |
| Static route key | Key form includes a variable at 79627 | 16 |

## Keys Deliberately Not Emitted

These schema keys have a verified shape. The converter still never emits them.

| Mist path | OpenAPI pointer | Reason |
| --- | --- | --- |
| `bgp_config[<session>].networks` | 71798 and 71870 | The value names Mist networks. Advertised prefixes stay unresolved (test 31). |
| `bgp_config[<session>].auth_key` | 71724 | Credentials stay out of output (D-14 and D-18). |
| `port_config[<port>].disabled` | 80118 and 80120 | The meaning is open (test 14). |
| `port_config[<port>].speed` | 80207 | The format is open (test 15). |
| `port_config[<port>].mtu` | 80158 | No Cisco source value maps to it in this record. |
| `port_config[<port>].description` | 80111 | Descriptions can hold customer data (D-14). |
| `dhcpd_config[<network>].fixed_bindings` | 77679 | No Cisco source family maps to it in this record. |
| `dhcpd_config[<network>].options` | 77719 | No Cisco source family maps to it in this record. |
| `dhcpd_config[<network>].servers` | 77730 | Relay mode is out of scope. |
| `dhcpd_config[<network>].server_id_override` | 77723 | Relay mode is out of scope. |
| `ip_configs[<network>].secondary_ips` | 79683 | Secondary addresses are out of scope. |
| `vrf_config.enabled` | 118044 and 118048 | Model support is open (UV-7). The converter omits the key until issue #4638 confirms support. |

## Unverified Keys

These keys have no register row in this record. The converter never emits them.

- `vars` at line 117442. The schema describes WLAN variables, not gateway variables (UV-9).
- The `networks` property of `deviceprofile_gateway` (UV-10).
- The `strings` schema at line 111562, which holds the VRF member list (UV-13).
