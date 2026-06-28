# Coding Guideline Compliance Report

- **Generated**: 2026-06-28 09:30:11 UTC
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
| MistHelper.py | 60.0 | D- | 0 | 0 | 6 | 61 | 67 |

## Machine-Readable Summary

```json
{
  "overall_score": 60.0,
  "overall_grade": "D-",
  "severity_totals": {
    "critical": 0,
    "high": 0,
    "medium": 6,
    "low": 61
  },
  "rule_totals": {
    "STRUCT-BLOCKS": 6,
    "STRUCT-COMPLEXITY": 55,
    "STRUCT-NESTING": 6
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 60.0,
      "grade": "D-",
      "violations": 67
    }
  ]
}
```

## File: MistHelper.py

- **Score**: 60.0 / 100
- **Grade**: D-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 23823 |
| Executable code lines | 11045 |
| Functions | 1314 |
| Classes | 96 |
| Average complexity | 2.7 |
| Max complexity | 10 |
| Inline comment coverage | 81.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _extract_gateway_models | 10 |
| execute | 10 |
| _partition_combined_inventory_rows | 9 |
| _get_country_codes_list | 9 |
| _handle_message | 9 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 2941 | low | STRUCT-COMPLEXITY | initialize_mist_session | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 5602 | low | STRUCT-COMPLEXITY | dict_list_as_pretty_table | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 6552 | low | STRUCT-COMPLEXITY | flatten_dict | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 7217 | low | STRUCT-COMPLEXITY | _init_router | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 7299 | low | STRUCT-COMPLEXITY | _route_to_polyglot | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8077 | low | STRUCT-COMPLEXITY | _fetch_all_clients_for_site | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8283 | low | STRUCT-COMPLEXITY | _fetch_and_filter_devices | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8540 | low | STRUCT-COMPLEXITY | _display_client_table | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 8766 | low | STRUCT-COMPLEXITY | get_device_identifier | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 9651 | low | STRUCT-COMPLEXITY | _partition_combined_inventory_rows | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10274 | low | STRUCT-COMPLEXITY | _load_port_stats_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 10697 | low | STRUCT-COMPLEXITY | _maybe_build_offline_record | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11391 | low | STRUCT-COMPLEXITY | _prompt_operator | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 11758 | low | STRUCT-COMPLEXITY | _fetch_license_records | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12756 | low | STRUCT-COMPLEXITY | device_stats | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12863 | low | STRUCT-COMPLEXITY | devices | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 12908 | low | STRUCT-COMPLEXITY | clients | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13443 | low | STRUCT-COMPLEXITY | _prompt_model_selection | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13534 | low | STRUCT-COMPLEXITY | export_sites_by_ap_model | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 13754 | low | STRUCT-COMPLEXITY | ha_cluster_info | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14266 | low | STRUCT-COMPLEXITY | _find_api_functions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14530 | low | STRUCT-COMPLEXITY | _extract_gateway_models | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14598 | low | STRUCT-COMPLEXITY | _get_country_codes_list | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14624 | low | STRUCT-COMPLEXITY | _extract_country_codes | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14638 | low | STRUCT-COMPLEXITY | _normalize_states_data | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14687 | low | STRUCT-COMPLEXITY | _filter_to_iso2_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14716 | low | STRUCT-COMPLEXITY | _extract_channel_country_codes | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14885 | low | STRUCT-COMPLEXITY | _collect_metrics_for_scope | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15080 | low | STRUCT-COMPLEXITY | _extract_results | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15460 | low | STRUCT-COMPLEXITY | fetch_synthetic_test_stats_with_retry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15842 | low | STRUCT-COMPLEXITY | _dispatch_marvis_choice | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16184 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16294 | low | STRUCT-COMPLEXITY | _handle_message | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16385 | low | STRUCT-COMPLEXITY | _split_arp_text_into_datasets | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16880 | low | STRUCT-COMPLEXITY | _detect_conflicts | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16919 | low | STRUCT-COMPLEXITY | _check_network_subnet_overlap | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17270 | low | STRUCT-COMPLEXITY | _execute | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17357 | low | STRUCT-COMPLEXITY | _parse_template_selection | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17483 | low | STRUCT-COMPLEXITY | _show_preview | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18603 | low | STRUCT-COMPLEXITY | _create_progress_display | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18704 | low | STRUCT-COMPLEXITY | _display_progress_distribution | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18736 | low | STRUCT-COMPLEXITY | _check_ssr_upgrades | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18811 | low | STRUCT-COMPLEXITY | _check_stored_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18855 | low | STRUCT-COMPLEXITY | _check_stored_upgrade | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18883 | low | STRUCT-COMPLEXITY | _check_audit_logs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18959 | low | STRUCT-COMPLEXITY | _check_site_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19375 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19480 | low | STRUCT-COMPLEXITY | _process_org | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19985 | low | STRUCT-COMPLEXITY | _fetch_site_template_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20036 | low | STRUCT-COMPLEXITY | _is_template_assigned_to_site | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20053 | low | STRUCT-COMPLEXITY | _fetch_and_filter_org_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 22816 | low | STRUCT-COMPLEXITY | _systematic_test_resolve_fast_mode | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23500 | low | STRUCT-COMPLEXITY | _resolve_cli_site_id | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23736 | low | STRUCT-COMPLEXITY | _dispatch_main_mode | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23757 | low | STRUCT-COMPLEXITY | _has_meaningful_cli_args | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 6552 | medium | STRUCT-NESTING | flatten_dict | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 7889 | medium | STRUCT-NESTING | _pool_drain_wait_loop | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 14624 | medium | STRUCT-NESTING | _extract_country_codes | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 14716 | medium | STRUCT-NESTING | _extract_channel_country_codes | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 15842 | medium | STRUCT-NESTING | _dispatch_marvis_choice | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 18704 | medium | STRUCT-NESTING | _display_progress_distribution | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 2941 | low | STRUCT-BLOCKS | initialize_mist_session | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 14530 | low | STRUCT-BLOCKS | _extract_gateway_models | Function has 9 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 14638 | low | STRUCT-BLOCKS | _normalize_states_data | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 16919 | low | STRUCT-BLOCKS | _check_network_subnet_overlap | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 17270 | low | STRUCT-BLOCKS | _execute | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 18704 | low | STRUCT-BLOCKS | _display_progress_distribution | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: Medium (6 task(s))

