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
The factory MUST NOT use the harvester category as the only routing signal.
Title, path, heading, and content signals are required.

The largest 20 documents contain 72,205 pages. That is 30 percent of the
corpus. Several of those documents are old versions of the same product guide.

Warning: do not build topic files from an old version when a newer product guide
exists. The agent can give old behavior for a current deployment.

## Largest source documents

| Pages | Category | Title |
| -: | - | - |
| 33,072 | `cli-reference` | Junos OS Junos CLI Reference |
| 2,553 | `uncategorized` | Junos OS MPLS Applications User Guide |
| 2,430 | `api` | REST API Version 17.0 References |
| 2,418 | `uncategorized` | Junos OS Routing Policies, Firewall Filters, and Traffic Policers |
| 2,404 | `api` | REST API Version 16.0 References |
| 2,344 | `uncategorized` | Juniper Secure Analytics Configuring DSMs Guide |
| 2,237 | `guides` | HPE Networking Apstra Data Center Director 6.2 User Guide |
| 2,220 | `uncategorized` | Junos OS EVPN User Guide |
| 2,191 | `guides` | Juniper Routing Director 2.10.0 User Guide |
| 2,158 | `guides` | Juniper Apstra 6.1 User Guide |
| 2,095 | `guides` | Juniper Routing Director 2.9.0 User Guide |
| 2,031 | `uncategorized` | Junos OS Broadband Subscriber Sessions User Guide |
| 1,935 | `guides` | Juniper Apstra 5.1.0 User Guide |
| 1,900 | `guides` | Juniper Routing Director 2.8.0 User Guide |
| 1,839 | `guides` | Juniper Routing Director 2.7.0 User Guide |
| 1,804 | `guides` | Juniper Routing Director 2.6.0 User Guide |
| 1,698 | `guides` | Juniper Routing Director 2.5.0 User Guide |
| 1,663 | `guides` | Juniper Apstra 4.2.2 / 4.2.1 / 4.2.0 User Guide |
| 1,649 | `uncategorized` | Junos OS BGP User Guide |
| 1,564 | `guides` | Juniper Apstra 6.0.0 User Guide |

## Source signals

The factory MUST compute one normalized signal string for each source document.
The signal string MUST include these fields when they exist.

1. Harvester category.
2. Catalog title.
3. Catalog file slug.
4. Catalog Markdown path.
5. Markdown frontmatter title.
6. Markdown heading levels 1 and 2.
7. The first 4,000 normalized prose words.

The factory MUST lowercase the signal string for matching. The factory MUST keep
identifiers unchanged in stored records.

## VersionedProductFamily rule

The factory MUST detect a versioned product family before it assigns topic work.
This rule fills the gap left by the harvester. The harvester applies a newest-in-
train rule to release notes. It does not apply that rule to user guides or API
references.

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

The factory MUST test domains in the priority order in this file. The first
matching rule assigns the document. No later rule can reassign it. If no rule
matches, the factory MUST assign the document to `juniper-general-reference`.

The priority order ranks unique technical pages after version deduplication.
Technical domains come first because they make an agent better at engineering
work. `juniper-business-solutions` and `juniper-legal-corporate` stay in scope,
but they have low expertise value. They mostly contain marketing, corporate,
and compliance text rather than operational procedure or reference facts.

The factory MUST write the assigned domain, matched rule, matched signal,
version family, and citation-only flag to `SourceDocument`. The factory MUST
fail if one document receives zero domains or more than one domain.

## Build priority and measured counts

The counts below come from `_catalog.csv` with this priority rule applied to the
category, title, file slug, and Markdown path. `Unique technical pages` removes
citation-only pages from the `VersionedProductFamily` rule.

