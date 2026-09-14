# Compliance Backlog Analysis

**Date**: 2026-09-14

## Overall score

| Measurement | Score | Grade |
| - | -: | - |
| Before | 94.5 | A |
| After | 94.5 | A |

The overall score did not move after rounding, because this pull request changes one file in a large source tree.

## Four low-scoring files

| File | Before | After | Status |
| - | -: | -: | - |
| `src\org\org_synthetic_probes_manager.py` | 34.0 F | 34.0 F | Deferred to follow-up. |
| `src\device\ap_profile_migration_manager.py` | 61.0 D- | 61.0 D- | Deferred to follow-up. |
| `src\utils\zscaler_catalogue.py` | 60.0 D- | 66.0 D | Comment coverage repaired. |
| `src\utils\zscaler_probe.py` | 63.0 D | 63.0 D | Deferred to follow-up. |

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

## Safety proof

- Before tests: 323 passed.
- After tests: 323 passed.
- Symbol check: `symbol_diff: no module-level name changed`.
- `MistHelper.py` was deliberately excluded because another agent owns the hot-file lock.
