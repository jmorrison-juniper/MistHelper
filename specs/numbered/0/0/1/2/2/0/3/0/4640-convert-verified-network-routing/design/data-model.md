# Data Model: Convert Verified Network and Routing Settings

## Scope

The converter holds all values in memory for one request. It writes no file, opens no socket, and calls no Mist API. Each entity below exists only while one conversion runs. The natural keys come from the source text and the port assignment, not from a generated identifier.

## Entities

| Entity | Fields | Natural key | States |
| --- | --- | --- | --- |
| SourceLine | Line number, command family, block identifier | Line number within one upload | Read, then attached to one block or to the global block |
| InterfaceBlock | Cisco interface name, kind (physical, SVI, or unsupported), IPv4 address, mask, DHCP client flag, switchport mode, access VLAN, trunk VLAN list, channel group, channel mode, encapsulation VLAN, shutdown flag, speed flag, VRF name | Cisco interface name | Parsed, then mapped or unresolved |
| PortAssignment | Cisco interface, Mist port, role (`wan` or `lan`), family (`SRX` or `SSR`) | Cisco interface and Mist port, each unique | Supplied by the caller, then validated |
| ConvertedNetwork | Name (`VLAN` plus VLAN ID), VLAN ID (1 to 4094), subnet (optional), gateway (optional) | Name | Derived, then emitted or unresolved |
| PortEntry | Mist port key (one port or an aggregate list), usage, IP configuration, networks, untagged network (SRX only), VLAN ID, aggregated flag, AE index, LACP disable flag | Mist port key | Derived from one assignment, then emitted or unresolved |
| DhcpPool | Network name, subnet, leading exclusion, trailing exclusion, derived range, gateway, DNS servers, DNS suffix, lease time | Network name | Parsed, then mapped or unresolved |
| StaticRoute | Destination CIDR, IPv4 next hop, line number | Destination CIDR | Parsed, then mapped or unresolved. Two next hops for one CIDR make both unresolved. |
| VrfInstance | Name, member network names | VRF name | Parsed, then mapped or unresolved |
| BgpSession | Session name (`BGP` plus ASN), local AS, neighbors, derived transport, derived type | Session name | Parsed, then mapped or unresolved |
| BgpNeighbor | Neighbor address, remote AS | Neighbor address within one session | Parsed, then mapped or unresolved |
| NtpServer | IPv4 address | Address | Parsed, then emitted once in input order |
| DomainSuffix | Domain name | Domain name | Parsed, then emitted or unresolved. Two different values make both unresolved. |
| RequiredVariable | Variable name | Variable name | Listed without a value |
| UnresolvedItem | Line number, command label without values, reason text | Line number and reason key | Emitted once for each rejected source line |

## Derivation Rules

- `ConvertedNetwork` comes from an SVI with a VLAN ID or from a VLAN ID used by an access or trunk port.
- `PortEntry` takes its role from one `PortAssignment`. Source hints never change the role.
- `DhcpPool` uses the subnet of one converted network. Its range is the usable subnet minus leading and trailing exclusions.
- `BgpSession` takes its transport from the converted subnet that contains the neighbor address.
- `VrfInstance` takes its members from interfaces that carry the VRF name and map to a converted network.

## State Transitions

```text
read -> validated -> mapped
read -> validated -> unresolved
read -> rejected -> unresolved
mapped -> emitted
unresolved -> listed
```

A rejected value produces one unresolved item and no emitted key. An unresolved item never changes into a mapped value inside one conversion. A second upload starts a new conversion with no shared state.

## Output Boundary

The output holds the emitted keys, the required variable names, and the unresolved items. The output holds no source description, no credential value, and no raw source line. The shape appears in `contracts\proposal-fragment.md`.
