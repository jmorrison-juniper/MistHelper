# Juniper domain taxonomy contract

## Purpose

This contract defines the domain skills that receive the Juniper corpus. The
factory MUST map each source document to exactly one domain skill. The factory
MUST also mark superseded product versions as citation-only when a newer guide
exists for the same product family.

## Evidence base

The taxonomy uses the converted corpus in
`C:\Users\jmorrison\Downloads\juniper-harvest-md`. The catalog summary reports
1,778 converted documents, 243,314 pages, and 313.8 MB of Markdown.

The corpus contains 439 uncategorized documents and 108,314 uncategorized pages.
The factory MUST classify by title, path, heading, and content signals. The
factory MUST NOT rely on the harvester category alone.

The top 20 documents contain 72,205 pages. That is 30 percent of the corpus.
Several top documents are old versions of the same product guide.

Warning: do not build topic files from an old version when a newer product guide
exists. The agent can give old behavior for a current deployment.

## Size rule

The factory MUST check each domain against these limits after version
deduplication.

1. A domain SHOULD hold no more than 80 source documents.
2. A domain SHOULD hold no more than 15,000 unique technical pages.
3. A domain that exceeds either limit MUST split, or this contract MUST state a
   named exception.
4. A stated exception MUST give the reason and the index method that keeps file
   sizes inside the locked hard limits.
5. No exception can exceed the file hard limits in `contracts\interfaces.md`.

`juniper-cli-reference` is the deliberate page-count exception. It is one
command reference work. The inventory agent measured that its largest PDF became
99 Markdown files. Its level 2 indexes MUST divide commands by first command
word, statement hierarchy, and product scope. An agent routes a command lookup
here when a question asks what a command does or what syntax it accepts.

## VersionedProductFamily rule

The factory MUST detect a versioned product family before it assigns topic work.
The harvester applies a newest-in-train rule to release notes. It does not apply
that rule to user guides or API references.

A source document belongs to a `VersionedProductFamily` when its title matches
one of these patterns.

| Family key | Title pattern | Version capture |
| - | - | - |
| `routing-director-user-guide` | `Juniper Routing Director <major>.<minor>[.<patch>] User Guide` | Semantic version. |
| `apstra-user-guide` | `*Apstra* <major>.<minor>[.<patch>] *User Guide` | Semantic version. |
| `rest-api-references` | `REST API Version <major>.<minor>[.<patch>] References` | Semantic version. |

Rules:

1. Sort versions by major, minor, and patch as integers.
2. Keep the newest version as the topic source.
3. Mark every older version as citation-only.
4. Keep citation-only documents in `SourceDocument` and `sources.md`.
5. Do not generate topic files from citation-only documents.
6. Permit a version-specific question to cite an older version.
7. Store `family_key`, `family_version`, and `citation_only` for each member.

Measured page effect from `_catalog.csv`:

| Family key | Documents | Topic source pages | Citation-only pages | Total pages |
| - | -: | -: | -: | -: |
| `routing-director-user-guide` | 6 | 2,191 | 9,336 | 11,527 |
| `apstra-user-guide` | 6 | 2,237 | 8,702 | 10,939 |
| `rest-api-references` | 2 | 2,430 | 2,404 | 4,834 |
| Total | 14 | 6,858 | 20,442 | 27,300 |

The rule removes 20,442 superseded pages from topic generation. These pages
remain citable. The detected families cover 27,300 pages, or about 11 percent of
the corpus.

## Assignment rule

The factory MUST test document type and domain rules in this file. The first
matching rule assigns the document. No later rule can reassign it. If no rule
matches, the factory MUST assign the document to `juniper-general-reference`.

The factory MUST write the assigned domain, matched rule, matched signal,
version family, and citation-only flag to `SourceDocument`. The factory MUST
fail if one document receives zero domains or more than one domain.

`juniper-routing-junos` is retired. It was too large to route. The routing
content is split into Junos fundamentals, routing protocols, MPLS transport,
routing policy and firewall filter, and subscriber services.

## Final domain table

The counts below come from `_catalog.csv` with this priority rule applied to the
category, title, file slug, and Markdown path. `Unique technical pages` removes
citation-only pages from the `VersionedProductFamily` rule. The table
reconciles to 1,778 documents and 243,314 pages.

