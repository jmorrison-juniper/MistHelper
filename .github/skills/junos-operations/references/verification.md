# Verification and corpus use

Use this reference to verify a Junos operations answer before you act on it.

## Corpus root

The staged corpus root is:

```text
C:\Users\jmorrison\Downloads\juniper-doc-archives\
```

The index path is relative to that root. Do not cite a path under
`documentation/references/`.

## Source selection rule

1. Open `references/corpus-index.csv`.
2. Select the row that matches the task topic.
3. Open the Markdown file below the staged corpus root.
4. Search for the command or statement.
5. Confirm the train and the command mode.
6. Keep any quote short.
7. Cite the source title and train in the answer.

If no indexed source confirms the command, do not use the command.

## Command confirmation method

The build pass confirmed commands with literal searches against the staged
Markdown corpus. A command counted as confirmed when the source contained the
command, the exact command family, or the Junos hierarchy that produces the set
command.

The pass confirmed 95 commands and command forms. The command tables in this
skill use those forms only.

## Indexed documents

The index contains 14 rows. Thirteen rows come from the 92-row manifest. One
row uses the staged `network-mgmt.md` guide as a supplemental SNMP source
because the manifest lacks a current SNMP operations guide.

The build stopped after these documents covered the subject:

- CLI and configuration mode.
- Commit, rollback, load, rescue, and groups.
- Software install, validation, snapshot, and rollback.
- Monitoring, logs, trace files, and archive commands.
- SNMP communities, traps, views, and read commands.
- NETCONF, XML, REST, OpenConfig, telemetry, scripts, events, and Python.

Release notes were not indexed because user guides covered the day to day
tasks with newer and clearer source text.

## Safety verification

Use this safety path before a production change:

1. Read the current device state with a `show configuration` command.
2. Save or confirm a rescue configuration.
3. Make the smallest candidate change.
4. Run `show | compare`.
5. Run `commit check`.
6. Run `commit confirmed 5 comment "remote safety timer"`.
7. Verify the access path from a second session.
8. Confirm the commit only after verification succeeds.

Warning: do not use a bare `commit` for a remote access change. The command can
remove all remote access and require console access.

Warning: do not start a software upgrade without an approved window. The reboot
interrupts traffic and management access.

## Offline acceptance checks

Run these checks from the repository worktree after you edit the skill:

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-operations\SKILL.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-operations\references\cli-configuration.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-operations\references\software-monitoring.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-operations\references\automation-interfaces.md
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 .github\skills\junos-operations\references\verification.md
```

The CSV index must use LF line endings and these columns:

```text
file,title,topic,train,pages,path
```

Each path must resolve to a real Markdown file below the staged corpus root.

## Known limits

The source set favors user guides over release notes. A platform-specific
release note can still change support for a command. Check the release note
when the platform or train is part of the decision.

SNMP examples use one supplemental staged guide outside the manifest. The
manifest contained many SNMP references but no current SNMP operations guide.

### The CLI command dictionary is absent

The skill indexes the Junos OS CLI User Guide, which explains the CLI modes, the
pipe, the commit, the rollback, and the configuration group. The corpus does not
hold the converted CLI Reference, which is the exhaustive dictionary of every
command and every statement.

The source PDF exists in four trains, at 81 MB for train 23.4 through 95 MB for
train 26.2. The converter reached 22 GB of memory on the smallest copy and did
not finish, so no train converted. Three attempts gave the same result.

| Subject | Source | State |
| - | - | - |
| CLI modes, pipe, commit, rollback, groups | `cli` and `cli-evo` | Indexed |
| Every command and statement, with each option | `cli-reference` | Absent |

Warning: do not state that a command option exists because this skill does not
list it. The skill holds the user guide, not the dictionary. If a task needs the
full option set of a command, read the CLI Reference on the Juniper
documentation site, or run `help reference <command>` on the device.
