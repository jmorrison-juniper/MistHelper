# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 05:06:08 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 58.0 / 100
- **Overall grade**: F

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| src\firmware\bulk_ap_upgrader.py | 58.0 | F | 0 | 1 | 11 | 19 | 31 |

## Machine-Readable Summary

```json
{
  "overall_score": 58.0,
  "overall_grade": "F",
  "severity_totals": {
    "critical": 0,
    "high": 1,
    "medium": 11,
    "low": 19
  },
  "rule_totals": {
    "CONV-COMMENTS": 1,
    "STRUCT-BLOCKS": 3,
    "STRUCT-COMPLEXITY": 16,
    "STRUCT-LENGTH": 10,
    "STRUCT-NESTING": 1
  },
  "files": [
    {
      "path": "src\\firmware\\bulk_ap_upgrader.py",
      "score": 58.0,
      "grade": "F",
      "violations": 31
    }
  ]
}
```

## File: src\firmware\bulk_ap_upgrader.py

- **Score**: 58.0 / 100
- **Grade**: F

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2251 |
| Executable code lines | 1231 |
| Functions | 130 |
| Classes | 2 |
| Average complexity | 3.3 |
| Max complexity | 10 |
| Inline comment coverage | 33.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_index_input | 10 |
| _build_model_version_ranges | 9 |
| _get_versions_for_model | 8 |
| _validate_upgrade_plan | 8 |
| _find_universal_versions_for_models | 8 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 310 | low | STRUCT-COMPLEXITY | _resolve_site_names | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 365 | low | STRUCT-COMPLEXITY | _select_multiple_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 387 | low | STRUCT-COMPLEXITY | _parse_index_input | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 555 | low | STRUCT-COMPLEXITY | _fetch_site_ap_stats | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 627 | low | STRUCT-COMPLEXITY | _build_model_version_ranges | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 694 | low | STRUCT-COMPLEXITY | _find_universal_versions | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 714 | low | STRUCT-COMPLEXITY | _get_versions_for_model | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 740 | low | STRUCT-COMPLEXITY | _display_model_versions | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 756 | low | STRUCT-COMPLEXITY | _get_user_version_selection | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 868 | low | STRUCT-COMPLEXITY | _validate_upgrade_plan | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1267 | low | STRUCT-COMPLEXITY | _get_upgrade_confirmation | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1291 | low | STRUCT-COMPLEXITY | _step8_execute_upgrades | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1706 | low | STRUCT-COMPLEXITY | _group_models_by_ap_type | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1809 | low | STRUCT-COMPLEXITY | _parse_family_selection | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1950 | low | STRUCT-COMPLEXITY | _find_universal_versions_for_models | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2002 | low | STRUCT-COMPLEXITY | _prompt_schedule_day | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 27 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 33.2%; uncommented lines: 27, 79, 94, 114, 128, 146, 157, 159, 161, 166, 180, 201. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 387 | medium | STRUCT-NESTING | _parse_index_input | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 781 | medium | STRUCT-LENGTH | _apply_version_selection | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 816 | medium | STRUCT-LENGTH | _partition_devices_by_version | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1112 | medium | STRUCT-LENGTH | _compute_upgrade_call_breakdown | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1358 | medium | STRUCT-LENGTH | _execute_single_version_upgrade | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1445 | medium | STRUCT-LENGTH | _upgrade_version_group | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1479 | medium | STRUCT-LENGTH | _log_dry_run_upgrade | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1596 | medium | STRUCT-LENGTH | _log_upgrade_results | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1623 | medium | STRUCT-LENGTH | _build_result_row | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1866 | medium | STRUCT-LENGTH | _present_family_candidates | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1893 | medium | STRUCT-LENGTH | _apply_family_version_choice | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 387 | low | STRUCT-BLOCKS | _parse_index_input | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 627 | low | STRUCT-BLOCKS | _build_model_version_ranges | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 714 | low | STRUCT-BLOCKS | _get_versions_for_model | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: High (1 task(s))

