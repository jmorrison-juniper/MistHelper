---
name: junos-high-availability
description: >-
  Use when a user asks how to plan, verify, configure, or troubleshoot Junos
  high availability. Use for Virtual Chassis, Graceful Routing Engine
  switchover, nonstop active routing, nonstop bridging, unified ISSU, NSSU,
  VRRP, SRX chassis clusters, redundancy groups, control links, fabric links,
  failover, and graceful restart. Require a cited Juniper source for each
  device command or statement before you answer.
argument-hint: State the platform, Junos train, high-availability feature, and planned action.
---

# Operate Junos high availability

Use this skill when an answer can change, test, or diagnose Junos redundancy.
Start with the safety check. Then load one reference file and cite the source.

This skill does not authorize a live change. A live change needs the normal
MistHelper issue, review, maintenance window, and typed confirmation process.

The verified snapshot date is 2026-09-17. The skill summarizes 10 staged
Juniper documents and 5,125 pages. These counts describe the staged corpus.
They do not describe the current Juniper site.

## 1. Decide whether this skill applies

Use this skill for these requests:

- A Virtual Chassis member, role, VCP, priority, split detection, or mixed mode.
- Graceful Routing Engine switchover, nonstop active routing, or nonstop bridging.
- A unified ISSU or a nonstop software upgrade.
- A VRRP group, priority, preempt rule, tracked interface, or virtual address.
- An SRX chassis cluster node, redundancy group, control link, fabric link, or failover.
- Graceful restart for BGP, OSPF, OSPFv3, IS-IS, RSVP, LDP, CCC, TCC, or VPN service.

Do not use this skill for these requests:

- A live Mist API request. Use `managing-mist-api` for that task.
- A Junos hardening control. Use `hardening-junos` for that task.
- A Python speed change. Use `optimizing-python` for that task.
- Fiber, Observium, or Podman work.

## 2. Load the reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose the source and cite it. | [Verification](./references/verification.md) | A source, a train, a gap check, and a validation method. |
| Work with Virtual Chassis. | [Virtual Chassis](./references/virtual-chassis.md) | The member, role, priority, VCP, split detection, and mixed mode rules. |
| Work with GRES, NSR, NSB, ISSU, NSSU, or graceful restart. | [Routing and upgrade](./references/routing-and-upgrade.md) | The required commands, prerequisites, checks, and warnings. |
| Work with VRRP or an SRX chassis cluster. | [VRRP and chassis cluster](./references/vrrp-and-cluster.md) | The group, priority, tracked item, virtual address, node, link, and failover rules. |
| Search or refresh the staged corpus. | [Corpus index](./references/corpus-index.csv) | The document title, topic, train, page count, and source path. |
| Report corpus gaps or acceptance checks. | [Verification](./references/verification.md) | The known gap, fallback train, risk, and offline checks. |

If two sources conflict, use this order:

1. The current repository code for what MistHelper does.
2. The newest readable Juniper document for the target platform.
3. The fallback Juniper train from [Verification](./references/verification.md).
4. Issue text or prior notes, marked as unverified until a source confirms them.

## 3. Search the staged corpus

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
The repository holds no Juniper document.

Use this procedure when the curated reference does not give enough detail.

1. Open `references/corpus-index.csv`.
2. Find the document for the platform and feature.
3. Open the Markdown file below the corpus root.
4. Confirm the statement or command in the source file.
5. Keep any quote short.
6. Name the document and Junos train in the answer.
7. If the row uses a fallback train, state the gap and the risk.

Do not cite an ignored vendor corpus path. A clean clone does not hold that content.

## 4. Build the answer

Every answer holds these parts:

1. State the platform and high-availability feature.
2. State the Junos train from the source.
3. State the exact command or statement, if the answer uses one.
4. Cite the source document for each command or statement.
5. State each warning before the step that can interrupt traffic.
6. Mark each missing source as unverified.
7. Give the read command that proves the device state.

Use obvious placeholders in examples. Use `device.example.invalid`,
`192.0.2.10`, and `/var/tmp/package-name.tgz`. Do not use a real hostname,
address, credential, serial number, or customer name.

## 5. Apply the safety rules

Warning: a Virtual Chassis role change can restart forwarding across the stack.
A wrong change can drop all site traffic that crosses the stack.

Warning: a mastership change moves the control plane. A wrong change can make
operators lose management access during the switchover.

Warning: a split-brain condition can make two partitions forward as independent
systems. That condition can drop or misdirect site traffic.

Warning: a chassis cluster failover moves traffic to the peer node. A wrong
failover can reset sessions and drop production traffic.

Warning: ISSU and NSSU start upgrade workflows on live hardware. An unsupported
image or missed prerequisite can interrupt forwarding and management access.

Never give a `set` or `show` command unless a staged source confirms it. If no
source confirms the command, say that the command is unverified.

## 6. Confirm commands before use

The curated references contain verified commands only. For a new command, search
the staged corpus first. Then add a short citation in the answer.

Use configuration reads before changes:

- `show virtual-chassis`
- `show system switchover`
- `show task replication`
- `show bgp replication`
- `show vrrp summary`
- `show chassis cluster status`
- `show chassis cluster interfaces`

Use operational checks after changes:

- `show virtual-chassis`
- `show system switchover`
- `show task replication`
- `show chassis in-service-upgrade`
- `show chassis nonstop-upgrade`
- `show version invoke-on all-routing-engines`

## 7. Report the evidence

End each answer with an evidence block.

```text
Evidence:
- Junos: <title>, <train> -- <rule or command>
- Command check: <command> -- confirmed in <title>, <train>
- Gap: <document> -- <affected train, fallback train, and risk>
- Unverified: <claim> -- <missing source or next check>
```

If the user asks for a change, do not rely on this skill alone. Use the
repository workflow, tests, and human review rules before you change code.