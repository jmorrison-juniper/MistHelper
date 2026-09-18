# Port security and Q-in-Q

This file covers MAC limiting, persistent MAC learning, DHCP snooping, dynamic
ARP inspection, storm control, Q-in-Q, and the service provider VLAN model.

Sources: `security-services`, `multicast-l2`, `subscriber-mgmt-vlan`, and
`interfaces-ethernet-switches`. All source rows use Junos train 26.2.

## 1. Port security safety

Port security can block users when a learned binding, limit, or control action
is wrong.

Caution: read the learned state before you set a port security control. A wrong
binding can block a valid host until the operator clears the table.

Use these read commands first:

| State | Command | Source |
| - | - | - |
| Learned switching table. | `show ethernet-switching table` | `security-services`, train 26.2, page 44. |
| Persistent MAC table. | `show ethernet-switching table persistent-mac` | `security-services`, train 26.2, page 388. |
| DHCP security bindings. | `show dhcp-security binding` | `security-services`, train 26.2, page 480. |
| VLAN DHCP security configuration. | `show vlans employee-vlan forwarding-options` | `security-services`, train 26.2, page 596. |

## 2. MAC limiting

MAC limiting controls the number of MAC addresses that a port or VLAN learns.
Choose the action before you configure the limit.

| Task | Command | Verify | Source |
| - | - | - | - |
| Set a MAC limit on one interface. | `set interface interface-name mac-limit limit action action` | `show ethernet-switching table` | `security-services`, train 26.2, page 33. |
| Set a MAC limit on all interfaces. | `set interface all mac-limit limit action action` | `show ethernet-switching table` | `security-services`, train 26.2, page 34. |
| Set a sample interface MAC limit. | `set interface ge-0/0/1 mac-limit 4` | `show ethernet-switching table` | `security-services`, train 26.2, page 39. |
| Set a secure access port MAC limit. | `set ethernet-switching-options secure-access-port interface ge-0/0/1 mac-limit 5 action drop` | `show ethernet-switching table` | `security-services`, train 26.2, page 486. |

Caution: the `drop` action can silently discard traffic from valid devices when
the limit is too small.

## 3. Persistent MAC learning

Persistent MAC learning keeps learned MAC addresses across interface events.
Use it with a MAC limit when a port must learn a fixed host set.

| Task | Command | Verify | Source |
| - | - | - | - |
| Enable persistent MAC learning on a generic interface. | `set interface interface-name persistent-learning` | `show ethernet-switching table persistent-mac` | `security-services`, train 26.2, page 34. |
| Enable persistent MAC learning on one interface. | `set interface ge-0/0/1 persistent-learning` | `show ethernet-switching table persistent-mac` | `security-services`, train 26.2, page 39. |
| Clear persistent MAC state after a host move. | `clear ethernet-switching table persistent-learning` | `show ethernet-switching table persistent-mac` | `security-services`, train 26.2, page 386. |

Caution: clear the old persistent MAC entry when a device moves. If the old port
restarts, the switch can restore the old entry and remove the new entry.

## 4. DHCP snooping and dynamic ARP inspection

DHCP snooping builds bindings for trusted and untrusted ports. Dynamic ARP
inspection uses those bindings to block forged ARP traffic.

| Task | Command | Verify | Source |
| - | - | - | - |
| Trust a DHCP server port. | `set interface interface-name dhcp-trusted` | `show dhcp-security binding` | `security-services`, train 26.2, page 35. |
| Trust a sample DHCP server port. | `set interface ge-0/0/8 dhcp-trusted` | `show dhcp-security binding` | `security-services`, train 26.2, page 39. |
| Enable ARP inspection on one VLAN. | `set vlan vlan-name arp-inspection` | `show vlans employee-vlan forwarding-options` | `security-services`, train 26.2, page 33. |
| Enable ARP inspection on all VLANs. | `set vlan all arp-inspection` | `show dhcp-security binding` | `security-services`, train 26.2, page 33. |
| Enable ARP inspection in ELS VLAN forwarding options. | `set vlans vlan-pri forwarding-options dhcp-security arp-inspection` | `show vlans employee-vlan forwarding-options` | `multicast-l2`, train 26.2, page 497. |
| Enable IP source guard in ELS VLAN forwarding options. | `set vlans vlan-pri forwarding-options dhcp-security ip-source-guard` | `show dhcp-security binding` | `multicast-l2`, train 26.2, page 497. |
| Set a static DHCP security binding. | `set interface interface-name static-ip ip-address vlan data-vlan mac mac-address` | `show dhcp-security binding` | `security-services`, train 26.2, page 479. |
| Set DHCP security trust-all for a VLAN. | `set vlans <vlan> forwarding-options dhcp-security trust-all` | `show dhcp-security binding` | `security-services`, train 26.2, page 474. |

