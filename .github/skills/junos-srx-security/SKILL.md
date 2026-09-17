---
name: junos-srx-security
description: >-
  Use when a user asks how to configure, audit, verify, or troubleshoot an SRX
  Series firewall or the management tools that control SRX security. Use for
  security zones, host inbound traffic, security policy, global policy, unified
  policy, NAT, proxy ARP, screens, ALG, application identification, UTM, IDP,
  Security Intelligence, IPsec VPN, Security Director, Policy Enforcer,
  sessions, flow, and packet path checks. Require a cited Juniper source and a
  verified command before you give a production command.
argument-hint: State the SRX model, Junos release, feature, traffic direction, and whether the request is a read or a change.
---

# Operate SRX security features

Use this skill for SRX firewall configuration, review, and troubleshooting. Start here, then open exactly one reference file that matches the task.

This skill does not approve a live device change. A live change still needs the normal MistHelper issue, review, typed confirmation, and maintenance window.

The verified snapshot date is 2026-09-17. The skill indexes 12 staged source documents and confirms 79 commands or command families from the corpus.

## 1. Decide whether this skill applies

Use this skill for these SRX tasks:

- Bind a logical interface to a security zone.
- Configure the host inbound traffic rule for system services or protocols.
- Configure a security policy match, action, or order.
- Configure a global policy or a unified policy with an application identifier.
- Configure source NAT, destination NAT, static NAT, or proxy ARP.
- Configure a screen for a flood, a scan, or a malformed packet.
- Configure an application layer gateway or application identification.
- Configure UTM, intrusion prevention, or a security intelligence feed.
- Configure an IPsec VPN proposal, policy, gateway, VPN, or tunnel interface.
- Use Security Director or Policy Enforcer for policy at scale.
- Read the session table, the flow state, or the packet path.

Do not use this skill for these tasks:

- Mist API inventory, site, or WLAN work. Use `managing-mist-api`.
- Generic Junos switch hardening. Use `hardening-junos`.
- Python speed work. Use `optimizing-python`.
- Fiber, Observium, or Podman work.

Warning: a wrong SRX policy, zone, or NAT change can drop traffic or expose a service. Use `commit confirmed` for a remote change so Junos rolls back the candidate configuration if access fails.

## 2. Load the one reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose the source and cite it. | [Verification](./references/verification.md) | The source document, release, path, and validation rule. |
| Configure a zone, an interface binding, host inbound traffic, a policy, policy order, global policy, or unified policy. | [Zones and policies](./references/zones-policies.md) | A safe command sequence and a verification command. |
| Configure NAT, proxy ARP, a screen, ALG, application identification, UTM, IDP, or security intelligence. | [NAT and threat services](./references/nat-threat-services.md) | A safe command sequence and a verification command. |
| Configure IPsec, use Security Director or Policy Enforcer, or inspect sessions and packet path. | [VPN, management, and flow](./references/vpn-management-flow.md) | A safe command sequence and a verification command. |
| Verify the corpus, the index, the command list, or the writing score. | [Verification](./references/verification.md) | Acceptance checks and known limits. |

If two sources conflict, use this order:

1. The current device state from `show configuration` or operational `show` commands.
2. The Junos guide for the device feature.
3. The Security Director or Policy Enforcer guide for management tasks.
4. The staged corpus index.
5. A release note, marked as lower confidence.

## 3. Build a safe answer

Every SRX answer must include these parts:

1. State the feature and the traffic direction.
2. State whether the request reads state or changes state.
3. Name the source document and release from `references/corpus-index.csv`.
4. Give the command from the matching reference file.
5. Give the verification command that proves the device state.
6. Warn before a policy, zone, NAT, VPN, or threat service change.
7. Use `commit confirmed` when the change can remove remote access.

Use obvious placeholders in examples. Use `192.0.2.10`, `198.51.100.10`, `203.0.113.10`, `ge-0/0/0.0`, `st0.0`, `REPLACE_WITH_SECRET`, and `device.example.invalid`. Do not use a real hostname, credential, serial number, address, or customer name.

## 4. Search the staged corpus only when needed

The corpus root is outside the repository.

```powershell
$env:JUNIPER_CORPUS_ROOT = 'C:\Users\jmorrison\Downloads\juniper-doc-archives'
```

Use this procedure when the curated reference does not contain the needed detail.

1. Open `references/corpus-index.csv`.
2. Select the newest row that matches the feature.
3. Join the `path` value to the corpus root.
4. Open the Markdown file under `markdown2\`.
5. Find the command or the statement in the source file.
6. Quote at most one short phrase.
7. Cite the document title and release from the index.
8. If the command is absent, state that the corpus did not confirm the command.

Do not cite a path under an ignored vendor directory. Cite the document title, release, and relative corpus path only.

## 5. Treat SRX changes as hazardous

Warning: a policy change can permit traffic that the operator intended to deny. Read the current policy order before you change a policy.

Warning: a zone or host inbound traffic change can remove management access. Test a second access path and use `commit confirmed` before you commit remotely.

Warning: a NAT or proxy ARP change can send traffic to the wrong host. Confirm the translated address and the egress interface before you commit.

Warning: a VPN change can interrupt protected traffic. Confirm the peer, the proposal, and the tunnel interface before you commit.

Warning: a UTM, IDP, ALG, screen, or feed change can drop valid sessions. Test the matched application and read the logs before you commit.

## 6. Answer by task type

For a read-only question, give the `show` command first. Then state what each field proves.

For a configuration question, give this order:

1. Read the current state.
2. Enter configuration mode.
3. Apply the smallest needed `set` command sequence.
4. Run `show | compare`.
5. Run `commit confirmed` for a remote change.
6. Test the traffic.
7. Run `commit` only after the test succeeds.

For a troubleshooting question, give this order:

1. Verify the zone and interface binding.
2. Verify host inbound traffic for traffic to the SRX.
3. Verify the route and the NAT rule.
4. Verify the policy match and order.
5. Verify the session table.
6. Verify the service log or counter.

## 7. Report evidence

End each answer with this evidence block.

```text
Evidence:
- SRX source: <title>, <release> -- <rule or command>
- Device read: <show command> -- <state it confirms>
- Safety: <warning or recovery command>
- Unverified: <claim> -- <missing source or next check>
```

Do not state a production command if no source confirms it. Say that the command is not confirmed by the staged corpus.
