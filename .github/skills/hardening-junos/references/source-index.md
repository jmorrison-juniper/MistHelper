# Source index

Use this index to choose a source before you answer. Name the source document
and the Junos train in each answer.

## Existing skill check

No `hardening-junos`, Junos security, or Junos hardening skill existed in the
current `.github/skills/` folder on the `origin/main` worktree. The current
session skill list also had no Junos hardening skill. The repository does have
security text and Mist API safety rules, so this change adds one new skill and
links those rules instead of copying them.

`documentation/foa` and `documentation/color-codes` are for fiber practice and
color codes. They do not cover Junos hardening.

## Indexed sources

| ID | Title | Train or version | Path or URL | Use |
| - | - | - | - | - |
| R1 | MistHelper security and safety | Repository source | `documentation/security.md` | General security rules. |
| R2 | Global coding standards | Repository source | `.github/instructions/coding-standards.instructions.md` | Secret logging and suppression policy. |
| R3 | MistHelper instructions | Repository source | `.github/copilot-instructions.md` | `.env`, SSH, and destructive-review rules. |
| R4 | Operation registry | Repository source | `src/utils/operation_registry.py` | Current destructive menu classification. |
| R5 | ZTP password renderer | Repository source | `src/device/_utility_commands_action.py` | One-time ZTP password display rule. |
| R6 | SSH runner manager | Repository source | `src/ssh/ssh_runner_manager.py` | SSH credential collection and plan display. |
| R7 | Container SSH configuration | Repository source | `Dockerfile` | Port 2200 and `ForceCommand` behavior. |
| J1 | `root-authentication` statement | Introduced before Junos OS Release 7.4 | https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/root-authentication-edit-system.html | Root authentication methods. |
| J2 | `request system zeroize` command | Introduced before Junos OS Release 9.0 | https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/request-system-zeroize.html | Device reset and data removal behavior. |
| J3 | Local Junos command help | Repository source | `documentation/Junos show_command_help.json` | Local command-name check only. |

## Source rules

Use repository sources for MistHelper behavior. Use Juniper sources for Junos
command effects. Use the local command help only to confirm that a command name
exists in the staged command-help data.

Do not cite the converted corpus as complete. The issue says the full corpus is
outside the repository. This skill keeps a small source index and marks missing
corpus details as unverified.
