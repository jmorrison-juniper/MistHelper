# Juniper domain taxonomy contract

## Purpose

This contract defines the domain skills that receive the Juniper corpus. The
factory MUST map each source document to exactly one domain skill.

## Evidence base

The taxonomy uses the converted corpus in
`C:\Users\jmorrison\Downloads\juniper-harvest-md`. The catalog summary reports
1,778 converted documents, 243,314 pages, and 313.8 MB of Markdown. The catalog
contains 439 uncategorized documents and 108,314 uncategorized pages. The
factory MUST NOT use the harvester category as the only routing signal.

The largest categories prove the main content groups.

| Category | Documents | Pages |
| - | -: | -: |
| uncategorized | 439 | 108,314 |
| installation-guides | 214 | 5,603 |
| release-notes | 201 | 7,200 |
| case-studies | 200 | 528 |
| guides | 117 | 56,815 |
| design | 98 | 1,492 |
| solution-briefs | 93 | 472 |
| datasheets | 79 | 412 |
| security-and-compliance | 28 | 15,807 |
| api | 16 | 7,657 |
| cli-reference | 5 | 34,239 |

The title and file distribution proves the main product groups.

| Signal | Matches in titles and file names |
| - | -: |
| `junos` | 373 |
| `case` | 281 |
| `cloud` | 184 |
| `security` | 133 |
| `jsa` | 127 |
| `apstra` | 118 |
| `routing` | 113 |
| `mist` | 80 |
| `wan` | 78 |
| `hardware` | 74 |
| `router` | 71 |
| `contrail` | 58 |
| `srx` | 56 |
| `switches` | 53 |
| `automation` | 49 |
| `evpn` | 44 |
| `api` | 42 |

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
identifiers unchanged in the stored document record.

## Assignment rule

The factory MUST test domains in the priority order in this file. The first
matching rule assigns the document. No later rule can reassign it. If no rule
matches, the factory MUST assign the document to `juniper-general-reference`.

The factory MUST write the assigned domain, matched rule, and matched signal to
`SourceDocument`. The factory MUST fail if one document receives zero domains or
more than one domain.

## Domain list and measured counts

The counts below come from `_catalog.csv` with this priority rule applied to the
category, title, file slug, and Markdown path. The implementation can refine a
match with headings and content, but it MUST keep each document in exactly one
domain.

| Priority | Skill | Documents | Pages |
| -: | - | -: | -: |
| 1 | `juniper-legal-corporate` | 88 | 5,332 |
| 2 | `juniper-business-solutions` | 606 | 7,780 |
| 3 | `juniper-software-lifecycle` | 241 | 9,970 |
| 4 | `juniper-training-learning` | 205 | 11,476 |
| 5 | `juniper-api-automation` | 41 | 17,776 |
| 6 | `juniper-datacenter-apstra` | 26 | 12,866 |
| 7 | `juniper-cloud-native-contrail` | 48 | 10,513 |
| 8 | `juniper-mist-ai-cloud` | 29 | 3,567 |
| 9 | `juniper-security-srx-firewall` | 121 | 32,927 |
| 10 | `juniper-security-analytics-compliance` | 40 | 10,613 |
| 11 | `juniper-sdwan-wan` | 4 | 36 |
| 12 | `juniper-observability-operations` | 85 | 33,070 |
| 13 | `juniper-evpn-vxlan-fabric` | 3 | 710 |
| 14 | `juniper-routing-junos` | 103 | 73,840 |
| 15 | `juniper-campus-branch-switching` | 42 | 7,380 |
| 16 | `juniper-wireless-access` | 25 | 427 |
| 17 | `juniper-hardware-platforms` | 22 | 1,308 |
| 18 | `juniper-installation-maintenance` | 23 | 775 |
| 19 | `juniper-general-reference` | 26 | 2,948 |
| - | Total | 1,778 | 243,314 |

## Domain rules

### 1. `juniper-legal-corporate`

Subjects owned: legal terms, corporate policy, trademark use, privacy, personal
data, sustainability, certificates, accessibility, and partner conduct.

