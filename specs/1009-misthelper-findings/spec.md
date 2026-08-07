# Feature Specification: Clear the Length Findings in MistHelper.py

**Issue**: #1009
**Status**: In progress

## Problem

`MistHelper.py` scored 77.0, grade C+, with 10 findings. Nine were `STRUCT-LENGTH`, each a
function sitting one to six lines over the 25-line limit. The tenth is `CONV-COMMENTS`, a
whole-file coverage measure.

This issue previously asked to extract "the final 15 candidates" so the analyzer report reduces
to just `menu_actions` and `GlobalImportManager`. That end state is not reachable by that work,
because the file holds 148 module-level functions. The audit on the issue records the arithmetic.

This spec takes the reachable goal instead: clear the findings.

## Requirements

- **FR-001**: Reduce each targeted function to 25 lines or fewer.
- **FR-002**: Split by concern, so each new helper has a name that states what it registers.
- **FR-003**: Preserve behavior exactly, including flag names, defaults, and help text.
- **FR-004**: Keep `MistHelper.py --help` working, which proves the parser still builds.

## Non-goals

- **NG-001**: Do not attempt the `CONV-COMMENTS` finding. It is a whole-file measure needing its
  own mechanical pass.
- **NG-002**: Do not extract functions out of `MistHelper.py`. The file holding 148 functions is
  not itself the defect. The findings are.
- **NG-003**: Do not change any flag spelling or default. The parser surface is a contract.

## Scope delivered in this pass

| Function | Before | Action |
| - | - | - |
| `_add_safety_arguments` | 31 lines | split into destructive-safety and external-call flags |
| `_add_interface_arguments` | 29 lines | split into interface-mode and auth/backend flags |
| `_add_output_format_arguments` | 27 lines | split out the systematic-test flags |
| `_reject_unsupported_flag_variants` | 31 lines | extracted the report-and-exit body |

Five length findings remain, listed on the issue. They sit in the session and login paths rather
than the argument parser, so they carry more behavioral risk and deserve their own pass.

## Success criteria

- **SC-001**: The compliance score rises above 77.0.
- **SC-002**: The four targeted functions no longer appear in the report.
- **SC-003**: Every quality gate passes: ruff, black, mypy.
- **SC-004**: `MistHelper.py --help` still prints usage.
- **SC-005**: The full unit and tools suites pass.