| Priority | Skill | Documents | Total pages | Unique technical pages | Citation-only documents | Citation-only pages |
| -: | - | -: | -: | -: | -: | -: |
| 1 | `juniper-routing-junos` | 413 | 100,067 | 90,731 | 5 | 9,336 |
| 2 | `juniper-cli-reference` | 5 | 34,239 | 34,239 | 0 | 0 |
| 3 | `juniper-security-srx-firewall` | 176 | 30,491 | 30,491 | 0 | 0 |
| 4 | `juniper-observability-operations` | 131 | 28,259 | 28,259 | 0 | 0 |
| 5 | `juniper-campus-branch-switching` | 110 | 8,206 | 8,206 | 0 | 0 |
| 6 | `juniper-evpn-vxlan-fabric` | 36 | 5,985 | 5,985 | 0 | 0 |
| 7 | `juniper-api-automation` | 27 | 7,899 | 5,495 | 1 | 2,404 |
| 8 | `juniper-datacenter-apstra` | 126 | 12,902 | 4,200 | 5 | 8,702 |
| 9 | `juniper-general-reference` | 28 | 3,027 | 3,027 | 0 | 0 |
| 10 | `juniper-mist-ai-cloud` | 48 | 2,492 | 2,492 | 0 | 0 |
| 11 | `juniper-hardware-platforms` | 36 | 1,553 | 1,553 | 0 | 0 |
| 12 | `juniper-business-solutions` | 315 | 1,501 | 1,501 | 0 | 0 |
| 13 | `juniper-installation-maintenance` | 75 | 1,441 | 1,441 | 0 | 0 |
| 14 | `juniper-security-analytics-compliance` | 34 | 1,161 | 1,161 | 0 | 0 |
| 15 | `juniper-sdwan-wan` | 39 | 946 | 946 | 0 | 0 |
| 16 | `juniper-training-learning` | 29 | 779 | 779 | 0 | 0 |
| 17 | `juniper-cloud-native-contrail` | 13 | 672 | 672 | 0 | 0 |
| 18 | `juniper-software-lifecycle` | 56 | 592 | 592 | 0 | 0 |
| 19 | `juniper-legal-corporate` | 37 | 574 | 574 | 0 | 0 |
| 20 | `juniper-wireless-access` | 44 | 528 | 528 | 0 | 0 |
| - | Total | 1,778 | 243,314 | 222,872 | 11 | 20,442 |

## Domain rules

### 1. `juniper-routing-junos`

Subjects owned: Junos OS routing, MX, PTX, ACX, MPLS, BGP, OSPF, IS-IS, segment
routing, subscriber management, BNG, routing policy, class of service,
multicast, and interfaces.

Routing keywords: Junos, routing, router, MX, PTX, ACX, MPLS, BGP, OSPF, IS-IS,
segment routing, subscriber, BNG, routing policy, class of service, multicast,
interfaces.

Assign a source document to this domain when signals contain `Junos`, `routing`,
`router`, `routers`, `MX`, `PTX`, `ACX`, `MPLS`, `BGP`, `OSPF`, `ISIS`, `IS-IS`,
`segment routing`, `subscriber`, `BNG`, `routing policy`, `firewall filter`,
`traffic policer`, `class of service`, `CoS`, `multicast`, or `interfaces`.
Do not assign a source document here when a higher-priority EVPN, VXLAN, CLI,
SD-WAN, or security rule matches.

### 2. `juniper-cli-reference`

Subjects owned: Junos CLI command lookup, command syntax, command hierarchy,
operational commands, configuration commands, command options, and command
reference pages.

Routing keywords: CLI reference, command reference, Junos command, syntax,
statement, hierarchy, option, `show`, `set`, `clear`, `request`, `configure`.

Assign a source document to this domain when the category is `cli-reference` or
signals contain `Junos CLI Reference`, `CLI Reference`, `command reference`, or
`statement reference`. The agent routes a command lookup to this domain when the
question asks what a command does, what syntax a command accepts, or where a
statement sits in the Junos hierarchy.

### 3. `juniper-security-srx-firewall`

Subjects owned: SRX, vSRX, cSRX, firewall policy, NAT, IPsec, VPN, UTM, IDP,
IPS, threat prevention, and security gateways.

Routing keywords: SRX, vSRX, cSRX, firewall, NAT, IPsec, VPN, UTM, IDP, IPS,
threat, security gateway, Sky ATP.

