# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 11:10:41 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 63.0 / 100
- **Overall grade**: D

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| src\firmware\site_auto_upgrade.py | 63.0 | D | 0 | 1 | 18 | 20 | 39 |

## Machine-Readable Summary

```json
{
  "overall_score": 63.0,
  "overall_grade": "D",
  "severity_totals": {
    "critical": 0,
    "high": 1,
    "medium": 18,
    "low": 20
  },
  "rule_totals": {
    "STRUCT-BLOCKS": 3,
    "STRUCT-COMPLEXITY": 17,
    "STRUCT-LENGTH": 19
  },
  "files": [
    {
      "path": "src\\firmware\\site_auto_upgrade.py",
      "score": 63.0,
      "grade": "D",
      "violations": 39
    }
  ]
}
```

## File: src\firmware\site_auto_upgrade.py

- **Score**: 63.0 / 100
- **Grade**: D

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1487 |
| Executable code lines | 748 |
| Functions | 58 |
| Classes | 1 |
| Average complexity | 4.4 |
| Max complexity | 10 |
| Inline comment coverage | 96.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_current_site_settings | 10 |
| _apply_family_selection | 9 |
| _get_shared_firmware_versions | 8 |
| _select_versions_interactively | 8 |
| _execute_msp_mode | 7 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 143 | low | STRUCT-COMPLEXITY | run_msp_mode | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 321 | low | STRUCT-COMPLEXITY | _fetch_current_site_settings | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 365 | low | STRUCT-COMPLEXITY | _apply_site_indices | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 386 | low | STRUCT-COMPLEXITY | _step3_fetch_available_versions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 414 | low | STRUCT-COMPLEXITY | _build_model_version_map | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 430 | low | STRUCT-COMPLEXITY | _step4_select_versions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 720 | low | STRUCT-COMPLEXITY | _execute_msp_mode | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 843 | low | STRUCT-COMPLEXITY | _parse_index_selection | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 928 | low | STRUCT-COMPLEXITY | _apply_family_selection | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 986 | low | STRUCT-COMPLEXITY | _pick_stable_version | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1039 | low | STRUCT-COMPLEXITY | parse_time_input | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1120 | low | STRUCT-COMPLEXITY | _apply_settings_to_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1197 | low | STRUCT-COMPLEXITY | _print_msp_summary | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1232 | low | STRUCT-COMPLEXITY | _get_shared_schedule | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1295 | low | STRUCT-COMPLEXITY | _get_shared_firmware_versions | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1348 | low | STRUCT-COMPLEXITY | _build_version_map_from_list | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1423 | low | STRUCT-COMPLEXITY | _select_versions_interactively | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 1232 | high | STRUCT-LENGTH | _get_shared_schedule | Function spans 61 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 48 | medium | STRUCT-LENGTH | __init__ | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 89 | medium | STRUCT-LENGTH | execute | Function spans 49 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 186 | medium | STRUCT-LENGTH | _apply_auto_upgrade_config | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 294 | medium | STRUCT-LENGTH | _select_single_site | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 386 | medium | STRUCT-LENGTH | _step3_fetch_available_versions | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 430 | medium | STRUCT-LENGTH | _step4_select_versions | Function spans 46 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 512 | medium | STRUCT-LENGTH | _step6_confirm_and_apply | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 555 | medium | STRUCT-LENGTH | _handle_msp_mode | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 609 | medium | STRUCT-LENGTH | _msp_select_entities | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 639 | medium | STRUCT-LENGTH | _msp_get_firmware_config | Function spans 37 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 678 | medium | STRUCT-LENGTH | _msp_confirm_and_apply | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 720 | medium | STRUCT-LENGTH | _execute_msp_mode | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 762 | medium | STRUCT-LENGTH | _apply_to_all_orgs | Function spans 43 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 928 | medium | STRUCT-LENGTH | _apply_family_selection | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1120 | medium | STRUCT-LENGTH | _apply_settings_to_sites | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1197 | medium | STRUCT-LENGTH | _print_msp_summary | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1295 | medium | STRUCT-LENGTH | _get_shared_firmware_versions | Function spans 51 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1423 | medium | STRUCT-LENGTH | _select_versions_interactively | Function spans 46 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 321 | low | STRUCT-BLOCKS | _fetch_current_site_settings | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 928 | low | STRUCT-BLOCKS | _apply_family_selection | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 1423 | low | STRUCT-BLOCKS | _select_versions_interactively | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: High (1 task(s))

