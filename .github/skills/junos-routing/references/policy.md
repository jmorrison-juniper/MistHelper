# Routing policy

Use this reference for policy terms, match conditions, actions, import policy,
export policy, communities, path preference, and routing recipes.

Public source URL for all rows:
`https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip`

## Contents

1. [Policy structure](#policy-structure)
2. [BGP import and export](#bgp-import-and-export)
3. [Communities](#communities)
4. [Path preference](#path-preference)
5. [Damping](#damping)
6. [Common recipes](#common-recipes)

## Policy structure

A policy statement contains terms. Each term has match conditions and actions.
Use one policy for one purpose when possible.

| Task | Verified command | Source |
| - | - | - |
| Match static routes. | `set policy-options policy-statement send-static term 1 from protocol static` | Routing Policy, 26.2, page 135, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/routing-policy.md`. |
| Accept the matched route. | `set policy-options policy-statement send-static term 1 then accept` | Routing Policy, 26.2, page 135. |
| Read the policy tree. | `show configuration policy-options` | IS-IS, 26.2, page 223, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/is-is.md`. |

Warning: an accepting term can export more routes than intended. Put a precise
match condition before an accept action.

## BGP import and export

Export controls what the router advertises. Import controls what the router
accepts and installs.

| Task | Verified command | Source |
| - | - | - |
| Export static routes to a BGP group. | `set protocols bgp group external-peers export send-static` | BGP, 26.2, page 462, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/bgp.md`. |
| Import a policy on one neighbor. | `set protocols bgp group external-peers neighbor 10.0.0.2 import import-communities` | Routing Policy, 26.2, page 613. |
| Verify advertised routes. | `show route advertising-protocol bgp` | Routing Policy, 26.2, page 140. |
| Verify received routes. | `show route receive-protocol bgp` | Routing Policy, 26.2, page 73. |

Caution: import policy can hide a valid route from the route table. Check the
receive table and the active route table.

## Communities

Use communities to mark routes for later policy decisions. Keep a stable naming
pattern for communities and policies.

| Task | Verified command | Source |
| - | - | - |
| Define a community. | `set policy-options community R3_PREFERRED members 64511:3` | Routing Policy, 26.2, page 572. |
| Match a community. | `set policy-options policy-statement change-local-preference term find-R1-routes from community` | Routing Policy, 26.2, page 571. |
| Add a community to static routes. | `set policy-options policy-statement send-static term 1 then community add R1_PREFERRED` | Routing Policy, 26.2, page 574. |
| Remove communities on import. | `set protocols bgp group external-peers neighbor 10.0.0.2 import remove-communities` | Routing Policy, 26.2, page 625. |

Warning: a community removal policy can remove a tag that another router needs.
Review downstream policy before you apply it.

## Path preference

Use local preference and protocol path selection with care. Local preference is
usually safer because it stays inside the local AS.

| Task | Verified command | Source |
| - | - | - |
| Raise local preference for static routes. | `set policy-options policy-statement send-static term 1 then local-preference 200` | Routing Policy, 26.2, page 136. |
| Ignore AS path length. | `set protocols bgp path-selection as-path-ignore` | BGP, 26.2, page 296. |
| Remove private AS values. | `set protocols bgp group ext neighbor 192.168.20.1 remove-private` | BGP, 26.2, page 307. |

Warning: changing path selection can move traffic to a less tested path. Verify
route choice and forwarding after the commit.

## Damping

Damping suppresses unstable routes. Use it only when repeated flaps cause a
larger problem than temporary suppression.

| Task | Verified command | Source |
| - | - | - |
| Enable BGP damping. | `set protocols bgp damping` | Routing Policy, 26.2, page 647. |
| Enable damping for multicast VPN signaling. | `set protocols bgp group ibgp family inet-mvpn signaling damping` | Routing Policy, 26.2, page 663. |

Warning: damping can keep a repaired prefix hidden. Tell the operator how to
verify the suppressed route state before use.

## Common recipes

### Export a static route to BGP

1. Configure the static route.
2. Match the static route in policy.
3. Accept the policy term.
4. Attach the policy to the BGP group.
5. Verify the advertised route.

Verified command set:

```text
set routing-options static route 0.0.0.0/0 next-hop 10.0.0.5
set policy-options policy-statement send-static term 1 from protocol static
set policy-options policy-statement send-static term 1 then accept
set protocols bgp group external-peers export send-static
show route advertising-protocol bgp
```

### Prefer one learned path

1. Match the route set with a community or protocol match.
2. Set local preference on the preferred path.
3. Verify the active route.
4. Verify the forwarding table.

Verified command set:

```text
set policy-options community R3_PREFERRED members 64511:3
set policy-options policy-statement send-static term 1 then local-preference 200
show route protocol bgp
show route forwarding-table
```

### Remove private AS values

1. Confirm that the neighbor expects private AS removal.
2. Configure the command on the correct neighbor.
3. Verify advertised routes.

Verified command set:

```text
set protocols bgp group ext neighbor 192.168.20.1 remove-private
show route advertising-protocol bgp
```

Warning: do not remove private AS values unless the peer requires that behavior.
The peer can reject or misinterpret paths.
