---
name: junos-routing
description: >-
  Use when a user asks how to configure, verify, or troubleshoot Junos routing
  on MX, EX, QFX, or SRX devices. Use for BGP, OSPF, IS-IS, routing policy,
  route leaking, routing instances, virtual routers, BFD, convergence timers,
  static routes, aggregate routes, generated routes, and next-hop resolution.
  Require a command that the staged Juniper corpus confirms before you give a
  device command.
argument-hint: State the platform, Junos train, routing protocol, policy goal, routing instance, and whether you need configuration or verification.
---

# Configure and verify Junos routing

Use this skill for Junos routing work on MX, EX, QFX, and SRX devices. It routes
an agent to a short reference before the agent gives a command.

This skill does not authorize a live change. A live change needs the normal
MistHelper issue, review, approval, and change window process.

The verified snapshot date is 2026-09-17. The source corpus has 7 documents and
7,570 pages. All source rows use Junos train 26.2.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Build or verify a BGP session, address family, route reflector, community, or damping rule.
- Build or verify an OSPF area, interface, metric, authentication rule, or adjacency.
- Build or verify an IS-IS level, interface, metric, authentication rule, or adjacency.
- Write a routing policy with terms, match conditions, actions, import, or export.
- Build or verify a routing instance, a virtual router, a VRF, or route leaking.
- Tune BFD, OSPF timers, IS-IS timers, or BGP session behavior for convergence.
- Configure static routes, aggregate routes, generated routes, or next-hop resolution.
- Confirm a `set` or `show` command before a change.

Do not use this skill for these requests:

- A Mist cloud operation. Use `managing-mist-api` for that task.
- A device hardening rule without a routing change. Use `hardening-junos` for that task.
- A Python speed change. Use `optimizing-python` for that task.
- Fiber, Observium, or Podman work.

Warning: a routing change can drop a session or black-hole traffic. Verify the
current route table and the peer state before you commit a change.

## 2. Load the one reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| BGP, OSPF, IS-IS, BFD, timers, static routes, aggregate routes, generated routes, or next-hop resolution. | [Protocols and routes](./references/protocols.md) | A protocol procedure with a verified command. |
| Routing policy, import policy, export policy, communities, path preference, damping, or route recipes. | [Routing policy](./references/policy.md) | A policy term or chain with a verified command. |
| Routing instances, virtual routers, VRFs, or route leaking. | [Routing instances](./references/instances.md) | An instance or route leaking procedure with a verified command. |
| Source selection, command confirmation, corpus refresh, or gap reporting. | [Verification](./references/verification.md) | A source, train, page, and command check. |
| Source row lookup. | [Corpus index](./references/corpus-index.csv) | A file, title, topic, train, page count, and corpus path. |

If two sources conflict, use this order:

1. The current device configuration and operational state.
2. The newest staged Junos guide for the device train.
3. The command that the staged corpus confirms exactly.
4. Older notes, marked as unverified.

## 3. Confirm a command before you answer

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
This root is outside the repository. The repository holds no Juniper document.

Use this procedure for each command:

1. Read [Corpus index](./references/corpus-index.csv).
2. Select the document that matches the protocol or policy topic.
3. Open the Markdown file below the corpus root.
4. Search for the exact command string.
5. If the command has an angle bracket placeholder, find a concrete example.
6. Record the source title, train, URL, staged path, and page number.
7. If the command is absent, do not give the command.

Caution: a command shape in memory is not evidence. Give only a command that the
staged corpus confirms.

## 4. Build the answer

Every routing answer holds these parts:

1. State the platform and the Junos train.
2. State the protocol, policy, or routing instance scope.
3. Give only the smallest verified command set.
4. Put warnings before disruptive commands.
5. Give a verification command and the expected state.
6. Cite the public Juniper URL before the staged corpus path.
7. Mark each missing source as unverified.

Use documentation addresses only when the corpus uses them. Otherwise use
`192.0.2.0/24`, `198.51.100.0/24`, and `203.0.113.0/24` in explanations.
Never use a customer hostname, address, credential, or serial number.

## 5. Use safe routing change rules

Apply these rules to every answer:

- Read the current configuration before you change it.
- Read the current route table before you change import, export, or leaking.
- Change one neighbor, one interface, or one policy term at a time.
- Prefer a candidate configuration and a confirmed commit window.
- Keep a rollback plan for every policy or route leaking change.
- Verify the route table, neighbor state, and forwarding table after the commit.
- Do not log secrets from authentication keys or key chains.

Warning: do not paste a policy that changes an export term to a production peer
without review. The peer can receive or lose routes immediately.

## 6. Cite sources

Use this citation form in the answer:

```text
Source: <title>, Junos train 26.2, https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip, staged path <path>, page <page>.
```

Do not cite a path under `documentation/references/`. That directory does not
exist for a reader who clones the repository.

## 7. Report evidence

End each answer with an evidence block.

```text
Evidence:
- Junos: <title>, train 26.2, <URL>, staged path <path>, page <page> -- <rule>.
- Device check: <show command> -- <state that proves the result>.
- Unverified: <claim> -- <missing source or next check>.
```