Assign a source document to this domain when signals contain `SRX`, `vSRX`,
`cSRX`, `firewall`, `IPsec`, `VPN`, `UTM`, `IDP`, `IPS`, `NAT`, `threat`,
`secure edge`, `security director`, `security gateway`, `Sky ATP`, or `advanced
threat`.

### 4. `juniper-observability-operations`

Subjects owned: Paragon, NorthStar, HealthBot, Routing Director, monitoring,
analytics, insights, orchestration, planners, proactive operations, and Junos
Space operations.

Routing keywords: Paragon, NorthStar, HealthBot, Routing Director, monitor,
analytics, insights, planner, orchestration, service assurance, Network
Director, Junos Space.

Assign a source document to this domain when signals contain `Paragon`,
`NorthStar`, `HealthBot`, `Routing Director`, `monitor`, `monitoring`,
`analytics`, `insights`, `insight`, `planner`, `orchestration`, `orchestrator`,
`proactive`, `service assurance`, `Network Director`, or `Junos Space`.

### 5. `juniper-campus-branch-switching`

Subjects owned: campus switching, branch switching, EX, QFX, Ethernet switching,
wired access, PoE, and access switch operations.

Routing keywords: campus, branch, switching, switch, switches, EX, QFX, wired
access, Ethernet, PoE, access switch.

Assign a source document to this domain when signals contain `campus`, `branch`,
`switching`, `switches`, `switch`, `EX` followed by digits, `QFX` followed by
digits, `access switch`, `Ethernet switch`, `wired access`, or `PoE`.

### 6. `juniper-evpn-vxlan-fabric`

Subjects owned: EVPN, VXLAN, IP fabric, spine-leaf fabric, virtual chassis,
MC-LAG, VPLS, MPLS layer 2 VPN, and data center overlay fabrics.

Routing keywords: EVPN, VXLAN, fabric, IP fabric, spine, leaf, virtual chassis,
MC-LAG, VPLS, layer 2 VPN, overlay.

Assign a source document to this domain when the title, path, heading, or
content signals contain `EVPN`, `VXLAN`, `EVPN-VXLAN`, `IP fabric`, `spine`,
`leaf`, `virtual chassis`, `MC-LAG`, `MPLS L2VPN`, `layer 2 VPN`, or `VPLS`.
This rule MUST read path signals such as
`uncategorized/ex__configuration__evpn-vxlan/evpn.md`. It MUST assign `Junos OS
EVPN User Guide` to this domain, although the harvester category is
`uncategorized`.

### 7. `juniper-api-automation`

Subjects owned: REST APIs, SDKs, NETCONF, YANG, PyEZ, Ansible, automation,
telemetry interfaces, event collectors, webhooks, and developer guides.

Routing keywords: API, REST, NETCONF, YANG, PyEZ, Ansible, automation, script,
SDK, developer, webhook, telemetry, event collector.

Assign a source document to this domain when the category is `api`. Also assign
it when signals contain `API`, `REST`, `NETCONF`, `YANG`, `PyEZ`, `Ansible`,
`automation`, `script`, `SDK`, `developer`, `webhook`, `telemetry`, or `event
collector`. Apply the `VersionedProductFamily` rule before topic generation for
REST API references.

### 8. `juniper-datacenter-apstra`

Subjects owned: Apstra, data center fabric, intent-based networking, Smart
Fabric Services, blueprint design, device profiles, and data center operations.

Routing keywords: Apstra, data center, intent-based, blueprint, SFS, Smart
Fabric Services, spine, leaf, fabric operations.

Assign a source document to this domain when signals contain `Apstra`, `data
center`, `datacenter`, `intent-based`, `SFS`, or `Smart Fabric`. Apply the
`VersionedProductFamily` rule before topic generation for Apstra user guides.

### 9. `juniper-general-reference`

Subjects owned: documents that do not match a more specific domain, broad
Juniper reference material, licensing references, safety guides, and low-signal
converted documents.

Routing keywords: general Juniper reference, licensing, safety, broad guide,
unknown source, low-signal title.

Assign a source document to this domain only when no earlier rule matches. This
is the required fallback domain.

### 10. `juniper-mist-ai-cloud`

