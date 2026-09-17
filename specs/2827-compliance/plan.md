# Implementation Plan: Compliance cleanup for org probes and AP profile migration

## Scope

This plan changes these files only:

- `src/org/org_synthetic_probes_manager.py`
- `src/device/ap_profile_migration_manager.py`
- `tests/unit/org/test_org_synthetic_probes_manager.py` if characterization coverage is needed
- `tests/unit/device/test_ap_profile_migration_manager.py` if characterization coverage is needed
- `specs/2827-compliance/spec.md`
- `specs/2827-compliance/plan.md`
- `specs/2827-compliance/tasks.md`
- `changelog.d/issue-2827-compliance.md`

## Constitution checks

- Five-Item Rule: existing files have grandfathered debt. This change reduces local function-length debt.
- Class-based architecture: new org setting code uses `SyntheticProbeSettingApplier`. AP helper code stays inside `APProfileMigrationManager`.
- Safety: no raw `input()` calls are added.
- Observability: new helper actions log before and after meaningful work.
- Deployment: local validation shards run before the pull request is ready.

## Technical approach

1. Preserve current destructive operation flow.
2. Extract repeated pacing summary logic inside `APProfileMigrationManager`.
3. Extract org setting payload, write, and report logic into `SyntheticProbeSettingApplier`.
4. Preserve all module-level names that string-based tests patch.
5. Re-run analyzer and validation shards.
