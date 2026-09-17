---
name: junos-switching
description: >-
  Use when a user asks how to configure, verify, or troubleshoot Junos layer 2
  switching. Use for Ethernet switching, bridge domains, MAC learning, MAC
  limits, VLAN tagging, native VLANs, voice VLANs, private VLANs, trunk ports,
  spanning tree, BPDU protection, link aggregation, LACP, DHCP snooping,
  dynamic ARP inspection, storm control, Q-in-Q, and service provider VLANs.
  Require a staged corpus source before you give a Junos command.
argument-hint: State the platform, Junos train, switching subject, interface, VLAN, and whether this is a live change.
---

# Operate Junos layer 2 switching

Use this skill when a reader needs Junos layer 2 switching help. Start with the
router table, then open one reference file.

This skill does not approve a live change. A live change needs the normal
MistHelper issue, review, change window, and confirmation process.

The verified snapshot date is 2026-09-17. The index holds 9 source documents and
6,094 pages from the staged Juniper corpus. The manifest supplied 4 documents.
This build added 5 more documents after a targeted search of the 26.2 and 25.4
staged corpus trees.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Ethernet switching on EX, QFX, MX, or ACX devices.
- A bridge domain, MAC learning, MAC aging, or a MAC limit.
- A VLAN, a VLAN member, a native VLAN, a trunk port, or a voice VLAN.
- A private VLAN and its primary, community, or isolated VLAN.
- STP, RSTP, MSTP, VSTP, a root bridge, an edge port, or BPDU protection.
- A LAG, an aggregated Ethernet interface, LACP, or a minimum link count.
- DHCP snooping, dynamic ARP inspection, IP source guard, or storm control.
- Q-in-Q, flexible VLAN tagging, stacked VLAN tagging, or VLAN tag rewrite.

Do not use this skill for these requests:

- A live Mist API request. Use `managing-mist-api` for that task.
- A firewall policy that does not depend on layer 2 switching.
- A wireless WLAN design that does not touch a Junos switch.
- Fiber, Observium, Podman, Python speed, or Python parallel work.

## 2. Load the reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose a source and cite it. | [Verification](./references/verification.md) | A source document, a Junos train, and a relative path. |
| Configure a bridge domain, MAC learning, MAC aging, or a MAC limit. | [Bridge and VLAN](./references/bridge-vlan.md) | The task, command, verification command, and citation. |
| Configure a VLAN, trunk port, native VLAN, voice VLAN, or private VLAN. | [Bridge and VLAN](./references/bridge-vlan.md) | The task, command, verification command, warning, and citation. |
| Configure STP, RSTP, MSTP, VSTP, an edge port, or BPDU protection. | [Spanning tree and LAG](./references/stp-lag.md) | The protocol command, verification command, warning, and citation. |
| Configure a LAG, LACP, minimum link count, or load balance behavior. | [Spanning tree and LAG](./references/stp-lag.md) | The interface command, verification command, and citation. |
| Configure port security, DHCP snooping, dynamic ARP inspection, or storm control. | [Port security and Q-in-Q](./references/port-security-qinq.md) | The control command, verification command, warning, and citation. |
| Configure Q-in-Q, service VLANs, tag push, tag pop, or tag swap. | [Port security and Q-in-Q](./references/port-security-qinq.md) | The VLAN tag command, verification command, and citation. |
| Prove this skill or refresh the index. | [Verification](./references/verification.md) | The offline checks and the command evidence rules. |

If two Juniper sources conflict, use this order:

1. The document that matches the device family.
2. The newest Junos train in `references/corpus-index.csv`.
3. A more specific feature guide before a broad user guide.
4. A command example before a concept paragraph.
5. A claim marked unverified only when no source confirms it.

## 3. Search the staged corpus

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
This root is outside the repository. The repository holds no Juniper document.

Use this procedure when the curated reference does not give enough detail.

1. Open `references/corpus-index.csv`.
2. Find the source row for the subject.
3. Join the row path to the corpus root.
4. Open the Markdown file under the corpus root.
5. Search for the exact command or statement.
6. Keep a vendor quote short when a quote is necessary.
7. Name the document, the Junos train, and the page in the answer.

If the corpus root is absent, state that the corpus is absent. Then answer only
from the curated reference files.

## 4. Build the answer

Every answer holds these parts:

1. State the switching subject and the device family.
2. State the Junos train from the source row.
3. State the command or verification command.
4. Cite the source document and page.
5. State each assumption that affects the command.
6. Mark each missing source as unverified.
7. Give a safe verification command before a change command.

Use obvious placeholders in examples. Use `ge-0/0/1`, `ae0`, `vlan10`,
`customer-1`, and `192.0.2.10`. Do not use a real hostname, address, serial
number, or customer name.

## 5. Apply layer 2 safety rules

Read the current device state before you change it. Prefer these commands:

- `show configuration interfaces`
- `show configuration vlans`
- `show vlans`
- `show ethernet-switching table`
- `show bridge mac-table`
- `show spanning-tree interface`
- `show lacp interfaces`

Warning: do not change spanning tree on a production access layer without a
rollback plan. A wrong root, edge, or BPDU setting can create a loop and drop
the access layer.

Warning: do not change the native VLAN on a production trunk without a peer
check. A mismatch can leak untagged traffic into the wrong VLAN and drop hosts.

Warning: do not enable `action-shutdown` storm control without a recovery path.
A traffic burst can disable the interface and interrupt users.

## 6. Report the evidence

End each answer with an evidence block.

```text
Evidence:
- Junos: <title>, train <train>, page <page> -- <command or rule>
- Verify: <show command> -- <device state to confirm>
- Unverified: <claim> -- <missing source or next check>
```

If the user asks for a code change, do not rely on this skill alone. Use the
repository workflow, tests, and review rules before you change code.