Subjects owned: Mist cloud, Marvis, AI-Native Networking, wireless assurance,
wired assurance, WAN assurance, location services, premium analytics, and Mist
Edge.

Routing keywords: Mist, Marvis, AI-Native, assurance, wireless assurance, wired
assurance, WAN assurance, location, premium analytics, Mist Edge.

Assign a source document to this domain when signals contain `Mist`, `Marvis`,
`AI-Native`, `AI native`, `assurance`, `premium analytics`, `Wi-Fi assurance`,
`wired assurance`, `WAN assurance`, `location services`, `Mist Edge`, or `cloud
services`.

### 11. `juniper-hardware-platforms`

Subjects owned: hardware datasheets, product platforms, chassis, line cards,
MICs, PICs, FPCs, transceivers, power supplies, fan trays, modules, adapters,
optics, and cables.

Routing keywords: datasheet, hardware, platform, chassis, line card, MIC, PIC,
FPC, transceiver, power supply, fan tray, module, optics, cable.

Assign a source document to this domain when the category is `datasheets`. Also
assign it when signals contain `datasheet`, `data sheet`, `hardware`,
`platform`, `appliance`, `chassis`, `line card`, `MIC`, `PIC`, `FPC`,
`transceiver`, `power supply`, `fan tray`, `module`, `adapter`, `optics`, or
`cable`.

### 12. `juniper-business-solutions`

Subjects owned: customer case studies, solution briefs, business outcomes,
industry use cases, white papers, analyst reports, brochures, flyers, and
marketing factsheets.

Routing keywords: case study, solution brief, white paper, analyst report,
customer story, use case, industry, enterprise, service provider, 5G, metro,
xHaul, finance, healthcare, retail.

Assign a source document to this domain when the category is `case-studies`,
`solution-briefs`, `white-papers`, `flyers`, `infographics`, `analyst-reports`,
`ebooks`, `executive-briefs`, `use-cases`, `brochures`, `factsheet`,
`editorials`, `articles`, `marketing-asset`, `reference-architectures`,
`validation-reports`, or `design`. Also assign it when signals contain `case
study`, `customer story`, `solution brief`, `white paper`, `analyst report`,
`executive brief`, `use case`, `vertical`, `retail`, `education`, `healthcare`,
`service provider`, `enterprise`, `metro`, `5G`, `xHaul`, `E-WAN`, `solution
overview`, or `test report brief`.

### 13. `juniper-installation-maintenance`

Subjects owned: installation guides, administration guides, rack and mount
steps, cabling, site preparation, FRU replacement, and field maintenance.

Routing keywords: installation, install, rack, mount, cabling, site preparation,
replace, replacement, FRU, administration guide, configuration essentials.

Assign a source document to this domain when the category is
`installation-guides`, `configuration-guides`, or `administration-guides`. Also
assign it when signals contain `installation`, `install`, `rack`, `mount`,
`cabling`, `site preparation`, `replace`, `replacement`, `field replaceable`,
`FRU`, `maintain`, `maintenance`, `unpack`, `ship kit`, `rail`, `administration
guide`, or `configuration essentials`.

### 14. `juniper-security-analytics-compliance`

Subjects owned: JSA, SIEM, log collectors, DSM guides, FIPS, Common Criteria,
FedRAMP, compliance evidence, and security validation reports.

Routing keywords: JSA, SIEM, log collector, DSM, FIPS, Common Criteria, FedRAMP,
compliance, validation report, evaluated configuration.

Assign a source document to this domain when the category is
`security-and-compliance`. Also assign it when signals contain `JSA`, `security
analytics`, `SIEM`, `log collector`, `DSM`, `FIPS`, `Common Criteria`, `FedRAMP`,
`compliance`, `validation report`, or `evaluated configuration`.

### 15. `juniper-sdwan-wan`

Subjects owned: Session Smart Router, SSR, Session Smart Conductor, SD-WAN, WAN
assurance, WAN edge, and 128 Technology material.

Routing keywords: Session Smart, SSR, SD-WAN, WAN assurance, WAN edge,
conductor, 128 Technology, branch WAN.

