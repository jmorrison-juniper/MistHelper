# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 06:39:17 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 51.0 / 100
- **Overall grade**: F

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| src\firmware\firmware_manager.py | 51.0 | F | 0 | 6 | 34 | 42 | 82 |

## Machine-Readable Summary

```json
{
  "overall_score": 51.0,
  "overall_grade": "F",
  "severity_totals": {
    "critical": 0,
    "high": 6,
    "medium": 34,
    "low": 42
  },
  "rule_totals": {
    "CONV-COMMENTS": 1,
    "CONV-NAME": 3,
    "STRUCT-BLOCKS": 11,
    "STRUCT-COMPLEXITY": 28,
    "STRUCT-LENGTH": 36,
    "STRUCT-NESTING": 2,
    "STRUCT-PARAMS": 1
  },
  "files": [
    {
      "path": "src\\firmware\\firmware_manager.py",
      "score": 51.0,
      "grade": "F",
      "violations": 82
    }
  ]
}
```

## File: src\firmware\firmware_manager.py

- **Score**: 51.0 / 100
- **Grade**: F

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2450 |
| Executable code lines | 1348 |
| Functions | 82 |
| Classes | 1 |
| Average complexity | 4.9 |
| Max complexity | 10 |
| Inline comment coverage | 6.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_msps_for_upgrade | 10 |
| _select_orgs_for_upgrade | 10 |
| _execute_msp_upgrade_plan | 10 |
| _handle_ssr_upgrade_error_response | 10 |
| check_firmware_upgrade_status | 9 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 104 | low | STRUCT-COMPLEXITY | _compare_version_parts | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 120 | low | STRUCT-COMPLEXITY | _is_firmware_downgrade | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 182 | low | STRUCT-COMPLEXITY | check_firmware_upgrade_status | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 244 | low | STRUCT-COMPLEXITY | _continuous_monitoring_mode | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 383 | low | STRUCT-COMPLEXITY | _show_org_level_upgrade_jobs | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 522 | low | STRUCT-COMPLEXITY | _upgrade_ap_firmware_by_gateway_template | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 631 | low | STRUCT-COMPLEXITY | _load_template_sites_mapping | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 662 | low | STRUCT-COMPLEXITY | _prompt_template_selection | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 750 | low | STRUCT-COMPLEXITY | execute_firmware_upgrade_with_mode_selection | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 874 | low | STRUCT-COMPLEXITY | _execute_msp_multi_org_upgrade | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 920 | low | STRUCT-COMPLEXITY | _select_msps_for_upgrade | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 976 | low | STRUCT-COMPLEXITY | _fetch_msp_org_list | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 992 | low | STRUCT-COMPLEXITY | _select_orgs_for_upgrade | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1052 | low | STRUCT-COMPLEXITY | _fetch_and_validate_org_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1084 | low | STRUCT-COMPLEXITY | _handle_site_page_input | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1100 | low | STRUCT-COMPLEXITY | _run_site_selection_loop | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1161 | low | STRUCT-COMPLEXITY | _parse_range_token | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1252 | low | STRUCT-COMPLEXITY | _execute_msp_upgrade_plan | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1350 | low | STRUCT-COMPLEXITY | _split_results_by_status | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1740 | low | STRUCT-COMPLEXITY | _parse_ssr_site_selection | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1871 | low | STRUCT-COMPLEXITY | _get_ssr_available_versions | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1905 | low | STRUCT-COMPLEXITY | _collect_ssr_inventory_data | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1947 | low | STRUCT-COMPLEXITY | _select_ssr_version_from_list | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2055 | low | STRUCT-COMPLEXITY | _load_org_ssr_inventory | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2087 | low | STRUCT-COMPLEXITY | _discover_site_ssr_devices | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2150 | low | STRUCT-COMPLEXITY | _handle_ssr_upgrade_error_response | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2226 | low | STRUCT-COMPLEXITY | _process_ssr_site_upgrade | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2326 | low | STRUCT-COMPLEXITY | _bulk_upgrade_ssr_firmware_by_site | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 9 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 6.3%; uncommented lines: 9, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23. | Add a same-line comment explaining intent on each executable line of changed code. |
| 1364 | low | CONV-NAME | r | Loop variable 'r' is a single letter. | Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'. |
| 1373 | low | CONV-NAME | r | Loop variable 'r' is a single letter. | Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'. |
| 1381 | low | CONV-NAME | r | Loop variable 'r' is a single letter. | Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 59 | high | STRUCT-PARAMS | __init__ | Function takes 8 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 182 | high | STRUCT-LENGTH | check_firmware_upgrade_status | Function spans 61 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 244 | high | STRUCT-LENGTH | _continuous_monitoring_mode | Function spans 74 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 522 | high | STRUCT-LENGTH | _upgrade_ap_firmware_by_gateway_template | Function spans 69 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1252 | high | STRUCT-LENGTH | _execute_msp_upgrade_plan | Function spans 97 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 59 | medium | STRUCT-LENGTH | __init__ | Function spans 44 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 120 | medium | STRUCT-LENGTH | _is_firmware_downgrade | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 383 | medium | STRUCT-LENGTH | _show_org_level_upgrade_jobs | Function spans 49 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 631 | medium | STRUCT-LENGTH | _load_template_sites_mapping | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 662 | medium | STRUCT-LENGTH | _prompt_template_selection | Function spans 56 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 719 | medium | STRUCT-LENGTH | _execute_template_based_upgrade | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 750 | medium | STRUCT-LENGTH | execute_firmware_upgrade_with_mode_selection | Function spans 60 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 750 | medium | STRUCT-NESTING | execute_firmware_upgrade_with_mode_selection | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 874 | medium | STRUCT-LENGTH | _execute_msp_multi_org_upgrade | Function spans 45 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 920 | medium | STRUCT-LENGTH | _select_msps_for_upgrade | Function spans 55 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 992 | medium | STRUCT-LENGTH | _select_orgs_for_upgrade | Function spans 59 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1100 | medium | STRUCT-LENGTH | _run_site_selection_loop | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1127 | medium | STRUCT-LENGTH | _select_sites_for_org_upgrade | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1190 | medium | STRUCT-LENGTH | _parse_selection_input | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1218 | medium | STRUCT-LENGTH | _display_upgrade_plan_summary | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1415 | medium | STRUCT-LENGTH | _bulk_upgrade_ap_firmware_by_site | Function spans 37 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1488 | medium | STRUCT-LENGTH | execute_switch_firmware_upgrade_with_mode_selection | Function spans 48 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1537 | medium | STRUCT-LENGTH | _bulk_upgrade_switch_firmware_by_site | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1567 | medium | STRUCT-LENGTH | _upgrade_switch_firmware_by_gateway_template | Function spans 53 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1633 | medium | STRUCT-LENGTH | execute_ssr_firmware_upgrade_with_mode_selection | Function spans 59 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1740 | medium | STRUCT-LENGTH | _parse_ssr_site_selection | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1740 | medium | STRUCT-NESTING | _parse_ssr_site_selection | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 1871 | medium | STRUCT-LENGTH | _get_ssr_available_versions | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1947 | medium | STRUCT-LENGTH | _select_ssr_version_from_list | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1993 | medium | STRUCT-LENGTH | _confirm_ssr_upgrade | Function spans 39 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2055 | medium | STRUCT-LENGTH | _load_org_ssr_inventory | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2087 | medium | STRUCT-LENGTH | _discover_site_ssr_devices | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2114 | medium | STRUCT-LENGTH | _validate_ssr_devices_for_version | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2150 | medium | STRUCT-LENGTH | _handle_ssr_upgrade_error_response | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2191 | medium | STRUCT-LENGTH | _call_ssr_upgrade_api | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2226 | medium | STRUCT-LENGTH | _process_ssr_site_upgrade | Function spans 50 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2296 | medium | STRUCT-LENGTH | _run_ssr_site_upgrades | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2326 | medium | STRUCT-LENGTH | _bulk_upgrade_ssr_firmware_by_site | Function spans 56 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2383 | medium | STRUCT-LENGTH | _upgrade_ssr_firmware_by_gateway_template | Function spans 57 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 104 | low | STRUCT-BLOCKS | _compare_version_parts | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 182 | low | STRUCT-BLOCKS | check_firmware_upgrade_status | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 662 | low | STRUCT-BLOCKS | _prompt_template_selection | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 750 | low | STRUCT-BLOCKS | execute_firmware_upgrade_with_mode_selection | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 920 | low | STRUCT-BLOCKS | _select_msps_for_upgrade | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 992 | low | STRUCT-BLOCKS | _select_orgs_for_upgrade | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 1100 | low | STRUCT-BLOCKS | _run_site_selection_loop | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 1161 | low | STRUCT-BLOCKS | _parse_range_token | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 1740 | low | STRUCT-BLOCKS | _parse_ssr_site_selection | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 2150 | low | STRUCT-BLOCKS | _handle_ssr_upgrade_error_response | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 2326 | low | STRUCT-BLOCKS | _bulk_upgrade_ssr_firmware_by_site | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: High (6 task(s))