- [ ] **CMP-001** `MistHelper.py:6552` - STRUCT-NESTING (Structure)
  - Symbol: `flatten_dict`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `flatten_dict` in `MistHelper.py`.
- [ ] **CMP-002** `MistHelper.py:7889` - STRUCT-NESTING (Structure)
  - Symbol: `_pool_drain_wait_loop`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_pool_drain_wait_loop` in `MistHelper.py`.
- [ ] **CMP-003** `MistHelper.py:14624` - STRUCT-NESTING (Structure)
  - Symbol: `_extract_country_codes`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-004** `MistHelper.py:14716` - STRUCT-NESTING (Structure)
  - Symbol: `_extract_channel_country_codes`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_extract_channel_country_codes` in `MistHelper.py`.
- [ ] **CMP-005** `MistHelper.py:15842` - STRUCT-NESTING (Structure)
  - Symbol: `_dispatch_marvis_choice`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_dispatch_marvis_choice` in `MistHelper.py`.
- [ ] **CMP-006** `MistHelper.py:18704` - STRUCT-NESTING (Structure)
  - Symbol: `_display_progress_distribution`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_display_progress_distribution` in `MistHelper.py`.

### Phase: Low (61 task(s))

- [ ] **CMP-007** `MistHelper.py:2941` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `initialize_mist_session`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `initialize_mist_session` in `MistHelper.py`.
- [ ] **CMP-008** `MistHelper.py:2941` - STRUCT-BLOCKS (Structure)
  - Symbol: `initialize_mist_session`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `initialize_mist_session` in `MistHelper.py`.
