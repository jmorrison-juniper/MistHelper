# IP fabric and multicast

Use this reference for spine and leaf design, the BGP underlay, overlay design
boundaries, and multicast inside a data center fabric.

Sources:

- BGP on QFX Series, QFX archive 2014-2015.
- Multicast Protocols on the QFX Series, QFX archive 2014-2015.
- Ethernet Switching Features on the QFX Series, QFX archive 2014-2015.
- Contrail Networking Fabric Lifecycle Management Guide, Contrail 2011.
- Contrail Feature Guide, Contrail 5.0.3.

## 1. Design scope

An IP fabric has a physical underlay and an overlay service layer. The Contrail
Fabric Lifecycle Management Guide states that the underlay is the physical switch,
router, and firewall infrastructure. It also states that overlay services run on
that underlay.

Use this skill for the fabric design. Use `junos-mpls-vpn` for EVPN and VXLAN
protocol details.

| Layer | Design question | Source |
| - | - | - |
| Underlay | Which spine and leaf links carry routed reachability. | Contrail Fabric Lifecycle Management Guide, Contrail 2011. |
| Underlay | Which autonomous system each BGP peer uses. | BGP on QFX Series, QFX archive 2014-2015. |
| Overlay | Whether routing occurs on the spine, border leaf, or leaf. | Contrail Fabric Lifecycle Management Guide, Contrail 2011. |
| Overlay protocol | How EVPN routes or VXLAN tunnels work. | Use `junos-mpls-vpn`. |
| Multicast | Which VLAN or routed instance forwards group traffic. | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |

## 2. Spine and leaf underlay checklist

Use this checklist before you write a BGP change:

1. Assign one loopback address to each fabric device.
2. Assign one point-to-point subnet to each spine and leaf link.
3. Set the router ID to the loopback address.
4. Configure the autonomous system for the device.
5. Configure one BGP group per peer role.
6. Export only the direct or loopback routes that the underlay needs.
7. Verify each peer before you add overlay services.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Set a point-to-point interface address. | `set interfaces ge-1/2/0 unit 0 family inet address 10.10.10.1/30` | BGP on QFX Series, QFX archive 2014-2015. | Adds an underlay link address. |
| Set an external BGP group. | `set protocols bgp group external-peers type external` | BGP on QFX Series, QFX archive 2014-2015. | Creates an eBGP peer group. |
| Set the peer autonomous system. | `set protocols bgp group external-peers peer-as 22` | BGP on QFX Series, QFX archive 2014-2015. | Sets the remote AS for the group. |
| Add an eBGP neighbor. | `set protocols bgp group external-peers neighbor 10.10.10.2` | BGP on QFX Series, QFX archive 2014-2015. | Adds one fabric peer. |
| Override the AS for one peer. | `set protocols bgp group external-peers neighbor 10.21.7.2 peer-as 79` | BGP on QFX Series, QFX archive 2014-2015. | Sets a peer-specific remote AS. |
| Set the local AS. | `set routing-options autonomous-system 17` | BGP on QFX Series, QFX archive 2014-2015. | Sets the local BGP AS. |
| Set an internal BGP group. | `set protocols bgp group internal-peers type internal` | BGP on QFX Series, QFX archive 2014-2015. | Creates an iBGP peer group. |
| Set an iBGP local address. | `set protocols bgp group internal-peers local-address 192.168.6.5` | BGP on QFX Series, QFX archive 2014-2015. | Uses the loopback as the session source. |
| Add an iBGP neighbor. | `set protocols bgp group internal-peers neighbor 192.168.40.4` | BGP on QFX Series, QFX archive 2014-2015. | Adds an overlay or route-reflector peer. |
| Read BGP peer state. | `show bgp neighbor 10.0.0.40` | BGP on QFX Series, QFX archive 2014-2015. | Confirms the session state and capabilities. |

Use example addresses only in lab text. Replace all addresses and AS numbers with
the approved fabric plan before a change.

## 3. Overlay design boundary

The Contrail Fabric Lifecycle Management Guide names these overlay designs:

- Centrally routed bridging places inter-virtual-network routing on a spine or a
  border leaf.
- Edge routed bridging places inter-virtual-network routing on the leaf that
  attaches workloads and servers.
- Ethernet overlay gives Layer 2 reachability and workload mobility.
- IP overlay routes tenant traffic with IP routes.

Do not explain EVPN route types, VXLAN packet fields, or route targets here. Use
`junos-mpls-vpn` for those protocol details.

## 4. Multicast design checklist

Use this checklist before you change multicast:

1. Identify whether the traffic is Layer 2 snooping or routed multicast.
2. For Layer 2, identify the VLAN and multicast router interface.
3. For routed multicast, identify the PIM interfaces and rendezvous point.
4. Verify receivers before you change the forwarding path.
5. Verify the multicast route after you change the path.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Enable IGMP snooping on a VLAN. | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Enables Layer 2 multicast membership learning. |
| Add a static multicast group. | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan interface ge-0/0/3 static group 225.100.100.100` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Pins a group to one interface. |
| Mark the multicast router interface. | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan interface ge-0/0/2 multicast-router-interface` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Forwards IGMP queries from multicast routers. |
| Set the robust count. | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan robust-count 4` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Changes the timeout tolerance. |
| Read IGMP snooping VLAN state. | `show igmp-snooping vlans vlan v10` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Shows interfaces, groups, routers, and receivers. |
| Read PIM neighbors. | `show pim neighbors` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Shows PIM neighbor state. |
| Read multicast next hops. | `show multicast next-hops` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Shows next-hop state for multicast forwarding. |
| Read multicast scope. | `show multicast scope` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Shows configured multicast scope rules. |
| Read MSDP peer state. | `show msdp` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. | Shows MSDP state when the design uses MSDP. |

Warning: do not change multicast router interfaces during a production video,
storage, or market data flow. Receivers can stop receiving group traffic.

## 5. Fabric verification order

Use this order for read-only troubleshooting:

1. Run `show interfaces terse` on each failed link.
2. Run `show bgp neighbor <peer-address>` for each underlay peer.
3. Run `show route protocol bgp` if the route is missing from the table.
4. Run `show igmp-snooping vlans vlan <vlan>` for Layer 2 multicast.
5. Run `show pim neighbors` for routed multicast.
6. Use `junos-mpls-vpn` if the problem is an EVPN or VXLAN protocol state.

The BGP and multicast guides confirm the command families. Confirm platform
support and release support before production changes.
