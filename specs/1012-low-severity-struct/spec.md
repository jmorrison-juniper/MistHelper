# Feature Specification: Clear the Last Two Low-Severity STRUCT Violations

**Issue**: #1012
**Status**: In progress

## Problem

The compliance analyzer grades `MistHelper.py` at 75.0, which is a C. It reports 15 violations:
1 High, 12 Medium, and 2 Low.

This issue tracks the Low tier. The recorded baseline was 184 Low violations, made of 116
STRUCT-COMPLEXITY at CC 6 to 9 and 68 STRUCT-BLOCKS at 6 to 11 logical blocks. Two remain.

| Line | Rule | Symbol | Measured | Target |
| - | - | - | - | - |
| 2672 | STRUCT-COMPLEXITY | `_preflight_verify_credentials` | CC 9 | 5 |
| 5163 | STRUCT-COMPLEXITY | `_establish_mist_session` | CC 6 | 5 |

Both functions also breach the Medium STRUCT-LENGTH rule, at 33 and 37 lines against a limit of
25. One decomposition clears both findings per function.

## Requirements

- **FR-001**: Reduce `_preflight_verify_credentials` to CC 5 or lower and 25 lines or fewer.
- **FR-002**: Reduce `_establish_mist_session` to CC 5 or lower and 25 lines or fewer.
- **FR-003**: Extract cohesive helpers with names that state what they do.
- **FR-004**: Preserve behavior exactly, including every log message, exit code, and branch.
- **FR-005**: Carry the existing inline comments onto the lines they explain.

## Non-goals

- **NG-001**: Do not address the High STRUCT-PARAMS finding. It is a false positive on a
  `requests` adapter override, recorded in #1800.
- **NG-002**: Do not address the CONV-COMMENTS coverage finding.
- **NG-003**: Do not change any caller of either function.

## Success criteria

- **SC-001**: The analyzer reports 0 Low-severity violations for `MistHelper.py`.
- **SC-002**: The compliance score rises above 75.0.
- **SC-003**: Every quality gate passes: ruff, black, mypy, radon, vulture, pytest.
- **SC-004**: The credential preflight and session tests pass without modification.
- **SC-005**: `python MistHelper.py --help` still succeeds, proving import-time health.
