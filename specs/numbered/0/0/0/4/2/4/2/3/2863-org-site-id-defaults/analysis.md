# Specification Analysis Report: Organization and site identifier defaults

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, the contracts, and the remote code state on main revision `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only review. The review compared each claim in the issue, the pull requests, the preserved branches, and the legacy record with the remote main tree. No test or scan ran. Each finding cites its evidence in `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Inconsistency | HIGH | Issue comments of 2026-10-01 | The reserved paths `src/api/tenant_fetch.py`, `specs/2863-tenant-identifier-slice/*`, and `src/websocket/service_ping_discovery.py` no longer match the main tree (RC-28, RC-48, RC-51). | Post a new reservation comment with current paths before any source edit (D-12). |
| A2 | Defect in legacy plan | HIGH | Legacy `plan.md` line 19 and `quickstart.md` line 15 | The legacy record names Python 3.13. The repository requires Python 3.15 (RC-11, RC-06). | Validate on Python 3.15.2 (D-13). |
| A3 | Defect in legacy record | HIGH | Legacy record folder `specs/2863-tenant-identifier-slice/` | A new direct child of `specs/` violates the managed-root rule (RC-48, `constitution.md:57-58`). | Use the numbered route for this record (D-14 context and `plan.md`). |
| A4 | Defect in legacy quickstart | MEDIUM | Legacy `quickstart.md` lines 49-55 | Two focused test paths do not exist on main (RC-49, RC-50). | Use `tests/unit/marvis/standalone/mist/access/api/` paths. |
| A5 | Stale claim | MEDIUM | Legacy `plan.md` lines 42 and 49 | The legacy plan says `src/api/` holds seven direct files. Main holds eight children in `src/mist/access/api/` (RC-36). | Record the folder debt in the plan (Complexity Tracking). |
| A6 | Defect in legacy record | LOW | Legacy `spec.md` line 4 | The branch name `jmorrison-juniper-tenant-identifier-validation` does not match `<type>/<issue>-<slug>` (RC-02). | Use `fix/2863-tenant-identifier-validation`. |
| A7 | Gate gap | MEDIUM | Legacy `quickstart.md` lines 176-177 | The legacy STE result is partial because the dictionary is unavailable. The gate needs a score of 80 or more. | Rerun the STE gate with the full dictionary before T-LOCAL-GATES. Unresolved in this environment. |
| A8 | Unverified result | MEDIUM | Legacy `quickstart.md` lines 63-72 | The legacy record reports 309 focused tests and 98.31 percent coverage. These came from a prior run (research, Unverified). | Rerun T-LOCAL-GATES. Do not copy these figures. |
| A9 | Stale claim | HIGH | Issue comment of 2026-10-06 | The manifest line `wiring.py:747` does not match main. Line 747 is a `try` statement. The organization default is at line 1309 (RC-73, RC-74). | Regenerate the manifest at the implementation revision (D-9). |
| A10 | Stale claim | HIGH | Issue comment of 2026-10-06 | The comment names menu 159 as the SSID workflow. Menu 159 is "Bounce port" (RC-58). The SSID workflow is menu 145 (RC-59, RC-60). | Batch 3 uses menu 145. |
| A11 | Stale claim | HIGH | Issue comment of 2026-10-06 | The comment says reboot and virtual chassis paths are outside the destructive set. The registry lists menus 158, 161, and 162 as destructive (RC-61, RC-62, RC-64). | Batch 4 requires human review (D-11). |
| A12 | Stale claim | MEDIUM | Issue comment of 2026-10-06 | The comment names open pull request #3997 as an overlap for `org_cascade/walk.py`. PR #3997 merged at 2026-10-06 22:54:03 UTC. Seven open pull requests showed no overlap on 2026-11-26. | No action. Recheck overlap before each edit. |
| A13 | Stale path | MEDIUM | PR #3035 files | PR #3035 changed `src/device/virtual_chassis.py` and `src/device/device_reboot_manager.py`. Main holds these files under `src/mist/resources/device/` (RC-72). | Use current paths in every task. |
| A14 | Stale branch | HIGH | Branch `jmorrison-juniper-fix-2863-identifier-defaults-batch-1` at commit `6eec0e4` | The branch is 398 commits behind main. It changes six upgrade portal modules, including `org_cascade/walk.py`, which PR #3997 changed (RC-57). | Do not push it. Re-derive batch 5 from main. Keep the branch until a replacement merges (`AGENTS.md:271-276`). |
| A15 | Stale branch | MEDIUM | Branch `recovery/2863-handoff-20261004` at commit `188956f` | The branch is 531 commits behind main. It holds the tenant slice in the old module path (RC-47, RC-56). | Keep the branch. Port its content into batch 1. |
| A16 | Counting conflict | MEDIUM | Issue comments and pull request bodies | Counts of 102, 110 (38 files), 145, and 76 use different rules and revisions (research, Unverified). The inventory section holds 2749 rows (RC-17). | Batch 2 records its own count at the implementation revision (D-9, FR-014). |
| A17 | Rule gap | MEDIUM | `MistHelper.py:3615` | The organization default `or ""` is not in the 2026-10-06 manifest (RC-75). | Batch 2 counts the `or ""` form (D-10). |
| A18 | Structural blocker | HIGH | `tests/guardrails/` and `.github/` | `tests/guardrails/` holds 79 children (RC-38). `.github/` holds 14 children (RC-39). The constitution forbids a new direct child in either folder. | Batch 2 waits for a remediation issue (D-14). |
| A19 | Process gap | LOW | Changelog fragment name | The fragment name uses the issue number. The rule names `pr-<number>.md` after a pull request exists (RC-08). | Rename the fragment in T-PR. |
| A20 | Label gap | LOW | Issue labels | The issue has `backend` and `src`. The constitution's scope set does not list these labels (RC-12). | The orchestrator decides the label change. This record changes no label. |
| A21 | Ownership unclear | MEDIUM | `tests/test_virtual_chassis.py` and `tests/unit/test_virtual_chassis.py` | Both files exist on main (RC-80, RC-81). PR #4358 merged on 2026-11-13. The 2026-11-10 comment described a rename that PR #4358 would make. | Confirm the canonical file before T010. |
| A22 | Validator gap | LOW | `ValidationUtils.validate_site_id` | The function accepts non-string values (RC-54). | Batch 1 uses its own validator (D-5). |
| A23 | Return contract | LOW | `virtual_chassis.py:583-586` | The chassis helper returns `False` and prints a message for a blank site. The failure is visible, but it is a soft failure. | Keep the return contract in T010. |
| A24 | Classification question | MEDIUM | Registry entry for menu 145 (RC-60) | Menu 145 writes site variables through `updateSiteInfo`. The registry category is `interactive`, and the skip reason says "write-capable phases". | This record keeps the category. The owner can reclassify the menu later. Unresolved. |
| A25 | Process note | LOW | `META_DIR` | The shared metadata folder holds 311 items. This record adds two files and no folder. | No action in this record. |
| A26 | Brief conflict | MEDIUM | Pull request body rule | The orchestrator template asks for `Closes #2863` in T-PR. The owner states `Part of #2863` for the first batch (2026-10-01 and 2026-10-21). | Use the owner wording for batch 1 (D-7). The orchestrator confirms the wording at T-PR. |

