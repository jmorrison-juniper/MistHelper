# Implementation and verification

## Contents

1. [Verify a high-availability claim](#verify-a-high-availability-claim)
2. [Command confirmation summary](#command-confirmation-summary)
3. [Gap register](#gap-register)
4. [Source limits](#source-limits)
5. [Offline acceptance checks](#offline-acceptance-checks)
6. [Sources](#sources)

## Verify a high-availability claim

Use this procedure before you act on an answer from this skill.

1. Open `references/corpus-index.csv`.
2. Find the row for the document title, file name, or topic.
3. Read the `file`, `title`, `topic`, `train`, `pages`, and `path` values.
4. Open the Markdown file below the staged corpus root.
5. Confirm that the source statement supports the claim.
6. Confirm that the cited train matches the answer.
7. If the row uses a fallback train, read the gap register.
8. State the affected trains and fallback train in the answer.
9. State the risk that a newer change can be absent.
10. Read the device with the matching `show` command before you change it.

Caution: if the staged corpus is absent, the reader cannot verify the source.
Rebuild the corpus before you apply a production change.

Warning: do not apply a production redundancy change from a summary alone. A
wrong command can drop traffic for a full site.

## Command confirmation summary

The build pass confirmed 83 command or statement forms in the staged corpus.
Each form below appears in at least one source document listed in the index.

| Area | Confirmed forms | Source |
| - | - | - |
| Virtual Chassis | `show virtual-chassis`, `set virtual-chassis member 0 mastership-priority 255`, `set virtual-chassis member 1 mastership-priority 255`, `request virtual-chassis vc-port set pic-slot slot-number port port-number`, `delete virtual-chassis no-split-detection`, `show virtual-chassis mode`, `request virtual-chassis mode mixed member 4`, `request virtual-chassis mode mixed reboot`, `request virtual-chassis mode mixed all-members reboot`, `request virtual-chassis mode mixed disable all-members`, `request system reboot all-members`, `request session member 1`, `show system switchover`, `request chassis routing-engine master acquire`, `delete member removed-member-id`, `request virtual-chassis recycle member-id member-id`, `request virtual-chassis mode mixed disable`, `request virtual-chassis renumber member-id 1 new-member-id 0`, `replace pattern ge-1/ with ge-0/` | Virtual Chassis User Guide for Switches, train 26.2. |
| Routing and upgrade | `set chassis redundancy graceful-switchover`, `set routing-options nonstop-routing`, `set system commit synchronize`, `show task replication`, `show bgp replication`, `show bfd session`, `show chassis hardware`, `request routing-engine login re1`, `show version invoke-on all-routing-engines`, `request system snapshot`, `request system software in-service-upgrade /var/tmp/package-name.tgz`, `show chassis in-service-upgrade`, `show log messages`, `show version`, `request system software validate in-service-upgrade /var/tmp/package-name.tgz enhanced-mode`, `show route summary`, `show chassis fpc`, `show interfaces terse`, `show ethernet-switching table`, `show lacp interfaces`, `show dot1x interface`, `show system services dhcp binding`, `ping ip-address rapid count 20`, `request system software nonstop-upgrade reboot /var/tmp/package-name-m.nZx-distribution.tgz`, `request system software nonstop-upgrade no-old-master-upgrade /var/tmp/package-name-m.nZx-distribution.tgz`, `show chassis nonstop-upgrade`, `request chassis routing-engine master switch`, `request system snapshot slice alternate routing-engine both` | Junos OS High Availability User Guide, train 26.2. |
| Graceful restart | `set graceful-restart`, `show bgp neighbor 192.0.2.10`, `show log`, `show ospf overview`, `show ospfv3 overview`, `show rsvp neighbor detail`, `show rsvp version`, `show ldp session detail`, `show connections`, `show route instance detail`, `show route protocol l2vpn` | Junos OS High Availability User Guide, train 26.2. |
| VRRP and cluster | `set vrrp-group group-id`, `set vrrp-group group-id virtual-address [ addresses ]`, `set vrrp-group group-id priority number`, `show protocols vrrp`, `show vrrp summary`, `set chassis cluster cluster-id 1 node 0 reboot`, `set chassis cluster cluster-id 1 node 1 reboot`, `show chassis cluster status`, `set chassis cluster control-ports fpc 4 port 0`, `set chassis cluster control-ports fpc 10 port 0`, `show chassis cluster interfaces`, `set interfaces fab0 fabric-options member-interfaces ge-0/0/1`, `set interfaces fab1 fabric-options member-interfaces ge-7/0/1`, `set chassis cluster redundancy-group 0 node 0 priority 254`, `set chassis cluster redundancy-group 0 node 1 priority 1`, `set chassis cluster redundancy-group 1 node 0 priority 200`, `set chassis cluster redundancy-group 1 node 1 priority 100`, `set chassis cluster redundancy-group 1 interface-monitor ge-0/0/1 weight 130`, `set chassis cluster redundancy-group 1 interface-monitor ge-0/0/2 weight 140`, `show chassis cluster information`, `set chassis cluster reth-count 5`, `set interfaces xe-1/0/0 gigether-options redundant-parent reth0`, `set interfaces reth0 redundant-ether-options redundancy-group 1`, `set interfaces reth0 unit 0 family inet address 192.0.2.1/24` | Junos OS High Availability User Guide, train 26.2. Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2. |

The count treats each distinct command or statement form as one confirmation.
It does not count repeated examples from the same source.

## Gap register

Two Virtual Chassis PDF files cannot be read from the newest affected trains.
Juniper published each file with a destroyed page tree.

Readable copies exist in trains 21.1 through 24.4. Use the newest readable
fallback train shown in the table.

| Document | Affected trains | Reason | Fallback train | Risk to the reader |
| - | - | - | - | - |
| `virtual-chassis-ex-4200-4500.pdf` | 25.2, 25.4, 26.2 | Juniper published the file with a destroyed page tree. | 24.4 | The answer can miss a change after train 24.4. |
| `virtual-chassis-ex-8200.pdf` | 25.2, 25.4, 26.2 | Juniper published the file with a destroyed page tree. | 24.2 | The answer can miss a change after train 24.2. |

Each row covers one document in three trains. The register therefore records six
unreadable files.

The skill must name the gap in any answer drawn from these documents. The
answer must also name the fallback train.

Caution: a fallback train can lack a later change. Confirm the control against
current release notes before a production change.

### How to use the gap register

1. Read the `file` value in `references/corpus-index.csv`.
2. If the file is in the gap table, use the fallback train in the row.
3. State the affected trains in the answer.
4. State the fallback train in the answer.
5. State that a change after the fallback train can be absent.

## Source limits

This skill distills source text. It does not copy long vendor passages. Use the
staged source for detailed syntax before a live change.

The high availability guide contains some command examples that wrap across
lines during PDF conversion. Confirm the full command in the source before you
run it on a device.

Do not cite ignored vendor corpus paths. Git does not track that content.

## Offline acceptance checks

Run these checks after a skill rebuild:

```text
python -m tools.ste_linter --min-score 80 .github/skills/junos-high-availability/SKILL.md
python -m tools.ste_linter --min-score 80 .github/skills/junos-high-availability/references/virtual-chassis.md
python -m tools.ste_linter --min-score 80 .github/skills/junos-high-availability/references/routing-and-upgrade.md
python -m tools.ste_linter --min-score 80 .github/skills/junos-high-availability/references/vrrp-and-cluster.md
python -m tools.ste_linter --min-score 80 .github/skills/junos-high-availability/references/verification.md
```

Also confirm these checks:

1. `references/corpus-index.csv` has LF line endings.
2. `references/corpus-index.csv` has the columns `file,title,topic,train,pages,path`.
3. Each index path resolves below `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
4. Rows for unreadable documents point to fallback trains.
5. The whole skill stays below 400 KB.

## Sources

- Junos OS High Availability User Guide, train 26.2.
- Junos OS High Availability User Guide, train 25.4.
- Junos OS Chassis Cluster User Guide for SRX Series Devices, train 26.2.
- Virtual Chassis User Guide for EX2200, EX3300, EX4200, EX4500 and EX4550 Switches, train 24.4 fallback.
- Junos OS Multinode High Availability, train 26.2.
- Junos OS Interchassis Redundancy Using Virtual Chassis User Guide for MX Series Routers, train 26.2.
- Virtual Chassis Fabric User Guide, train 26.2.
- Junos OS for EX Series Ethernet Switches Virtual Chassis User Guide for EX8200 Switches, train 24.2 fallback.
- Virtual Chassis User Guide for Switches, train 26.2.