- [ ] **CMP-001** `src\firmware\site_auto_upgrade.py:1232` - STRUCT-LENGTH (Structure)
  - Symbol: `_get_shared_schedule`
  - Problem: Function spans 61 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_get_shared_schedule` in `src\firmware\site_auto_upgrade.py`.

### Phase: Medium (18 task(s))

- [ ] **CMP-002** `src\firmware\site_auto_upgrade.py:48` - STRUCT-LENGTH (Structure)
  - Symbol: `__init__`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `__init__` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-003** `src\firmware\site_auto_upgrade.py:89` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 49 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-004** `src\firmware\site_auto_upgrade.py:186` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_auto_upgrade_config`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_auto_upgrade_config` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-005** `src\firmware\site_auto_upgrade.py:294` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_single_site`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_single_site` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-006** `src\firmware\site_auto_upgrade.py:386` - STRUCT-LENGTH (Structure)
  - Symbol: `_step3_fetch_available_versions`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_step3_fetch_available_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-007** `src\firmware\site_auto_upgrade.py:430` - STRUCT-LENGTH (Structure)
  - Symbol: `_step4_select_versions`
  - Problem: Function spans 46 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_step4_select_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-008** `src\firmware\site_auto_upgrade.py:512` - STRUCT-LENGTH (Structure)
  - Symbol: `_step6_confirm_and_apply`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_step6_confirm_and_apply` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-009** `src\firmware\site_auto_upgrade.py:555` - STRUCT-LENGTH (Structure)
  - Symbol: `_handle_msp_mode`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_handle_msp_mode` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-010** `src\firmware\site_auto_upgrade.py:609` - STRUCT-LENGTH (Structure)
  - Symbol: `_msp_select_entities`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_msp_select_entities` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-011** `src\firmware\site_auto_upgrade.py:639` - STRUCT-LENGTH (Structure)
  - Symbol: `_msp_get_firmware_config`
  - Problem: Function spans 37 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_msp_get_firmware_config` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-012** `src\firmware\site_auto_upgrade.py:678` - STRUCT-LENGTH (Structure)
  - Symbol: `_msp_confirm_and_apply`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_msp_confirm_and_apply` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-013** `src\firmware\site_auto_upgrade.py:720` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_msp_mode`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_msp_mode` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-014** `src\firmware\site_auto_upgrade.py:762` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_to_all_orgs`
  - Problem: Function spans 43 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_to_all_orgs` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-015** `src\firmware\site_auto_upgrade.py:928` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_family_selection`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_family_selection` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-016** `src\firmware\site_auto_upgrade.py:1120` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_settings_to_sites`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_settings_to_sites` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-017** `src\firmware\site_auto_upgrade.py:1197` - STRUCT-LENGTH (Structure)
  - Symbol: `_print_msp_summary`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_print_msp_summary` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-018** `src\firmware\site_auto_upgrade.py:1295` - STRUCT-LENGTH (Structure)
  - Symbol: `_get_shared_firmware_versions`
  - Problem: Function spans 51 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_get_shared_firmware_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-019** `src\firmware\site_auto_upgrade.py:1423` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_versions_interactively`
  - Problem: Function spans 46 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_versions_interactively` in `src\firmware\site_auto_upgrade.py`.

### Phase: Low (20 task(s))

- [ ] **CMP-020** `src\firmware\site_auto_upgrade.py:143` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `run_msp_mode`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `run_msp_mode` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-021** `src\firmware\site_auto_upgrade.py:321` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_current_site_settings`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_current_site_settings` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-022** `src\firmware\site_auto_upgrade.py:321` - STRUCT-BLOCKS (Structure)
  - Symbol: `_fetch_current_site_settings`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_fetch_current_site_settings` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-023** `src\firmware\site_auto_upgrade.py:365` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_apply_site_indices`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_apply_site_indices` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-024** `src\firmware\site_auto_upgrade.py:386` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_step3_fetch_available_versions`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_step3_fetch_available_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-025** `src\firmware\site_auto_upgrade.py:414` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_model_version_map`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_model_version_map` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-026** `src\firmware\site_auto_upgrade.py:430` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_step4_select_versions`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_step4_select_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-027** `src\firmware\site_auto_upgrade.py:720` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute_msp_mode`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute_msp_mode` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-028** `src\firmware\site_auto_upgrade.py:843` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_index_selection`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_index_selection` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-029** `src\firmware\site_auto_upgrade.py:928` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_apply_family_selection`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_apply_family_selection` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-030** `src\firmware\site_auto_upgrade.py:928` - STRUCT-BLOCKS (Structure)
  - Symbol: `_apply_family_selection`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_apply_family_selection` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-031** `src\firmware\site_auto_upgrade.py:986` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_pick_stable_version`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_pick_stable_version` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-032** `src\firmware\site_auto_upgrade.py:1039` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `parse_time_input`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `parse_time_input` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-033** `src\firmware\site_auto_upgrade.py:1120` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_apply_settings_to_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_apply_settings_to_sites` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-034** `src\firmware\site_auto_upgrade.py:1197` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_print_msp_summary`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_print_msp_summary` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-035** `src\firmware\site_auto_upgrade.py:1232` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_shared_schedule`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_shared_schedule` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-036** `src\firmware\site_auto_upgrade.py:1295` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_shared_firmware_versions`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_shared_firmware_versions` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-037** `src\firmware\site_auto_upgrade.py:1348` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_version_map_from_list`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_version_map_from_list` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-038** `src\firmware\site_auto_upgrade.py:1423` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_select_versions_interactively`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_select_versions_interactively` in `src\firmware\site_auto_upgrade.py`.
- [ ] **CMP-039** `src\firmware\site_auto_upgrade.py:1423` - STRUCT-BLOCKS (Structure)
  - Symbol: `_select_versions_interactively`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_select_versions_interactively` in `src\firmware\site_auto_upgrade.py`.

