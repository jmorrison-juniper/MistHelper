# Coding Guideline Compliance Report

- **Generated**: 2026-07-02 09:22:58 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 60.0 / 100
- **Overall grade**: D-

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| src\firmware\org_ap_upgrader.py | 60.0 | D- | 0 | 2 | 11 | 14 | 27 |

## Machine-Readable Summary

```json
{
  "overall_score": 60.0,
  "overall_grade": "D-",
  "severity_totals": {
    "critical": 0,
    "high": 2,
    "medium": 11,
    "low": 14
  },
  "rule_totals": {
    "CONV-COMMENTS": 1,
    "STRUCT-COMPLEXITY": 14,
    "STRUCT-LENGTH": 11,
    "STRUCT-PARAMS": 1
  },
  "files": [
    {
      "path": "src\\firmware\\org_ap_upgrader.py",
      "score": 60.0,
      "grade": "D-",
      "violations": 27
    }
  ]
}
```

## File: src\firmware\org_ap_upgrader.py

- **Score**: 60.0 / 100
- **Grade**: D-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2393 |
| Executable code lines | 1445 |
| Functions | 157 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 7 |
| Inline comment coverage | 16.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _organize_by_version | 7 |
| _parse_time_input | 7 |
| _parse_canary_phase_values | 7 |
| run | 6 |
| _fetch_msp_orgs | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 122 | low | STRUCT-COMPLEXITY | run | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 480 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 670 | low | STRUCT-COMPLEXITY | _print_msp_summary | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 883 | low | STRUCT-COMPLEXITY | _fetch_org_aps | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 911 | low | STRUCT-COMPLEXITY | _get_org_inventory | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 960 | low | STRUCT-COMPLEXITY | _fetch_site_aps | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1173 | low | STRUCT-COMPLEXITY | _build_model_version_mapping | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1458 | low | STRUCT-COMPLEXITY | _organize_by_version | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1487 | low | STRUCT-COMPLEXITY | _step6_configure_upgrade | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1597 | low | STRUCT-COMPLEXITY | _parse_time_input | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1637 | low | STRUCT-COMPLEXITY | _try_parse_after | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 1906 | low | STRUCT-COMPLEXITY | _parse_canary_phase_values | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2199 | low | STRUCT-COMPLEXITY | _print_dry_run_entry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 2347 | low | STRUCT-COMPLEXITY | _process_upgrade_response | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 11 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 16.0%; uncommented lines: 11, 13, 14, 15, 16, 17, 18, 71, 72, 73, 75, 76. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 41 | high | STRUCT-PARAMS | __init__ | Function takes 11 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 41 | medium | STRUCT-LENGTH | __init__ | Function spans 45 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 178 | medium | STRUCT-LENGTH | _execute_msp_mode | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 232 | medium | STRUCT-LENGTH | _confirm_msp_orgs | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 264 | medium | STRUCT-LENGTH | _execute_org_upgrades | Function spans 42 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 448 | medium | STRUCT-LENGTH | _select_orgs_from_msp | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 761 | medium | STRUCT-LENGTH | _step1_select_site_scope | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 883 | medium | STRUCT-LENGTH | _fetch_org_aps | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1340 | medium | STRUCT-LENGTH | _apply_version_selection | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1928 | medium | STRUCT-LENGTH | _configure_canary_phases | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2242 | medium | STRUCT-LENGTH | _execute_upgrades | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2347 | medium | STRUCT-LENGTH | _process_upgrade_response | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: High (2 task(s))

- [ ] **CMP-001** `src\firmware\org_ap_upgrader.py:11` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 16.0%; uncommented lines: 11, 13, 14, 15, 16, 17, 18, 71, 72, 73, 75, 76.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-002** `src\firmware\org_ap_upgrader.py:41` - STRUCT-PARAMS (Structure)
  - Symbol: `__init__`
  - Problem: Function takes 11 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `__init__` in `src\firmware\org_ap_upgrader.py`.

### Phase: Medium (11 task(s))

- [ ] **CMP-003** `src\firmware\org_ap_upgrader.py:41` - STRUCT-LENGTH (Structure)
  - Symbol: `__init__`
  - Problem: Function spans 45 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `__init__` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-004** `src\firmware\org_ap_upgrader.py:178` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_msp_mode`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_msp_mode` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-005** `src\firmware\org_ap_upgrader.py:232` - STRUCT-LENGTH (Structure)
  - Symbol: `_confirm_msp_orgs`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_confirm_msp_orgs` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-006** `src\firmware\org_ap_upgrader.py:264` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_org_upgrades`
  - Problem: Function spans 42 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_org_upgrades` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-007** `src\firmware\org_ap_upgrader.py:448` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_orgs_from_msp`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_orgs_from_msp` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-008** `src\firmware\org_ap_upgrader.py:761` - STRUCT-LENGTH (Structure)
  - Symbol: `_step1_select_site_scope`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_step1_select_site_scope` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-009** `src\firmware\org_ap_upgrader.py:883` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_org_aps`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_org_aps` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-010** `src\firmware\org_ap_upgrader.py:1340` - STRUCT-LENGTH (Structure)
  - Symbol: `_apply_version_selection`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_apply_version_selection` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-011** `src\firmware\org_ap_upgrader.py:1928` - STRUCT-LENGTH (Structure)
  - Symbol: `_configure_canary_phases`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_configure_canary_phases` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-012** `src\firmware\org_ap_upgrader.py:2242` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_upgrades`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_upgrades` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-013** `src\firmware\org_ap_upgrader.py:2347` - STRUCT-LENGTH (Structure)
  - Symbol: `_process_upgrade_response`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_process_upgrade_response` in `src\firmware\org_ap_upgrader.py`.

### Phase: Low (14 task(s))

- [ ] **CMP-014** `src\firmware\org_ap_upgrader.py:122` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `run`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `run` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-015** `src\firmware\org_ap_upgrader.py:480` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-016** `src\firmware\org_ap_upgrader.py:670` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_print_msp_summary`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_print_msp_summary` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-017** `src\firmware\org_ap_upgrader.py:883` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_org_aps`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_org_aps` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-018** `src\firmware\org_ap_upgrader.py:911` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_org_inventory`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_org_inventory` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-019** `src\firmware\org_ap_upgrader.py:960` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_aps`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_aps` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-020** `src\firmware\org_ap_upgrader.py:1173` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_model_version_mapping`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_model_version_mapping` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-021** `src\firmware\org_ap_upgrader.py:1458` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_organize_by_version`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_organize_by_version` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-022** `src\firmware\org_ap_upgrader.py:1487` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_step6_configure_upgrade`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_step6_configure_upgrade` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-023** `src\firmware\org_ap_upgrader.py:1597` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_time_input`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_time_input` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-024** `src\firmware\org_ap_upgrader.py:1637` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_try_parse_after`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_try_parse_after` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-025** `src\firmware\org_ap_upgrader.py:1906` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_canary_phase_values`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_canary_phase_values` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-026** `src\firmware\org_ap_upgrader.py:2199` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_print_dry_run_entry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_print_dry_run_entry` in `src\firmware\org_ap_upgrader.py`.
- [ ] **CMP-027** `src\firmware\org_ap_upgrader.py:2347` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_upgrade_response`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_upgrade_response` in `src\firmware\org_ap_upgrader.py`.

