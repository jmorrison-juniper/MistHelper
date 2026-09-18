# Virtual Chassis reference

Use this reference for EX and QFX Virtual Chassis work. Cite the document title
and train in each answer.

## Source selection

| Platform or topic | Source document | Train | Index row |
| - | - | - | - |
| Current EX and QFX Virtual Chassis | Virtual Chassis User Guide for Switches | 26.2 | `virtual-chassis` |
| QFX-specific Virtual Chassis | Virtual Chassis User Guide for Switches | 26.2 | `virtual-chassis-qfx` |
| EX2200, EX3300, EX4200, EX4500, and EX4550 | Virtual Chassis User Guide for EX2200, EX3300, EX4200, EX4500 and EX4550 Switches | 24.4 fallback | `virtual-chassis-ex-4200-4500` |
| EX8200 | Junos OS for EX Series Ethernet Switches Virtual Chassis User Guide for EX8200 Switches | 24.2 fallback | `virtual-chassis-ex-8200` |
| MX interchassis redundancy | Junos OS Interchassis Redundancy Using Virtual Chassis User Guide for MX Series Routers | 26.2 | `virtual-chassis-mx` |
| Virtual Chassis Fabric | Virtual Chassis Fabric User Guide | 26.2 | `virtual-chassis-fabric` |

Caution: two EX Virtual Chassis guides use fallback trains. Read
[Verification](./verification.md) before you answer from those guides.

## Member and role rules

A Virtual Chassis member can operate in the primary Routing Engine role, the
backup Routing Engine role, or the linecard role. A standalone switch that
supports Virtual Chassis acts as member 0 and as the primary of itself. A
nonprovisioned Virtual Chassis elects primary and backup members. A
preprovisioned Virtual Chassis lets the operator assign roles.

Source: Virtual Chassis User Guide for Switches, train 26.2.

Use these read commands first:

```text
show virtual-chassis
```

The `show virtual-chassis` command displays member IDs, status, serial numbers,
models, priorities, roles, and VCP interfaces. The guide uses it to verify a
primary and backup role change.

## Mastership priority

Use mastership priority to influence the primary and backup election in a
nonprovisioned Virtual Chassis. The guide shows priority 255 for two members
when it configures GRES in a Virtual Chassis.

Warning: a mastership priority change can move the control plane. A wrong value
can cause an unplanned switchover and interrupt management access.

Verified commands:

```text
set virtual-chassis member 0 mastership-priority 255
set virtual-chassis member 1 mastership-priority 255
show virtual-chassis
```

Source: Junos OS High Availability User Guide, train 26.2.

## VCP port rules

A Virtual Chassis Port, or VCP, connects members. The guide shows automatic VCP
conversion and manual VCP conversion. A manual conversion uses the operational
command that sets a PIC slot and port number.

Warning: a wrong VCP change can isolate a member. The stack can drop traffic to
that member during the outage.

Verified commands:

```text
request virtual-chassis vc-port set pic-slot slot-number port port-number
show virtual-chassis
```

Source: Virtual Chassis User Guide for Switches, train 26.2.

Apply a manual VCP change one link at a time. The guide warns that connecting
both VCPs on a new switch at the same time can make an existing member
non-operational for several seconds.

## Split detection

Split detection is enabled by default. Juniper recommends `no-split-detection`
for a two-member Virtual Chassis. Juniper strongly recommends that split
detection stays enabled for a Virtual Chassis with more than two members.

Warning: wrong split detection can create a split-brain condition. Two partitions
can forward as independent systems and drop site traffic.

Verified command:

```text
delete virtual-chassis no-split-detection
```

Source: Virtual Chassis User Guide for Switches, train 26.2.

Use this rule:

- If the Virtual Chassis has two members, verify the intended split detection behavior before a change.
- If the Virtual Chassis has more than two members, remove `no-split-detection` unless a platform source says otherwise.
- After a member add or remove action, run `show virtual-chassis` and verify every expected member.

## Mixed mode

Some EX and QFX combinations need mixed mode because member switches have
operational differences. Other combinations can interoperate without mixed mode
when they use the same Junos OS image.

Warning: a wrong mixed mode change can make a member inactive. A mixed stack can
lose redundancy and drop traffic during the reboot.

Verified commands:

```text
show virtual-chassis mode
request virtual-chassis mode mixed member 4
request virtual-chassis mode mixed reboot
request virtual-chassis mode mixed all-members reboot
request virtual-chassis mode mixed disable all-members
request system reboot all-members
```

Sources: Virtual Chassis User Guide for Switches, train 26.2. The EX4200 and
EX4500 troubleshooting guide is a fallback source at train 24.4.

Use this rule:

- Confirm the exact platform combination before you set mixed mode.
- If you add a mixed-mode member to a non-mixed stack, set mixed mode on all members.
- If you remove a member and the stack becomes non-mixed, remove mixed mode and reboot the stack.

## GRES in a Virtual Chassis

GRES lets the primary and backup Routing Engines switch roles without interrupting
packet forwarding. The backup Routing Engine synchronizes kernel and forwarding
state from the primary.

Warning: a GRES role change moves the control plane. Wait at least two minutes
between Routing Engine failovers, or state can fail to synchronize.

Verified commands:

```text
show virtual-chassis
request session member 1
show system switchover
request chassis routing-engine master acquire
```

Source: Virtual Chassis User Guide for Switches, train 26.2.

Read `show system switchover` on the backup Routing Engine. The source states
that the command is not supported on the primary Routing Engine.

## Removal and recycle rules

When a member leaves the Virtual Chassis, the primary keeps the member ID in its
configuration database. The `show virtual-chassis` output can continue to show
that member as `NotPrsnt`.

Warning: a member removal can change interface names and role assignment. A
wrong recycle can make a replacement inherit the wrong configuration.

Verified commands:

```text
delete member removed-member-id
request virtual-chassis recycle member-id member-id
request virtual-chassis mode mixed disable
request virtual-chassis renumber member-id 1 new-member-id 0
replace pattern ge-1/ with ge-0/
```

Source: Virtual Chassis User Guide for Switches, train 26.2.

## Evidence checklist

Before a Virtual Chassis answer is complete, confirm these items:

1. The source document matches the platform family.
2. The train is the newest readable train for that document.
3. The command appears in the staged corpus.
4. The answer starts each disruptive action with `Warning`.
5. The answer states the fallback train when the source row uses a fallback.