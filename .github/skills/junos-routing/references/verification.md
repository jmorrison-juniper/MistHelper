# Verification

Use this reference to choose a source, confirm a command, and report gaps.

Public source URL for the staged routing corpus:
`https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip`

## Contents

1. [Source selection](#source-selection)
2. [Command confirmation rule](#command-confirmation-rule)
3. [Confirmed command register](#confirmed-command-register)
4. [Dropped command register](#dropped-command-register)
5. [Offline acceptance checks](#offline-acceptance-checks)
6. [Skill limits](#skill-limits)

## Source selection

Use `references/corpus-index.csv` before you answer. The index has one row for
each staged document.

| Topic | Preferred source | Train | Path |
| - | - | - | - |
| BGP | Junos OS BGP User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/bgp.md` |
| OSPF | Junos OS OSPF User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ospf.md` |
| IS-IS | Junos OS IS-IS User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/is-is.md` |
| Routing policy | Junos OS Routing Policies, Firewall Filters, and Traffic Policers User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/routing-policy.md` |
| Route leaking | Junos OS BGP User Guide or Routing Policy User Guide | 26.2 | Use the exact command row. |
| Segment routing | Segment Routing User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/segment-routing.md` |
| RIP | Junos OS RIP User Guide | 26.2 | `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/rip.md` |

Do not cite the staged path alone. Cite the public URL first, then cite the
staged path and page.

## Command confirmation rule

A command is usable only when the staged Markdown contains the exact string.
A statement with a placeholder is not enough evidence for a production command.

Use this process:

1. Search `markdown2\` below the corpus root for the exact command.
2. If the source uses a placeholder, search for a concrete example.
3. Record the page marker before the command.
4. If no page marker exists, mark the command as unverified.
5. If the command is unverified, do not give it.

Warning: an invented command can cause a production outage. Do not write a
command unless this register or a new corpus search confirms it.

## Confirmed command register

This register holds 64 commands confirmed during skill creation.

| Command | Source and page |
| - | - |
| `set routing-options autonomous-system 17` | Routing Policy, 26.2, page 65. |
| `set routing-options router-id 172.16.1.1` | Routing Policy, 26.2, page 65. |
| `set protocols bgp group external-peers type external` | Routing Policy, 26.2, page 613. |
| `set protocols bgp group external-peers peer-as 64510` | BGP, 26.2, page 1461. |
| `set protocols bgp group external-peers neighbor 10.0.0.1` | Routing Policy, 26.2, page 614. |
| `set protocols bgp group routeset1 neighbor 10.0.10.13 family inet unicast` | Routing Policy, 26.2, page 387. |
| `set protocols bgp group external-peers export send-static` | BGP, 26.2, page 462. |
| `set protocols bgp group internal-peers type internal` | Routing Policy, 26.2, page 65. |
| `set protocols bgp group internal-peers local-address 10.0.0.1` | OSPF, 26.2, page 492. |
| `set protocols bgp group internal-peers cluster 192.168.6.5` | BGP, 26.2, page 1239. |
| `set protocols bgp group external multihop ttl 2` | BGP, 26.2, page 215. |
| `set protocols bgp path-selection as-path-ignore` | BGP, 26.2, page 296. |
| `set protocols bgp damping` | Routing Policy, 26.2, page 647. |
| `set protocols bgp group ext neighbor 192.168.20.1 remove-private` | BGP, 26.2, page 307. |
| `set policy-options policy-statement send-static term 1 from protocol static` | Routing Policy, 26.2, page 135. |
| `set policy-options policy-statement send-static term 1 then accept` | Routing Policy, 26.2, page 135. |
| `set protocols bgp group external-peers neighbor 10.0.0.2 import import-communities` | Routing Policy, 26.2, page 613. |
| `set protocols bgp group external-peers neighbor 10.0.0.2 import remove-communities` | Routing Policy, 26.2, page 625. |
| `set policy-options community R3_PREFERRED members 64511:3` | Routing Policy, 26.2, page 572. |
| `set policy-options policy-statement change-local-preference term find-R1-routes from community` | Routing Policy, 26.2, page 571. |
| `set policy-options policy-statement send-static term 1 then local-preference 200` | Routing Policy, 26.2, page 136. |
| `set policy-options policy-statement send-static term 1 then community add R1_PREFERRED` | Routing Policy, 26.2, page 574. |
| `set protocols bgp group ibgp family inet-mvpn signaling damping` | Routing Policy, 26.2, page 663. |
| `set protocols ospf area 0.0.0.0 interface fe-1/0/1 metric 5` | OSPF, 26.2, page 232. |
| `set protocols ospf area 0.0.0.1 interface ge-0/2/0 passive` | OSPF, 26.2, page 45. |
| `set protocols ospf area 0.0.0.0 interface xe-0/0/0:0.0 interface-type p2p` | OSPF, 26.2, page 577. |
| `set protocols ospf area 07 stub` | OSPF, 26.2, page 111. |
| `set protocols ospf area 0.0.0.9 nssa` | OSPF, 26.2, page 117. |
| `set protocols ospf traffic-engineering` | Routing Policy, 26.2, page 663. |
| `set protocols ospf area 0.0.0.0 interface so-0/2/0 authentication md5 5 key PssWd8` | OSPF, 26.2, page 292. |
| `set protocols ospf area 0.0.0.0 interface fe-0/0/1 bfd-liveness-detection minimum-interval 300` | OSPF, 26.2, page 358. |
| `set protocols isis interface ge-0/0/0.0` | IS-IS, 26.2, page 38. |
| `set protocols isis interface lo0.0 passive` | BGP, 26.2, page 1010. |
| `set protocols isis level 2 wide-metrics-only` | IS-IS, 26.2, page 270. |
| `set protocols isis interface ge-0/0/1.0 level 2 metric 100` | IS-IS, 26.2, page 65. |
| `set protocols isis interface ge-0/0/1.0 point-to-point` | IS-IS, 26.2, page 65. |
| `set protocols isis spf-options delay 1000` | IS-IS, 26.2, page 365. |
| `set protocols isis level 2 authentication-key-chain base-key-global` | IS-IS, 26.2, page 110. |
| `set protocols isis interface ge-0/0/0.0 family inet bfd-liveness-detection minimum-interval 200` | IS-IS, 26.2, page 232. |
| `set protocols isis interface ge-1/2/0.0 bfd-liveness-detection authentication key-chain secret123` | IS-IS, 26.2, page 246. |
| `set routing-options static route 0.0.0.0/0 next-hop 10.0.0.5` | Routing Policy, 26.2, page 136. |
| `set routing-options aggregate route 172.16.32.0/21` | Routing Policy, 26.2, page 182. |
| `set routing-options generate route 0.0.0.0/0 policy if-upstream-routes-exist` | Routing Policy, 26.2, page 185. |
| `set routing-instances VR1 instance-type virtual-router` | Routing Policy, 26.2, page 1655. |
| `set routing-instances VR1 interface ge-1/0/8.0` | Routing Policy, 26.2, page 1655. |
| `set routing-instances VR1 interface ge-1/1/0.0` | Routing Policy, 26.2, page 1655. |
| `set routing-instances red vrf-import vrf-import-red` | BGP, 26.2, page 812. |
| `set routing-instances red vrf-export vrf-export-red` | BGP, 26.2, page 812. |
| `set routing-options rib-groups FBF-rib import-rib inet.0` | Routing Policy, 26.2, page 1367. |
| `set routing-options rib-groups FBF-rib import-rib webtraffic.inet.0` | Routing Policy, 26.2, page 1367. |
| `set routing-options interface-routes rib-group inet FBF-rib` | Routing Policy, 26.2, page 1367. |
| `set protocols ospf rib-group fbf-group` | Routing Policy, 26.2, page 1634. |
| `set routing-instances vpn-1 protocols ospf export parent_vpn_routes` | Routing Policy, 26.2, page 661. |
| `show bgp summary` | Routing Policy, 26.2, page 653. |
| `show route advertising-protocol bgp` | Routing Policy, 26.2, page 140. |
| `show route receive-protocol bgp` | Routing Policy, 26.2, page 73. |
| `show ospf neighbor` | Routing Policy, 26.2, page 1251. |
| `show isis adjacency` | IS-IS, 26.2, page 41. |
| `show route protocol bgp` | Routing Policy, 26.2, page 71. |
| `show route table` | Routing Policy, 26.2, page 564. |
| `show route forwarding-table` | Routing Policy, 26.2, page 1556. |
| `show configuration protocols isis` | IS-IS, 26.2, page 798. |
| `show configuration policy-options` | IS-IS, 26.2, page 223. |
| `show configuration routing-options` | Automation Scripting, 26.2, page 997, `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/automation-scripting.md`. |

## Dropped command register

These candidate commands were not written as procedures because the exact string
was not confirmed in the staged corpus.

| Dropped command | Reason |
| - | - |
| `show configuration protocols bgp` | The exact string was absent. |
| `show configuration protocols ospf` | The exact string was absent. |
| `show configuration routing-instances` | The exact string was absent. |
| `set protocols bgp group external-peers family inet unicast` | The corpus confirmed a neighbor-level form instead. |
| `set protocols bgp group external-peers neighbor 10.0.4.1` | The corpus confirmed different neighbor addresses. |
| `set protocols bgp group internal-peers cluster 172.16.1.1` | The corpus confirmed cluster `192.168.6.5` instead. |
| `set routing-instances vpn-a routing-options instance-import` | No exact example was found. |

## Offline acceptance checks

Run these checks from the skill worktree after any edit:

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-routing\SKILL.md .github\skills\junos-routing\references\protocols.md .github\skills\junos-routing\references\policy.md .github\skills\junos-routing\references\instances.md .github\skills\junos-routing\references\verification.md
```

Then confirm the index paths:

```powershell
.venv\Scripts\python.exe -c "from pathlib import Path; import csv; root=Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github\skills\junos-routing\references\corpus-index.csv', newline=''))); missing=[r['path'] for r in rows if not (root/r['path']).exists()]; print(len(rows), missing)"
```

## Skill limits

This skill summarizes the staged corpus. It does not replace the full Juniper
documents.

If the corpus root is absent, state that the corpus is absent. Then answer only
from the curated reference files and mark any new command as unverified.

If the device runs a train other than 26.2, say that the source train differs.
Then ask the operator to verify the command in the target train documentation
before a production change.
