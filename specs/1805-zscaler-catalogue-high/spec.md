# Feature Specification: Clear the Structural High-Severity Violations in zscaler_catalogue.py

**Issue**: #1000 (compliance backlog)
**Status**: In progress

## Problem

`src/utils/zscaler_catalogue.py` scored 59.0, grade F, the second-worst file in the repository.
It carried 47 violations, four of them high severity:

| Line | Rule | Symbol | Detail |
| - | - | - | - |
| 22 | CONV-COMMENTS | file | inline-comment coverage 1.8 percent |
| 454 | STRUCT-LENGTH | `_merge_observations_into_cenr` | 67 lines against a limit of 25 |
| 871 | STRUCT-PARAMS | `_absorb_city_records` | 6 parameters against a limit of 5 |
| 934 | STRUCT-LENGTH | `merge_clouds` | 68 lines against a limit of 25 |

## Requirements

- **FR-001**: Reduce `_merge_observations_into_cenr` to 25 lines or fewer of body.
- **FR-002**: Reduce `_absorb_city_records` to 5 parameters or fewer.
- **FR-003**: Reduce `merge_clouds` to 25 lines or fewer of body.
- **FR-004**: Raise the inline-comment coverage above its 1.8 percent starting point.
- **FR-005**: Preserve behavior exactly, including the on-disk document shape.

## Non-goals

- **NG-001**: Do not attempt full inline-comment coverage. See the note below.
- **NG-002**: Do not change the CENR schema or the cache TTL, which the module docstring
  records as locked design decisions.
- **NG-003**: Do not touch the 25 medium STRUCT-LENGTH findings in this pass.

## Why full comment coverage is out of scope

`CONV-COMMENTS` is a whole-file measure. The file is 1321 lines and started at 1.8 percent
coverage. Clearing that rule means writing a comment on roughly 1000 lines, which is a
mechanical pass of its own and would bury the three structural changes in an unreviewable diff.

This spec raises coverage as a side effect of the work it does, and leaves the rest to a
dedicated pass.

## Success criteria

- **SC-001**: All three structural high-severity violations are gone.
- **SC-002**: The compliance score rises above 59.0.
- **SC-003**: Every quality gate passes: ruff, black, mypy.
- **SC-004**: The zscaler and CENR tests pass without modification.