Assign a source document to this domain when the title, path, heading, or
content signals contain `Session Smart`, `SSR`, `SD-WAN`, `SDWAN`, `WAN
assurance`, `WAN edge`, `128 Technology`, `conductor`, or `branch WAN`. This
rule MUST read path and title signals so uncategorized Session Smart or SD-WAN
documents do not fall into the fallback domain.

### 16. `juniper-training-learning`

Subjects owned: Day One books, getting-started material, quick starts, labs,
learning guides, exams, certification study, and course material.

Routing keywords: Day One, getting started, quick start, lab, learning,
certification, exam, student, course, tutorial, starter.

Assign a source document to this domain when signals contain `day one`,
`dayone`, `getting started`, `quick start`, `quickstart`, `lab`, `learning`,
`certification`, `exam`, `student`, `course`, or `poster`.

### 17. `juniper-cloud-native-contrail`

Subjects owned: Contrail, CN2, Kubernetes networking, OpenShift networking,
container network interfaces, virtual networks, and cloud-native routing.

Routing keywords: Contrail, CN2, Kubernetes, OpenShift, cloud native, CNI,
container, virtual network, cloud router.

Assign a source document to this domain when signals contain `Contrail`, `cloud
native`, `cloud-native`, `CN2`, `Kubernetes`, `OpenShift`, `containerized`,
`CNI`, or `virtual network`.

### 18. `juniper-software-lifecycle`

Subjects owned: release notes, software updates, interim fixes, upgrade paths,
known issues, resolved issues, end of life notices, and migration notes.

Routing keywords: release notes, upgrade, update, interim fix, resolved issue,
known issue, migration, end of life, end of support, software installation.

Assign a source document to this domain when the category is `release-notes` or
`migration`. Also assign it when signals contain `release notes`, `upgrade`,
`update`, `interim`, `fix`, `end of life`, `EOL`, `end of support`, `EOS`, or
`software installation`. The harvester already keeps the newest train for
release notes. This domain must not replace the `VersionedProductFamily` rule
for user guides.

### 19. `juniper-legal-corporate`

Subjects owned: legal terms, corporate policy, trademark use, privacy, personal
data, sustainability, certificates, accessibility, and partner conduct.

Routing keywords: legal, privacy, corporate policy, trademark, sustainability,
certificate, accessibility, code of conduct, personal data, carbon, ESG, service
description.

Assign a source document to this domain when the category is `legal`,
`sustainability`, `certificates`, or `service-descriptions`. Also assign it when
signals contain `anti-corruption`, `code of conduct`, `trademark`, `privacy`,
`personal data`, `conflict minerals`, `slavery`, `accessibility`, `cookie`,
`ESG`, `CDP`, or `certificate`.

### 20. `juniper-wireless-access`

Subjects owned: access points, WLANs, Wi-Fi, BLE, RF design, antennas, radios,
and wireless site behavior outside Mist assurance content.

Routing keywords: wireless, Wi-Fi, WLAN, access point, AP, BLE, RF, radio,
antenna, wireless design.

Assign a source document to this domain when signals contain `wireless`,
`Wi-Fi`, `WiFi`, `WLAN`, `access point`, `AP` followed by digits, `BLE`, `radio`,
or `antenna`.

## Conflict rules

1. A CLI reference document always goes to `juniper-cli-reference`.
2. An EVPN or VXLAN document goes to `juniper-evpn-vxlan-fabric` before routing.
3. A Session Smart or SD-WAN document goes to `juniper-sdwan-wan` before Mist.
4. A release note goes to `juniper-software-lifecycle`.
5. A corporate or legal document goes to `juniper-legal-corporate` only when a
   higher-priority technical rule does not match.
6. A product solution brief goes to `juniper-business-solutions` when no
   higher-priority technical rule matches.
7. A document that names Mist assurance goes to `juniper-mist-ai-cloud` before
   it can go to wireless.
8. A document that names SRX goes to `juniper-security-srx-firewall` before it
   can go to hardware or routing.
9. A document that names JSA goes to `juniper-security-analytics-compliance`
   when an SRX rule does not match.

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

Warning: do not accept a domain report that checks zero documents. A zero-count
report hides a failed corpus read and can publish an empty skill set.
