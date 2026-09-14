# Implementation Plan: Compliance Backlog Remediation

**Branch**: `chore/1000-compliance-backlog`
**Date**: 2026-09-14

## Summary

Use the fresh compliance measurement instead of the stale issue text. Reconcile both specification directories. Make only one low-risk source change in `src\utils\zscaler_catalogue.py`.

## Ordered remediation approach

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

## This pull request

1. Update the 1009 records with the measured backlog.
2. Mark the 1008 plan superseded and show the stale evidence.
3. Add same-line explanatory comments to executable lines in `src\utils\zscaler_catalogue.py`.
4. Keep all structural violations as follow-up work.
5. Add one release-note fragment.

## Out of scope

- Do not edit `MistHelper.py`.
- Do not split long functions in this pass.
- Do not change a function signature.
- Do not move code between modules.
- Do not change control flow.
