# Feature Specification: Compliance Backlog Remediation

**Feature Branch**: `chore/1000-compliance-backlog`
**Updated**: 2026-09-14
**Status**: Active

## Measured truth

The current source tree replaces the stale backlog in issue #1000. The command `rtk python tools/check_compliance.py src/ -r -q` reports `Overall score: 94.5/100  Grade: A`.

`MistHelper.py` remains out of scope for this branch. Another agent owns that hot file, so this work records its debt only as follow-up work.

## Current ranked backlog

| Rank | Violations | Score | Grade | File |
| - | -: | -: | - | - |
| 1 | 90 | 34.0 | F | `src\org\org_synthetic_probes_manager.py` |
| 2 | 52 | 61.0 | D- | `src\device\ap_profile_migration_manager.py` |
| 3 | 46 | 60.0 | D- | `src\utils\zscaler_catalogue.py` |
| 4 | 39 | 60.0 | D- | `src\upgrade_portal\app\routes\upgrade.py` |
| 5 | 34 | 62.0 | D- | `src\upgrade_portal\upgrade\options.py` |
| 6 | 31 | 64.0 | D | `src\firmware\upgrade_service.py` |
| 7 | 28 | 63.0 | D | `src\utils\zscaler_probe.py` |
| 8 | 26 | 70.0 | C- | `src\upgrade_portal\app\wiring.py` |
| 9 | 26 | 75.0 | C | `src\upgrade_portal\compare\service.py` |
| 10 | 25 | 53.0 | F | `src\upgrade_portal\upgrade\driver.py` |

## Scope for this branch

This branch reconciles the stale compliance records and applies one safe mechanical repair. The source change is limited to `src\utils\zscaler_catalogue.py`. The change adds same-line comments only, so it preserves behavior.

## Requirements

- The specification must use the fresh `src/` measurement as the source of truth.
- The old 1008 top-20 list must be marked superseded, because most named files now score A or A+.
- The one source repair must not split functions, change signatures, move code, or edit `MistHelper.py`.
- The remaining structural debt must move to one follow-up issue #2645.
- The pull request body must link issues #1000 and #1003.

## Acceptance criteria

- `src\utils\zscaler_catalogue.py` improves from 60.0 D- to 66.0 D by comment coverage only.
- `tools.symbol_diff` reports `no module-level name changed` for `src\utils\zscaler_catalogue.py`.
- The targeted test selection reports 323 passing tests before and after the source change.
- `analysis.md` records the before and after score table.
- The pull request links one follow-up issue #2645 for the structural refactor of the four low-scoring files.
