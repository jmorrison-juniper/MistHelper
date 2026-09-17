---
name: junos-operations
description: >-
  Use when a user asks for day to day Junos operations on a Juniper device.
  Use for the CLI, configuration mode, commit safety, rollback, load, rescue
  configuration, configuration groups, software install, software upgrade,
  snapshot, log review, trace files, SNMP, telemetry, NETCONF, the Junos XML
  protocol, REST, commit scripts, op scripts, event policies, and Python on
  Junos. Require a cited Junos source and prefer commit confirmed for remote
  changes.
argument-hint: State the platform, Junos train, access method, task, and whether the session is local or remote.
---

# Operate a Junos device

Use this skill for day to day Junos work. The reader starts here, selects one
reference, and then runs the verified command from that reference.

The verified snapshot date is 2026-09-17. The curated set indexes 14 source
documents. Thirteen documents come from the 92-row `junos-operations` manifest.
One supplemental staged corpus guide supplies SNMP command examples because the
manifest does not contain a current SNMP operations guide.

This skill does not authorize a live change. A live change needs the normal
MistHelper issue, review, typed confirmation, and recovery plan.

Warning: use `commit confirmed` for a remote configuration change. A bare
`commit` can remove all remote access. Console access can be necessary to
recover the device.

Warning: a software upgrade reboots the device. The reboot interrupts traffic
and management access until the device returns.

## 1. Decide whether this skill applies

Use this skill for these requests:

- The Junos CLI, operational mode, configuration mode, pipes, and shortcuts.
- Configuration edits, commit checks, commit confirmed, rollback, load, and rescue configuration.
- Software install, upgrade, validation, snapshot, and image rollback.
- Monitoring commands, system logs, trace files, and log archive tasks.
- SNMP communities, traps, views, and read commands.
- Streaming telemetry, OpenConfig, gRPC, and subscription checks.
- NETCONF, the Junos XML protocol, and the REST interface.
- Commit scripts, op scripts, event policies, and Python automation.

Do not use this skill for these requests:

- Mist Cloud API work. Use `managing-mist-api` for that task.
- Device hardening, zeroize, or security control review. Use `hardening-junos` for that task.
- Fiber, Observium, Podman, Python speed, or Python parallel work.
- A live destructive change without human approval.

## 2. Load one reference

Read only the reference that matches the task. Each reference gives a command,
a short purpose, the source document, and the Junos train.

| Task | Reference | Result |
| - | - | - |
| Use the CLI or edit configuration. | [CLI and configuration](./references/cli-configuration.md) | A safe command path from login to commit or rollback. |
| Install software or read device state. | [Software and monitoring](./references/software-monitoring.md) | A validated install, snapshot, rollback, log, trace, or show command. |
| Configure SNMP, telemetry, or programmatic access. | [Automation and interfaces](./references/automation-interfaces.md) | A NETCONF, XML, REST, SNMP, telemetry, or script command. |
| Verify a source or a command. | [Verification](./references/verification.md) | The corpus path, index rule, safety rule, and acceptance result. |
| Select the source document. | [Corpus index](./references/corpus-index.csv) | The file, title, topic, train, page count, and corpus path. |

If two sources conflict, use this order:

1. The newest user guide for the platform and train.
2. The CLI user guide for command mode and syntax behavior.
3. The install guide for software actions.
4. The automation guide for scripts and event policies.
5. Release notes only when no user guide covers the train-specific behavior.

## 3. Answer with evidence

Every answer must contain these parts:

1. State the platform and Junos train when the user gives them.
2. State the exact command or configuration statement.
3. State the source document and train.
4. State whether the command runs in operational mode or configuration mode.
5. Give a `show` command that verifies the result.
6. Add a warning before a command can interrupt traffic or remove access.

Use this evidence block at the end of each answer:

```text
Evidence:
- Source: <title>, <train> -- <command or rule>
- Verify: <show command>
- Gap: <missing platform, missing train, or missing corpus source>
```

If the corpus does not support a command, state that no source supports it. Do
not invent a command.

## 4. Use a safe remote-change pattern

Use this pattern for any remote configuration change:

1. Read the current state with `show configuration <hierarchy>`.
2. Enter configuration mode with `configure`.
3. Make the smallest change.
4. Run `show | compare`.
5. Run `commit check`.
6. Run `commit confirmed 5 comment "remote safety timer"`.
7. Test the new access path.
8. Run `commit comment "confirm remote change"` only after the test succeeds.
9. Run `rollback 1` if the test fails before the timer expires.

Warning: do not use a bare `commit` until the new access path works. A wrong
firewall, login, SSH, SNMP, or routing change can remove all remote access.

## 5. Cite these primary sources

Use these sources first:

- `Junos OS CLI User Guide for Junos OS`, train 26.2.
- `Junos OS Software Installation and Upgrade Guide`, train 26.2.
- `Junos OS Automation Scripting User Guide`, train 22.1.
- `Junos OS NETCONF XML Management Protocol Developer Guide`, train 26.2.
- `Junos XML Management Protocol Developer Guide`, train 26.2.
- `Junos OS REST API Guide`, train 26.2.
- `Junos OS OpenConfig User Guide`, train 26.2.
- `Junos OS Monitoring, Sampling, and Collection Services Interfaces User Guide`, train 26.2.

The source paths live below the staged corpus root:
`C:\Users\jmorrison\Downloads\juniper-doc-archives\`.

Do not cite a path under `documentation/references/`. That directory is absent
from this skill and remains gitignored.

## 6. Use placeholders only

Use these placeholders in examples:

- Hostname: `device.example.invalid`
- Address: `192.0.2.10`
- Community: `REPLACE_COMMUNITY`
- File name: `junos-install.tgz`
- Server: `https://server.example.invalid/path/junos-install.tgz`

Do not put a real credential, address, serial number, customer name, or private
URL in an answer.

## 7. Escalate when the request can cause harm

Stop and require a human change plan for these tasks:

- A software upgrade on a production device.
- A change to SSH, login, routing, firewall filters, or the management instance.
- A commit script or event policy that can change configuration automatically.
- A REST, NETCONF, or XML action that changes configuration.
- A rollback on a device that has unknown local changes.

Warning: an automatic configuration action can repeat a bad change. Disable or
remove the action before you troubleshoot repeated commits.