- [ ] **CMP-009** `MistHelper.py:5602` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `dict_list_as_pretty_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `dict_list_as_pretty_table` in `MistHelper.py`.
- [ ] **CMP-010** `MistHelper.py:6552` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `flatten_dict`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `flatten_dict` in `MistHelper.py`.
- [ ] **CMP-011** `MistHelper.py:7217` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_init_router`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_init_router` in `MistHelper.py`.
- [ ] **CMP-012** `MistHelper.py:7299` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_route_to_polyglot`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_route_to_polyglot` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:8077` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_all_clients_for_site`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_all_clients_for_site` in `MistHelper.py`.
- [ ] **CMP-014** `MistHelper.py:8283` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_devices`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_devices` in `MistHelper.py`.
- [ ] **CMP-015** `MistHelper.py:8540` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_client_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_client_table` in `MistHelper.py`.
- [ ] **CMP-016** `MistHelper.py:8766` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `get_device_identifier`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `get_device_identifier` in `MistHelper.py`.
- [ ] **CMP-017** `MistHelper.py:9651` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_partition_combined_inventory_rows`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_partition_combined_inventory_rows` in `MistHelper.py`.
- [ ] **CMP-018** `MistHelper.py:10274` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_port_stats_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_port_stats_sites` in `MistHelper.py`.
- [ ] **CMP-019** `MistHelper.py:10697` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_maybe_build_offline_record`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_maybe_build_offline_record` in `MistHelper.py`.
- [ ] **CMP-020** `MistHelper.py:11391` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_operator`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_operator` in `MistHelper.py`.
- [ ] **CMP-021** `MistHelper.py:11758` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_license_records`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_license_records` in `MistHelper.py`.
- [ ] **CMP-022** `MistHelper.py:12756` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `device_stats`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `device_stats` in `MistHelper.py`.
- [ ] **CMP-023** `MistHelper.py:12863` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `devices`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `devices` in `MistHelper.py`.
- [ ] **CMP-024** `MistHelper.py:12908` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `clients`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `clients` in `MistHelper.py`.
- [ ] **CMP-025** `MistHelper.py:13443` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_model_selection`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_model_selection` in `MistHelper.py`.
- [ ] **CMP-026** `MistHelper.py:13534` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `export_sites_by_ap_model`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `export_sites_by_ap_model` in `MistHelper.py`.
- [ ] **CMP-027** `MistHelper.py:13754` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `ha_cluster_info`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `ha_cluster_info` in `MistHelper.py`.
- [ ] **CMP-028** `MistHelper.py:14266` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_api_functions`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_api_functions` in `MistHelper.py`.
- [ ] **CMP-029** `MistHelper.py:14530` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_gateway_models`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_gateway_models` in `MistHelper.py`.
- [ ] **CMP-030** `MistHelper.py:14530` - STRUCT-BLOCKS (Structure)
  - Symbol: `_extract_gateway_models`
  - Problem: Function has 9 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_extract_gateway_models` in `MistHelper.py`.
- [ ] **CMP-031** `MistHelper.py:14598` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_country_codes_list`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_country_codes_list` in `MistHelper.py`.
- [ ] **CMP-032** `MistHelper.py:14624` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_country_codes`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-033** `MistHelper.py:14638` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_normalize_states_data`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-034** `MistHelper.py:14638` - STRUCT-BLOCKS (Structure)
  - Symbol: `_normalize_states_data`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-035** `MistHelper.py:14687` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_to_iso2_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_to_iso2_country_codes` in `MistHelper.py`.
