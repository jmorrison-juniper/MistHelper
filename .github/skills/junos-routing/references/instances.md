# Routing instances and route leaking

Use this reference for virtual routers, VRFs, interface binding, and route
leaking between route tables.

Public source URL for all rows:
`https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip`

## Contents

1. [Choose the instance type](#choose-the-instance-type)
2. [Build a virtual router](#build-a-virtual-router)
3. [Leak routes with VRF policy](#leak-routes-with-vrf-policy)
4. [Leak routes with RIB groups](#leak-routes-with-rib-groups)
5. [Leak routes from OSPF](#leak-routes-from-ospf)
6. [Verify an instance](#verify-an-instance)

## Choose the instance type

A virtual router gives a separate route table and interfaces. A VRF adds VPN
policy behavior. Use the type that matches the service boundary.

Warning: a wrong instance type can isolate routes from the expected table. Check
the route table name before you commit.

## Build a virtual router

| Task | Verified command | Source |
| - | - | - |
| Create a virtual router. | `set routing-instances VR1 instance-type virtual-router` | Routing Policy, 26.2, page 1655, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/routing-policy.md`. |
| Add one interface. | `set routing-instances VR1 interface ge-1/0/8.0` | Routing Policy, 26.2, page 1655. |
| Add another interface. | `set routing-instances VR1 interface ge-1/1/0.0` | Routing Policy, 26.2, page 1655. |
| Read route tables. | `show route table` | Routing Policy, 26.2, page 564. |

Caution: moving an interface into an instance can remove it from the main route
table. Confirm the interface owner before the change.

## Leak routes with VRF policy

Use VRF import and export policies for VPN-style leaking. Match communities and
route targets in a deliberate policy.

| Task | Verified command | Source |
| - | - | - |
| Import routes into a VRF. | `set routing-instances red vrf-import vrf-import-red` | BGP, 26.2, page 812, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/bgp.md`. |
| Export routes from a VRF. | `set routing-instances red vrf-export vrf-export-red` | BGP, 26.2, page 812. |
| Define a matching community. | `set policy-options community R3_PREFERRED members 64511:3` | Routing Policy, 26.2, page 572. |
| Read BGP routes. | `show route protocol bgp` | Routing Policy, 26.2, page 71. |

Warning: a broad VRF import policy can leak routes into the wrong tenant. Match
only the intended route targets or communities.

## Leak routes with RIB groups

RIB groups copy selected routes from one route table into another route table.
Use them for interface routes or protocol routes that must appear in more than
one table.

| Task | Verified command | Source |
| - | - | - |
| Add the source table to a RIB group. | `set routing-options rib-groups FBF-rib import-rib inet.0` | Routing Policy, 26.2, page 1367. |
| Add the target table to a RIB group. | `set routing-options rib-groups FBF-rib import-rib webtraffic.inet.0` | Routing Policy, 26.2, page 1367. |
| Attach interface routes to the RIB group. | `set routing-options interface-routes rib-group inet FBF-rib` | Routing Policy, 26.2, page 1367. |
| Attach OSPF to a RIB group. | `set protocols ospf rib-group fbf-group` | Routing Policy, 26.2, page 1634. |
| Read route tables. | `show route table` | Routing Policy, 26.2, page 564. |

Warning: RIB groups can copy routes into an unintended table. Confirm each
`import-rib` table and each attached protocol.

## Leak routes from OSPF

Use protocol export inside a routing instance only when the design requires
routes from another table or protocol to enter OSPF.

| Task | Verified command | Source |
| - | - | - |
| Export parent VPN routes into OSPF. | `set routing-instances vpn-1 protocols ospf export parent_vpn_routes` | Routing Policy, 26.2, page 661. |
| Verify OSPF neighbors. | `show ospf neighbor` | Routing Policy, 26.2, page 1251. |
| Verify route tables. | `show route table` | Routing Policy, 26.2, page 564. |

Warning: exporting leaked routes into OSPF can spread them across an area. Limit
the policy to the intended prefixes.

## Verify an instance

Use these checks after any instance or route leaking change:

1. Read the route table with `show route table`.
2. Confirm the expected protocol route with `show route protocol bgp` when BGP carries it.
3. Confirm the forwarding state with `show route forwarding-table`.
4. Confirm the peer state with `show bgp summary` or `show ospf neighbor`.
5. If a route is absent, verify the import policy before you change the protocol.

Caution: an inactive route can still match a policy. Verify the active route and
the forwarding table before you close the change.
