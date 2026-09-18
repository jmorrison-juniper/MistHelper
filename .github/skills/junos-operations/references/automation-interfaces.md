# Automation and programmatic interfaces

Use this reference for SNMP, streaming telemetry, NETCONF, the Junos XML
protocol, REST, commit scripts, op scripts, event policies, and Python.

## Source map

| Source | Train | Use |
| - | - | - |
| `Junos OS Automation Scripting User Guide` | 22.1 | Commit scripts, op scripts, event policies, Python, and event traps. |
| `Junos OS NETCONF XML Management Protocol Developer Guide` | 26.2 | NETCONF service, sessions, lock, load, commit, and rescue actions. |
| `Junos XML Management Protocol Developer Guide` | 26.2 | XML protocol operations and compare output. |
| `Junos OS REST API Guide` | 26.2 | REST service and API Explorer. |
| `Junos OS OpenConfig User Guide` | 26.2 | gRPC, gNMI, and OpenConfig telemetry. |
| `Junos OS Network Management and Monitoring Guide` | 26.2 | SNMP communities, traps, views, and SNMP read commands. |

## SNMP communities, traps, and views

| Task | Command | Mode | Source |
| - | - | - | - |
| Read SNMP configuration. | `show configuration snmp` | Operational | Network management guide 26.2. |
| Configure a read-only community. | `set snmp community REPLACE_COMMUNITY authorization read-only` | Configuration | Network management guide 26.2, from the `community` statement under `[edit snmp]`. |
| Limit a community to clients. | `set snmp community REPLACE_COMMUNITY clients 192.0.2.10/32` | Configuration | Network management guide 26.2, from the `community` statement under `[edit snmp]`. |
| Configure a trap target. | `set snmp trap-group NOC targets 192.0.2.10` | Configuration | Network management guide 26.2, from the `trap-group` statement under `[edit snmp]`. |
| Configure a trap category. | `set snmp trap-group NOC categories authentication` | Configuration | Network management guide 26.2, from the `trap-group` statement under `[edit snmp]`. |
| Configure a trap version. | `set snmp trap-group NOC version v2` | Configuration | Network management guide 26.2, from the `trap-group` statement under `[edit snmp]`. |
| Define a MIB view. | `set snmp view NOC-VIEW oid 1.3.6.1 include` | Configuration | Network management guide 26.2, from the `view` statement under `[edit snmp]`. |
| Read SNMP counters. | `show snmp statistics` | Operational | QFabric troubleshooting guide 26.2. |
| Walk a MIB. | `show snmp mib walk system` | Operational | Automation guide 22.1. |

Warning: use `commit confirmed` for an SNMP access change. A wrong client,
view, or community can remove monitoring until console access restores it.

Prefer SNMPv3 when the platform and monitoring system support it. Do not put a
real community string in an example, log, or pull request.

## Streaming telemetry and OpenConfig

| Task | Command | Mode | Source |
| - | - | - | - |
| Confirm OpenConfig package support. | `request system software add` | Operational | OpenConfig guide 26.2. |
| Configure analytics trace. | `set services analytics traceoptions flag xmlproxy` | Configuration | NETCONF guide 26.2. |
| Configure inband telemetry device ID. | `set services inband-flow-telemetry device-id 15001` | Configuration | Flow monitoring guide 26.2. |
| Configure telemetry metadata length. | `set services inband-flow-telemetry meta-data-stack-length 100` | Configuration | Flow monitoring guide 26.2. |
| Configure telemetry hop limit. | `set services inband-flow-telemetry hop-limit 5` | Configuration | Flow monitoring guide 26.2. |
| Configure VXLAN flow telemetry. | `set services inband-flow-telemetry flow-type vxlan` | Configuration | Flow monitoring guide 26.2. |
| Configure a collector address. | `set services inband-flow-telemetry profile p_term collector destination-address 192.0.2.10` | Configuration | Flow monitoring guide 26.2. |
| Configure a collector port. | `set services inband-flow-telemetry profile p_term collector destination-port 3055` | Configuration | Flow monitoring guide 26.2. |
| View analyzer statistics. | `show services inband-flow-telemetry stats` | Operational | Flow monitoring guide 26.2. |

OpenConfig and telemetry support differs by platform. Verify the platform and
release before you paste a telemetry configuration.

## NETCONF

