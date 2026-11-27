# Contract: Skip Report for the Two Guardrail Modules

## Identity

- Modules: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` and `tests/guardrails/test_snmp_base_oid_defaults.py`.
- Windows form: Windows 11 with PowerShell 7 and the `.venv` environment.
- Linux form: an Ubuntu host with bash.
- Command: `python -m pytest <browser module> <SNMP module> -rs -q`.

## Windows Form

| Output | Required value |
| - | - |
| Summary counts | `11 passed, 20 skipped`, with no failed case and no error |
| Exit code | 0 |
| Skip reason, browser module | `Needs bash for the Ubuntu mirror script, which Windows cannot run (issue #4877).` |
| Skip reason, SNMP module | `Needs /bin/bash for the start script, which Windows lacks (issue #4877).` |
| Folded lines | One line for each reason. Each line gives the count of cases and the reason. |

The default run folds skip reasons (RC-59 in `design/research.md`). The counts on the folded lines sum to 20.

## Verbose Form

The default `addopts` value uses `-v`. Each skipped case prints `SKIPPED` and its reason (RC-57). The terminal width can trim the reason. Use `-rs` for the full text.

## Linux Form

| Output | Required value |
| - | - |
| Summary | `31 passed` |
| Skipped cases | None |

## Reason Rules

- Use ASCII characters only.
- Name the cause and cite issue #4877.
- Use no contraction and no semicolon.

## Outside This Contract

A shell case that fails on a Windows host is outside this contract. Such a failure is a defect in the change. T-LOCAL-GATES stops until the defect is fixed.
