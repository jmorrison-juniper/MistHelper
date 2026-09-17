# CLI and configuration operations

Use this reference for command-line access and candidate configuration work.
The primary source is `Junos OS CLI User Guide for Junos OS`, train 26.2.

## Source map

| Source | Train | Use |
| - | - | - |
| `Junos OS CLI User Guide for Junos OS` | 26.2 | CLI modes, shortcuts, pipes, commit, rollback, rescue configuration, groups, and load. |
| `Junos OS Software Installation and Upgrade Guide` | 26.2 | Rollback after an install and rescue configuration during recovery. |
| `Junos XML Management Protocol Developer Guide` | 26.2 | Compare output used by protocol clients. |

## CLI modes

| Task | Command | Mode | Source |
| - | - | - | - |
| Enter configuration mode. | `configure` | Operational | CLI guide 26.2. |
| Enter configuration mode at a hierarchy. | `edit` | Operational | CLI guide 26.2. |
| Leave configuration mode. | `exit configuration-mode` | Configuration | CLI guide 26.2. |
| Run an operational command while editing. | `run show interfaces terse` | Configuration | CLI guide 26.2. |
| Show top-level operational help. | `?` | Operational | CLI guide 26.2. |
| Complete a command or show choices. | `<Space>` or `?` | Both | CLI guide 26.2. |

The prompt tells the mode. The `>` prompt shows operational mode. The `#`
prompt shows configuration mode.

## Keyboard shortcuts

| Need | Shortcut | Source |
| - | - | - |
| Move to the start of the line. | `Ctrl+a` | CLI guide 26.2. |
| Move to the end of the line. | `Ctrl+e` | CLI guide 26.2. |
| Delete from the cursor to the end. | `Ctrl+k` | CLI guide 26.2. |
| Clear the command line. | `Ctrl+u` or `Ctrl+x` | CLI guide 26.2. |
| Search command history in reverse. | `Ctrl+r` | CLI guide 26.2. |
| Redraw the current line. | `Ctrl+l` | CLI guide 26.2. |
| Move back through command history. | `Ctrl+p` | CLI guide 26.2. |
| Move forward through command history. | `Ctrl+n` | CLI guide 26.2. |

A busy engineer usually needs `Ctrl+u` first. It clears a bad command before the
engineer presses Enter.

## Pipes and display forms

| Task | Command | Mode | Source |
| - | - | - | - |
| Match output lines. | `show interfaces terse | match ge-0/0` | Operational | CLI guide 26.2. |
| Exclude output lines. | `show configuration | except inactive` | Configuration | CLI guide 26.2. |
| Show the last lines of output. | `show log messages | last 50` | Operational | CLI guide 26.2. |
| Count output lines. | `show interfaces terse | count` | Operational | CLI guide 26.2. |
| Save output to a file. | `show configuration | save config.txt` | Operational | CLI guide 26.2. |
| Show configuration as set commands. | `show configuration | display set` | Operational | CLI guide 26.2. |
| Compare candidate configuration. | `show | compare` | Configuration | CLI guide 26.2. |
| Compare against a prior revision. | `show | compare rollback 1` | Configuration | CLI guide 26.2. |
| Compare in XML form. | `show | compare | display xml` | Configuration | CLI guide 26.2 and XML guide 26.2. |

Use `display set` when you need commands that rebuild a configuration. Use
`show | compare` before each commit.

## Configuration safety path

| Step | Command | Purpose | Source |
| - | - | - | - |
| Start a candidate change. | `configure` | Open the candidate configuration. | CLI guide 26.2. |
| Review the exact change. | `show | compare` | Show the difference from active configuration. | CLI guide 26.2. |
| Check syntax and references. | `commit check` | Test the candidate without applying it. | CLI guide 26.2. |
| Apply with a timer. | `commit confirmed 5 comment "remote safety timer"` | Roll back automatically if the engineer loses access. | CLI guide 26.2. |
| Confirm after access works. | `commit comment "confirm remote change"` | Make the confirmed commit permanent. | CLI guide 26.2. |
| Cancel the candidate. | `rollback 0` | Return the candidate to the active configuration. | CLI guide 26.2. |
| Revert the last commit. | `rollback 1` | Load the previous committed configuration. | CLI guide 26.2. |
| Commit the reversion. | `commit confirmed 5 comment "rollback safety timer"` | Apply the reversion with a timer. | CLI guide 26.2. |

Warning: use `commit confirmed` for a remote change. A bare `commit` can remove
all remote access, and the recovery can require console access.

## Load and save configuration

| Task | Command | Mode | Source |
| - | - | - | - |
| Merge a file into the candidate. | `load merge filename.conf` | Configuration | CLI guide 26.2. |
| Replace a hierarchy from a file. | `load replace filename.conf` | Configuration | CLI guide 26.2. |
| Override the full candidate. | `load override filename.conf` | Configuration | CLI guide 26.2. |
| Patch the candidate. | `load patch filename.patch` | Configuration | CLI guide 26.2. |
| Load from terminal input. | `load merge terminal` | Configuration | CLI guide 26.2. |
| Save the candidate to a file. | `save candidate.conf` | Configuration | CLI guide 26.2. |
| Save active configuration as set commands. | `show configuration | display set | save rescue-set.conf` | Operational | Install guide 26.2. |

Use `load merge` for normal additions. Use `load replace` only when the file
contains replace markers or a complete hierarchy.

## Rescue configuration

| Task | Command | Mode | Source |
| - | - | - | - |
| Save a rescue configuration. | `request system configuration rescue save` | Operational | CLI guide 26.2 and install guide 26.2. |
| Show the rescue configuration. | `show system configuration rescue` | Operational | CLI guide 26.2. |
| Roll back to the rescue configuration. | `rollback rescue` | Configuration | CLI guide 26.2. |
| Delete the rescue configuration. | `request system configuration rescue delete` | Operational | CLI guide 26.2. |

Save a rescue configuration after the device reaches a known-good state. Do not
wait until a failure starts.

## Configuration groups

| Task | Command | Mode | Source |
| - | - | - | - |
| Create a group statement. | `set groups noc system login message "Authorized access only"` | Configuration | CLI guide 26.2. |
| Apply a group. | `set apply-groups noc` | Configuration | CLI guide 26.2. |
| Apply a group in one hierarchy. | `set system apply-groups noc-system` | Configuration | CLI guide 26.2. |
| Exclude a group in one hierarchy. | `set system apply-groups-except noc-system` | Configuration | CLI guide 26.2. |
| Show inherited configuration. | `show configuration | display inheritance` | Operational | CLI guide 26.2. |
| Show inherited set commands. | `show configuration | display inheritance | display set` | Operational | CLI guide 26.2. |

Use groups for repeated configuration only. Do not hide a one-device exception
inside a group.

## Recovery checklist

1. Run `show system commit` and identify the last known-good commit.
2. Run `configure`.
3. Run `rollback <number>`.
4. Run `show | compare`.
5. Run `commit confirmed 5 comment "recover access"`.
6. Verify access with a new session.
7. Run `commit comment "confirm recovery"`.

Warning: do not close the working session until a second access path works. A
wrong rollback can keep the same access fault.