Warning: do not trust an access port that faces users. A rogue DHCP server can
hand out wrong gateway data and interrupt host access.

## 5. Storm control

Storm control limits broadcast, unknown unicast, and multicast floods. Some
platforms can shut an interface when a storm exceeds a profile.

Warning: do not enable `action-shutdown` without a recovery plan. A traffic
burst can disable the interface and interrupt users.

| Task | Command | Verify | Source |
| - | - | - | - |
| Create a storm control profile. | `set forwarding-options storm-control-profiles scp all bandwidth-percentage 5` | `show configuration` | `evpn`, train 26.2, page 544. |
| Apply a storm control profile. | `set interfaces et-0/0/23 unit 0 family ethernet-switching storm-control scp` | `show configuration interfaces` | `evpn`, train 26.2, page 544. |
| Shut the port when the storm profile triggers. | `set forwarding-options storm-control-profiles scp all action-shutdown` | `show configuration` | `evpn`, train 26.2, page 544. |
| Set a recovery timeout. | `set interfaces ge-0/0/0 unit 0 family ethernet-switching storm-control scp recovery-timeout 120` | `show interfaces ae0 terse` | `evpn`, train 26.2, page 544. |

The `evpn` source is in the same 26.2 corpus tree. It is not in the index
because the index stays focused on classic layer 2 switching sources.

## 6. Q-in-Q and service provider VLANs

Q-in-Q carries a customer VLAN inside a service provider VLAN. The outer tag is
the service VLAN. The inner tag is the customer VLAN.

| Task | Command | Verify | Source |
| - | - | - | - |
| Enable stacked VLAN tagging from an interface edit level. | `set stacked-vlan-tagging` | `show configuration interfaces` | `subscriber-mgmt-vlan`, train 26.2, page 33. |
| Enable flexible VLAN tagging from an interface edit level. | `set flexible-vlan-tagging` | `show configuration interfaces` | `subscriber-mgmt-vlan`, train 26.2, page 35. |
| Enable flexible VLAN tagging on a LAG. | `set interfaces ae0 flexible-vlan-tagging` | `show configuration interfaces ae0` | `subscriber-mgmt-vlan`, train 26.2, page 115. |
| Enable VLAN tagging from an interface edit level. | `set vlan-tagging` | `show configuration interfaces` | `subscriber-mgmt-vlan`, train 26.2, page 117. |
| Set the outer service VLAN tag. | `set interfaces interface-name unit logical-unit-number vlan-tags outer vlan-id` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 384. |
| Set the inner customer VLAN tag. | `set interfaces interface-name unit logical-unit-number vlan-tags inner vlan-id` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 384. |
| Push a VLAN tag at ingress. | `set interfaces et-0/0/1:1 unit 0 input-vlan-map push` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 317. |
| Pop a VLAN tag at egress. | `set interfaces et-0/0/1:1 unit 0 output-vlan-map pop` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 317. |
| Swap a VLAN tag at ingress. | `set interfaces intf-name unit 100 input-vlan-map swap` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 390. |
| Enable Q-in-Q tunneling on a VLAN. | `set vlans customer-1 dot1q-tunneling` | `show vlans customer-1` | `multicast-l2`, train 26.2, page 748. |
| Tunnel STP across the customer VLAN. | `set vlans customer-1 dot1q-tunneling layer2-protocol-tunneling stp` | `show vlans customer-1` | `multicast-l2`, train 26.2, page 748. |
| Tunnel all supported layer 2 protocols. | `set vlans customer-1 dot1q-tunneling layer2-protocol-tunneling all` | `show vlans customer-1` | `multicast-l2`, train 26.2, page 748. |

Caution: confirm the tag direction before you use push, pop, or swap. A wrong
map can put customer traffic in the wrong service VLAN.

## 7. Answer pattern

```text
Read <show command> first. If the binding, tag, or storm state differs from the design, stop.
Use <set command> during the approved change window.
Evidence:
- Junos: <source>, train <train>, page <page> -- <command>
- Verify: <show command> -- confirms <state>
```
