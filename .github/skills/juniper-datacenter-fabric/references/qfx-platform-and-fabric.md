# QFX platform and fabric

Use this reference for QFX hardware facts, interface names, port modes, shared
buffers, Virtual Chassis Fabric, QFabric, and Junos Fusion coverage.

Sources:

- Junos OS Basics on the QFX Series, QFX archive 2014-2015.
- Interfaces on the QFX Series, QFX archive 2014-2015.
- Traffic Management on the QFX Series, QFX archive 2014-2015.
- Storage on the QFX Series, QFX archive 2014-2015.
- QFX3000-G QFabric System Deployment Guide, Junos OS 13.2X52.
- Troubleshooting and Monitoring on the QFX Series, QFX archive 2014-2015.

## 1. Choose the platform task

| Task | First read | Why |
| - | - | - |
| Identify a physical port. | `show interfaces terse` | It shows the interface name and link state. |
| Check a QFabric node name. | `show fabric administration inventory node-devices` | It maps node names to serial numbers and models. |
| Check a QFabric node group. | `show configuration fabric resources` | It shows node group membership. |
| Check shared buffer partitions. | `show configuration class-of-service shared-buffer` | It shows the configured buffer pool split. |
| Check live shared buffer use. | `show class-of-service shared-buffer` | It shows ingress and egress pool use. |
| Check interface switching state. | `show ethernet-switching interfaces` | It shows VLAN membership and blocking state. |

Warning: do not change a port mode during production traffic. The interface can
restart, and every server on that port can lose the link.

## 2. QFX interface names

QFX interface names follow the Junos pattern `type-fpc/pic/port.unit`. The QFabric
software package can add the node name before the interface name. The source gives
the form `device-name:type-fpc/pic/port.logical-unit-number`.

| Interface form | Meaning | Source |
| - | - | - |
| `xe-0/0/3.0` | A 10-Gigabit Ethernet logical interface. | Interfaces on the QFX Series, QFX archive 2014-2015. |
| `et-0/0/3` | A 40-Gigabit Ethernet physical port. | Interfaces on the QFX Series, QFX archive 2014-2015. |
| `xe-0/0/3:0` through `xe-0/0/3:3` | Four channelized 10-Gigabit Ethernet ports from one 40-Gigabit port. | Interfaces on the QFX Series, QFX archive 2014-2015. |
| `node-device1:xe-0/0/1.0` | A QFabric node interface with a node prefix. | Interfaces on the QFX Series, QFX archive 2014-2015. |
| `fc-0/0/0.0` | A Fibre Channel logical interface. | Storage on the QFX Series, QFX archive 2014-2015. |

Use `show interfaces terse` before you infer the interface type. Do not infer the
port mode from the name alone, because the platform and system mode can limit the
valid mapping.

## 3. Port mode and channelization workflow

Use this workflow before a port change:

1. Read the platform release and model with `show version`.
2. Read the interface state with `show interfaces terse`.
3. Read the configured interface with `show configuration interfaces <interface>`.
4. Compare the platform port table in the Interfaces guide.
5. Schedule a maintenance window if the change can restart the port.
6. Use `commit confirmed 2` for remote changes that can remove access.
7. Verify the state again with `show interfaces terse`.

The Interfaces guide confirms that a channelized 40-Gigabit Ethernet interface can
create `xe-0/0/3:0`, `xe-0/0/3:1`, `xe-0/0/3:2`, and `xe-0/0/3:3` on supported
QFX systems. The same guide confirms QFX3500 QFabric port ranges for `fc-0/0/0`,
`xe-0/0/0`, and other ports.

Do not give a platform port map unless the exact QFX model and release are known.
The QFX3500, QFX3600, QFX5100-24Q, and QFX5100-96S rules differ.

## 4. QFabric and Virtual Chassis Fabric

QFabric uses Node devices, Interconnect devices, and Director devices. The QFabric
Deployment Guide gives the hardware architecture, port mappings, oversubscription
ratios, node groups, and fabric forwarding class sets.

Virtual Chassis Fabric appears in the QFX corpus as a data center fabric option.
The staged corpus gives troubleshooting and operational coverage, but it does not
replace the platform release notes. Confirm member support on the exact release.

Junos Fusion appears only as limited corpus coverage in this staged set. If the
user asks for a Junos Fusion command and this reference does not list it, search the
staged corpus. Mark the result as unverified until a source confirms it.

Warning: do not remove a QFabric or Virtual Chassis Fabric member without a tested
recovery plan. A wrong member change can isolate a rack from the fabric.

## 5. QFabric safe reads

| Goal | Command | Source and release | Result |
| - | - | - | - |
| List node names, serial numbers, models, and connection state. | `show fabric administration inventory node-devices` | Storage on the QFX Series, QFX archive 2014-2015. | Confirms that the Director device detects each Node device. |
| Read node group membership. | `show configuration fabric resources` | Storage on the QFX Series, QFX archive 2014-2015. | Confirms which Node devices belong to a node group. |
| Read interface VLAN state in a QFabric partition. | `show ethernet-switching interfaces` | Interfaces on the QFX Series, QFX archive 2014-2015. | Shows node-prefixed logical interfaces and VLAN membership. |
| Read the chassis setting that supports LAG limits. | `show configuration chassis` | Storage on the QFX Series, QFX archive 2014-2015. | Helps verify node group LAG support. |

## 6. Shared buffer workflow

Use this workflow for buffer or lossless queue work:

1. Read the current buffer configuration.
2. Read live buffer use.
3. Identify each lossless class and multicast class.
4. Confirm whether storage traffic uses the path.
5. Change one interface group at a time.
6. Verify shared buffer and interface counters after the change.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Read configured buffer partitions. | `show configuration class-of-service shared-buffer` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Shows ingress and egress percentages. |
| Read live shared buffer allocation. | `show class-of-service shared-buffer` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Shows total, dedicated, shared, lossless, lossy, and multicast buffer values. |
| Configure ingress shared buffer use. | At `[edit class-of-service shared-buffer]`, use `set ingress percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Sets the ingress shared pool percentage. |
| Configure egress shared buffer use. | At `[edit class-of-service shared-buffer]`, use `set egress percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Sets the egress shared pool percentage. |
| Configure a lossless ingress partition. | At `[edit class-of-service shared-buffer]`, use `set ingress buffer-partition lossless percent 5` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Reserves part of the ingress pool for lossless traffic. |
| Configure a multicast egress partition. | At `[edit class-of-service shared-buffer]`, use `set egress buffer-partition multicast percent 20` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Reserves part of the egress pool for multicast traffic. |

Warning: do not reduce a lossless shared buffer during storage traffic. The switch
can drop lossless frames when the pool becomes too small.

## 7. Platform answer pattern

Use this answer shape:

```text
The platform is <model> on <release>. The safe first command is <show command>.
The source is <title>, <release>. Use it to verify <state>. Do not change <object>
until you schedule a maintenance window, because <specific consequence>.
```
