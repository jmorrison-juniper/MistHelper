# Coding Guideline Compliance Report

- **Generated**: 2026-06-28 10:12:32 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 1

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 77.0 / 100
- **Overall grade**: C+

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| MistHelper.py | 77.0 | C+ | 0 | 0 | 0 | 48 | 48 |

## Machine-Readable Summary

```json
{
  "overall_score": 77.0,
  "overall_grade": "C+",
  "severity_totals": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 48
  },
  "rule_totals": {
    "STRUCT-BLOCKS": 3,
    "STRUCT-COMPLEXITY": 45
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 77.0,
      "grade": "C+",
      "violations": 48
    }
  ]
}
```

## File: MistHelper.py

- **Score**: 77.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 23983 |
| Executable code lines | 11122 |
| Functions | 1343 |
| Classes | 96 |
| Average complexity | 2.6 |
| Max complexity | 7 |
| Inline comment coverage | 81.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _systematic_test_resolve_fast_mode | 7 |
| dict_list_as_pretty_table | 7 |
| _init_router | 7 |
| _route_to_polyglot | 7 |
| _fetch_and_filter_devices | 7 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 5613 | low | STRUCT-COMPLEXITY | dict_list_as_pretty_table | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 7236 | low | STRUCT-COMPLEXITY | _init_router | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 7318 | low | STRUCT-COMPLEXITY | _route_to_polyglot | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8099 | low | STRUCT-COMPLEXITY | _fetch_all_clients_for_site | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8305 | low | STRUCT-COMPLEXITY | _fetch_and_filter_devices | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8562 | low | STRUCT-COMPLEXITY | _display_client_table | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8788 | low | STRUCT-COMPLEXITY | get_device_identifier | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10305 | low | STRUCT-COMPLEXITY | _load_port_stats_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10728 | low | STRUCT-COMPLEXITY | _maybe_build_offline_record | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11422 | low | STRUCT-COMPLEXITY | _prompt_operator | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11789 | low | STRUCT-COMPLEXITY | _fetch_license_records | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12787 | low | STRUCT-COMPLEXITY | device_stats | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12894 | low | STRUCT-COMPLEXITY | devices | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12939 | low | STRUCT-COMPLEXITY | clients | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13474 | low | STRUCT-COMPLEXITY | _prompt_model_selection | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13565 | low | STRUCT-COMPLEXITY | export_sites_by_ap_model | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13785 | low | STRUCT-COMPLEXITY | ha_cluster_info | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14297 | low | STRUCT-COMPLEXITY | _find_api_functions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14654 | low | STRUCT-COMPLEXITY | _filter_valid_alpha2_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14688 | low | STRUCT-COMPLEXITY | _extract_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14704 | low | STRUCT-COMPLEXITY | _normalize_states_data | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14753 | low | STRUCT-COMPLEXITY | _filter_to_iso2_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14782 | low | STRUCT-COMPLEXITY | _extract_channel_country_codes | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14953 | low | STRUCT-COMPLEXITY | _collect_metrics_for_scope | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15148 | low | STRUCT-COMPLEXITY | _extract_results | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15528 | low | STRUCT-COMPLEXITY | fetch_synthetic_test_stats_with_retry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16420 | low | STRUCT-COMPLEXITY | _handle_message | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16510 | low | STRUCT-COMPLEXITY | _split_arp_text_into_datasets | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17005 | low | STRUCT-COMPLEXITY | _detect_conflicts | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17044 | low | STRUCT-COMPLEXITY | _check_network_subnet_overlap | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17395 | low | STRUCT-COMPLEXITY | _execute | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17613 | low | STRUCT-COMPLEXITY | _show_preview | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18733 | low | STRUCT-COMPLEXITY | _create_progress_display | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18868 | low | STRUCT-COMPLEXITY | _check_ssr_upgrades | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18943 | low | STRUCT-COMPLEXITY | _check_stored_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18987 | low | STRUCT-COMPLEXITY | _check_stored_upgrade | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19015 | low | STRUCT-COMPLEXITY | _check_audit_logs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19091 | low | STRUCT-COMPLEXITY | _check_site_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19507 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19612 | low | STRUCT-COMPLEXITY | _process_org | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20117 | low | STRUCT-COMPLEXITY | _fetch_site_template_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20193 | low | STRUCT-COMPLEXITY | _fetch_and_filter_org_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 22956 | low | STRUCT-COMPLEXITY | _systematic_test_resolve_fast_mode | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23640 | low | STRUCT-COMPLEXITY | _resolve_cli_site_id | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23917 | low | STRUCT-COMPLEXITY | _has_meaningful_cli_args | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 14704 | low | STRUCT-BLOCKS | _normalize_states_data | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 17044 | low | STRUCT-BLOCKS | _check_network_subnet_overlap | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 17395 | low | STRUCT-BLOCKS | _execute | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: Low (48 task(s))

