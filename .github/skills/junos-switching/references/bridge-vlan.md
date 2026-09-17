# Bridge and VLAN

This file covers bridge domains, MAC learning, MAC limits, VLANs, trunk ports,
native VLANs, voice VLANs, and private VLANs.

Sources: `bridging-learning`, `multicast-l2`, and `security-services`. All rows
use Junos train 26.2.

## 1. Bridge domains

Use a bridge domain on MX or ACX platforms when the design uses the bridge
configuration hierarchy. Use the `vlans` hierarchy on EX and QFX switches unless
the platform source says otherwise.

| Task | Command | Verify | Source |
| - | - | - | - |
| Create a bridge domain. | `set bridge-domains customer1 domain-type bridge` | `show bridge-domains` | `bridging-learning`, train 26.2, page 26. |
| Add an interface to a bridge domain. | `set bridge-domains customer1 interface ge-2/0/0.0` | `show bridge-domains` | `bridging-learning`, train 26.2, page 26. |
| Set a VLAN ID on a bridge unit. | `set interfaces ge-2/0/0 unit 0 vlan-id 600` | `show interfaces` | `bridging-learning`, train 26.2, page 26. |
| Read learned MAC addresses. | `show bridge mac-table` | Confirm the learned address, VLAN, and interface. | `bridging-learning`, train 26.2, page 29. |
| Read detailed learned MAC data. | `show bridge mac-table extensive` | Confirm age, flags, and bridge domain detail. | `bridging-learning`, train 26.2, page 30. |

A bridge domain can isolate a tenant or service. Confirm the interface unit and
VLAN ID before you attach it to the bridge domain.

## 2. MAC learning and MAC limits

MAC learning records source MAC addresses and maps them to VLANs and interfaces.
A MAC limit controls how many addresses a VLAN, bridge domain, or interface can
learn.

| Task | Command | Verify | Source |
| - | - | - | - |
| Set the bridge MAC aging time. | `set global-mac-table-aging-time time` | `show bridge mac-table extensive` | `bridging-learning`, train 26.2, page 49. |
| Set a bridge domain MAC aging time. | `set mac-table-aging-time time` | `show bridge-domains` | `bridging-learning`, train 26.2, page 50. |
| Set a VLAN MAC table limit. | `set vlan-name switch-options mac-table-size limit packet-action action` | `show ethernet-switching table` | `multicast-l2`, train 26.2, page 94. |
| Set an interface MAC limit. | `set interface interface-name interface-mac-limit limit packet-action action` | `show ethernet-switching table` | `multicast-l2`, train 26.2, page 93. |
| Set a bridge domain MAC table limit. | `set bridge-domain-name bridge-options mac-table-size limit packet-action action` | `show bridge mac-table` | `security-services`, train 26.2, page 465. |

Caution: choose the packet action before you set a MAC limit. A wrong action can
blackhole a valid host until the table ages or the operator clears it.

## 3. Basic VLANs and access ports

Use these commands for common EX and QFX VLAN work. Replace names and numbers
with the approved design values.

| Task | Command | Verify | Source |
| - | - | - | - |
| Create a VLAN with one VLAN ID. | `set vlans vlan-name vlan-id vlan-id-number` | `show vlans` | `multicast-l2`, train 26.2, page 42. |
| Create a VLAN with a VLAN ID range. | `set vlans vlan-name vlan-id-list vlan-ids | vlan-id--vlan-id` | `show vlans` | `multicast-l2`, train 26.2, page 42. |
| Add a port to a VLAN from the interface hierarchy. | `set interface interface-name family ethernet-switching vlan members vlan-name` | `show ethernet-switching interfaces` | `multicast-l2`, train 26.2, page 42. |
| Configure an access port. | `set interfaces ge-0/0/1 unit 0 family ethernet-switching interface-mode access` | `show interfaces ae0 terse` | `multicast-l2`, train 26.2, page 181. |
| Add the access port to a VLAN. | `set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members v10` | `show ethernet-switching table` | `multicast-l2`, train 26.2, page 181. |

## 4. Trunk ports and the native VLAN

A trunk port carries tagged VLAN traffic. The native VLAN carries untagged
traffic on a trunk.

Warning: do not change a native VLAN until you verify the connected peer. A
native VLAN mismatch can put untagged traffic in the wrong VLAN.

| Task | Command | Verify | Source |
| - | - | - | - |
| Configure a trunk port. | `set interfaces intf-name unit 0 family ethernet-switching interface-mode trunk` | `show ethernet-switching table` | `multicast-l2`, train 26.2, page 390. |
| Add VLAN members to a trunk. | `set unit unit-number family ethernet-switching vlan members vlan-id` | `show ethernet-switching table` | `multicast-l2`, train 26.2, page 496. |
| Set a native VLAN on an interface. | `set interfaces interface-name native-vlan-id vlan-id` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 71. |
| Set a native VLAN on a sample trunk. | `set interfaces ge-0/2/0 native-vlan-id 1` | `show configuration interfaces` | `multicast-l2`, train 26.2, page 255. |

Use an access port for one data VLAN. Use a trunk port when the peer expects
multiple tagged VLANs.

## 5. Voice VLANs

A voice VLAN lets a phone carry voice traffic while a connected host uses a data
VLAN on the same access port. The source also states that the VoIP VLAN cannot
be a private VLAN.

| Task | Command | Verify | Source |
| - | - | - | - |
| Create the voice VLAN. | `set vlans voip vlan-id 33` | `show vlans` | `multicast-l2`, train 26.2, page 492. |
| Map the interface to the voice VLAN. | `set switch-options voip interface ge-0/0/8.0 vlan voip` | `show configuration` | `multicast-l2`, train 26.2, page 492. |
| Set a voice VLAN ID in the voice VLAN hierarchy. | `set voip vlan-id 33` | `show configuration` | `multicast-l2`, train 26.2, page 493. |

Caution: do not make the voice VLAN a private VLAN. The source says that a VoIP
VLAN cannot be a primary, community, or isolated private VLAN.

## 6. Private VLANs

A private VLAN separates hosts that share one primary VLAN. Use a community VLAN
for hosts that can talk to each other. Use an isolated VLAN for hosts that must
not talk to each other.

| Task | Command | Verify | Source |
| - | - | - | - |
| Create a community VLAN. | `set vlans vlan-hr private-vlan community vlan-id 200` | `show vlans` | `multicast-l2`, train 26.2, page 496. |
| Create an isolated VLAN. | `set vlans vlan-iso private-vlan isolated vlan-id 400` | `show vlans` | `multicast-l2`, train 26.2, page 496. |
| Map a community VLAN to the primary VLAN. | `set community-vlan-name primary-vlan primary-vlan-name` | `show vlans` | `multicast-l2`, train 26.2, page 508. |
| Add a private VLAN trunk port. | `set vlans pvlan100 interface ge-0/0/0.0 pvlan-trunk` | `show vlans pvlan100` | `multicast-l2`, train 26.2, page 547. |
| Stop local switching in the private VLAN. | `set vlans pvlan100 no-local-switching` | `show vlans pvlan100` | `multicast-l2`, train 26.2, page 592. |

Warning: test a private VLAN design before production use. A wrong primary,
community, or isolated mapping can isolate valid hosts.

## 7. Answer pattern

```text
Use <command> for <task>. This command is from <source>, train <train>, page <page>.
First read <show command>. If the device output differs from the design, stop.
Evidence:
- Junos: <source>, train <train>, page <page> -- <command>
- Verify: <show command> -- confirms <state>
```

