# Verification

## Contents

1. [Purpose](#purpose)
2. [Source method](#source-method)
3. [Command confirmation register](#command-confirmation-register)
4. [Dropped commands](#dropped-commands)
5. [Offline acceptance checks](#offline-acceptance-checks)
6. [Skill limits](#skill-limits)

## Purpose

Use this file to prove that a command in this skill came from the staged Juniper
corpus. The corpus root is outside the repository.

Corpus root:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives\
```

Manifest:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives\skill-manifests\junos-interfaces-cos.json
```

The staged source train is Junos 26.2. The manifest lists 16 documents and 6,332
pages.

## Source method

1. Read `references/corpus-index.csv`.
2. Open the Markdown path under the corpus root.
3. Search the exact command string.
4. Count the `<!-- page N -->` markers before the match.
5. Cite the matching page number in the answer.
6. If a command is absent, do not write the command.

Warning: do not apply a production configuration change from this summary alone.
A wrong command can drop traffic or change the wrong interface.

## Command confirmation register

This register lists the commands that this skill gives to a reader. Each command
appeared in the staged corpus before inclusion.

| Count | Command | Source document | Train | Page |
| - | - | - | - | - |
| 1 | `show interfaces terse` | Junos OS Interfaces Fundamentals for Junos OS | 26.2 | 17 |
| 2 | `show interfaces terse ge*` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 438 |
| 3 | `show interfaces terse et*` | Junos OS Evolved Interfaces Fundamentals for Junos OS Evolved | 26.2 | 97 |
| 4 | `show interfaces diagnostics optics et-0/0/10` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 333 |
| 5 | `show chassis hardware` | Next Gen Services Interfaces User Guide for Routing Devices | 26.2 | 119 |
| 6 | `show interfaces extensive ge-0/0/1 | find "queue counters"` | Junos OS Class of Service User Guide for Routers | 26.2 | 57 |
| 7 | `show forwarding-options enhanced-hash-key` | Interfaces User Guide for Switches | 26.2 | 121 |
| 8 | `show configuration forwarding-options hash-key` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 77 |
| 9 | `show configuration interfaces` | Junos OS Class of Service User Guide for Routers | 26.2 | 575 |
| 10 | `show configuration class-of-service` | Junos OS Class of Service User Guide for Routers | 26.2 | 575 |
| 11 | `show configuration class-of-service forwarding-classes` | Junos OS Class of Service User Guide for Routers | 26.2 | 586 |
| 12 | `show configuration class-of-service classifiers` | Junos OS Class of Service User Guide for Routers | 26.2 | 586 |
| 13 | `show configuration class-of-service interfaces` | Junos OS Class of Service User Guide for Routers | 26.2 | 587 |
| 14 | `show firewall` | Junos OS Class of Service User Guide for Routers | 26.2 | 197 |
| 15 | `show class-of-service` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 2 |
| 16 | `show class-of-service scheduler-map` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 45 |
| 17 | `set interfaces ge-0/0/0 description "to R2 ge-0/0/0"` | Junos OS Adaptive Services Interfaces User Guide for Routing Devices | 26.2 | 810 |
| 18 | `set disable` | Junos OS Interfaces Fundamentals for Junos OS | 26.2 | 43 |
| 19 | `set interfaces xe-7/0/2 mtu 9192` | Next Gen Services Interfaces User Guide for Routing Devices | 26.2 | 391 |
| 20 | `set interfaces ge-0/0/0 ether-options no-auto-negotiation` | Interfaces User Guide for Switches | 26.2 | 16 |
| 21 | `set interfaces ge-0/0/0 speed 100m` | Interfaces User Guide for Switches | 26.2 | 16 |
| 22 | `set interfaces ge-0/0/0 link-mode full-duplex` | Interfaces User Guide for Switches | 26.2 | 16 |
| 23 | `set interfaces ge-0/0/3 link-mode half-duplex` | Interfaces User Guide for Switches | 26.2 | 28 |
| 24 | `set speed 100g` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 192 |
| 25 | `set interfaces ge-0/0/0 unit 0 family inet address 10.1.12.2/30` | Junos OS Adaptive Services Interfaces User Guide for Routing Devices | 26.2 | 810 |
| 26 | `set interfaces ge-0/0/0 vlan-tagging` | Junos OS Interfaces Fundamentals for Junos OS | 26.2 | 70 |
| 27 | `set interfaces ge-0/0/0.0 vlan-id 101` | Junos OS Interfaces Fundamentals for Junos OS | 26.2 | 70 |
| 28 | `set interfaces ge-0/0/0 unit 0 family ethernet-switching filter input voip_class` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 24 |
| 29 | `set interfaces ge-2/0/8 unit 0 family inet filter output mf-classifier` | Junos OS Class of Service User Guide for Routers | 26.2 | 219 |
| 30 | `set chassis aggregated-devices ethernet device-count 10` | Junos OS Class of Service User Guide for Routers | 26.2 | 1073 |
| 31 | `set interfaces xe-0/0/2 ether-options 802.3ad ae0` | Interfaces User Guide for Switches | 26.2 | 46 |
| 32 | `set interfaces ae0 aggregated-ether-options lacp active` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 90 |
| 33 | `set interfaces ae0 aggregated-ether-options link-speed 1g` | Junos OS Ethernet Interfaces User Guide for Routing Devices | 26.2 | 90 |
| 34 | `set link-speed mixed` | Junos OS Interfaces Fundamentals for Junos OS | 26.2 | 62 |
| 35 | `set forwarding-options enhanced-hash-key ecmp-dlb per-packet` | Interfaces User Guide for Switches | 26.2 | 111 |
| 36 | `set class-of-service forwarding-classes class video queue-num 4` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 24 |
| 37 | `edit class-of-service classifiers dscp ba-classifier` | Junos OS Class of Service User Guide for Routers | 26.2 | 119 |
| 38 | `set forwarding-class be-class loss-priority high code-points 000001` | Junos OS Class of Service User Guide for Routers | 26.2 | 119 |
| 39 | `set class-of-service interfaces ge-0/0/1 unit 0 classifiers dscp dscp_custom` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 201 |
| 40 | `set firewall family inet filter f1 term t1 then loss-priority high` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 105 |
| 41 | `set firewall family inet filter mf-classifier term BE-data then forwarding-class BE-data` | Junos OS Class of Service User Guide for Routers | 26.2 | 620 |
| 42 | `set interfaces ge-2/0/5 unit 0 family inet filter input mf-classifier` | Junos OS Class of Service User Guide for Routers | 26.2 | 252 |
| 43 | `edit class-of-service rewrite-rules dscp rewrite-dscps` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 123 |
| 44 | `set forwarding-class be-class loss-priority low code-point 000000` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 123 |
| 45 | `set class-of-service interfaces ge-2/0/8 unit 0 rewrite-rules dscp IPv4-rewrite-table` | Junos OS Class of Service User Guide for Routers | 26.2 | 620 |
| 46 | `set class-of-service schedulers video-sched priority low` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 26 |
| 47 | `set class-of-service schedulers video-sched transmit-rate percent 15` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 26 |
| 48 | `set class-of-service schedulers db-sched buffer-size percent 10` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 26 |
| 49 | `set class-of-service schedulers nc-sched priority strict-high` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 26 |
| 50 | `set class-of-service scheduler-maps ethernet-cos-map forwarding-class mail scheduler mail-sched` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 26 |
| 51 | `set class-of-service interfaces ge-0/0/0 shaping-rate 100m` | Junos OS for EX Series Ethernet Switches Class of Service User Guide | 26.2 | 24 |
| 52 | `set firewall policer policer_IFL then loss-priority high` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 68 |
| 53 | `set firewall policer policer_IFL then forwarding-class best-effort` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 68 |
| 54 | `set interfaces ge-1/3/1 unit 0 family inet policer input policer_IFL` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 68 |
| 55 | `set class-of-service drop-profiles dp-low interpolate fill-level 80 drop-probability 80` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 302 |
| 56 | `set class-of-service drop-profiles dp-low interpolate fill-level 100 drop-probability 100` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 302 |
| 57 | `set class-of-service drop-profiles dp-high interpolate fill-level 60 drop-probability 80` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 302 |
| 58 | `set class-of-service drop-profiles dp-high interpolate fill-level 80 drop-probability 100` | Junos OS Class of Service User Guide for Security Devices | 26.2 | 302 |

## Dropped commands

These candidate commands did not appear as exact commands in the staged corpus.
They do not appear in the skill as commands to run.

| Candidate | Reason |
| - | - |
| `set interfaces ge-0/0/0 disable` | The corpus showed `set disable` from the interface hierarchy instead. |
| `set forwarding-options hash-key family multiservice no-mac-addresses` | The corpus described the statement, but the exact set command was absent. |
| `set forwarding-options enhanced-hash-key family multiservice no-mac-addresses` | The corpus described the statement, but the exact set command was absent. |
| `set interfaces xe-7/0/1 speed` | The corpus did not show this command form. |
| `set interfaces xe-7/0/1 link-mode` | The corpus did not show this command form. |

## Offline acceptance checks

Run these checks after you edit the skill:

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-interfaces-cos\SKILL.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-interfaces-cos\references\interfaces.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-interfaces-cos\references\class-of-service.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-interfaces-cos\references\verification.md
```

Also confirm the CSV rows:

```powershell
.venv\Scripts\python.exe -c "import csv, pathlib; root=pathlib.Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github\skills\junos-interfaces-cos\references\corpus-index.csv', newline=''))); missing=[row['path'] for row in rows if not (root / row['path']).is_file()]; print(len(rows), missing)"
```

## Skill limits

This skill summarizes the staged source documents. It does not replace current
release notes, platform restrictions, or local `?` command help.

Use a platform-matched source when the platform matters. If the source is for a
different platform family, mark the answer as a fallback.
