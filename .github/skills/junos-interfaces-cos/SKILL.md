---
name: junos-interfaces-cos
description: >-
  Use when a user asks how to read, configure, or verify Junos interfaces or
  Junos class of service. Use for interface names, physical interface settings,
  logical units, addresses, VLAN tagging, interface filters, optics,
  transceivers, aggregated Ethernet, load balance hashing, forwarding classes,
  queues, classifiers, rewrite rules, schedulers, policers, shapers, drop
  profiles, and weighted random early detection. Require a cited Junos source
  before you give a device command.
argument-hint: State the platform, Junos train, interface name, service risk, and configuration task.
---

# Operate Junos interfaces and class of service

Use this skill when MistHelper or an operator needs a Junos interface command
or a class-of-service command. Start at this router file. Then read one
reference file that matches the task.

This skill does not authorize a live change. A live change needs the normal
MistHelper issue, review, and typed confirmation process.

The verified snapshot date is 2026-09-17. The staged corpus contains 16
documents and 6,332 pages. The staged source train is Junos 26.2.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Explain a Junos interface name, such as `ge-0/0/0.0`.
- Configure speed, duplex, MTU, a description, or the `disable` statement.
- Configure a logical unit, an address, VLAN tagging, or a filter.
- Read optics, transceivers, and diagnostics.
- Configure aggregated Ethernet or a load balance hash.
- Configure a forwarding class, queue, classifier, rewrite rule, or marker.
- Configure a scheduler, scheduler map, transmit rate, buffer size, or priority.
- Configure a policer, shaper, drop profile, or WRED behavior.
- Verify a live interface or queue before a planned change.

Do not use this skill for these requests:

- A Mist API task. Use `managing-mist-api` for that task.
- A Python speed change. Use `optimizing-python` for that task.
- Podman, Observium, or fiber work.
- A Junos security hardening task. Use `hardening-junos` for that task.

## 2. Load the reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose a source and cite it. | [Verification](./references/verification.md) | A source, a train, and a validation method. |
| Configure or verify an interface. | [Interfaces](./references/interfaces.md) | A command, a risk warning, and a source citation. |
| Configure or verify class of service. | [Class of service](./references/class-of-service.md) | A command, a risk warning, and a source citation. |
| Check the corpus rows. | [Corpus index](./references/corpus-index.csv) | The staged source list and relative Markdown paths. |

If two sources conflict, use this order:

1. The current device configuration.
2. The newest source document that matches the platform.
3. The source document for the same platform family.
4. The source document for another platform family, marked as a fallback.
5. A prior note or issue, marked as unverified.

## 3. Search the staged corpus

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
The repository holds no Juniper document.

Use this procedure when the curated reference does not give enough detail.

1. Open `references/corpus-index.csv`.
2. Find the document row for the topic.
3. Open the Markdown file under the corpus root.
4. Use the page marker before the next page break as the page number.
5. Confirm the exact `set` or `show` command in the source.
6. Quote only the short command or short statement that proves the answer.
7. Name the document title, Junos train, and page number.

If the corpus root is absent, state that the corpus is absent. Then answer only
from the curated reference files.

Warning: do not invent a Junos command. A wrong command on a production device
can drop traffic or change an unintended interface.

## 4. Build the answer

Every answer must contain these parts:

1. State the platform and Junos train from the source.
2. State the interface, queue, classifier, scheduler, or policer scope.
3. Give the verified command in a code block.
4. State the risk before any live change command.
5. Give the read command that proves the device state.
6. Cite the source document, train, and page number.
7. Mark each missing source as unverified.

Use obvious placeholders in examples. Use `ge-0/0/0`, `ae0`, `192.0.2.1/24`,
`VOICE`, and `BUSINESS`. Do not use a real hostname, address, serial number, or
customer name.

## 5. Warn before harm

Warning: an MTU change can drop traffic when the two ends do not match. Verify
the peer MTU before you commit the change.

Warning: a speed or duplex change can drop traffic when negotiation fails. Verify
the peer setting before you commit the change.

Warning: a class-of-service change can starve traffic when queues or rates are
wrong. Verify queue counters before and after you commit the change.

Warning: disabling an interface drops all traffic on that interface. Confirm the
recovery path before you commit the change.

## 6. Give the evidence block

End each answer with this block.

```text
Evidence:
- Junos: <title>, Junos <train>, page <page> -- <command or rule>.
- Device read: <show command> -- <state to verify>.
- Unverified: <claim> -- <missing source or next check>.
```

Never cite a path under `documentation/references/`. That directory is ignored
to keep vendor material out of the repository.
