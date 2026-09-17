# Spanning tree and LAG

This file covers STP, RSTP, MSTP, VSTP, BPDU protection, root selection, LAGs,
LACP, minimum link count, and load balance behavior.

Sources: `stp-l2`, `interfaces-ethernet-switches`, and `mc-lag`. All rows use
Junos train 26.2.

## 1. Spanning tree safety

Spanning tree prevents loops when redundant layer 2 paths exist. A wrong root,
edge, or BPDU setting can create an outage.

Warning: do not change spanning tree on a production access layer without a
rollback plan. A wrong spanning tree setting can create a loop and drop the
access layer.

Before you change spanning tree, read these states:

| State | Command | Source |
| - | - | - |
| Bridge role and root data. | `show spanning-tree bridge` | `stp-l2`, train 26.2, page 128. |
| Interface role and state. | `show spanning-tree interface` | `stp-l2`, train 26.2, page 63. |
| Bridge statistics. | `show spanning-tree statistics bridge` | `stp-l2`, train 26.2, page 158. |
| Candidate RSTP configuration. | `show configuration protocols rstp` | `stp-l2`, train 26.2, page 198. |

## 2. RSTP tasks

RSTP is the usual choice for many modern access networks. Confirm platform
support before you replace an existing protocol.

| Task | Command | Verify | Source |
| - | - | - | - |
| Set the RSTP bridge priority. | `set protocols rstp bridge-priority 16k` | `show spanning-tree bridge` | `stp-l2`, train 26.2, page 44. |
| Set the cost for all RSTP interfaces. | `set protocols rstp interface all cost 1000` | `show spanning-tree interface` | `stp-l2`, train 26.2, page 44. |
| Set point-to-point mode for all RSTP interfaces. | `set protocols rstp interface all mode point-to-point` | `show spanning-tree interface` | `stp-l2`, train 26.2, page 44. |
| Set an RSTP cost on one interface. | `set protocols rstp interface ge-0/0/14 cost 1000` | `show spanning-tree interface` | `stp-l2`, train 26.2, page 48. |
| Block an edge port when BPDUs arrive. | `set interface ge-0/0/6 bpdu-timeout-action block` | `show configuration protocols rstp` | `stp-l2`, train 26.2, page 197. |

Use a lower bridge priority on the intended root bridge. Keep the design root
stable across the distribution layer.

## 3. MSTP tasks

MSTP maps groups of VLANs to spanning tree instances. Keep the region name,
revision, and VLAN map identical on all switches in the region.

| Task | Command | Verify | Source |
| - | - | - | - |
| Set the MSTP region name. | `set protocols mstp configuration-name region1` | `show configuration` | `stp-l2`, train 26.2, page 108. |
| Set the bridge priority for MSTI 1. | `set protocols mstp msti 1 bridge-priority 16k` | `show spanning-tree bridge` | `stp-l2`, train 26.2, page 108. |
| Map VLANs to MSTI 1. | `set protocols mstp msti 1 vlan [10 20]` | `show configuration` | `stp-l2`, train 26.2, page 108. |
| Set the cost for an MSTP interface. | `set protocols mstp interface xe-0/0/9:0 cost 1000` | `show spanning-tree interface` | `stp-l2`, train 26.2, page 108. |
| Set point-to-point mode for an MSTP interface. | `set protocols mstp interface xe-0/0/9:0 mode point-to-point` | `show spanning-tree interface` | `stp-l2`, train 26.2, page 108. |

Caution: do not change one MSTP region member alone. A mismatch can create a
separate region and change the path for many VLANs.

## 4. VSTP and STP notes

VSTP runs a separate spanning tree per VLAN. The staged source warns that the
command for all VLANs and all interfaces can exceed the supported limit on a
large switch.

| Task | Command | Verify | Source |
| - | - | - | - |
| Enable VSTP for all VLANs and interfaces. | `set protocols vstp vlan all interface all` | `show spanning-tree bridge` | `stp-l2`, train 26.2, page 140. |
| Set a bridge priority from the protocol edit level. | `set bridge-priority bridge-priority` | `show spanning-tree bridge` | `stp-l2`, train 26.2, page 36. |
| Set the BPDU destination address from the protocol edit level. | `set bpdu-destination-mac-address provider-bridge-group` | `show configuration protocols` | `stp-l2`, train 26.2, page 35. |