Routing keywords: legal, privacy, policy, trademark, sustainability, certificate,
accessibility, code of conduct, personal data, carbon, ESG, service description.

Assign a source document to this domain when the category is `legal`,
`sustainability`, `certificates`, or `service-descriptions`. Also assign it when
signals contain `anti-corruption`, `code of conduct`, `trademark`, `privacy`,
`personal data`, `conflict minerals`, `accessibility`, `cookie`, `ESG`, `CDP`, or
`certificate`.

### 2. `juniper-business-solutions`

Subjects owned: customer case studies, solution briefs, business outcomes,
industry use cases, white papers, analyst reports, brochures, flyers, and
marketing factsheets.

Routing keywords: case study, solution brief, white paper, analyst report,
customer story, use case, industry, enterprise, service provider, 5G, metro,
xHaul, finance, healthcare, retail.

Assign a source document to this domain when the category is `case-studies`,
`solution-briefs`, `white-papers`, `flyers`, `infographics`, `analyst-reports`,
`ebooks`, `executive-briefs`, `use-cases`, `brochures`, `factsheet`, `editorials`,
`articles`, `marketing-asset`, `reference-architectures`, `validation-reports`,
or `design`. Also assign it when signals contain `case study`, `customer story`,
`solution brief`, `white paper`, `analyst report`, `executive brief`, `use case`,
`metro`, `5G`, `xHaul`, `E-WAN`, `solution overview`, or `test report brief`.

### 3. `juniper-software-lifecycle`

Subjects owned: release notes, software updates, interim fixes, upgrade paths,
known issues, resolved issues, end of life notices, and migration notes.

Routing keywords: release notes, upgrade, update, interim fix, resolved issue,
known issue, migration, end of life, end of support, software installation.

Assign a source document to this domain when the category is `release-notes` or
`migration`. Also assign it when signals contain `release notes`, `upgrade`,
`update`, `interim`, `fix`, `end of life`, `EOL`, `end of support`, `EOS`, or
`software installation`.

### 4. `juniper-training-learning`

Subjects owned: Day One books, getting-started material, quick starts, labs,
learning guides, exams, certification study, and course material.

Routing keywords: Day One, getting started, quick start, lab, learning,
certification, exam, student, course, tutorial, starter.

Assign a source document to this domain when signals contain `day one`,
`dayone`, `getting started`, `quick start`, `quickstart`, `lab`, `learning`,
`certification`, `exam`, `student`, `course`, or `poster`.

### 5. `juniper-api-automation`

Subjects owned: REST APIs, SDKs, NETCONF, YANG, PyEZ, Ansible, automation,
telemetry interfaces, event collectors, webhooks, and developer guides.

Routing keywords: API, REST, NETCONF, YANG, PyEZ, Ansible, automation, script,
SDK, developer, webhook, telemetry, event collector.

Assign a source document to this domain when the category is `api`. Also assign
it when signals contain `API`, `REST`, `NETCONF`, `YANG`, `PyEZ`, `Ansible`,
`automation`, `script`, `SDK`, `developer`, `webhook`, `telemetry`, or `event
collector`.

### 6. `juniper-datacenter-apstra`

Subjects owned: Apstra, data center fabric, intent-based networking, Smart
Fabric Services, blueprint design, device profiles, and data center operations.

Routing keywords: Apstra, data center, intent-based, blueprint, SFS, Smart
Fabric Services, spine, leaf, fabric operations.

Assign a source document to this domain when signals contain `Apstra`, `data
center`, `datacenter`, `intent-based`, `SFS`, or `Smart Fabric`.

### 7. `juniper-cloud-native-contrail`

Subjects owned: Contrail, CN2, Kubernetes networking, OpenShift networking,
container network interfaces, virtual networks, and cloud-native routing.

Routing keywords: Contrail, CN2, Kubernetes, OpenShift, cloud native, CNI,
container, virtual network, cloud router.

