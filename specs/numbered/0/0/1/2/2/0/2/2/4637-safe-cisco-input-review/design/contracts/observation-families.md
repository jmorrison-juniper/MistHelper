# Contract: Observation Families

This contract defines the display-only observation document. The module `state/intake/observations.py` holds `FAMILY_RULES` and `ObservationReview`. The observations convert no setting and make no Mist call. The eleven families map to rows C07 to C17 of the full-parity comparison in PR #4596.

## Document Shape (version 1)

```json
{"version": 1, "display_only": true, "conversion": "not performed", "sections": [{"family": "identity", "title": "Identity and location", "status": "observed", "items": [{"line": 3, "label": "hostname", "value": null, "value_state": "omitted", "status": "observed"}]}], "unsupported_lines": [{"line": 9, "command": "[unsupported source line]", "reason": "Unknown or unsupported syntax."}]}
```

- `version` is the integer 1.
- `sections` lists the eleven families in the fixed order of the table below. A family without an item has status `not-observed` and an empty `items` list.
- `items` keeps the source order.
- `value_state` is `shown` or `omitted`. An omitted value is `null`.
- `unsupported_lines` lists each line that no family recognizes, in source order.

## Item Status

| Status | Meaning |
| --- | --- |
| `observed` | The line matches a rule and its values pass the rule. |
| `ambiguous` | An interface block has no IPv4 address, or it has two IPv4 addresses. |
| `duplicate` | The same family and the same shown values appeared on an earlier line. |
| `malformed` | A mask or an address fails validation. The value is omitted. |

## Family Rules

Each rule matches the first words of a trimmed line, in lowercase. The longest matching prefix wins. The table lists the prefixes. The value policy names each shown value.

| Key | Title | Row | Prefixes | Shown values | Omitted values |
| --- | --- | --- | --- | --- | --- |
| identity | Identity and location | C07 | `hostname`, `snmp-server location`, `snmp-server contact` | None | Hostname, location, and contact text |
| interfaces | Interface addressing and VLANs | C08 | `interface`, `ip address`, `switchport access vlan`, `switchport trunk allowed vlan`, `channel-group` | Interface name, IPv4 address, mask, VLAN values, and group number | None |
| dhcp | DHCP pools and exclusions | C09 | `ip dhcp pool`, `network`, `ip dhcp excluded-address` | Pool name, network, mask, and excluded addresses | None |
| routing | Static routes, VRFs, and BGP | C10 | `ip route`, `vrf definition`, `ip vrf`, `router bgp`, `neighbor` | All words after the prefix | None |
| dns | DNS servers and domain | C11 | `ip name-server`, `ip domain name` | IPv4 addresses and the domain name | None |
| time | NTP and clock | C12 | `ntp server`, `clock timezone` | All words after the prefix | None |
| management | Syslog and SNMP egress | C13 | `logging host`, `snmp-server host`, `snmp-server community`, `snmp-server user` | Host addresses | Community and user values |
| identity-access | Local accounts and AAA | C14 | `username`, `enable secret`, `tacacs-server host`, `tacacs-server key`, `radius-server host`, `aaa` | Host addresses and the family marker | Usernames, secrets, and keys |
| security | ACLs, classes, policies, zones, and crypto | C15 | `ip access-list`, `access-list`, `class-map`, `policy-map`, `zone security`, `crypto` | Object names and numbers | Crypto key material and entries |
| cellular-redundancy | Cellular and standby groups | C16 | `interface cellular`, `standby` | Interface number and group number | None |
| flow-export | Flow export | C17 | `ip flow-export destination`, `ip flow-export version`, `flow exporter` | Destination address, port, version, and exporter name | None |

## Parsing Rules

1. A blank line and a line that starts with `!` produce no item. The source keeps no record of them.
2. A `banner` line and every line of its body produce an unsupported line with the command `[banner text]` and the reason `Banner text is not parsed.`
3. An `ip address` line belongs to the nearest preceding `interface` line.
4. A mask is valid when the standard library reads it as a contiguous IPv4 netmask. An invalid mask gives status `malformed` and omits the value.
5. An address that fails the IPv4 or IPv6 check gives status `malformed` and omits the value.
6. A repeated family, prefix, and shown value gives status `duplicate` on the later line.
7. A line that no rule matches becomes an unsupported line with the command `[unsupported source line]` and the reason `Unknown or unsupported syntax.`
8. Each unsupported line keeps its line number. The command category never includes the source text.

## Logging

The module logs one info line before the build and one debug line after it. Each line carries counts only. It never logs a value from the source.