| Task | Command | Mode | Source |
| - | - | - | - |
| Enable NETCONF over SSH. | `set system services netconf ssh` | Configuration | NETCONF guide 26.2. |
| Enable NETCONF trace output. | `set system services netconf traceoptions file netconf` | Configuration | NETCONF guide 26.2. |
| Read the NETCONF log. | `show log netconf` | Operational | NETCONF guide 26.2. |
| Save a rescue configuration for NETCONF recovery. | `request system configuration rescue save` | Operational | NETCONF guide 26.2. |
| Load a merge file by NETCONF workflow. | `load merge filename.conf` | Configuration | NETCONF guide 26.2. |
| Commit a NETCONF-loaded change safely. | `commit confirmed 5 comment "netconf safety timer"` | Configuration | NETCONF guide 26.2 and CLI guide 26.2. |

Warning: use a confirmed commit for NETCONF configuration changes. A bad remote
change can disconnect the NETCONF session and all other management sessions.

## Junos XML protocol

| Task | Operation or command | Source |
| - | - | - |
| Read set-form configuration before XML work. | `show configuration | display set` | XML guide 26.2. |
| Compare candidate configuration. | `show | compare` | XML guide 26.2. |
| Compare a revision. | `show | compare revision <revision-id>` | XML guide 26.2. |
| Read a protocol trace file. | `show log <filename>` | XML guide 26.2. |
| Save a rescue file before remote work. | `request system configuration rescue save` | XML guide 26.2. |

Use XML protocol examples only after you confirm the device release and the RPC
shape in the source guide.

## REST interface

| Task | Command | Mode | Source |
| - | - | - | - |
| Enable REST API Explorer. | `set system services rest enable-explorer` | Configuration | REST API guide 26.2. |
| Commit REST service changes safely. | `commit confirmed 5 comment "rest safety timer"` | Configuration | CLI guide 26.2. |
| Verify the REST configuration. | `show configuration system services rest` | Operational | REST API guide 26.2. |

Warning: expose REST only through an approved management network. A wrong REST
service configuration can expose device control to an unapproved client.

## Commit scripts

| Task | Command | Mode | Source |
| - | - | - | - |
| Configure a commit script. | `set system scripts commit file source-route.xsl` | Configuration | Automation guide 22.1. |
| Configure commit script trace output. | `set system scripts commit traceoptions file commit-script.log` | Configuration | Automation guide 22.1. |
| Enable Python for scripts. | `set system scripts language python` | Configuration | Automation guide 22.1. |
| Enable Python 3 for scripts where supported. | `set system scripts language python3` | Configuration | NETCONF guide 26.2. |
| Read commit script logs. | `show log commit-script.log` | Operational | Automation guide 22.1. |
| Test with a commit check. | `commit check` | Configuration | CLI guide 26.2. |

Warning: a commit script can block commits or change the candidate result. Test
it on a lab device before you enable it on production.

## Op scripts

| Task | Command | Mode | Source |
| - | - | - | - |
| Configure an op script. | `set system scripts op file connect-ipv6.py` | Configuration | Automation guide 22.1. |
| Enable Python for op scripts. | `set system scripts language python` | Configuration | Automation guide 22.1. |
| Read op script logs. | `show log op-script.log | last 100` | Operational | Automation guide 22.1. |
| Run an operational check from configuration mode. | `run show log op-script.log | last 100` | Configuration | CLI guide 26.2. |

Keep op script output short. Long output can hide the line that matters during
an outage.

## Event policies

| Task | Command | Mode | Source |
| - | - | - | - |
| Start an event policy. | `set event-options policy raise-trap-on-ospf-nbrdown events rpd_ospf_nbrdown` | Configuration | Automation guide 22.1. |
| Add an event action. | `set event-options policy policy1 then execute-commands output-filename ge-interfaces` | Configuration | Automation guide 22.1. |
| Raise an SNMP trap from an event. | `set event-options policy raise-trap-on-ospf-nbrdown then raise-trap` | Configuration | Automation guide 22.1. |
| Verify event policy configuration. | `show configuration event-options` | Operational | Automation guide 22.1. |

Warning: an event policy can repeat an action each time an event occurs. A bad
policy can fill logs or repeat an unwanted operational command.

## Python interpreter on Junos

| Task | Command | Mode | Source |
| - | - | - | - |
| Enable Python scripts. | `set system scripts language python` | Configuration | Automation guide 22.1. |
| Enable Python 3 scripts where supported. | `set system scripts language python3` | Configuration | NETCONF guide 26.2. |
| Configure a Python op script. | `set system scripts op file connect-ipv6.py` | Configuration | Automation guide 22.1. |
| Configure the Python event script user. | `set event-options event-script file config-change.py python-script-user admin` | Configuration | Automation guide 22.1. |
| Check script output. | `show log op-script.log | last 100` | Operational | Automation guide 22.1. |

Use the platform documentation to confirm the Python version. Do not assume that
all devices support the same interpreter.
