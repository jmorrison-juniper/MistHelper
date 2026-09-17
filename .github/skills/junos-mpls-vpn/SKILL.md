---
name: junos-mpls-vpn
description: >-
  Use when a user asks about Junos MPLS, LDP, RSVP, segment routing,
  layer 3 VPN, layer 2 VPN, VPLS, layer 2 circuit, EVPN, VXLAN,
  OVSDB VXLAN, provider edge design, service verification, or service
  repair. Confirm each Junos command in the staged Juniper corpus before
  you give it to an operator.
argument-hint: State the service type, device role, Junos train, platform, and the task or symptom.
---

# Junos MPLS and VPN skill

Use this skill for Junos MPLS and the VPN services that use MPLS or VXLAN.
Start here, then open exactly one reference file for the task.

This skill does not authorize a live network change. A live change needs a
change window, a rollback plan, and the normal MistHelper review process.

The verified snapshot date is 2026-09-17. The source set has 6 documents and
7,069 staged pages. The Junos train is 26.2 for each row in the index.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Explain MPLS label switching, label stacks, labels, and LSP selection.
- Configure or verify LDP, RSVP, traffic engineering, and fast repair.
- Configure or verify segment routing where the MPLS guide covers it.
- Configure or verify a layer 3 VPN on provider edge routers.
- Configure or verify a layer 2 VPN, VPLS, or layer 2 circuit.
- Configure or verify EVPN over MPLS or EVPN over VXLAN.
- Explain EVPN type routes, multihoming, and data center overlays.
- Check an OVSDB and VXLAN design that uses the staged Juniper guides.

Do not use this skill for these requests:

- A live Mist API request. Use `managing-mist-api` for that task.
- A Junos hardening control. Use `hardening-junos` for that task.
- A firewall policy design without MPLS, VPN, EVPN, or VXLAN.
- Fiber, Observium, Podman, or Python speed work.

Warning: do not paste a sample VPN or MPLS command into production. A wrong
route target, interface, or LSP path can break a customer service.

## 2. Load the reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Explain MPLS, LDP, RSVP, traffic engineering, or segment routing. | [MPLS core](./references/mpls-core.md) | A task path, a verified command, and a source page. |
| Configure or verify L3VPN, L2VPN, VPLS, or a layer 2 circuit. | [VPN services](./references/vpn-services.md) | The service model, the command set, and the verification command. |
| Configure or verify EVPN, VXLAN, multihoming, or OVSDB VXLAN. | [EVPN and VXLAN](./references/evpn-vxlan.md) | The control plane, the data plane, and a verified command. |
| Choose a source, cite it, or inspect gaps. | [Verification](./references/verification.md) | The source rule, command proof, and command drop list. |
| Rebuild or audit the staged source list. | [Corpus index](./references/corpus-index.csv) | The six source rows and their staged Markdown paths. |

If a task crosses subjects, answer in this order:

1. Prove transport reachability with the MPLS core reference.
2. Prove route exchange with the VPN services reference.
3. Prove overlay state with the EVPN and VXLAN reference.
4. Prove the cited source with the verification reference.

## 3. Cite sources in every answer

Every answer must name the source document and Junos train. Cite the public
Juniper URL first. Then cite the staged corpus path and page.

Use this citation shape:

```text
Source: Junos OS MPLS Applications User Guide, Junos 26.2.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/mpls.md, page 88.
```

Never cite a path under `documentation/references/`. That directory is ignored
by Git and is absent for a reader who clones this repository.

Keep each quote short. Distil the vendor text and cite it.

## 4. Confirm a command before you give it

Use the curated references first. If the command is not there, search the
staged corpus under this root:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives
```

Search the files listed in `references/corpus-index.csv`. Confirm a concrete
command line, not only a placeholder form. If the corpus shows a placeholder,
find a concrete example before you write the command.

If you cannot confirm a command, do not write it as a command. State that the
command is unverified and give the next search step.

## 5. Build a safe answer

Every answer holds these parts:

1. State the service and the device role.
2. State the Junos train from the source.
3. State the exact verified command when a command is necessary.
4. State the check command that proves the current state.
5. Give a warning before each risky change.
6. Cite the public URL, the staged corpus path, and the page.
7. Name each unverified claim.

Use documentation sample values only when you identify them as samples. Ask the
operator to replace names, addresses, and AS numbers during their change plan.

## 6. Apply risk rules

MPLS and VPN commands can move production traffic. Treat these actions as risky:

- Change a route distinguisher, route target, VRF import, or VRF export rule.
- Change a PE to CE routing session.
- Change an RSVP LSP path, bandwidth value, or protection statement.
- Change an LDP or RSVP interface under `protocols`.
- Change EVPN multihoming, an ESI, or a VXLAN VNI.
- Delete VPLS or EVPN protocol configuration.

Warning: a wrong MPLS or VPN change can remove reachability for many sites. Use
`commit confirmed 2` on remote changes, and verify the rollback path first.

## 7. Report the evidence

End each answer with an evidence block.

```text
Evidence:
- Junos: <title>, Junos <train>, <public URL> -- <fact or command>.
- Corpus: <relative staged path>, page <n> -- <short proof>.
- Device: <show command> -- <state to verify>.
- Unverified: <claim> -- <missing source or next check>.
```

If no source supports the claim, state that no source supports the claim. Do not
invent a Junos command.