| Priority | Skill | Documents | Total pages | Unique technical pages | Size status |
| -: | - | -: | -: | -: | - |
| 1 | `juniper-cli-reference` | 5 | 34,239 | 34,239 | Exception. One command reference work. |
| 2 | `juniper-observability-operations` | 115 | 37,508 | 37,508 | Exception. Split again only after the domain cap changes. |
| 3 | `juniper-security-srx-firewall` | 143 | 29,505 | 29,505 | Exception. SRX and Security Director share one firewall task surface. |
| 4 | `juniper-security-analytics-compliance` | 87 | 19,791 | 19,791 | Exception. JSA and compliance share audit evidence. |
| 5 | `juniper-api-automation` | 78 | 19,731 | 17,327 | Exception. API references route by product and path. |
| 6 | `juniper-junos-fundamentals` | 51 | 11,121 | 11,121 | Pass. |
| 7 | `juniper-software-lifecycle` | 236 | 9,835 | 9,835 | Exception. Many small release-note records. |
| 8 | `juniper-campus-branch-switching` | 102 | 9,170 | 9,170 | Exception. Pages fit, and document rows are short. |
| 9 | `juniper-hardware-platforms` | 77 | 7,775 | 7,775 | Pass. |
| 10 | `juniper-routing-protocols` | 14 | 6,332 | 6,332 | Pass. |
| 11 | `juniper-evpn-vxlan-fabric` | 36 | 5,985 | 5,985 | Pass. |
| 12 | `juniper-subscriber-services` | 6 | 4,740 | 4,740 | Pass. |
| 13 | `juniper-routing-policy-firewall` | 10 | 4,661 | 4,661 | Pass. |
| 14 | `juniper-datacenter-apstra` | 86 | 12,318 | 3,616 | Exception. Citation-only Apstra versions cause the document count. |
| 15 | `juniper-general-reference` | 33 | 3,261 | 3,261 | Pass. |
| 16 | `juniper-mist-ai-cloud` | 97 | 3,251 | 3,251 | Exception. Wireless and Mist assurance share one agent route. |
| 17 | `juniper-mpls-transport` | 11 | 3,029 | 3,029 | Pass. |
| 18 | `juniper-routing-director-operations` | 25 | 11,943 | 2,607 | Pass. |
| 19 | `juniper-training-learning` | 38 | 1,852 | 1,852 | Pass. |
| 20 | `juniper-security-vpn-threat` | 37 | 1,820 | 1,820 | Pass. |
| 21 | `juniper-installation-maintenance` | 83 | 1,620 | 1,620 | Exception. The document count is three over the guide limit. |
| 22 | `juniper-business-solutions` | 321 | 1,589 | 1,589 | Exception. Low expertise value, but still in scope. |
| 23 | `juniper-sdwan-wan` | 39 | 946 | 946 | Pass. |
| 24 | `juniper-cloud-native-contrail` | 11 | 718 | 718 | Pass. |
| 25 | `juniper-legal-corporate` | 37 | 574 | 574 | Pass. Low expertise value, but still in scope. |
| - | Total | 1,778 | 243,314 | 222,872 | 20,442 citation-only pages. |

`juniper-business-solutions` and `juniper-legal-corporate` stay last. They mostly
hold marketing, corporate, and compliance text. They are in scope because an
agent can receive questions about customer proof, policy, legal terms, or
sustainability claims.

## Required split rules

### Split for the retired `juniper-routing-junos` domain

The factory MUST split old routing content with these rules.

| New skill | Owns | Match rule |
| - | - | - |
| `juniper-junos-fundamentals` | CLI model, configuration hierarchy, commit, rollback, system services, user management, authentication, routing engines, interfaces, and basic Junos operation. | Match `Junos`, `configuration hierarchy`, `commit`, `rollback`, `system services`, `user management`, `authentication`, `routing engine`, or `interfaces` after the protocol rules run. |
| `juniper-routing-protocols` | BGP, OSPF, IS-IS, RIP, route reflection, multicast, PIM, IGMP, MSDP, and routing protocol behavior. | Match `BGP`, `OSPF`, `ISIS`, `IS-IS`, `RIP`, `route reflection`, `multicast`, `PIM`, `IGMP`, `MSDP`, or `routing protocol`. |
| `juniper-mpls-transport` | MPLS, LDP, RSVP, segment routing, traffic engineering, and layer 3 VPN. | Match `MPLS`, `LDP`, `RSVP`, `segment routing`, `SR-MPLS`, `traffic engineering`, `layer 3 VPN`, or `L3VPN`. |
| `juniper-routing-policy-firewall` | Routing policy, firewall filters, traffic policers, class of service, route filters, and prefix lists. | Match `routing policy`, `firewall filter`, `traffic policer`, `class of service`, `CoS`, `route filter`, or `prefix list`. |
| `juniper-subscriber-services` | Broadband subscriber management, subscriber sessions, BNG, AAA subscriber control, dynamic profiles, PPPoE, and DHCP subscriber workflows. | Match `broadband subscriber`, `subscriber management`, `subscriber sessions`, `BNG`, `AAA subscriber`, `dynamic profiles`, `PPPoE`, or `DHCP subscriber`. |

