---
name: juniper-datacenter-fabric
description: >-
  Use when a user asks about Juniper data center switching or fabric design.
  Use for QFX platforms, port modes, interface names, shared buffers, IP Clos
  fabrics, spine and leaf underlays, BGP in a fabric, overlays as a design,
  Virtual Chassis Fabric, QFabric, Junos Fusion where the corpus covers it,
  data center bridging, priority flow control, enhanced transmission selection,
  congestion notification, FCoE, FIP snooping, Fibre Channel gateways, Contrail
  virtual networks, vRouter, controllers, and multicast in a fabric. For EVPN
  and VXLAN protocol details, route the user to the junos-mpls-vpn skill.
argument-hint: State the platform, Junos or Contrail release, fabric role, and the task.
---

# Juniper data center fabric

Use this skill for Juniper data center switches and the fabric that joins them.
Start here, then open one reference file.

This skill gives a safe command path for a junior NOC engineer. It does not
authorize a live change. A live change needs the normal MistHelper issue,
review, maintenance window, typed confirmation, and rollback plan.

The verified snapshot date is 2026-09-17. The staged manifest holds 98
documents and 16,539 pages. The skill indexes all 98 documents. The curated
references include a 59-row command register. They confirm 61 unique command spans
from the staged corpus.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Identify a QFX port, port mode, channelized port, or interface name.
- Check a QFX buffer, scheduler, forwarding class set, or CoS state.
- Plan an IP Clos spine and leaf fabric with a BGP underlay.
- Explain the overlay design that uses EVPN-VXLAN in a data center fabric.
- Find where the EVPN or VXLAN protocol detail lives.
- Review Virtual Chassis Fabric, QFabric, or Junos Fusion coverage.
- Configure or verify PFC, ETS, DCBX, or congestion notification.
- Configure or verify FCoE, FIP snooping, or Fibre Channel gateway state.
- Explain Contrail virtual networks, vRouter, controllers, and fabric automation.
- Verify multicast, IGMP snooping, PIM, or MSDP inside a fabric.

Do not use this skill for these requests:

- EVPN and VXLAN protocol behavior. Use `junos-mpls-vpn` for that task.
- A live Mist API request. Use `managing-mist-api` for that task.
- A Junos hardening control. Use `hardening-junos` for that task.
- A fiber cable, color code, loss budget, or MPO polarity question.

## 2. Load one reference

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Identify a QFX platform, interface, port mode, buffer, or fabric member. | [QFX platform and fabric](./references/qfx-platform-and-fabric.md) | A platform fact, safe read command, or change warning. |
| Plan or verify a BGP spine and leaf fabric or fabric multicast. | [IP fabric and multicast](./references/ip-fabric-and-multicast.md) | A design check, underlay command, or multicast verification command. |
| Configure or verify DCB, storage traffic, FCoE, FIP, or Contrail. | [DCB, storage, and Contrail](./references/dcb-storage-contrail.md) | A DCB or storage command set, or a Contrail design pointer. |
| Prove that a command or citation is safe to use. | [Verification](./references/verification.md) | A source check procedure and the command register. |
| Choose a source document and release. | [Corpus index](./references/corpus-index.csv) | The source title, topic, release, page count, and staged path. |

If two sources conflict, use this order:

1. The device running release and platform support statement.
2. The newest staged Juniper document for that platform.
3. The feature guide that owns the command syntax.
4. A release note for a support or limit claim.
5. A design guide, marked as design guidance.

## 3. Stay inside the boundary

This skill covers the data center design that uses EVPN and VXLAN. It does not
repeat the protocol detail. If a user asks how EVPN routes, VXLAN tunnels, route
targets, or Ethernet segments work, route the user to `junos-mpls-vpn`.

Use this skill to answer these design questions:

- Which switch role carries the leaf, spine, border leaf, or superspine task.
- Which underlay addresses and autonomous systems the fabric needs.
- Which overlay architecture places routing on a spine, border leaf, or leaf.
- Which QFX interface, port mode, or buffer object a design touches.
- Which DCB or FCoE setting can affect storage traffic.

## 4. Build the answer

Every answer holds these parts:

1. State the platform, fabric role, and release that the answer targets.
2. State the task, such as read-only verification or a planned change.
3. Name the source document and release for each command or fact.
4. Give the smallest safe command that answers the question.
5. State whether the command is read-only or changes configuration.
6. Add a warning before a port mode, fabric member, or DCB change.
7. Point to `junos-mpls-vpn` for EVPN or VXLAN protocol detail.
8. Mark each missing source as unverified.

Use obvious placeholders in examples. Use `leaf1.example.invalid`, `192.0.2.10`,
`198.51.100.10`, `AS65001`, and `REPLACE_WITH_VALUE`. Do not use a real host,
address, credential, serial number, or customer name.

## 5. Warn before harm

Warning: do not change a QFX port mode during production traffic. The interface
can restart, and every server on that port can lose the link.

Warning: do not remove a fabric member without a maintenance window. The fabric
can lose redundancy or isolate a rack.

Warning: do not change PFC, ETS, DCBX, or FCoE on a storage path without a tested
rollback. A wrong value can pause storage traffic or drop Fibre Channel sessions.

Warning: do not apply Contrail fabric automation to brownfield devices until you
compare the generated plan with the current configuration. The workflow can
replace working underlay or overlay state.

## 6. Search the staged corpus

The staged corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives`.
The repository does not hold the vendor documents. The skill never cites a path
under `documentation/references/`.

Use this procedure when the curated files do not answer the question:

1. Open [Corpus index](./references/corpus-index.csv).
2. Filter by the topic that matches the task.
3. Choose the newest release that matches the platform.
4. Open the Markdown file below the staged corpus root.
5. Confirm the command or statement in the source.
6. Quote only the shortest needed phrase.
7. Name the document title and release in the answer.
8. If no source supports the claim, state that no source supports it.

## 7. Report the evidence

End each answer with an evidence block.

```text
Evidence:
- Source: <title>, <release> -- <command or design fact>
- Device read: <show command> -- <state to verify>
- Boundary: junos-mpls-vpn -- EVPN and VXLAN protocol detail, if applicable
- Unverified: <claim> -- <missing source or next check>
```
