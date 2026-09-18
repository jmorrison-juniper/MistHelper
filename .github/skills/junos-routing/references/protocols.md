# Protocols and routes

Use this reference for BGP, OSPF, IS-IS, BFD, convergence, static routes,
aggregate routes, generated routes, and next-hop resolution.

Public source URL for all rows:
`https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip`

## Contents

1. [BGP](#bgp)
2. [OSPF](#ospf)
3. [IS-IS](#is-is)
4. [BFD and convergence](#bfd-and-convergence)
5. [Static, aggregate, and generated routes](#static-aggregate-and-generated-routes)
6. [Next-hop and route verification](#next-hop-and-route-verification)

## BGP

BGP exchanges routes between autonomous systems and inside one autonomous
system. Use BGP when policy, scale, or multi-hop peering matters.

### Build an external BGP session

Use the smallest neighbor configuration first. Add policy after the session
reaches the Established state.

Warning: a wrong peer AS or export policy can drop a BGP session or advertise
wrong routes. Confirm the peer plan before you commit.

| Task | Verified command | Source |
| - | - | - |
| Set the local AS. | `set routing-options autonomous-system 17` | Routing Policy, 26.2, page 65, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/routing-policy.md`. |
| Create an external group. | `set protocols bgp group external-peers type external` | Routing Policy, 26.2, page 613. |
| Set the peer AS. | `set protocols bgp group external-peers peer-as 64510` | BGP, 26.2, page 1461, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/bgp.md`. |
| Add a neighbor. | `set protocols bgp group external-peers neighbor 10.0.0.1` | Routing Policy, 26.2, page 614. |
| Enable IPv4 unicast for a neighbor. | `set protocols bgp group routeset1 neighbor 10.0.10.13 family inet unicast` | Routing Policy, 26.2, page 387. |
| Export a policy. | `set protocols bgp group external-peers export send-static` | BGP, 26.2, page 462. |
| Verify the session. | `show bgp summary` | Routing Policy, 26.2, page 653. |

### Build an internal BGP session

Use internal BGP when routers share one autonomous system. Set a stable router
ID before you build a route reflector.

| Task | Verified command | Source |
| - | - | - |
| Set the router ID. | `set routing-options router-id 172.16.1.1` | Routing Policy, 26.2, page 65. |
| Create an internal group. | `set protocols bgp group internal-peers type internal` | Routing Policy, 26.2, page 65. |
| Set a local address. | `set protocols bgp group internal-peers local-address 10.0.0.1` | OSPF, 26.2, page 492, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ospf.md`. |
| Configure a route reflector cluster. | `set protocols bgp group internal-peers cluster 192.168.6.5` | BGP, 26.2, page 1239. |
| Permit a multi-hop peer. | `set protocols bgp group external multihop ttl 2` | BGP, 26.2, page 215. |

Warning: a route reflector can reflect a route loop when cluster design is
wrong. Confirm the cluster ID and client list before you commit.

### Influence BGP path selection

Use protocol knobs sparingly. Prefer routing policy for local preference,
community handling, and route acceptance.

| Task | Verified command | Source |
| - | - | - |
| Ignore AS path length in path selection. | `set protocols bgp path-selection as-path-ignore` | BGP, 26.2, page 296. |
| Enable route damping. | `set protocols bgp damping` | Routing Policy, 26.2, page 647. |
| Remove private AS values on one neighbor. | `set protocols bgp group ext neighbor 192.168.20.1 remove-private` | BGP, 26.2, page 307. |
| Verify received routes. | `show route receive-protocol bgp` | Routing Policy, 26.2, page 73. |
| Verify advertised routes. | `show route advertising-protocol bgp` | Routing Policy, 26.2, page 140. |
| Verify installed BGP routes. | `show route protocol bgp` | Routing Policy, 26.2, page 71. |

Warning: route damping can suppress unstable routes longer than the fault lasts.
Use it only when the design requires suppression.

## OSPF

OSPF uses areas, interface cost, and adjacency state to build shortest paths.
Start with the area and interface. Add authentication and tuning after the
basic adjacency is stable.

### Build an OSPF area

| Task | Verified command | Source |
| - | - | - |
| Add an interface with a cost. | `set protocols ospf area 0.0.0.0 interface fe-1/0/1 metric 5` | OSPF, 26.2, page 232. |
| Make an interface passive. | `set protocols ospf area 0.0.0.1 interface ge-0/2/0 passive` | OSPF, 26.2, page 45. |
| Configure a point-to-point interface. | `set protocols ospf area 0.0.0.0 interface xe-0/0/0:0.0 interface-type p2p` | OSPF, 26.2, page 577. |
| Configure a stub area. | `set protocols ospf area 07 stub` | OSPF, 26.2, page 111. |
| Configure an NSSA. | `set protocols ospf area 0.0.0.9 nssa` | OSPF, 26.2, page 117. |
| Enable traffic engineering. | `set protocols ospf traffic-engineering` | Routing Policy, 26.2, page 663. |
| Verify neighbors. | `show ospf neighbor` | Routing Policy, 26.2, page 1251. |

Warning: changing an OSPF area type can flush LSAs and change reachability.
Confirm all routers in the area before you commit.

### Add OSPF authentication

Use authentication where the link design requires peer validation. Store secrets
outside chat and ticket text.

| Task | Verified command | Source |
| - | - | - |
| Configure MD5 authentication on an interface. | `set protocols ospf area 0.0.0.0 interface so-0/2/0 authentication md5 5 key PssWd8` | OSPF, 26.2, page 292. |

Warning: changing an OSPF authentication key can drop adjacency immediately.
Coordinate the key and the commit time on both routers.

## IS-IS

IS-IS uses levels, metrics, and interface settings to build the link-state
database. Use wide metrics in modern designs unless the network requires legacy
metrics.

### Build IS-IS reachability

| Task | Verified command | Source |
| - | - | - |
| Add a transit interface. | `set protocols isis interface ge-0/0/0.0` | IS-IS, 26.2, page 38, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/is-is.md`. |
| Add a passive loopback. | `set protocols isis interface lo0.0 passive` | BGP, 26.2, page 1010. |
| Use level 2 wide metrics. | `set protocols isis level 2 wide-metrics-only` | IS-IS, 26.2, page 270. |
| Set a level 2 metric. | `set protocols isis interface ge-0/0/1.0 level 2 metric 100` | IS-IS, 26.2, page 65. |
| Set point-to-point operation. | `set protocols isis interface ge-0/0/1.0 point-to-point` | IS-IS, 26.2, page 65. |
| Verify adjacency state. | `show isis adjacency` | IS-IS, 26.2, page 41. |
| Verify IS-IS configuration. | `show configuration protocols isis` | IS-IS, 26.2, page 798. |

Warning: enabling `wide-metrics-only` can change how old neighbors read metric
values. Confirm that all neighbors support the design.

### Add IS-IS authentication

| Task | Verified command | Source |
| - | - | - |
| Configure a level 2 key chain. | `set protocols isis level 2 authentication-key-chain base-key-global` | IS-IS, 26.2, page 110. |

Warning: changing an IS-IS key chain can drop adjacency. Stage both ends before
you commit the active key.

## BFD and convergence

BFD detects a failed path faster than protocol hello timers. Use BFD only on
links and peers that can absorb the packet rate.

| Protocol | Verified command | Source |
| - | - | - |
| OSPF | `set protocols ospf area 0.0.0.0 interface fe-0/0/1 bfd-liveness-detection minimum-interval 300` | OSPF, 26.2, page 358. |
| IS-IS | `set protocols isis interface ge-0/0/0.0 family inet bfd-liveness-detection minimum-interval 200` | IS-IS, 26.2, page 232. |
| IS-IS BFD authentication key chain | `set protocols isis interface ge-1/2/0.0 bfd-liveness-detection authentication key-chain secret123` | IS-IS, 26.2, page 246. |
| IS-IS SPF delay | `set protocols isis spf-options delay 1000` | IS-IS, 26.2, page 365. |

Warning: BFD timers that are too low can flap routes during transient delay.
Test the timer under normal load before production use.

## Static, aggregate, and generated routes

Use static routes for explicit reachability. Use aggregate routes to summarize
child routes. Use generated routes when a route must exist only while a policy
condition is true.

| Task | Verified command | Source |
| - | - | - |
| Install a default static route. | `set routing-options static route 0.0.0.0/0 next-hop 10.0.0.5` | Routing Policy, 26.2, page 136. |
| Create an aggregate route. | `set routing-options aggregate route 172.16.32.0/21` | Routing Policy, 26.2, page 182. |
| Create a generated default route with policy. | `set routing-options generate route 0.0.0.0/0 policy if-upstream-routes-exist` | Routing Policy, 26.2, page 185. |
| Verify route tables. | `show route table` | Routing Policy, 26.2, page 564. |

Warning: a default route can send all unknown traffic to the next hop. Confirm
the next hop and rollback path before you commit.

## Next-hop and route verification

Use route table checks to prove control-plane state. Use the forwarding table to
prove data-plane installation.

| Goal | Verified command | Source |
| - | - | - |
| Read route tables. | `show route table` | Routing Policy, 26.2, page 564. |
| Read BGP routes. | `show route protocol bgp` | Routing Policy, 26.2, page 71. |
| Read advertised BGP routes. | `show route advertising-protocol bgp` | Routing Policy, 26.2, page 140. |
| Read received BGP routes. | `show route receive-protocol bgp` | Routing Policy, 26.2, page 73. |
| Read forwarding entries. | `show route forwarding-table` | Routing Policy, 26.2, page 1556. |

Caution: a route can exist in the route table and still miss the forwarding
table. Check both states during an outage.