- [ ] **CMP-001** `MistHelper.py:5613` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `dict_list_as_pretty_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `dict_list_as_pretty_table` in `MistHelper.py`.
- [ ] **CMP-002** `MistHelper.py:7236` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_init_router`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_init_router` in `MistHelper.py`.
- [ ] **CMP-003** `MistHelper.py:7318` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_route_to_polyglot`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_route_to_polyglot` in `MistHelper.py`.
- [ ] **CMP-004** `MistHelper.py:8099` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_all_clients_for_site`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_all_clients_for_site` in `MistHelper.py`.
- [ ] **CMP-005** `MistHelper.py:8305` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_devices`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_devices` in `MistHelper.py`.
- [ ] **CMP-006** `MistHelper.py:8562` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_client_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_client_table` in `MistHelper.py`.
- [ ] **CMP-007** `MistHelper.py:8788` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `get_device_identifier`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `get_device_identifier` in `MistHelper.py`.
- [ ] **CMP-008** `MistHelper.py:10305` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_port_stats_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_port_stats_sites` in `MistHelper.py`.
- [ ] **CMP-009** `MistHelper.py:10728` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_maybe_build_offline_record`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_maybe_build_offline_record` in `MistHelper.py`.
- [ ] **CMP-010** `MistHelper.py:11422` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_operator`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_operator` in `MistHelper.py`.
- [ ] **CMP-011** `MistHelper.py:11789` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_license_records`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_license_records` in `MistHelper.py`.
- [ ] **CMP-012** `MistHelper.py:12787` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `device_stats`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `device_stats` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:12894` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `devices`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `devices` in `MistHelper.py`.
- [ ] **CMP-014** `MistHelper.py:12939` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `clients`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `clients` in `MistHelper.py`.
- [ ] **CMP-015** `MistHelper.py:13474` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_model_selection`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_model_selection` in `MistHelper.py`.
- [ ] **CMP-016** `MistHelper.py:13565` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `export_sites_by_ap_model`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `export_sites_by_ap_model` in `MistHelper.py`.
- [ ] **CMP-017** `MistHelper.py:13785` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `ha_cluster_info`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `ha_cluster_info` in `MistHelper.py`.
- [ ] **CMP-018** `MistHelper.py:14297` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_api_functions`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_api_functions` in `MistHelper.py`.
- [ ] **CMP-019** `MistHelper.py:14654` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_valid_alpha2_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_valid_alpha2_codes` in `MistHelper.py`.
- [ ] **CMP-020** `MistHelper.py:14688` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-021** `MistHelper.py:14704` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_normalize_states_data`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-022** `MistHelper.py:14704` - STRUCT-BLOCKS (Structure)
  - Symbol: `_normalize_states_data`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-023** `MistHelper.py:14753` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_to_iso2_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_to_iso2_country_codes` in `MistHelper.py`.
- [ ] **CMP-024** `MistHelper.py:14782` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_channel_country_codes`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_channel_country_codes` in `MistHelper.py`.
- [ ] **CMP-025** `MistHelper.py:14953` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_collect_metrics_for_scope`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_collect_metrics_for_scope` in `MistHelper.py`.
- [ ] **CMP-026** `MistHelper.py:15148` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_results`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_results` in `MistHelper.py`.
- [ ] **CMP-027** `MistHelper.py:15528` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `fetch_synthetic_test_stats_with_retry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `fetch_synthetic_test_stats_with_retry` in `MistHelper.py`.
- [ ] **CMP-028** `MistHelper.py:16420` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_handle_message`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_handle_message` in `MistHelper.py`.
- [ ] **CMP-029** `MistHelper.py:16510` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_split_arp_text_into_datasets`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_split_arp_text_into_datasets` in `MistHelper.py`.
- [ ] **CMP-030** `MistHelper.py:17005` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_detect_conflicts`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_detect_conflicts` in `MistHelper.py`.
- [ ] **CMP-031** `MistHelper.py:17044` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-032** `MistHelper.py:17044` - STRUCT-BLOCKS (Structure)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-033** `MistHelper.py:17395` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute` in `MistHelper.py`.
- [ ] **CMP-034** `MistHelper.py:17395` - STRUCT-BLOCKS (Structure)
  - Symbol: `_execute`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_execute` in `MistHelper.py`.
- [ ] **CMP-035** `MistHelper.py:17613` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_show_preview`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_show_preview` in `MistHelper.py`.
- [ ] **CMP-036** `MistHelper.py:18733` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_create_progress_display`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_create_progress_display` in `MistHelper.py`.
- [ ] **CMP-037** `MistHelper.py:18868` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_ssr_upgrades`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_ssr_upgrades` in `MistHelper.py`.
- [ ] **CMP-038** `MistHelper.py:18943` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrades` in `MistHelper.py`.
- [ ] **CMP-039** `MistHelper.py:18987` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrade`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrade` in `MistHelper.py`.
- [ ] **CMP-040** `MistHelper.py:19015` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_audit_logs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_audit_logs` in `MistHelper.py`.
- [ ] **CMP-041** `MistHelper.py:19091` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_site_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_site_upgrades` in `MistHelper.py`.
- [ ] **CMP-042** `MistHelper.py:19507` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `MistHelper.py`.
- [ ] **CMP-043** `MistHelper.py:19612` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_org`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_org` in `MistHelper.py`.
- [ ] **CMP-044** `MistHelper.py:20117` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_template_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_template_wlans` in `MistHelper.py`.
- [ ] **CMP-045** `MistHelper.py:20193` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_org_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_org_wlans` in `MistHelper.py`.
- [ ] **CMP-046** `MistHelper.py:22956` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_systematic_test_resolve_fast_mode`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_systematic_test_resolve_fast_mode` in `MistHelper.py`.
- [ ] **CMP-047** `MistHelper.py:23640` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_resolve_cli_site_id`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_resolve_cli_site_id` in `MistHelper.py`.
- [ ] **CMP-048** `MistHelper.py:23917` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_has_meaningful_cli_args`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_has_meaningful_cli_args` in `MistHelper.py`.

