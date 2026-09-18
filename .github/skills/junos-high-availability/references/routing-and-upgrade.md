# Routing, switchover, and upgrade reference

Use this reference for GRES, NSR, NSB, unified ISSU, NSSU, and graceful restart.
Cite the document title and train in each answer.

## Source selection

| Topic | Source document | Train | Index row |
| - | - | - | - |
| GRES, NSR, NSB, unified ISSU, NSSU, and graceful restart | Junos OS High Availability User Guide | 26.2 | `high-availability` |
| Alternate high availability guide copy | Junos OS High Availability User Guide | 25.4 | `high-availability 2` |
| Virtual Chassis Fabric NSSU | Virtual Chassis Fabric User Guide | 26.2 | `virtual-chassis-fabric` |
| EX8200 NSSU | Junos OS for EX Series Ethernet Switches Virtual Chassis User Guide for EX8200 Switches | 24.2 fallback | `virtual-chassis-ex-8200` |

## GRES

Graceful Routing Engine switchover, or GRES, synchronizes the backup Routing
Engine with the primary Routing Engine. It preserves kernel state and forwarding
state during a Routing Engine role change.

Warning: a Routing Engine switchover moves the control plane. A wrong or early
switchover can interrupt management access.

Verified commands:

```text
set chassis redundancy graceful-switchover
show system switchover
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this rule:

- Run `show system switchover` on the backup Routing Engine.
- Confirm `Graceful switchover: On`.
- Confirm that the configuration database and kernel database are ready.

## NSR

Nonstop active routing, or NSR, requires GRES. NSR lets the backup Routing
Engine take control without a restart of supported routing protocols. The guide
states that the switchover is transparent to neighbors.

Warning: an NSR switchover before BGP synchronization completes can flap BGP.
Confirm BGP replication before a planned switchover.

Verified commands:

```text
set chassis redundancy graceful-switchover
set routing-options nonstop-routing
set system commit synchronize
show task replication
show bgp replication
show bfd session
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this rule:

- Configure `commit synchronize` with NSR.
- Read `show task replication` for protocol state.
- If BGP runs, read `show bgp replication`.
- Confirm `Protocol state` is idle and `Synchronization state` is complete before a BGP NSR switchover.

Caution: the guide states that restarting `rpd` on the primary Routing Engine
after NSR starts disrupts protocol adjacency and can cause traffic loss.

## NSB

Nonstop bridging, or NSB, requires GRES. NSB synchronizes supported Layer 2
protocol information between the primary and backup Routing Engines.

Warning: a Routing Engine switchover without NSB can disrupt Layer 2 protocol
state. Layer 2 traffic can reconverge during the switchover.

Verified commands:

```text
set chassis redundancy graceful-switchover
set protocols layer2-control nonstop-bridging
```

Source: Junos OS High Availability User Guide, train 26.2.

Use NSB before NSSU when the platform supports it. The high availability guide
recommends NSB so supported Layer 2 protocols operate seamlessly during the
Routing Engine switchover that is part of NSSU.

## Unified ISSU

Unified in-service software upgrade, or unified ISSU, upgrades software while the
system continues to forward traffic. The source requires GRES and NSR. Some
platforms also need NSB.

Warning: unified ISSU starts a live software upgrade. An unsupported package or
missed prerequisite can interrupt forwarding and management access.

Verified commands:

```text
show chassis hardware
set chassis redundancy graceful-switchover
set routing-options nonstop-routing
set system commit synchronize
show task replication
request routing-engine login re1
show system switchover
show version invoke-on all-routing-engines
request system snapshot
request system software in-service-upgrade /var/tmp/package-name.tgz
show chassis in-service-upgrade
show log messages
show version
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this prerequisite list:

1. Confirm two Routing Engines with `show chassis hardware`.
2. Enable GRES and NSR.
3. Enable `commit synchronize`.
4. Confirm NSR with `show task replication`.
5. Confirm GRES on the backup Routing Engine.
6. Confirm both Routing Engines run the same Junos release.
7. Back up the system software when the plan requires it.
8. Start the upgrade from a console session.

For enhanced mode, the guide confirms this validation command:

```text
request system software validate in-service-upgrade /var/tmp/package-name.tgz enhanced-mode
```

Caution: the staged guide text omits the command name before the enhanced-mode
start example in one converted line. Confirm the exact enhanced-mode start
syntax in the source before you run it.

## Single-RE ISSU

Single-RE ISSU preserves forwarding state, but OSPF and BGP rebuild protocol
state through graceful restart after the control plane recovers.

Warning: single-RE ISSU starts immediately when you enter the command. The
source states that the process cannot be paused or interrupted.

Verified commands:

```text
request system software in-service-upgrade /var/tmp/package-name.tgz
show log messages
show version
show route summary
show chassis fpc
show interfaces terse
show ethernet-switching table
show lacp interfaces
show dot1x interface
show system services dhcp binding
ping ip-address rapid count 20
```

Source: Junos OS High Availability User Guide, train 26.2.

The source states that single-RE ISSU is not supported for Virtual Chassis.

## NSSU

Nonstop software upgrade, or NSSU, upgrades EX switches and Virtual Chassis
members one at a time. NSSU can take longer than a normal software add because
it upgrades each line card or member sequentially.

Warning: NSSU cannot downgrade software and cannot roll back after completion.
A wrong target release can leave no simple rollback path.

Verified commands:

```text
request system software nonstop-upgrade reboot /var/tmp/package-name-m.nZx-distribution.tgz
request system software nonstop-upgrade no-old-master-upgrade /var/tmp/package-name-m.nZx-distribution.tgz
show version invoke-on all-routing-engines
show chassis nonstop-upgrade
request chassis routing-engine master switch
request system snapshot slice alternate routing-engine both
```

Source: Junos OS High Availability User Guide, train 26.2. The EX8200 fallback
source is Junos OS for EX Series Ethernet Switches Virtual Chassis User Guide
for EX8200 Switches, train 24.2.

Use this prerequisite list for EX switches and Virtual Chassis:

1. Confirm every member and Routing Engine runs the same Junos release.
2. Confirm GRES is enabled.
3. Confirm NSR is enabled.
4. Enable NSB when the platform supports it.
5. Confirm LAG member links sit on different members or line cards.
6. For an EX Virtual Chassis, confirm a ring topology.
7. For an EX Virtual Chassis, confirm primary and backup members are adjacent.
8. For an EX Virtual Chassis, confirm preprovisioned roles.
9. For a two-member Virtual Chassis, confirm `no-split-detection`.

## Graceful restart

Graceful restart lets a router continue forwarding while the control plane
recovers state from neighbors. Helper mode is enabled by default even when
graceful restart is not enabled.

Warning: changing BGP or LDP graceful restart after a session starts resets that
session. Traffic can reconverge while peers negotiate capability again.

Verified commands and statements:

```text
set graceful-restart
show bgp neighbor 192.0.2.10
show log
show ospf overview
show ospfv3 overview
show rsvp neighbor detail
show rsvp version
show ldp session detail
show connections
show route instance detail
show route protocol l2vpn
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this protocol table:

| Protocol or service | Configuration hierarchy | Verification command |
| - | - | - |
| Global graceful restart | `[edit routing-options graceful-restart]` | `show route instance detail` when a routing instance depends on it. |
| BGP | `[edit protocols bgp graceful-restart]` | `show bgp neighbor 192.0.2.10` |
| OSPF | `[edit protocols ospf graceful-restart]` | `show ospf overview` and trace log output. |
| OSPFv3 | `[edit protocols ospfv3 graceful-restart]` | `show ospfv3 overview` and trace log output. |
| IS-IS | `[edit protocols isis traceoptions flag graceful-restart]` for tracking | `show log` |
| RSVP, CCC, and TCC | `[edit protocols rsvp graceful-restart]` | `show rsvp neighbor detail`, `show rsvp version`, or `show connections` |
| LDP | `[edit protocols ldp graceful-restart]` | `show ldp session detail` |
| Layer 3 VPN | `[edit routing-instances instance-name routing-options graceful-restart]` | `show route instance detail` |
| Layer 2 VPN | Protocol graceful restart plus VPN configuration | `show route protocol l2vpn` |

The guide gives per-protocol disable statements for BGP, OSPF, OSPFv3, RSVP,
CCC, TCC, and LDP. Do not claim support for a protocol unless the source names
that protocol or the target platform guide confirms it.