Caution: use VSTP only when the VLAN count and platform limits support it. A
large all-VLAN command can exceed device limits.

## 5. BPDU protection

BPDU protection helps protect an edge port from an unexpected switch. Confirm
the recovery procedure before you deploy a blocking action.

| Task | Command | Verify | Source |
| - | - | - | - |
| Block BPDUs on one interface. | `set layer2-control bpdu-block interface et-0/0/0.0` | `show configuration protocols layer2-control` | `stp-l2`, train 26.2, page 167. |
| Drop BPDUs on one interface. | `set layer2-control bpdu-block interface et-0/0/0.0 drop` | `show configuration protocols layer2-control` | `stp-l2`, train 26.2, page 170. |
| Configure BPDU block under the protocols hierarchy. | `set protocols layer2-control bpdu-block interface ge-0/0/5` | `show configuration protocols layer2-control` | `stp-l2`, train 26.2, page 178. |
| Configure an RSTP edge port with BPDU block. | `set rstp bpdu-block-on-edge interface et-0/0/0.0 edge` | `show configuration protocols rstp` | `stp-l2`, train 26.2, page 172. |

Warning: do not set BPDU block on a switch-to-switch link. Blocking control
BPDUs can hide a loop and drop the access layer.

## 6. LAG and LACP tasks

A LAG combines physical links into one aggregated Ethernet interface. LACP lets
peers negotiate membership.

| Task | Command | Verify | Source |
| - | - | - | - |
| Bind a physical link to an aggregated Ethernet interface. | `set ether-options 802.3ad aex` | `show interfaces ae0 terse` | `interfaces-ethernet-switches`, train 26.2, page 37. |
| Set the LAG link speed. | `set aex aggregated-ether-options link-speed speed` | `show interfaces ae0 terse` | `interfaces-ethernet-switches`, train 26.2, page 37. |
| Set the minimum link count. | `set aex aggregated-ether-options minimum-links number` | `show interfaces ae0 terse` | `interfaces-ethernet-switches`, train 26.2, page 38. |
| Set the minimum bandwidth. | `set aex aggregated-ether-options minimum-bandwidth` | `show interfaces ae0 terse` | `interfaces-ethernet-switches`, train 26.2, page 38. |
| Enable active LACP. | `set interfaces ae0 aggregated-ether-options lacp active` | `show lacp interfaces xe-0/1/0` | `interfaces-ethernet-switches`, train 26.2, page 44. |
| Use fast LACP timers. | `set interfaces ae0 aggregated-ether-options lacp periodic fast` | `show lacp statistics interfaces` | `interfaces-ethernet-switches`, train 26.2, page 44. |
| Add a sample member link. | `set interfaces xe-0/0/2 ether-options 802.3ad ae0` | `show interfaces ae0 terse` | `interfaces-ethernet-switches`, train 26.2, page 44. |
| Read LACP state. | `show lacp interfaces xe-0/1/0` | Confirm actor and partner state. | `interfaces-ethernet-switches`, train 26.2, page 54. |

Caution: do not raise the minimum link count above the number of healthy links.
The aggregated interface can go down and interrupt traffic.

## 7. Load balance behavior

Junos can install per-packet load balance behavior with a policy statement. Use
this only when the routing design requires it.

| Task | Command | Verify | Source |
| - | - | - | - |
| Configure per-packet load balance action. | `set policy-options policy-statement loadbal then load-balance per-packet` | `show route forwarding-table` | `interfaces-ethernet-switches`, train 26.2, page 110. |
| Enable dynamic load balance in a firewall term. | `set firewall family inet filter filter-name term term-name then dynamic-load-balance enable` | `show firewall filter` | `interfaces-ethernet-switches`, train 26.2, page 119. |

## 8. MC-LAG source use

Use `mc-lag` when two chassis present one LAG to a downstream device. This skill
uses it as a concept source only. Do not give an MC-LAG configuration command
unless you verify each interchassis, ICCP, and platform statement in that source.

## 9. Answer pattern

```text
Warning: <state the outage risk if the change touches spanning tree or LAG availability>.
Read <show command> first. Use <set command> only during the approved change window.
Evidence:
- Junos: <source>, train <train>, page <page> -- <command>
- Verify: <show command> -- confirms <state>
```