## Coverage Summary

| Requirement | Tasks | Planned test | Notes |
|-------------|-------|--------------|-------|
| FR-001 | T001, T002 | `test_required_identifier_refused_before_sdk` | |
| FR-002 | T001, T002 | `test_required_identifier_refused_before_sdk` | Site case. |
| FR-003 | T003 | `test_none_site_keeps_organization_only` | |
| FR-004 | T001, T002 | `test_optional_site_invalid_refused_before_org_sdk` | |
| FR-005 | T001, T002 | `test_refusal_names_field_without_value` | |
| FR-006 | T001, T002 | `test_refusal_logs_field_only` | |
| FR-007 | T003 | `test_valid_opaque_identifiers_reach_sdk_unchanged` | |
| FR-008 | T003 | `test_union_results_stay_sorted_and_unique` | |
| FR-009 | T004 | `test_cloud_failures_keep_empty_contract` | Existing tests run unchanged. |
| FR-010 | T004 | `test_resolver_runtime_error_propagates` | |
| FR-011 | T005 | `test_discovery_surfaces_refusal_as_error` | |
| FR-012 | T-LOCAL-GATES step 14 | Structure check command | Structural check, not a test. |
| FR-013 | T006 | `tests/guardrails/test_changelog_fragment_policy.py` (existing) | |
| FR-014 | T007 | `test_guard_rejects_zero_file_and_zero_parse_scope` | Blocked. |
| FR-015 | T007, T008 | `test_guard_fails_on_new_masking_default`, `test_guard_rejects_malformed_or_wrong_baseline` | Blocked. |
| FR-016 | T009, T010, T011 | `test_ssid_empty_site_refused_before_write`, `test_chassis_convert_missing_site_refused_before_sdk`, `test_reboot_missing_site_refused_before_sdk` | Batches 3 and 4. |

## Unresolved Items

- The menu-to-function trace for menus 158, 161, and 162 is not traced in this record (Unverified).
- The canonical chassis test file is not confirmed (A21).
- The guard folder needs a remediation issue (A18, D-14). The orchestrator opens that issue. This record does not open it.
- The STE gate needs the licensed dictionary (A7).
- The count rule for batch 2 is not fixed until batch 2 runs (A16, D-9).
- The classification of menu 145 is an owner question (A24).
