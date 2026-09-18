# Implementation and verification

Use this reference to prove a data center fabric answer before a live change.

## 1. Verify a command

Use this procedure before you give a configuration command:

1. Open `references/corpus-index.csv`.
2. Find the source document by file name, title, or topic.
3. Open the Markdown file under the staged corpus root.
4. Search for the command name or configuration statement.
5. Confirm that the source release matches the platform release.
6. Confirm that the command is read-only or configuration mode.
7. Add a warning if the command changes a port mode, fabric member, DCB, or storage path.
8. If no source confirms the command, do not give the command.

The staged corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives`.
Never cite a path under `documentation/references/`.

## 2. Command register

This table lists the commands and statements that the curated files confirmed.
The table has 59 rows. The full skill contains 61 unique confirmed command spans.

| Area | Command or statement | Source and release |
| - | - | - |
| QFX interface | `show interfaces terse` | Interfaces on the QFX Series, QFX archive 2014-2015. |
| QFX interface | `show ethernet-switching interfaces` | Interfaces on the QFX Series, QFX archive 2014-2015. |
| QFX interface | `show configuration interfaces <interface>` | Interfaces on the QFX Series, QFX archive 2014-2015. |
| QFabric | `show fabric administration inventory node-devices` | Storage on the QFX Series, QFX archive 2014-2015. |
| QFabric | `show configuration fabric resources` | Storage on the QFX Series, QFX archive 2014-2015. |
| QFabric | `show configuration chassis` | Storage on the QFX Series, QFX archive 2014-2015. |
| Buffer | `show configuration class-of-service shared-buffer` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Buffer | `show class-of-service shared-buffer` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Buffer | At `[edit class-of-service shared-buffer]`, use `set ingress percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Buffer | At `[edit class-of-service shared-buffer]`, use `set egress percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Buffer | At `[edit class-of-service shared-buffer]`, use `set ingress buffer-partition lossless percent 5` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Buffer | At `[edit class-of-service shared-buffer]`, use `set egress buffer-partition multicast percent 20` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| BGP | `set interfaces ge-1/2/0 unit 0 family inet address 10.10.10.1/30` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group external-peers type external` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group external-peers peer-as 22` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group external-peers neighbor 10.10.10.2` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group external-peers neighbor 10.21.7.2 peer-as 79` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set routing-options autonomous-system 17` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group internal-peers type internal` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group internal-peers local-address 192.168.6.5` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `set protocols bgp group internal-peers neighbor 192.168.40.4` | BGP on QFX Series, QFX archive 2014-2015. |
| BGP | `show bgp neighbor 10.0.0.40` | BGP on QFX Series, QFX archive 2014-2015. |
| Multicast | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan interface ge-0/0/3 static group 225.100.100.100` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan interface ge-0/0/2 multicast-router-interface` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | At `[edit protocols]`, use `set igmp-snooping vlan employee-vlan robust-count 4` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | `show igmp-snooping vlans vlan v10` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | `show pim neighbors` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | `show multicast next-hops` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | `show multicast scope` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| Multicast | `show msdp` | Multicast Protocols on the QFX Series, QFX archive 2014-2015. |
| DCB | At `[edit class-of-service]`, use `set classifiers ieee-802.1 fcoe-classifier forwarding-class fcoe loss-priority low code-points 011` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | `set class-of-service congestion-notification-profile fcoe-cnp input ieee-802.1 code-point 011 pfc` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 unit 0 classifiers ieee-802.1 fcoe-classifier` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 congestion-notification-profile fcoe-cnp` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | `show class-of-service congestion-notification` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | `show class-of-service congestion-notification fcoe-cnp` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCB | `show dcbx neighbors` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set schedulers fcoe-sched priority low transmit-rate 3g` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set schedulers fcoe-sched shaping-rate percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set scheduler-maps fcoe-map forwarding-class fcoe scheduler fcoe-sched` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set forwarding-class-sets fcoe-pg class fcoe` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set traffic-control-profiles fcoe-tcp scheduler-map fcoe-map guaranteed-rate 3g` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 forwarding-class-set fcoe-pg output-traffic-control-profile fcoe-tcp` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCBX | `set protocols dcbx interface interface-name priority-flow-control no-auto-negotiation` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCBX | `set protocols dcbx interface interface-name enhanced-transmission-selection no-auto-negotiation` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCBX | At `[edit protocols dcbx interface interface-name]`, use `set enhanced-transmission-selection no-recommendation-tlv` | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| FCoE | `set interfaces vlan unit 100 family fibre-channel port-mode f-port` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `set chassis fpc 0 pic 0 fibre-channel port-range 0 5` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `set interfaces fc-0/0/0 unit 0 family fibre-channel port-mode np-port` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fibre-channel interfaces` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fibre-channel fabric` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fibre-channel proxy np-port` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fibre-channel proxy np-port detail` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fibre-channel proxy statistics` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fip snooping` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fip snooping detail` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `show fip snooping statistics` | Storage on the QFX Series, QFX archive 2014-2015. |
| FCoE | `request fibre-channel proxy load-rebalance dry-run` | Storage on the QFX Series, QFX archive 2014-2015. |

## 3. Source coverage

The index includes all 98 manifest rows. Each row resolves to a real Markdown file
under the staged corpus root during the 2026-09-17 build.

Topic counts from the index:

- `contrail-networking`: Contrail design, operations, and release notes.
- `qfx-platform`: QFX basics, interfaces, QFabric, and platform release notes.
- `dcb-and-buffer`: QFX traffic management and shared buffers.
- `dcb-and-storage`: FCoE, FIP, and storage guides.
- `ip-fabric-routing`: BGP, IS-IS, RIP, and routing options.
- `fabric-multicast`: routed multicast and Layer 2 multicast.
- `qfx-operations`: management, security, services, and troubleshooting.

## 4. Skill limits

This skill distills the staged corpus. It does not copy vendor passages. It does
not replace a platform release note, JTAC guidance, or a change plan.

Do not apply a command when one of these items is missing:

- The platform model.
- The running release.
- The source document and release.
- The rollback plan for a harmful change.
- The storage owner approval for a DCB or FCoE change.

## 5. Offline acceptance checks

Run these checks after an edit:

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\juniper-datacenter-fabric\SKILL.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\juniper-datacenter-fabric\references\qfx-platform-and-fabric.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\juniper-datacenter-fabric\references\ip-fabric-and-multicast.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\juniper-datacenter-fabric\references\dcb-storage-contrail.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\juniper-datacenter-fabric\references\verification.md
```

Also verify the index:

```powershell
.venv\Scripts\python.exe -c "import csv, pathlib; root=pathlib.Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github\skills\juniper-datacenter-fabric\references\corpus-index.csv', newline=''))); missing=[r['path'] for r in rows if not (root / r['path']).exists()]; print(len(rows), 'rows', len(missing), 'missing')"
```