The split places these large sources in the correct domain.

| Source document | Domain |
| - | - |
| Junos OS MPLS Applications User Guide | `juniper-mpls-transport` |
| Junos OS Routing Policies, Firewall Filters, and Traffic Policers User Guide | `juniper-routing-policy-firewall` |
| Junos OS Broadband Subscriber Sessions User Guide | `juniper-subscriber-services` |
| Junos OS BGP User Guide | `juniper-routing-protocols` |

### Split for security content

The factory MUST split security content with these rules.

| Skill | Owns | Match rule |
| - | - | - |
| `juniper-security-srx-firewall` | SRX, vSRX, cSRX, firewall policy, NAT, Security Director, and security gateways. | Match `SRX`, `vSRX`, `cSRX`, `firewall`, `NAT`, `Security Director`, or `security gateway`. |
| `juniper-security-vpn-threat` | IPsec, VPN, UTM, IDP, IPS, threat prevention, Sky ATP, and secure edge. | Match `IPsec`, `VPN`, `UTM`, `IDP`, `IPS`, `threat`, `Sky ATP`, `advanced threat`, or `secure edge`. |
| `juniper-security-analytics-compliance` | JSA, SIEM, log collectors, DSM guides, FIPS, Common Criteria, FedRAMP, and validation reports. | Match `JSA`, `secure analytics`, `SIEM`, `log collector`, `DSM`, `FIPS`, `Common Criteria`, `FedRAMP`, `compliance`, or `validation report`. |

### Split for operations content

The factory MUST split operations content with these rules.

| Skill | Owns | Match rule |
| - | - | - |
| `juniper-routing-director-operations` | Routing Director user guides and troubleshooting guides. | Match `Routing Director`. |
| `juniper-observability-operations` | Paragon, NorthStar, HealthBot, monitoring, analytics, insights, planners, and service assurance. | Match `Paragon`, `NorthStar`, `HealthBot`, `monitoring`, `analytics`, `insights`, `planner`, or `service assurance`. |

## Domain rules

The factory MUST apply the rule table in the order shown below. Each rule tests
the normalized signal string.