Assign a source document to this domain when signals contain `Contrail`, `cloud
native`, `cloud-native`, `CN2`, `Kubernetes`, `OpenShift`, `containerized`,
`CNI`, or `virtual network`.

### 8. `juniper-mist-ai-cloud`

Subjects owned: Mist cloud, Marvis, AI-Native Networking, wireless assurance,
wired assurance, WAN assurance, location services, premium analytics, and Mist
Edge.

Routing keywords: Mist, Marvis, AI-Native, assurance, wireless assurance, wired
assurance, WAN assurance, location, premium analytics, Mist Edge.

Assign a source document to this domain when signals contain `Mist`, `Marvis`,
`AI-Native`, `AI native`, `assurance`, `premium analytics`, `Wi-Fi assurance`,
`wired assurance`, `WAN assurance`, `location services`, `Mist Edge`, or `cloud
services`.

### 9. `juniper-security-srx-firewall`

Subjects owned: SRX, vSRX, cSRX, firewall policy, NAT, IPsec, VPN, UTM, IDP,
IPS, threat prevention, and security gateways.

Routing keywords: SRX, vSRX, cSRX, firewall, NAT, IPsec, VPN, UTM, IDP, IPS,
threat, security gateway, Sky ATP.

Assign a source document to this domain when signals contain `SRX`, `vSRX`,
`cSRX`, `firewall`, `IPsec`, `VPN`, `UTM`, `IDP`, `IPS`, `NAT`, `threat`,
`secure edge`, `security director`, `security gateway`, `Sky ATP`, or `advanced
threat`.

### 10. `juniper-security-analytics-compliance`

Subjects owned: JSA, SIEM, log collectors, DSM guides, FIPS, Common Criteria,
FedRAMP, compliance evidence, and security validation reports.

Routing keywords: JSA, SIEM, log collector, DSM, FIPS, Common Criteria, FedRAMP,
compliance, validation report, evaluated configuration.

Assign a source document to this domain when the category is
`security-and-compliance`. Also assign it when signals contain `JSA`, `security
analytics`, `SIEM`, `log collector`, `DSM`, `FIPS`, `Common Criteria`, `FedRAMP`,
`compliance`, `validation report`, or `evaluated configuration`.

### 11. `juniper-sdwan-wan`

Subjects owned: Session Smart Router, SSR, Session Smart Conductor, SD-WAN,
WAN edge, and 128 Technology material.

Routing keywords: Session Smart, SSR, SD-WAN, WAN edge, conductor, 128
Technology, branch WAN.

Assign a source document to this domain when signals contain `Session Smart`,
`SSR`, `SD-WAN`, `SDWAN`, `WAN edge`, `128 Technology`, `conductor`, or `branch
WAN`.

### 12. `juniper-observability-operations`

Subjects owned: Paragon, NorthStar, HealthBot, monitoring, analytics, insights,
orchestration, planners, proactive operations, and Junos Space operations.

Routing keywords: Paragon, NorthStar, HealthBot, monitor, analytics, insights,
planner, orchestration, service assurance, Network Director, Junos Space.

Assign a source document to this domain when signals contain `Paragon`,
`NorthStar`, `HealthBot`, `monitor`, `monitoring`, `analytics`, `insights`,
`insight`, `planner`, `orchestration`, `orchestrator`, `proactive`, `service
assurance`, `Network Director`, or `Junos Space`.

### 13. `juniper-evpn-vxlan-fabric`

Subjects owned: EVPN, VXLAN, IP fabric, spine-leaf fabric, virtual chassis,
MC-LAG, VPLS, and layer 2 VPN fabric designs.

Routing keywords: EVPN, VXLAN, fabric, IP fabric, spine, leaf, virtual chassis,
MC-LAG, VPLS, layer 2 VPN.

Assign a source document to this domain when signals contain `EVPN`, `VXLAN`,
`fabric`, `IP fabric`, `spine`, `leaf`, `virtual chassis`, `MC-LAG`, `MPLS L2VPN`,
`layer 2 VPN`, or `VPLS`.

### 14. `juniper-routing-junos`