- [ ] **CMP-001** `src\firmware\firmware_manager.py:9` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 6.3%; uncommented lines: 9, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-002** `src\firmware\firmware_manager.py:59` - STRUCT-PARAMS (Structure)
  - Symbol: `__init__`
  - Problem: Function takes 8 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `__init__` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-003** `src\firmware\firmware_manager.py:182` - STRUCT-LENGTH (Structure)
  - Symbol: `check_firmware_upgrade_status`
  - Problem: Function spans 61 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `check_firmware_upgrade_status` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-004** `src\firmware\firmware_manager.py:244` - STRUCT-LENGTH (Structure)
  - Symbol: `_continuous_monitoring_mode`
  - Problem: Function spans 74 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_continuous_monitoring_mode` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-005** `src\firmware\firmware_manager.py:522` - STRUCT-LENGTH (Structure)
  - Symbol: `_upgrade_ap_firmware_by_gateway_template`
  - Problem: Function spans 69 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_upgrade_ap_firmware_by_gateway_template` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-006** `src\firmware\firmware_manager.py:1252` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_msp_upgrade_plan`
  - Problem: Function spans 97 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_msp_upgrade_plan` in `src\firmware\firmware_manager.py`.

### Phase: Medium (34 task(s))

- [ ] **CMP-007** `src\firmware\firmware_manager.py:59` - STRUCT-LENGTH (Structure)
  - Symbol: `__init__`
  - Problem: Function spans 44 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `__init__` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-008** `src\firmware\firmware_manager.py:120` - STRUCT-LENGTH (Structure)
  - Symbol: `_is_firmware_downgrade`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_is_firmware_downgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-009** `src\firmware\firmware_manager.py:383` - STRUCT-LENGTH (Structure)
  - Symbol: `_show_org_level_upgrade_jobs`
  - Problem: Function spans 49 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_show_org_level_upgrade_jobs` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-010** `src\firmware\firmware_manager.py:631` - STRUCT-LENGTH (Structure)
  - Symbol: `_load_template_sites_mapping`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_load_template_sites_mapping` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-011** `src\firmware\firmware_manager.py:662` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_template_selection`
  - Problem: Function spans 56 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_template_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-012** `src\firmware\firmware_manager.py:719` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_template_based_upgrade`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_template_based_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-013** `src\firmware\firmware_manager.py:750` - STRUCT-LENGTH (Structure)
  - Symbol: `execute_firmware_upgrade_with_mode_selection`
  - Problem: Function spans 60 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-014** `src\firmware\firmware_manager.py:750` - STRUCT-NESTING (Structure)
  - Symbol: `execute_firmware_upgrade_with_mode_selection`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `execute_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-015** `src\firmware\firmware_manager.py:874` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_msp_multi_org_upgrade`
  - Problem: Function spans 45 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_msp_multi_org_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-016** `src\firmware\firmware_manager.py:920` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_msps_for_upgrade`
  - Problem: Function spans 55 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_msps_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-017** `src\firmware\firmware_manager.py:992` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_orgs_for_upgrade`
  - Problem: Function spans 59 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_orgs_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-018** `src\firmware\firmware_manager.py:1100` - STRUCT-LENGTH (Structure)
  - Symbol: `_run_site_selection_loop`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_run_site_selection_loop` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-019** `src\firmware\firmware_manager.py:1127` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_sites_for_org_upgrade`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_sites_for_org_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-020** `src\firmware\firmware_manager.py:1190` - STRUCT-LENGTH (Structure)
  - Symbol: `_parse_selection_input`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_parse_selection_input` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-021** `src\firmware\firmware_manager.py:1218` - STRUCT-LENGTH (Structure)
  - Symbol: `_display_upgrade_plan_summary`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_display_upgrade_plan_summary` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-022** `src\firmware\firmware_manager.py:1415` - STRUCT-LENGTH (Structure)
  - Symbol: `_bulk_upgrade_ap_firmware_by_site`
  - Problem: Function spans 37 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_bulk_upgrade_ap_firmware_by_site` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-023** `src\firmware\firmware_manager.py:1488` - STRUCT-LENGTH (Structure)
  - Symbol: `execute_switch_firmware_upgrade_with_mode_selection`
  - Problem: Function spans 48 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute_switch_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-024** `src\firmware\firmware_manager.py:1537` - STRUCT-LENGTH (Structure)
  - Symbol: `_bulk_upgrade_switch_firmware_by_site`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_bulk_upgrade_switch_firmware_by_site` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-025** `src\firmware\firmware_manager.py:1567` - STRUCT-LENGTH (Structure)
  - Symbol: `_upgrade_switch_firmware_by_gateway_template`
  - Problem: Function spans 53 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_upgrade_switch_firmware_by_gateway_template` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-026** `src\firmware\firmware_manager.py:1633` - STRUCT-LENGTH (Structure)
  - Symbol: `execute_ssr_firmware_upgrade_with_mode_selection`
  - Problem: Function spans 59 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute_ssr_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-027** `src\firmware\firmware_manager.py:1740` - STRUCT-LENGTH (Structure)
  - Symbol: `_parse_ssr_site_selection`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_parse_ssr_site_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-028** `src\firmware\firmware_manager.py:1740` - STRUCT-NESTING (Structure)
  - Symbol: `_parse_ssr_site_selection`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_parse_ssr_site_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-029** `src\firmware\firmware_manager.py:1871` - STRUCT-LENGTH (Structure)
  - Symbol: `_get_ssr_available_versions`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_get_ssr_available_versions` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-030** `src\firmware\firmware_manager.py:1947` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_ssr_version_from_list`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_ssr_version_from_list` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-031** `src\firmware\firmware_manager.py:1993` - STRUCT-LENGTH (Structure)
  - Symbol: `_confirm_ssr_upgrade`
  - Problem: Function spans 39 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_confirm_ssr_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-032** `src\firmware\firmware_manager.py:2055` - STRUCT-LENGTH (Structure)
  - Symbol: `_load_org_ssr_inventory`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_load_org_ssr_inventory` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-033** `src\firmware\firmware_manager.py:2087` - STRUCT-LENGTH (Structure)
  - Symbol: `_discover_site_ssr_devices`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_discover_site_ssr_devices` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-034** `src\firmware\firmware_manager.py:2114` - STRUCT-LENGTH (Structure)
  - Symbol: `_validate_ssr_devices_for_version`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_validate_ssr_devices_for_version` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-035** `src\firmware\firmware_manager.py:2150` - STRUCT-LENGTH (Structure)
  - Symbol: `_handle_ssr_upgrade_error_response`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_handle_ssr_upgrade_error_response` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-036** `src\firmware\firmware_manager.py:2191` - STRUCT-LENGTH (Structure)
  - Symbol: `_call_ssr_upgrade_api`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_call_ssr_upgrade_api` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-037** `src\firmware\firmware_manager.py:2226` - STRUCT-LENGTH (Structure)
  - Symbol: `_process_ssr_site_upgrade`
  - Problem: Function spans 50 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_process_ssr_site_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-038** `src\firmware\firmware_manager.py:2296` - STRUCT-LENGTH (Structure)
  - Symbol: `_run_ssr_site_upgrades`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_run_ssr_site_upgrades` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-039** `src\firmware\firmware_manager.py:2326` - STRUCT-LENGTH (Structure)
  - Symbol: `_bulk_upgrade_ssr_firmware_by_site`
  - Problem: Function spans 56 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_bulk_upgrade_ssr_firmware_by_site` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-040** `src\firmware\firmware_manager.py:2383` - STRUCT-LENGTH (Structure)
  - Symbol: `_upgrade_ssr_firmware_by_gateway_template`
  - Problem: Function spans 57 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_upgrade_ssr_firmware_by_gateway_template` in `src\firmware\firmware_manager.py`.