| Priority | Skill | Routing keywords | Assignment rule |
| -: | - | - | - |
| 1 | `juniper-cli-reference` | CLI reference, command reference, Junos command, syntax, statement, hierarchy, option, `show`, `set`, `clear`, `request`, `configure`. | Match category `cli-reference`, `Junos CLI Reference`, `CLI Reference`, `command reference`, or `statement reference`. |
| 2 | `juniper-evpn-vxlan-fabric` | EVPN, VXLAN, fabric, IP fabric, spine, leaf, virtual chassis, MC-LAG, VPLS, layer 2 VPN, overlay. | Match `EVPN`, `VXLAN`, `EVPN-VXLAN`, `IP fabric`, `spine`, `leaf`, `virtual chassis`, `MC-LAG`, `MPLS L2VPN`, `layer 2 VPN`, or `VPLS`. Read path signals such as `uncategorized/ex__configuration__evpn-vxlan/evpn.md`. |
| 3 | `juniper-sdwan-wan` | Session Smart, SSR, SD-WAN, WAN assurance, WAN edge, conductor, 128 Technology, branch WAN. | Match `Session Smart`, `SSR`, `SD-WAN`, `SDWAN`, `WAN assurance`, `WAN edge`, `128 Technology`, `conductor`, or `branch WAN`. |
| 4 | `juniper-routing-policy-firewall` | Routing policy, firewall filters, traffic policers, class of service, route filters, prefix lists. | Match `routing policy`, `firewall filter`, `traffic policer`, `class of service`, `CoS`, `policy framework`, `route filter`, or `prefix list`. |
| 5 | `juniper-api-automation` | API, REST, NETCONF, YANG, PyEZ, Ansible, automation, script, SDK, developer, webhook, telemetry. | Match category `api`, `API`, `REST`, `NETCONF`, `YANG`, `PyEZ`, `Ansible`, `automation`, `script`, `SDK`, `developer`, `webhook`, or `telemetry`. |
| 6 | `juniper-software-lifecycle` | Release notes, upgrade, update, interim fix, resolved issue, known issue, migration, end of life. | Match category `release-notes`, category `migration`, `release notes`, `upgrade`, `update`, `interim`, `fix`, `end of life`, `EOL`, `end of support`, or `EOS`. |
| 7 | `juniper-security-analytics-compliance` | JSA, SIEM, log collector, DSM, FIPS, Common Criteria, FedRAMP, compliance, validation report. | Match category `security-and-compliance`, `JSA`, `secure analytics`, `security analytics`, `SIEM`, `log collector`, `DSM`, `FIPS`, `Common Criteria`, `FedRAMP`, `compliance`, or `validation report`. |
| 8 | `juniper-security-vpn-threat` | IPsec, VPN, UTM, IDP, IPS, threat, Sky ATP, secure edge. | Match `IPsec`, `VPN`, `UTM`, `IDP`, `IPS`, `threat`, `Sky ATP`, `advanced threat`, or `secure edge`. |
| 9 | `juniper-security-srx-firewall` | SRX, vSRX, cSRX, firewall, NAT, Security Director, security gateway. | Match `SRX`, `vSRX`, `cSRX`, `firewall`, `NAT`, `Security Director`, or `security gateway`. |
| 10 | `juniper-routing-director-operations` | Routing Director, path computation, monitoring, troubleshooting. | Match `Routing Director`. Apply the version rule before topic generation. |
| 11 | `juniper-observability-operations` | Paragon, NorthStar, HealthBot, monitor, analytics, insights, planner, service assurance. | Match `Paragon`, `NorthStar`, `HealthBot`, `monitor`, `monitoring`, `analytics`, `insights`, `planner`, `orchestration`, `proactive`, or `service assurance`. |
| 12 | `juniper-subscriber-services` | Broadband subscriber, subscriber management, BNG, AAA, dynamic profiles, PPPoE, DHCP subscriber. | Match `broadband subscriber`, `subscriber management`, `subscriber sessions`, `BNG`, `AAA subscriber`, `dynamic profiles`, `PPPoE`, or `DHCP subscriber`. |
| 13 | `juniper-mpls-transport` | MPLS, LDP, RSVP, segment routing, traffic engineering, layer 3 VPN. | Match `MPLS`, `LDP`, `RSVP`, `segment routing`, `SR-MPLS`, `traffic engineering`, `layer 3 VPN`, or `L3VPN`. |
| 14 | `juniper-routing-protocols` | BGP, OSPF, IS-IS, RIP, route reflection, multicast, PIM, IGMP, MSDP. | Match `BGP`, `OSPF`, `ISIS`, `IS-IS`, `RIP`, `route reflection`, `multicast`, `PIM`, `IGMP`, `MSDP`, or `routing protocol`. |
| 15 | `juniper-junos-fundamentals` | Junos, configuration hierarchy, commit, rollback, system services, user management, interfaces. | Match `Junos`, `configuration hierarchy`, `commit`, `rollback`, `system services`, `user management`, `authentication`, `routing engine`, `chassis cluster`, or `interfaces` after the higher rules run. |
| 16 | `juniper-datacenter-apstra` | Apstra, data center, intent-based, blueprint, SFS, Smart Fabric Services. | Match `Apstra`, `data center`, `datacenter`, `intent-based`, `SFS`, or `Smart Fabric`. Apply the version rule before topic generation. |
| 17 | `juniper-cloud-native-contrail` | Contrail, CN2, Kubernetes, OpenShift, cloud native, CNI, container, virtual network. | Match `Contrail`, `cloud native`, `cloud-native`, `CN2`, `Kubernetes`, `OpenShift`, `containerized`, `CNI`, or `virtual network`. |
| 18 | `juniper-mist-ai-cloud` | Mist, Marvis, AI-Native, assurance, Wi-Fi, WLAN, access point, BLE, RF, location. | Match `Mist`, `Marvis`, `AI-Native`, `assurance`, `premium analytics`, `Wi-Fi`, `WLAN`, `access point`, `AP` followed by digits, `BLE`, `radio`, `antenna`, or `location services`. |
| 19 | `juniper-campus-branch-switching` | Campus, branch, switching, EX, QFX, wired access, Ethernet, PoE. | Match `campus`, `branch`, `switching`, `switches`, `switch`, `EX` followed by digits, `QFX` followed by digits, `Ethernet switch`, `wired access`, or `PoE`. |
| 20 | `juniper-hardware-platforms` | Datasheet, hardware, chassis, line card, MIC, PIC, FPC, optics, cable. | Match category `datasheets`, `datasheet`, `data sheet`, `hardware`, `platform`, `chassis`, `line card`, `MIC`, `PIC`, `FPC`, `transceiver`, `power supply`, `fan tray`, `module`, `adapter`, `optics`, or `cable`. |
| 21 | `juniper-installation-maintenance` | Installation, rack, mount, cabling, site preparation, FRU, replacement. | Match category `installation-guides`, category `configuration-guides`, category `administration-guides`, `installation`, `install`, `rack`, `mount`, `cabling`, `replacement`, `FRU`, or `maintenance`. |
| 22 | `juniper-training-learning` | Day One, getting started, quick start, lab, learning, certification, exam. | Match `day one`, `dayone`, `getting started`, `quick start`, `quickstart`, `lab`, `learning`, `certification`, `exam`, `student`, or `course`. |
| 23 | `juniper-business-solutions` | Case study, solution brief, white paper, analyst report, customer story, industry. | Match category `case-studies`, `solution-briefs`, `white-papers`, `flyers`, `infographics`, `analyst-reports`, `ebooks`, `executive-briefs`, `use-cases`, `brochures`, `factsheet`, `editorials`, `articles`, `marketing-asset`, `reference-architectures`, `validation-reports`, or `design`. |
| 24 | `juniper-legal-corporate` | Legal, privacy, corporate policy, trademark, sustainability, certificate, code of conduct. | Match category `legal`, `sustainability`, `certificates`, or `service-descriptions`. Also match `anti-corruption`, `code of conduct`, `trademark`, `privacy`, `personal data`, `conflict minerals`, `accessibility`, `ESG`, `CDP`, or `certificate`. |
| 25 | `juniper-general-reference` | General Juniper reference, licensing, safety, broad guide, unknown source. | Assign only when no earlier rule matches. This is the required fallback domain. |