- [ ] **CMP-001** `src\firmware\bulk_ap_upgrader.py:27` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 33.2%; uncommented lines: 27, 79, 94, 114, 128, 146, 157, 159, 161, 166, 180, 201.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\firmware\bulk_ap_upgrader.py`.

### Phase: Medium (11 task(s))

- [ ] **CMP-002** `src\firmware\bulk_ap_upgrader.py:387` - STRUCT-NESTING (Structure)
  - Symbol: `_parse_index_input`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_parse_index_input` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-003** `src\firmware\bulk_ap_upgrader.py:781` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_version_selection`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_version_selection` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-004** `src\firmware\bulk_ap_upgrader.py:816` - STRUCT-LENGTH (Structure)
  - Symbol: `_partition_devices_by_version`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_partition_devices_by_version` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-005** `src\firmware\bulk_ap_upgrader.py:1112` - STRUCT-LENGTH (Structure)
  - Symbol: `_compute_upgrade_call_breakdown`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_compute_upgrade_call_breakdown` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-006** `src\firmware\bulk_ap_upgrader.py:1358` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_single_version_upgrade`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_single_version_upgrade` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-007** `src\firmware\bulk_ap_upgrader.py:1445` - STRUCT-LENGTH (Structure)
  - Symbol: `_upgrade_version_group`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_upgrade_version_group` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-008** `src\firmware\bulk_ap_upgrader.py:1479` - STRUCT-LENGTH (Structure)
  - Symbol: `_log_dry_run_upgrade`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_log_dry_run_upgrade` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-009** `src\firmware\bulk_ap_upgrader.py:1596` - STRUCT-LENGTH (Structure)
  - Symbol: `_log_upgrade_results`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_log_upgrade_results` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-010** `src\firmware\bulk_ap_upgrader.py:1623` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_result_row`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_result_row` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-011** `src\firmware\bulk_ap_upgrader.py:1866` - STRUCT-LENGTH (Structure)
  - Symbol: `_present_family_candidates`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_present_family_candidates` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-012** `src\firmware\bulk_ap_upgrader.py:1893` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_family_version_choice`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_family_version_choice` in `src\firmware\bulk_ap_upgrader.py`.

### Phase: Low (19 task(s))

- [ ] **CMP-013** `src\firmware\bulk_ap_upgrader.py:310` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_resolve_site_names`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_resolve_site_names` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-014** `src\firmware\bulk_ap_upgrader.py:365` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_select_multiple_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_select_multiple_sites` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-015** `src\firmware\bulk_ap_upgrader.py:387` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_index_input`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_index_input` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-016** `src\firmware\bulk_ap_upgrader.py:387` - STRUCT-BLOCKS (Structure)
  - Symbol: `_parse_index_input`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_parse_index_input` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-017** `src\firmware\bulk_ap_upgrader.py:555` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_ap_stats`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_ap_stats` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-018** `src\firmware\bulk_ap_upgrader.py:627` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_model_version_ranges`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_model_version_ranges` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-019** `src\firmware\bulk_ap_upgrader.py:627` - STRUCT-BLOCKS (Structure)
  - Symbol: `_build_model_version_ranges`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_build_model_version_ranges` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-020** `src\firmware\bulk_ap_upgrader.py:694` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_universal_versions`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_universal_versions` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-021** `src\firmware\bulk_ap_upgrader.py:714` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_versions_for_model`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_versions_for_model` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-022** `src\firmware\bulk_ap_upgrader.py:714` - STRUCT-BLOCKS (Structure)
  - Symbol: `_get_versions_for_model`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_get_versions_for_model` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-023** `src\firmware\bulk_ap_upgrader.py:740` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_model_versions`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_model_versions` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-024** `src\firmware\bulk_ap_upgrader.py:756` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_user_version_selection`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_user_version_selection` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-025** `src\firmware\bulk_ap_upgrader.py:868` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_validate_upgrade_plan`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_validate_upgrade_plan` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-026** `src\firmware\bulk_ap_upgrader.py:1267` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_upgrade_confirmation`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_upgrade_confirmation` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-027** `src\firmware\bulk_ap_upgrader.py:1291` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_step8_execute_upgrades`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_step8_execute_upgrades` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-028** `src\firmware\bulk_ap_upgrader.py:1706` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_group_models_by_ap_type`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_group_models_by_ap_type` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-029** `src\firmware\bulk_ap_upgrader.py:1809` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_family_selection`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_family_selection` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-030** `src\firmware\bulk_ap_upgrader.py:1950` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_universal_versions_for_models`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_universal_versions_for_models` in `src\firmware\bulk_ap_upgrader.py`.
- [ ] **CMP-031** `src\firmware\bulk_ap_upgrader.py:2002` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_schedule_day`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_schedule_day` in `src\firmware\bulk_ap_upgrader.py`.

