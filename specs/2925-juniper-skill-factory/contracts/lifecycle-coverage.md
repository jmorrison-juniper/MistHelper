# Life cycle coverage contract

## Purpose

This contract defines the life cycle tags for Juniper skill topics. A topic MUST
have one or more tags. A domain MUST report any missing tag as a coverage gap.

## Tag set

| Tag | Stage | Question that the topic answers |
| - | - | - |
| `day0` | Design and select | Which architecture, product, feature, or limit fits the need. |
| `day1` | Deploy and install | How the agent configures, installs, connects, or starts the system. |
| `day2` | Operate and maintain | How the agent verifies, monitors, troubleshoots, or repairs the system. |
| `day2plus` | Change and scale | How the agent upgrades, migrates, expands, automates, or changes the system. |

A topic can carry multiple tags when one source range covers more than one
stage. The factory MUST store each tag as a separate `TopicLifecycle` row or as
a normalized array field that a validator can query.

## `day0` signals

A topic earns `day0` when the source text helps the agent choose a design,
product, topology, architecture, feature, or limit before deployment.

Strong signals:

- Architecture, reference architecture, design, blueprint, topology, and
  planning language.
- Product selection, model comparison, license choice, sizing, throughput,
  scale, and capacity language.
- Requirements, prerequisites, supported platforms, supported releases, and
  compatibility language.
- Hardware datasheets, optics tables, port maps, power budgets, and
  environmental limits.
- Security models, compliance scope, design constraints, and risk models.

Examples of `day0` topics:

- Choose an SRX model for a throughput need.
- Choose an EVPN-VXLAN fabric topology.
- Select an Apstra blueprint design.
- Read a Mist assurance license requirement.
- Check the maximum number of BGP peers.

## `day1` signals

A topic earns `day1` when the source text helps the agent install, configure, or
start the system for the first time.

Strong signals:

- Install, rack, mount, cable, power, unpack, and site preparation language.
- Initial setup, zero touch provisioning, bootstrap, onboarding, and claim
  language.
- Configuration steps, CLI procedures, templates, profiles, and setup wizards.
- First login, first commit, activation, pairing, adoption, and enrollment
  language.
- Upgrade installation only when the procedure creates the first usable system.

Examples of `day1` topics:

- Rack an EX switch and connect power.
- Claim an access point in Mist.
- Configure an initial BGP neighbor.
- Deploy an Apstra server.
- Add a device to Junos Space for the first time.

## `day2` signals

A topic earns `day2` when the source text helps the agent operate, verify,
monitor, troubleshoot, or repair an existing system.

Strong signals:

- Verify, monitor, view, show, check, trace, test, and troubleshoot language.
- Alarm, alert, event, log, metric, insight, service level, and health language.
- Replace, repair, recover, restore, failover, rollback, and remediation
  language.
- Operational state, statistics, counters, packet capture, and diagnostics
  language.
- Known problems and symptoms when the text gives a repair path.

Examples of `day2` topics:

- Use `show interfaces` to verify link state.
- Read Mist insight causes for poor Wi-Fi experience.
- Troubleshoot IPsec tunnel establishment.
- Replace a failed power supply.
- Review Paragon service assurance alarms.

## `day2plus` signals

A topic earns `day2plus` when the source text helps the agent change, expand,
automate, upgrade, or migrate a working system.

Strong signals:

- Upgrade, migrate, convert, scale, expand, extend, automate, integrate, and
  orchestrate language.
- Release notes, resolved issues, known issues, and behavior changes.
- API workflows, bulk changes, import, export, and event-driven automation.
- New feature enablement after deployment.
- Capacity expansion, cluster growth, license expansion, and topology change.

Examples of `day2plus` topics:

- Upgrade Junos OS and verify the target release.
- Migrate a firewall policy to a new SRX platform.
- Automate configuration with PyEZ.
- Expand an EVPN fabric with new leaf switches.
- Enable a new Mist service after deployment.

## Tag selection rule

The factory MUST score source signals for all four tags. It MUST assign every
tag with a positive score. If every score is zero, the factory MUST assign
`day0` and mark the topic with `coverage_reason: inferred-general`.

The scoring order is:

1. Read frontmatter and catalog category.
2. Read the topic heading and parent headings.
3. Read the source range for action words.
4. Read tables and captions for limits or procedures.
5. Read nearby headings when a topic contains only a table or figure.

The factory MUST store the matched signals for each assigned tag. The report
MUST show at least one signal for each tag on each topic.

## Category defaults

The category default is a weak signal. A strong title or content signal can add
another tag.

| Category | Default tags |
| - | - |
| `datasheets` | `day0` |
| `design` | `day0` |
| `reference-architectures` | `day0` |
| `installation-guides` | `day1` |
| `configuration-guides` | `day1` |
| `administration-guides` | `day1`, `day2` |
| `cli-reference` | `day1`, `day2` |
| `guides` | `day1`, `day2` |
| `release-notes` | `day2plus` |
| `api` | `day2plus` |
| `security-and-compliance` | `day0`, `day2` |
| `case-studies` | `day0` |
| `solution-briefs` | `day0` |
| `white-papers` | `day0` |
| `legal` | `day0` |
| `sustainability` | `day0` |
| `uncategorized` | no default |

## Coverage gap report

A domain has a coverage gap when it has zero topics for one or more life cycle
tags. The gap does not fail the build, because the source corpus can lack a
stage. The gap MUST appear in the level 1 `INDEX.md` and in the factory domain
report.

The gap report MUST include these fields.

| Field | Type | Rule |
| - | - | - |
| `domain` | string | Domain skill name. |
| `missing_tag` | enum | One of the four life cycle tags. |
| `topics_checked` | integer | Count of topics in the domain. |
| `documents_checked` | integer | Count of documents in the domain. |
| `best_near_match` | string | Topic with the closest signal, or `none`. |
| `recommended_source_query` | string | Query for the next corpus harvest. |

A domain report that checks zero topics MUST fail. A zero-topic report means the
factory did not measure coverage.

## Required wording in indexes

When a domain has full coverage, the level 1 `INDEX.md` MUST state:

```text
No life cycle coverage gaps were found.
```

When a domain misses a stage, the level 1 `INDEX.md` MUST state:

```text
Coverage gap: no topic covers <tag>. Search the source corpus for <query>.
```

Caution: a coverage gap is recoverable. The skill can still answer questions
from covered topics, but it must state that the missing stage is not covered.