### Phase: Low (42 task(s))

- [ ] **CMP-041** `src\firmware\firmware_manager.py:104` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_compare_version_parts`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_compare_version_parts` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-042** `src\firmware\firmware_manager.py:104` - STRUCT-BLOCKS (Structure)
  - Symbol: `_compare_version_parts`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_compare_version_parts` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-043** `src\firmware\firmware_manager.py:120` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_is_firmware_downgrade`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_is_firmware_downgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-044** `src\firmware\firmware_manager.py:182` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `check_firmware_upgrade_status`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `check_firmware_upgrade_status` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-045** `src\firmware\firmware_manager.py:182` - STRUCT-BLOCKS (Structure)
  - Symbol: `check_firmware_upgrade_status`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `check_firmware_upgrade_status` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-046** `src\firmware\firmware_manager.py:244` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_continuous_monitoring_mode`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_continuous_monitoring_mode` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-047** `src\firmware\firmware_manager.py:383` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_show_org_level_upgrade_jobs`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_show_org_level_upgrade_jobs` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-048** `src\firmware\firmware_manager.py:522` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_upgrade_ap_firmware_by_gateway_template`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_upgrade_ap_firmware_by_gateway_template` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-049** `src\firmware\firmware_manager.py:631` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_template_sites_mapping`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_template_sites_mapping` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-050** `src\firmware\firmware_manager.py:662` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_template_selection`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_template_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-051** `src\firmware\firmware_manager.py:662` - STRUCT-BLOCKS (Structure)
  - Symbol: `_prompt_template_selection`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_prompt_template_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-052** `src\firmware\firmware_manager.py:750` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `execute_firmware_upgrade_with_mode_selection`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `execute_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-053** `src\firmware\firmware_manager.py:750` - STRUCT-BLOCKS (Structure)
  - Symbol: `execute_firmware_upgrade_with_mode_selection`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `execute_firmware_upgrade_with_mode_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-054** `src\firmware\firmware_manager.py:874` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute_msp_multi_org_upgrade`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute_msp_multi_org_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-055** `src\firmware\firmware_manager.py:920` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_select_msps_for_upgrade`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_select_msps_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-056** `src\firmware\firmware_manager.py:920` - STRUCT-BLOCKS (Structure)
  - Symbol: `_select_msps_for_upgrade`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_select_msps_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-057** `src\firmware\firmware_manager.py:976` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_org_list`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_org_list` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-058** `src\firmware\firmware_manager.py:992` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_select_orgs_for_upgrade`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_select_orgs_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-059** `src\firmware\firmware_manager.py:992` - STRUCT-BLOCKS (Structure)
  - Symbol: `_select_orgs_for_upgrade`
  - Problem: Function has 8 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_select_orgs_for_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-060** `src\firmware\firmware_manager.py:1052` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_validate_org_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_validate_org_sites` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-061** `src\firmware\firmware_manager.py:1084` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_handle_site_page_input`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_handle_site_page_input` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-062** `src\firmware\firmware_manager.py:1100` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_run_site_selection_loop`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_run_site_selection_loop` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-063** `src\firmware\firmware_manager.py:1100` - STRUCT-BLOCKS (Structure)
  - Symbol: `_run_site_selection_loop`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_run_site_selection_loop` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-064** `src\firmware\firmware_manager.py:1161` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_range_token`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_range_token` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-065** `src\firmware\firmware_manager.py:1161` - STRUCT-BLOCKS (Structure)
  - Symbol: `_parse_range_token`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_parse_range_token` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-066** `src\firmware\firmware_manager.py:1252` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute_msp_upgrade_plan`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute_msp_upgrade_plan` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-067** `src\firmware\firmware_manager.py:1350` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_split_results_by_status`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_split_results_by_status` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-068** `src\firmware\firmware_manager.py:1364` - CONV-NAME (Conventions)
  - Symbol: `r`
  - Problem: Loop variable 'r' is a single letter.
  - Fix: Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'.
  - Done when: analyzer reports no CONV-NAME for `r` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-069** `src\firmware\firmware_manager.py:1373` - CONV-NAME (Conventions)
  - Symbol: `r`
  - Problem: Loop variable 'r' is a single letter.
  - Fix: Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'.
  - Done when: analyzer reports no CONV-NAME for `r` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-070** `src\firmware\firmware_manager.py:1381` - CONV-NAME (Conventions)
  - Symbol: `r`
  - Problem: Loop variable 'r' is a single letter.
  - Fix: Use a full descriptive name, e.g. 'for device in devices' not 'for d in devices'.
  - Done when: analyzer reports no CONV-NAME for `r` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-071** `src\firmware\firmware_manager.py:1740` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_ssr_site_selection`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_ssr_site_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-072** `src\firmware\firmware_manager.py:1740` - STRUCT-BLOCKS (Structure)
  - Symbol: `_parse_ssr_site_selection`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_parse_ssr_site_selection` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-073** `src\firmware\firmware_manager.py:1871` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_ssr_available_versions`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_ssr_available_versions` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-074** `src\firmware\firmware_manager.py:1905` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_collect_ssr_inventory_data`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_collect_ssr_inventory_data` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-075** `src\firmware\firmware_manager.py:1947` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_select_ssr_version_from_list`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_select_ssr_version_from_list` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-076** `src\firmware\firmware_manager.py:2055` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_org_ssr_inventory`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_org_ssr_inventory` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-077** `src\firmware\firmware_manager.py:2087` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_discover_site_ssr_devices`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_discover_site_ssr_devices` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-078** `src\firmware\firmware_manager.py:2150` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_handle_ssr_upgrade_error_response`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_handle_ssr_upgrade_error_response` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-079** `src\firmware\firmware_manager.py:2150` - STRUCT-BLOCKS (Structure)
  - Symbol: `_handle_ssr_upgrade_error_response`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_handle_ssr_upgrade_error_response` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-080** `src\firmware\firmware_manager.py:2226` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_ssr_site_upgrade`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_ssr_site_upgrade` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-081** `src\firmware\firmware_manager.py:2326` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_bulk_upgrade_ssr_firmware_by_site`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_bulk_upgrade_ssr_firmware_by_site` in `src\firmware\firmware_manager.py`.
- [ ] **CMP-082** `src\firmware\firmware_manager.py:2326` - STRUCT-BLOCKS (Structure)
  - Symbol: `_bulk_upgrade_ssr_firmware_by_site`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_bulk_upgrade_ssr_firmware_by_site` in `src\firmware\firmware_manager.py`.