- [ ] **CMP-036** `MistHelper.py:14716` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_channel_country_codes`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_channel_country_codes` in `MistHelper.py`.
- [ ] **CMP-037** `MistHelper.py:14885` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_collect_metrics_for_scope`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_collect_metrics_for_scope` in `MistHelper.py`.
- [ ] **CMP-038** `MistHelper.py:15080` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_results`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_results` in `MistHelper.py`.
- [ ] **CMP-039** `MistHelper.py:15460` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `fetch_synthetic_test_stats_with_retry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `fetch_synthetic_test_stats_with_retry` in `MistHelper.py`.
- [ ] **CMP-040** `MistHelper.py:15842` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_dispatch_marvis_choice`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_dispatch_marvis_choice` in `MistHelper.py`.
- [ ] **CMP-041** `MistHelper.py:16184` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `execute`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `execute` in `MistHelper.py`.
- [ ] **CMP-042** `MistHelper.py:16294` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_handle_message`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_handle_message` in `MistHelper.py`.
- [ ] **CMP-043** `MistHelper.py:16385` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_split_arp_text_into_datasets`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_split_arp_text_into_datasets` in `MistHelper.py`.
- [ ] **CMP-044** `MistHelper.py:16880` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_detect_conflicts`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_detect_conflicts` in `MistHelper.py`.
- [ ] **CMP-045** `MistHelper.py:16919` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-046** `MistHelper.py:16919` - STRUCT-BLOCKS (Structure)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-047** `MistHelper.py:17270` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute` in `MistHelper.py`.
- [ ] **CMP-048** `MistHelper.py:17270` - STRUCT-BLOCKS (Structure)
  - Symbol: `_execute`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_execute` in `MistHelper.py`.
- [ ] **CMP-049** `MistHelper.py:17357` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_template_selection`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_template_selection` in `MistHelper.py`.
- [ ] **CMP-050** `MistHelper.py:17483` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_show_preview`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_show_preview` in `MistHelper.py`.
- [ ] **CMP-051** `MistHelper.py:18603` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_create_progress_display`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_create_progress_display` in `MistHelper.py`.
- [ ] **CMP-052** `MistHelper.py:18704` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_progress_distribution`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_progress_distribution` in `MistHelper.py`.
- [ ] **CMP-053** `MistHelper.py:18704` - STRUCT-BLOCKS (Structure)
  - Symbol: `_display_progress_distribution`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_display_progress_distribution` in `MistHelper.py`.
- [ ] **CMP-054** `MistHelper.py:18736` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_ssr_upgrades`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_ssr_upgrades` in `MistHelper.py`.
- [ ] **CMP-055** `MistHelper.py:18811` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrades` in `MistHelper.py`.
- [ ] **CMP-056** `MistHelper.py:18855` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrade`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrade` in `MistHelper.py`.
- [ ] **CMP-057** `MistHelper.py:18883` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_audit_logs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_audit_logs` in `MistHelper.py`.
- [ ] **CMP-058** `MistHelper.py:18959` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_site_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_site_upgrades` in `MistHelper.py`.
- [ ] **CMP-059** `MistHelper.py:19375` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `MistHelper.py`.
- [ ] **CMP-060** `MistHelper.py:19480` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_org`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_org` in `MistHelper.py`.
- [ ] **CMP-061** `MistHelper.py:19985` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_template_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_template_wlans` in `MistHelper.py`.
- [ ] **CMP-062** `MistHelper.py:20036` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_is_template_assigned_to_site`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_is_template_assigned_to_site` in `MistHelper.py`.
- [ ] **CMP-063** `MistHelper.py:20053` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_org_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_org_wlans` in `MistHelper.py`.
- [ ] **CMP-064** `MistHelper.py:22816` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_systematic_test_resolve_fast_mode`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_systematic_test_resolve_fast_mode` in `MistHelper.py`.
- [ ] **CMP-065** `MistHelper.py:23500` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_resolve_cli_site_id`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_resolve_cli_site_id` in `MistHelper.py`.
- [ ] **CMP-066** `MistHelper.py:23736` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_dispatch_main_mode`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_dispatch_main_mode` in `MistHelper.py`.
- [ ] **CMP-067** `MistHelper.py:23757` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_has_meaningful_cli_args`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_has_meaningful_cli_args` in `MistHelper.py`.

