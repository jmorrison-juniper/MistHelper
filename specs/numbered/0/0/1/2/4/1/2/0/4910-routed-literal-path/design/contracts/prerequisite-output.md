# Contract: Prerequisite and Setup Output

**Scope**: The output of four commands of the Spec Kit workflow:

- `check-prerequisites.ps1 -Json`, with or without `-IncludeTasks`.
- `check-prerequisites.ps1` in text mode.
- `setup-tasks.ps1 -Json`.
- `setup-tasks.ps1` in text mode.

**Status**: This contract holds before and after the change. The change edits only the probe flags. It adds no field, no order change, and no line text.

## JSON Output of check-prerequisites.ps1

| Field | Type | Rule |
| - | - | - |
| `FEATURE_DIR` | string | The absolute path of the feature folder. |
| `AVAILABLE_DOCS` | array of strings | The optional documents that exist, relative to `FEATURE_DIR`. |

The order of `AVAILABLE_DOCS` is fixed:

1. `design/research.md`
2. `design/data-model.md`
3. `design/contracts`
4. `design/quickstart.md`
5. `tasks.md`, only when the command receives `-IncludeTasks` and the file exists.

## JSON Output of setup-tasks.ps1

| Field | Type | Rule |
| - | - | - |
| `FEATURE_DIR` | string | The absolute path of the feature folder. |
| `AVAILABLE_DOCS` | array of strings | The optional documents that exist, in the order of the table above, without `tasks.md`. |
| `TASKS_TEMPLATE` | string | The absolute path of the tasks template, or an empty string. |
| `TASKS_TEMPLATE_CONTENT` | string | The text of the tasks template. |

## Probe Rules

- A document appears in `AVAILABLE_DOCS` only when its literal probe returns `True`.
- The contracts entry appears only when the `contracts` folder holds at least one child.
- The path separator follows the platform. `GetRelativePath` returns `\` on Windows and `/` on Linux.
- A probe on a path that holds wildcard characters returns the same result as a probe on a plain path.

## Text Output

Each command prints `FEATURE_DIR` and `AVAILABLE_DOCS:`. Then the command prints one line for each optional document:

- `  [OK] research.md` when the document exists. The name is the document name.
- `  [FAIL] research.md` when the document does not exist. The name is the document name.

The names are `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`. `check-prerequisites.ps1` also prints `tasks.md` when `-IncludeTasks` is set.

## Exit Codes and Error Channel

- A successful listing exits with code 0. A missing optional document does not change the exit code.
- Errors print to standard error with `[Console]::Error.WriteLine`. The change keeps this channel.
- The change adds `Write-Verbose` and `Write-Debug` lines. Both streams are silent by default, so standard output does not change.

## Verification

The behavior tests in `tests/guardrails/test_spec_route_contract.py` check the rules above for a bracket folder. The guard in `tests/guardrails/test_routed_core_port.py` checks the probe flags.
