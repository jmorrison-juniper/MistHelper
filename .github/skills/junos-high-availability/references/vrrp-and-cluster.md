# VRRP and SRX chassis cluster reference

Use this reference for VRRP and SRX chassis cluster work. Cite the document title
and train in each answer.

## Source selection

| Topic | Source document | Train | Index row |
| - | - | - | - |
| VRRP | Junos OS High Availability User Guide | 26.2 | `high-availability` |
| SRX chassis cluster | Junos OS Chassis Cluster User Guide for SRX Series Devices | 26.2 | `chassis-cluster-security-devices` |
| Multinode HA | Junos OS Multinode High Availability | 26.2 | `multinode-high-availability` |

## VRRP purpose

VRRP groups multiple routing devices into a virtual router. One device acts as
the primary router. Other devices act as backups. If the primary fails, one
backup becomes the new primary.

Warning: a wrong VRRP priority or virtual address can move the default gateway.
Hosts can lose connectivity during the election.

## VRRP group and virtual address

A VRRP group lives under an interface address. The virtual address must be the
same on all routers in the group. Do not include a prefix length in the virtual
address.

Verified commands:

```text
set vrrp-group group-id
set vrrp-group group-id virtual-address [ addresses ]
set vrrp-group group-id priority number
show protocols vrrp
show vrrp summary
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this rule:

- Use group identifiers from 0 through 255.
- Use one interface per VRRP group unless the design requires more.
- Use priority 255 only on a router that owns the virtual IP address.
- Use priorities 1 through 254 for backup routers.
- Remember that the default backup priority is 100.

## VRRP preempt rule

Preempt lets a higher-priority VRRP router become primary after it recovers. If
the virtual IP address is the same as the physical interface address, the guide
states that the priority must be 255 and preempt must be configured.

Warning: preempt can move gateway traffic after a router recovers. A repeated
failure can cause repeated gateway changes.

Verified hierarchy:

```text
[edit interfaces interface-name unit logical-unit-number family inet address address vrrp-group group-id preempt]
```

Source: Junos OS High Availability User Guide, train 26.2.

## VRRP tracked interface and route

VRRP can track a logical interface, a route, or bandwidth. Junos subtracts the
priority cost from the configured VRRP priority when the tracked item fails.
The sum of all priority costs must not exceed the configured group priority.

Warning: a wrong tracking cost can trigger an unwanted election. The gateway can
move to a backup router and drop active traffic.

Verified configuration fragment:

```text
track {
    interface interface-name {
        bandwidth-threshold bits-per-second priority-cost priority;
        priority-cost priority;
    }
    priority-hold-time seconds;
}
```

Verified source example items:

```text
route 59.0.58.153/32 routing-instance default priority-cost 5
interface et-0/0/0 priority-cost 30
```

Source: Junos OS High Availability User Guide, train 26.2.

Use this rule:

- Do not configure priority 255 when interface tracking is enabled.
- Track no more than 10 logical interfaces for each VRRP group.
- Use `priority-hold-time` to reduce elections caused by an interface flap.
- If `asymmetric-hold-time` is set, VRRP does not wait for the hold time when a tracked interface fails.

## Chassis cluster purpose

A chassis cluster combines two SRX firewalls into one logical device. The nodes
synchronize configuration, kernel state, and session information. One node acts
as primary, and the peer node acts as secondary.

Warning: enabling a chassis cluster reboots devices and changes interface names.
A wrong node ID or cluster ID can isolate the firewall.

Verified commands:

```text
set chassis cluster cluster-id 1 node 0 reboot
set chassis cluster cluster-id 1 node 1 reboot
show chassis cluster status
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

Use this rule:

- Use the same cluster ID on both nodes.
- Use node ID 0 on one chassis and node ID 1 on the peer chassis.
- Set cluster ID 0 only when you intend to disable clustering.
- Confirm both devices run the same Junos release before clustering.
- Confirm both devices use the same hardware model before clustering.

## Control link

The control link carries control traffic between nodes. Some SRX platforms use
dedicated control ports. SRX5000 platforms require control ports before the
cluster is formed.

Warning: a failed control link can cause a cluster fault. The firewall can fail
over or lose synchronization.

Verified commands:

```text
set chassis cluster control-ports fpc 4 port 0
set chassis cluster control-ports fpc 10 port 0
show chassis cluster interfaces
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

## Fabric link

The fabric link carries data traffic and state between nodes. It also carries
traffic that enters one node and exits or receives service on the peer node.

Warning: a failed fabric link can make redundancy groups ineligible. Traffic can
fail over or drop during recovery.

Verified commands:

```text
set interfaces fab0 fabric-options member-interfaces ge-0/0/1
set interfaces fab1 fabric-options member-interfaces ge-7/0/1
show chassis cluster interfaces
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

Use this rule:

- Use interfaces of the same type as fabric children.
- Configure an equal number of child links for `fab0` and `fab1`.
- Do not configure filters, policies, or services on a fabric interface.
- If a switch carries fabric links, enable jumbo frames on the switch ports.

## Redundancy group

A redundancy group controls primary and secondary ownership for a set of cluster
resources. Redundancy group 0 controls the Routing Engine role. Redundancy group
1 and later can control data interfaces.

Warning: an RG0 failover restarts processes on the new primary Routing Engine.
The failover can lose routing state and degrade performance.

Verified commands:

```text
set chassis cluster redundancy-group 0 node 0 priority 254
set chassis cluster redundancy-group 0 node 1 priority 1
set chassis cluster redundancy-group 1 node 0 priority 200
set chassis cluster redundancy-group 1 node 1 priority 100
show chassis cluster status
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

Use this rule:

- Do not place data plane monitoring on redundancy group 0 unless a platform source requires it.
- Use interface monitoring on redundancy groups 1 and later.
- Confirm failover counts after each planned failover.

## Interface monitoring and failover

A monitored interface has a weight. When that interface fails, Junos subtracts
the weight from the redundancy group threshold. The default threshold is 255.
When the threshold reaches 0, the redundancy group fails over to the peer node.

Warning: a wrong monitoring weight can cause an unplanned failover. Active
sessions can reset when traffic moves to the peer node.

Verified commands:

```text
set chassis cluster redundancy-group 1 interface-monitor ge-0/0/1 weight 130
set chassis cluster redundancy-group 1 interface-monitor ge-0/0/2 weight 140
show chassis cluster information
show chassis cluster interfaces
show chassis cluster status
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

## Redundant Ethernet interfaces

A redundant Ethernet interface, or `reth`, binds physical child interfaces from
the cluster nodes. The `reth-count` statement creates the number of redundant
Ethernet interfaces.

Warning: a wrong `reth` binding can move traffic to the wrong redundancy group.
The firewall can drop traffic for the affected zone.

Verified commands:

```text
set chassis cluster reth-count 5
set interfaces xe-1/0/0 gigether-options redundant-parent reth0
set interfaces reth0 redundant-ether-options redundancy-group 1
set interfaces reth0 unit 0 family inet address 192.0.2.1/24
show chassis cluster interfaces
```

Source: Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.

## Evidence checklist

Before a VRRP or chassis cluster answer is complete, confirm these items:

1. The source document matches the platform family.
2. The train is the newest readable train for the feature.
3. The command appears in the staged corpus.
4. The answer starts each disruptive action with `Warning`.
5. The answer gives a read command that proves the state.