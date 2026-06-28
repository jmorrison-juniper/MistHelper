# Coding Guideline Compliance Report

- **Generated**: 2026-06-28 10:59:48 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 80.0 / 100
- **Overall grade**: B-

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| MistHelper.py | 80.0 | B- | 0 | 0 | 0 | 26 | 26 |

## Machine-Readable Summary

```json
{
  "overall_score": 80.0,
  "overall_grade": "B-",
  "severity_totals": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 26
  },
  "rule_totals": {
    "STRUCT-COMPLEXITY": 26
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 80.0,
      "grade": "B-",
      "violations": 26
    }
  ]
}
```

## File: MistHelper.py

- **Score**: 80.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 24134 |
| Executable code lines | 11207 |
| Functions | 1371 |
| Classes | 96 |
| Average complexity | 2.6 |
| Max complexity | 6 |
| Inline comment coverage | 80.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_cli_site_id | 6 |
| _has_meaningful_cli_args | 6 |
| get_device_identifier | 6 |
| _load_port_stats_sites | 6 |
| _maybe_build_offline_record | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8844 | low | STRUCT-COMPLEXITY | get_device_identifier | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10361 | low | STRUCT-COMPLEXITY | _load_port_stats_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10784 | low | STRUCT-COMPLEXITY | _maybe_build_offline_record | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11478 | low | STRUCT-COMPLEXITY | _prompt_operator | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11845 | low | STRUCT-COMPLEXITY | _fetch_license_records | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12843 | low | STRUCT-COMPLEXITY | device_stats | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12950 | low | STRUCT-COMPLEXITY | devices | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12995 | low | STRUCT-COMPLEXITY | clients | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13631 | low | STRUCT-COMPLEXITY | export_sites_by_ap_model | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13851 | low | STRUCT-COMPLEXITY | ha_cluster_info | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14728 | low | STRUCT-COMPLEXITY | _filter_valid_alpha2_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14762 | low | STRUCT-COMPLEXITY | _extract_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14834 | low | STRUCT-COMPLEXITY | _filter_to_iso2_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15041 | low | STRUCT-COMPLEXITY | _row_matches_scope | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15630 | low | STRUCT-COMPLEXITY | fetch_synthetic_test_stats_with_retry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16619 | low | STRUCT-COMPLEXITY | _split_arp_text_into_datasets | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17114 | low | STRUCT-COMPLEXITY | _detect_conflicts | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18863 | low | STRUCT-COMPLEXITY | _create_progress_display | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18998 | low | STRUCT-COMPLEXITY | _check_ssr_upgrades | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19156 | low | STRUCT-COMPLEXITY | _check_audit_logs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19650 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19755 | low | STRUCT-COMPLEXITY | _process_org | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20260 | low | STRUCT-COMPLEXITY | _fetch_site_template_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20336 | low | STRUCT-COMPLEXITY | _fetch_and_filter_org_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23791 | low | STRUCT-COMPLEXITY | _resolve_cli_site_id | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 24068 | low | STRUCT-COMPLEXITY | _has_meaningful_cli_args | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: Low (26 task(s))

- [ ] **CMP-001** `MistHelper.py:8844` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `get_device_identifier`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `get_device_identifier` in `MistHelper.py`.
- [ ] **CMP-002** `MistHelper.py:10361` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_port_stats_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_port_stats_sites` in `MistHelper.py`.
- [ ] **CMP-003** `MistHelper.py:10784` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_maybe_build_offline_record`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_maybe_build_offline_record` in `MistHelper.py`.
- [ ] **CMP-004** `MistHelper.py:11478` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_operator`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_operator` in `MistHelper.py`.
- [ ] **CMP-005** `MistHelper.py:11845` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_license_records`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_license_records` in `MistHelper.py`.
- [ ] **CMP-006** `MistHelper.py:12843` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `device_stats`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `device_stats` in `MistHelper.py`.
- [ ] **CMP-007** `MistHelper.py:12950` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `devices`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `devices` in `MistHelper.py`.
- [ ] **CMP-008** `MistHelper.py:12995` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `clients`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `clients` in `MistHelper.py`.
- [ ] **CMP-009** `MistHelper.py:13631` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `export_sites_by_ap_model`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `export_sites_by_ap_model` in `MistHelper.py`.
- [ ] **CMP-010** `MistHelper.py:13851` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `ha_cluster_info`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `ha_cluster_info` in `MistHelper.py`.
- [ ] **CMP-011** `MistHelper.py:14728` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_valid_alpha2_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_valid_alpha2_codes` in `MistHelper.py`.
- [ ] **CMP-012** `MistHelper.py:14762` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:14834` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_to_iso2_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_to_iso2_country_codes` in `MistHelper.py`.
- [ ] **CMP-014** `MistHelper.py:15041` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_row_matches_scope`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_row_matches_scope` in `MistHelper.py`.
- [ ] **CMP-015** `MistHelper.py:15630` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `fetch_synthetic_test_stats_with_retry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `fetch_synthetic_test_stats_with_retry` in `MistHelper.py`.
- [ ] **CMP-016** `MistHelper.py:16619` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_split_arp_text_into_datasets`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_split_arp_text_into_datasets` in `MistHelper.py`.
- [ ] **CMP-017** `MistHelper.py:17114` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_detect_conflicts`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_detect_conflicts` in `MistHelper.py`.
- [ ] **CMP-018** `MistHelper.py:18863` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_create_progress_display`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_create_progress_display` in `MistHelper.py`.
- [ ] **CMP-019** `MistHelper.py:18998` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_ssr_upgrades`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_ssr_upgrades` in `MistHelper.py`.
- [ ] **CMP-020** `MistHelper.py:19156` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_audit_logs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_audit_logs` in `MistHelper.py`.
- [ ] **CMP-021** `MistHelper.py:19650` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `MistHelper.py`.
- [ ] **CMP-022** `MistHelper.py:19755` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_org`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_org` in `MistHelper.py`.
- [ ] **CMP-023** `MistHelper.py:20260` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_template_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_template_wlans` in `MistHelper.py`.
- [ ] **CMP-024** `MistHelper.py:20336` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_org_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_org_wlans` in `MistHelper.py`.
- [ ] **CMP-025** `MistHelper.py:23791` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_resolve_cli_site_id`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_resolve_cli_site_id` in `MistHelper.py`.
- [ ] **CMP-026** `MistHelper.py:24068` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_has_meaningful_cli_args`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_has_meaningful_cli_args` in `MistHelper.py`.