## Index methods for exceptions

An exception domain MUST keep the locked file size limits by grouping its level 1
index. The level 1 index MUST list groups first and document rows second. The
level 2 index MUST hold the detailed topic route.

| Exception domain | Index method |
| - | - |
| `juniper-cli-reference` | Group by first command word, configuration statement hierarchy, and product scope. |
| `juniper-observability-operations` | Group by product family, then by operate, monitor, troubleshoot, and report. |
| `juniper-security-srx-firewall` | Group by SRX platform, firewall policy, NAT, J-Web, and Security Director. |
| `juniper-security-analytics-compliance` | Group by JSA, DSM, FIPS, Common Criteria, FedRAMP, and validation evidence. |
| `juniper-api-automation` | Group by product API, API version, resource path prefix, and automation tool. |
| `juniper-software-lifecycle` | Group by product, release train, and issue type. |
| `juniper-campus-branch-switching` | Group by EX, QFX, campus design, wired access, and switch operations. |
| `juniper-datacenter-apstra` | Group by Apstra version family, blueprint task, and fabric operation. |
| `juniper-mist-ai-cloud` | Group by Mist cloud, Marvis, wireless assurance, wired assurance, and location. |
| `juniper-installation-maintenance` | Group by product family, rack task, cabling task, and replacement task. |
| `juniper-business-solutions` | Group by industry, offer, and proof type. Keep only high-value claims in topics. |

## Required domain report

Each factory run MUST write a domain report. The report MUST state these values.

1. Total documents checked.
2. Total pages checked.
3. Document count and page count for each domain.
4. Unique technical pages for each domain after version deduplication.
5. Citation-only document count and page count for each domain.
6. Fallback document count.
7. The top 20 unmatched title tokens in the fallback domain.
8. The count of documents that matched by category only.
9. The count of documents that matched by title, path, heading, or content
   signal.
10. The count of documents in each `VersionedProductFamily`.
11. The newest version kept for each `VersionedProductFamily`.
12. The citation-only page saving for each `VersionedProductFamily`.
13. The size status for each domain.
14. The exception method for each domain that exceeds the size rule.

Warning: do not accept a domain report that checks zero documents. A zero-count
report hides a failed corpus read and can publish an empty skill set.
