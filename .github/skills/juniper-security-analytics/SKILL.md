---
name: juniper-security-analytics
description: >-
  Use when a user asks about Juniper Secure Analytics, STRM, or Juniper ATP
  Appliance as a SIEM source. Use for JSA deployment, managed hosts, log
  sources, DSMs, protocols, event parsing, event storage, flow sources, PCAP,
  rules, building blocks, offenses, false positives, AQL, saved searches,
  reports, dashboards, retention, health checks, backups, and upgrades.
  Require a cited Juniper source for each command, query, or procedure.
argument-hint: State the JSA release, component, log source, rule, search, or operational task.
---

# Analyze Juniper Secure Analytics

Use this skill for Juniper Secure Analytics, STRM, and Juniper ATP Appliance.
JSA is the Juniper SIEM platform. STRM is its earlier name. JATP can send CEF,
LEEF, or syslog notifications into a SIEM.

This skill never authorizes a live change. A retention change can delete
evidence. A rule change can hide an attack. A deployment change can stop event
collection.

The verified snapshot date is 2026-09-17. The source manifest holds 225
documents and 37,722 pages. This skill indexed all 225 documents.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Plan a JSA Console, Event Processor, Flow Processor, Data Node, or All-in-One appliance.
- Add, test, or repair a log source, protocol, parser, DSM, or log source extension.
- Explain event collection, parsing, coalescing, normalization, storage, or Ariel search.
- Add, test, or repair NetFlow, IPFIX, sFlow, J-Flow, packet capture, or SRX PCAP.
- Create or tune a rule, a building block, an offense, or a false positive.
- Write or verify an AQL query, saved search, time window, or index decision.
- Create a report, a dashboard item, a retention bucket, a backup, or an upgrade plan.
- Send JATP CEF, LEEF, or syslog events to a SIEM or JSA log source.

Do not use this skill for these requests:

- Mist Cloud API work. Use `managing-mist-api` for that task.
- Junos hardening or device command review. Use `hardening-junos` for that task.
- Fiber, Observium, Podman, or Python performance work.

## 2. Load one reference

Read only the reference that the task needs.

| Task | Reference | Result |
| - | - | - |
| Choose the component or data path. | [Platform and pipeline](./references/platform-pipeline.md) | The component, the pipeline stage, and the source citation. |
| Add or repair a log source. | [Log sources and search](./references/log-sources-and-search.md) | The DSM, protocol, parser, test, or AQL procedure. |
| Investigate an offense or tune a rule. | [Rules, offenses, and operations](./references/rules-offenses-operations.md) | A safe rule, offense, false positive, report, retention, backup, or upgrade procedure. |
| Verify a claim or search the corpus. | [Verification](./references/verification.md) | The source selection rule, corpus path rule, and acceptance checks. |
| Find a source document. | [Corpus index](./references/corpus-index.csv) | A row with file, title, topic, release, pages, and path. |

## 3. Choose the source

Use the newest readable administration guide or user guide that covers the task.
Use a smaller guide only when it is the most specific source for that subject.

| Source ID | Source document | Release | Use |
| - | - | - | - |
| JSA-DP | Juniper Secure Analytics Architecture and Deployment Guide | JSA 7.4.2 | Components, data flow, Data Nodes, All-in-One, and backup strategy. |
| JSA-AD | Juniper Secure Analytics Administration Guide | JSA 7.4.2 | Managed hosts, health, backups, retention, flow sources, and deployment changes. |
| JSA-UG | Juniper Secure Analytics Users Guide | JSA 7.4.2 | Dashboards, offenses, searches, rules, reports, and investigations. |
| JSA-DSM | Juniper Secure Analytics Configuring DSMs Guide | JSA 7.4.2 | DSMs, log sources, protocols, parser order, tests, and extensions. |
| JSA-AQL | Juniper Secure Analytics Ariel Query Language (AQL) Guide | JSA 7.4.2 | AQL syntax, query examples, time windows, functions, and fields. |
| JSA-TUNE | Juniper Secure Analytics Tuning Guide | JSA 7.4.2 | Deployment tuning, false positives, building blocks, and search performance. |
| JSA-PCAP | Juniper Secure Analytics Managing Juniper SRX PCAP Data | JSA 7.4.2 | SRX packet capture and PCAP Syslog Combination setup. |
| JSA-UP | Upgrading Juniper Secure Analytics to 7.4.2 | JSA 7.4.2 | Upgrade sequence and upgrade cautions. |
| JATP-SIEM | CEF, LEEF & Syslog Support for SIEM User's Guide | JATP 2018 | JATP SIEM connector, CEF, LEEF, syslog, and QRadar DSM plug-in. |
| JATP-OP | Juniper Advanced Threat Prevention Appliance Operator's Guide | JATP 5.0 | JATP dashboards, incidents, kill chain views, and traffic collectors. |

If two sources conflict, use this order:

1. The newest readable JSA guide for the same task.
2. The specific guide for the feature, such as PCAP or AQL.
3. STRM guidance only when the user works on STRM.
4. JATP guidance only for the JATP source system or SIEM connector.
5. Release notes, when they state a version-specific change.

## 4. Build the answer

Every answer must hold these parts:

1. State the component, log source, rule, search, or operation.
2. State the JSA, STRM, or JATP release from the source.
3. Cite the source document title and release.
4. Give the verified procedure, command, or AQL query.
5. State the verification step that proves the result.
6. Mark each missing source as unverified.

Use obvious placeholders in examples. Use `jsa.example.invalid`, `jatp.example.invalid`,
`192.0.2.10`, and `REPLACE_WITH_TOKEN`. Do not use a real hostname, address,
credential, serial number, or customer name.

## 5. Warn before harm

Warning: do not change a retention bucket until legal hold and incident response approve it. The change can delete evidence.

Warning: do not disable or narrow a rule until a second search proves the traffic is benign. The change can hide an attack.

Warning: do not deploy a full configuration change without a maintenance window. The change can restart collection services.

Warning: do not delete a log source until a replacement collects the same events. The deletion can create an evidence gap.

Warning: do not upgrade mixed JSA appliances out of order. A version mismatch can stop rules, offenses, or searches.

## 6. Search the staged corpus

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
The source files are outside the repository. The repository must not commit vendor text.

Use this procedure when the curated reference does not answer the question.

1. Open `references/corpus-index.csv`.
2. Filter by topic, title, or file name.
3. Select the newest readable release that matches the task.
4. Join the corpus root with the `path` value.
5. Open the Markdown file under `markdown2\`.
6. Confirm the procedure, command, query, or field in the source.
7. Distill the source. Do not copy long vendor text.
8. Cite the title and release in the answer.

If the corpus root is absent, state that the corpus is absent. Continue from the
curated reference files only.

## 7. Evidence block

End each answer with an evidence block.

```text
Evidence:
- JSA: <title>, <release> -- <procedure, query, or rule>
- STRM: <title>, <release> -- <procedure, query, or rule>
- JATP: <title>, <release> -- <procedure, query, or rule>
- Unverified: <claim> -- <missing source or next check>
```