Subjects owned: Junos OS routing, MX, PTX, ACX, MPLS, BGP, OSPF, IS-IS, segment
routing, subscriber management, BNG, routing policy, class of service,
multicast, and interfaces.

Routing keywords: Junos, routing, router, MX, PTX, ACX, MPLS, BGP, OSPF, IS-IS,
segment routing, subscriber, BNG, routing policy, class of service, multicast,
interfaces.

Assign a source document to this domain when the category is `cli-reference`.
Also assign it when signals contain `Junos`, `routing`, `router`, `routers`,
`MX`, `PTX`, `ACX`, `MPLS`, `BGP`, `OSPF`, `ISIS`, `IS-IS`, `segment routing`,
`subscriber`, `BNG`, `policy`, `class of service`, `CoS`, `multicast`, or
`interfaces`.

### 15. `juniper-campus-branch-switching`

Subjects owned: campus switching, branch switching, EX, QFX, Ethernet switching,
wired access, PoE, and access switch operations.

Routing keywords: campus, branch, switching, switch, switches, EX, QFX, wired
access, Ethernet, PoE, access switch.

Assign a source document to this domain when signals contain `campus`, `branch`,
`switching`, `switches`, `switch`, `EX` followed by digits, `QFX` followed by
digits, `access switch`, `Ethernet switch`, `wired access`, or `PoE`.

### 16. `juniper-wireless-access`

Subjects owned: access points, WLANs, Wi-Fi, BLE, RF design, antennas, radios,
and wireless site behavior outside Mist assurance content.

Routing keywords: wireless, Wi-Fi, WLAN, access point, AP, BLE, RF, radio,
antenna, wireless design.

Assign a source document to this domain when signals contain `wireless`, `Wi-Fi`,
`WiFi`, `WLAN`, `access point`, `AP` followed by digits, `BLE`, `radio`, or
`antenna`.

### 17. `juniper-hardware-platforms`

Subjects owned: hardware datasheets, product platforms, chassis, line cards,
MICs, PICs, FPCs, transceivers, power supplies, fan trays, modules, adapters,
optics, and cables.

Routing keywords: datasheet, hardware, platform, chassis, line card, MIC, PIC,
FPC, transceiver, power supply, fan tray, module, optics, cable.

Assign a source document to this domain when the category is `datasheets`. Also
assign it when signals contain `datasheet`, `data sheet`, `hardware`, `platform`,
`appliance`, `chassis`, `line card`, `MIC`, `PIC`, `FPC`, `transceiver`, `power
supply`, `fan tray`, `module`, `adapter`, `optics`, or `cable`.

### 18. `juniper-installation-maintenance`

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

### 19. `juniper-general-reference`

Subjects owned: documents that do not match a more specific domain, broad
Juniper reference material, licensing references, safety guides, and low-signal
converted documents.

Routing keywords: general Juniper reference, licensing, safety, broad guide,
unknown source, low-signal title.

Assign a source document to this domain only when no earlier rule matches. This
is the required fallback domain.

## Conflict rules

1. A release note always goes to `juniper-software-lifecycle`, even when its
   title names a product domain.
2. A corporate or legal document always goes to `juniper-legal-corporate`.
3. A product solution brief goes to `juniper-business-solutions` when the brief
   gives business value instead of operational facts.
4. A document that names Mist assurance goes to `juniper-mist-ai-cloud` before
   it can go to wireless or SD-WAN.
5. A document that names SRX goes to `juniper-security-srx-firewall` before it
   can go to hardware or routing.
6. A document that names JSA goes to `juniper-security-analytics-compliance`.

## Required domain report

Each factory run MUST write a domain report. The report MUST state these values.

1. Total documents checked.
2. Total pages checked.
3. Document count and page count for each domain.
4. Fallback document count.
5. The top 20 unmatched title tokens in the fallback domain.
6. The count of documents that matched by category only.
7. The count of documents that matched by title or content signal.

Warning: do not accept a domain report that checks zero documents. A zero-count
report hides a failed corpus read and can publish an empty skill set.
