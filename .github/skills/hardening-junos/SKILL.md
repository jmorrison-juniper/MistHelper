---
name: hardening-junos
description: >-
  Use when a user asks how to harden, secure, reset, enroll, or audit a Junos
  device that MistHelper can touch. Use for credentials, SSH access, ZTP,
  zeroize, generated configuration commands, device registration, destructive
  operations, secret logging, hardening checklists, and DISA STIG rules.
  Require repository evidence first, then Junos documentation for each device
  command or statement.
argument-hint: State the device family, Junos train, MistHelper path, and the control or action under review.
---

# Harden a Junos device through MistHelper

Use this skill when MistHelper touches a Junos device or gives device security
advice. Start with the repository rule, then cite the Junos source.

This skill does not authorize a live change. A live change needs the normal
MistHelper issue, branch, review, and confirmation process.

The verified snapshot date is 2026-09-16. The skill holds 67 baseline controls
and 181 DISA STIG rules. These counts describe the staged documents. They do not
describe the current Juniper site.

## 1. Decide whether this skill applies

Use this skill for these requests:

- A MistHelper SSH path to an EX, QFX, SRX, MX, or SSR device.
- A ZTP password, registration command, or generated configuration command.
- A Junos command that can erase data, reset a device, or change access.
- A rule about secret storage, secret logging, or operator display.
- A review of a MistHelper change that affects Junos device security.
- A hardening control from the Juniper checklist.
- A DISA STIG rule for an EX switch.

Do not use this skill for these requests:

- A firewall policy design that does not use a MistHelper path.
- A live Mist API request. Use `managing-mist-api` for that task.
- A Python speed change. Use `optimizing-python` for that task.
- Fiber, Observium, or Podman work.

## 2. Load the reference that matches the task

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose the source and cite it. | [Source index](./references/source-index.md) | A source, a train, and a path. |
| Apply repository security law. | [Repository decisions](./references/repository-decisions.md) | A safe MistHelper answer. |
| Check Junos commands and statements. | [Junos verified rules](./references/junos-verified-rules.md) | A command or statement with a source. |
| Apply a hardening control from the checklist. | [Baseline controls](./references/baseline-controls.md) | The control, the command, the reason, the risk, and the citation. |
| Review a configuration against the 67 controls. | [Baseline controls](./references/baseline-controls.md) | A pass, fail, or not-assessable result for each control. |
| Answer a DISA STIG question, or map a failure to a rule. | [STIG rules](./references/stig-rules.md) | The rule identifier, severity, check, and fix. |
| Search or refresh the staged corpus. | [Corpus operations](./references/corpus-operations.md) | The corpus root, archive code, gap status, and rebuild procedure. |
| Report gaps and validation. | [Validation and gaps](./references/validation-and-gaps.md) and [Verification](./references/verification.md) | A verified or unverified claim list. |

If two sources conflict, use this order:

1. The current repository code for what MistHelper does.
2. The repository security decision record for accepted risk.
3. Current Juniper documentation for Junos commands and statements.
4. The local Junos command help file for a command name check.
5. Issue text or prior notes, marked as unverified until a source confirms them.

## 3. Search the staged corpus

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
This root is outside the repository. The repository holds no Juniper document.

Use this procedure when the curated reference does not give enough detail.

1. Read [Corpus operations](./references/corpus-operations.md) and find the archive code.
2. Search the security subset first.
3. Search the full unique set only when the first search fails.
4. Open the document below the corpus root.
5. Quote the source statement. Keep the quote short.
6. Name the document, the Junos train, and the source location in the answer.

If the corpus root is absent, state that the corpus is absent. Then give the
rebuild procedure from [Corpus operations](./references/corpus-operations.md).
Continue to answer from the curated reference files.

## 4. Build the answer

Every answer holds these parts:

1. State the MistHelper path that the answer affects.
2. State the Junos command, statement, control, or device action.
3. Name the Junos train or release note from the source.
4. Cite the repository file and line for each MistHelper rule.
5. Cite the Juniper page for each Junos rule.
6. Mark each missing source as unverified.
7. Give the evidence command that proves the device state.

Use obvious placeholders in examples. Use `device.example.invalid`,
`192.0.2.10`, and `REPLACE_WITH_TOKEN`. Do not use a real hostname, address,
credential, serial number, or customer name.

## 5. Apply the MistHelper safety rules

These rules are repository law.

- Never log a token, password, or private key.
- Keep tokens in `.env` or in the operator's secure secret store.
- Never commit `.env`, `.env.*`, or a copied credential file.
- Use typed confirmation before a destructive operation.
- Keep log output in ASCII.
- Fix a security finding at its cause.
- Use `#nosec` only for a verified false positive with a written reason.

Warning: a wrong hardening step can lock the operator out of a production
device. Do not give the step unless a cited source verifies it.

## 6. Handle destructive actions

Treat zeroize, reboot, firmware upgrade, port bounce, configuration push, and
bulk device movement as destructive until the current registry proves otherwise.

Warning: a destructive action can erase configuration or interrupt traffic.
Require an explicit typed confirmation and a recovery plan before execution.

For `request system zeroize`, the Juniper source says the command removes
configuration and key values, removes user-created files, reboots the device,
and restores the factory default configuration. Treat that command as
irreversible unless the change plan proves a supported recovery path.

## 7. Report the evidence

End each answer with an evidence block.

```text
Evidence:
- MistHelper: <file>:<line> -- <rule or behavior>
- Junos: <title>, <train>, <URL> -- <rule or behavior>
- Unverified: <claim> -- <missing source or next check>
```

If the user asks for a change, do not rely on this skill alone. Use the
repository workflow, tests, and human review rules before you change code.
