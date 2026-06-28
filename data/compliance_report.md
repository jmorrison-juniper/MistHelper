# Coding Guideline Compliance Report

- **Generated**: 2026-06-28 09:08:15 UTC
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
| MistHelper.py | 60.0 | D- | 0 | 0 | 16 | 65 | 81 |

## Machine-Readable Summary

```json
{
  "overall_score": 60.0,
  "overall_grade": "D-",
  "severity_totals": {
    "critical": 0,
    "high": 0,
    "medium": 16,
    "low": 65
  },
  "rule_totals": {
    "STRUCT-BLOCKS": 6,
    "STRUCT-COMPLEXITY": 59,
    "STRUCT-LENGTH": 9,
    "STRUCT-NESTING": 7
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 60.0,
      "grade": "D-",
      "violations": 81
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
| Lines of code | 23785 |
| Executable code lines | 11006 |
| Functions | 1300 |
| Classes | 96 |
| Average complexity | 2.7 |
| Max complexity | 10 |
| Inline comment coverage | 81.9% |

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
| 14594 | low | STRUCT-COMPLEXITY | _get_country_codes_list | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14620 | low | STRUCT-COMPLEXITY | _extract_country_codes | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14634 | low | STRUCT-COMPLEXITY | _normalize_states_data | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14683 | low | STRUCT-COMPLEXITY | _filter_to_iso2_country_codes | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14712 | low | STRUCT-COMPLEXITY | _extract_channel_country_codes | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 14881 | low | STRUCT-COMPLEXITY | _collect_metrics_for_scope | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15076 | low | STRUCT-COMPLEXITY | _extract_results | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15456 | low | STRUCT-COMPLEXITY | fetch_synthetic_test_stats_with_retry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 15838 | low | STRUCT-COMPLEXITY | _dispatch_marvis_choice | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16180 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16290 | low | STRUCT-COMPLEXITY | _handle_message | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16381 | low | STRUCT-COMPLEXITY | _split_arp_text_into_datasets | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16876 | low | STRUCT-COMPLEXITY | _detect_conflicts | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 16915 | low | STRUCT-COMPLEXITY | _check_network_subnet_overlap | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17266 | low | STRUCT-COMPLEXITY | _execute | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17353 | low | STRUCT-COMPLEXITY | _parse_template_selection | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 17479 | low | STRUCT-COMPLEXITY | _show_preview | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18599 | low | STRUCT-COMPLEXITY | _create_progress_display | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18700 | low | STRUCT-COMPLEXITY | _display_progress_distribution | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18732 | low | STRUCT-COMPLEXITY | _check_ssr_upgrades | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18807 | low | STRUCT-COMPLEXITY | _check_stored_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18851 | low | STRUCT-COMPLEXITY | _check_stored_upgrade | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18879 | low | STRUCT-COMPLEXITY | _check_audit_logs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 18955 | low | STRUCT-COMPLEXITY | _check_site_upgrades | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19371 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19476 | low | STRUCT-COMPLEXITY | _process_org | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 19981 | low | STRUCT-COMPLEXITY | _fetch_site_template_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20032 | low | STRUCT-COMPLEXITY | _is_template_assigned_to_site | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20049 | low | STRUCT-COMPLEXITY | _fetch_and_filter_org_wlans | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 20790 | low | STRUCT-COMPLEXITY | _display_wlans | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 21209 | low | STRUCT-COMPLEXITY | audit_log_analysis | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 22799 | low | STRUCT-COMPLEXITY | _systematic_test_resolve_fast_mode | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23319 | low | STRUCT-COMPLEXITY | _configure_runtime_options | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23391 | low | STRUCT-COMPLEXITY | _run_tui_event_loop | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23462 | low | STRUCT-COMPLEXITY | _resolve_cli_site_id | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23698 | low | STRUCT-COMPLEXITY | _dispatch_main_mode | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 23719 | low | STRUCT-COMPLEXITY | _has_meaningful_cli_args | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 6552 | medium | STRUCT-NESTING | flatten_dict | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 7889 | medium | STRUCT-NESTING | _pool_drain_wait_loop | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 14530 | medium | STRUCT-NESTING | _extract_gateway_models | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 14620 | medium | STRUCT-NESTING | _extract_country_codes | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 14712 | medium | STRUCT-NESTING | _extract_channel_country_codes | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 15838 | medium | STRUCT-NESTING | _dispatch_marvis_choice | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 18700 | medium | STRUCT-NESTING | _display_progress_distribution | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 20790 | medium | STRUCT-LENGTH | _display_wlans | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 21060 | medium | STRUCT-LENGTH | _export_audit_trail | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 21209 | medium | STRUCT-LENGTH | audit_log_analysis | Function spans 59 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 22744 | medium | STRUCT-LENGTH | _systematic_test_run_option | Function spans 53 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 22971 | medium | STRUCT-LENGTH | run_interactive_test | Function spans 38 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 23011 | medium | STRUCT-LENGTH | _launch_web_portal | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 23206 | medium | STRUCT-LENGTH | _setup_runtime_flags | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 23319 | medium | STRUCT-LENGTH | _configure_runtime_options | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 23391 | medium | STRUCT-LENGTH | _run_tui_event_loop | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 2941 | low | STRUCT-BLOCKS | initialize_mist_session | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 14530 | low | STRUCT-BLOCKS | _extract_gateway_models | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 14634 | low | STRUCT-BLOCKS | _normalize_states_data | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 16915 | low | STRUCT-BLOCKS | _check_network_subnet_overlap | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 17266 | low | STRUCT-BLOCKS | _execute | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 18700 | low | STRUCT-BLOCKS | _display_progress_distribution | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

### Phase: Medium (16 task(s))

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
- [ ] **CMP-003** `MistHelper.py:14530` - STRUCT-NESTING (Structure)
  - Symbol: `_extract_gateway_models`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_extract_gateway_models` in `MistHelper.py`.
- [ ] **CMP-004** `MistHelper.py:14620` - STRUCT-NESTING (Structure)
  - Symbol: `_extract_country_codes`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-005** `MistHelper.py:14712` - STRUCT-NESTING (Structure)
  - Symbol: `_extract_channel_country_codes`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_extract_channel_country_codes` in `MistHelper.py`.
- [ ] **CMP-006** `MistHelper.py:15838` - STRUCT-NESTING (Structure)
  - Symbol: `_dispatch_marvis_choice`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_dispatch_marvis_choice` in `MistHelper.py`.
- [ ] **CMP-007** `MistHelper.py:18700` - STRUCT-NESTING (Structure)
  - Symbol: `_display_progress_distribution`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_display_progress_distribution` in `MistHelper.py`.
- [ ] **CMP-008** `MistHelper.py:20790` - STRUCT-LENGTH (Structure)
  - Symbol: `_display_wlans`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_display_wlans` in `MistHelper.py`.
- [ ] **CMP-009** `MistHelper.py:21060` - STRUCT-LENGTH (Structure)
  - Symbol: `_export_audit_trail`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_export_audit_trail` in `MistHelper.py`.
- [ ] **CMP-010** `MistHelper.py:21209` - STRUCT-LENGTH (Structure)
  - Symbol: `audit_log_analysis`
  - Problem: Function spans 59 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `audit_log_analysis` in `MistHelper.py`.
- [ ] **CMP-011** `MistHelper.py:22744` - STRUCT-LENGTH (Structure)
  - Symbol: `_systematic_test_run_option`
  - Problem: Function spans 53 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_systematic_test_run_option` in `MistHelper.py`.
- [ ] **CMP-012** `MistHelper.py:22971` - STRUCT-LENGTH (Structure)
  - Symbol: `run_interactive_test`
  - Problem: Function spans 38 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run_interactive_test` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:23011` - STRUCT-LENGTH (Structure)
  - Symbol: `_launch_web_portal`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_launch_web_portal` in `MistHelper.py`.
- [ ] **CMP-014** `MistHelper.py:23206` - STRUCT-LENGTH (Structure)
  - Symbol: `_setup_runtime_flags`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_setup_runtime_flags` in `MistHelper.py`.
- [ ] **CMP-015** `MistHelper.py:23319` - STRUCT-LENGTH (Structure)
  - Symbol: `_configure_runtime_options`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_configure_runtime_options` in `MistHelper.py`.
- [ ] **CMP-016** `MistHelper.py:23391` - STRUCT-LENGTH (Structure)
  - Symbol: `_run_tui_event_loop`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_run_tui_event_loop` in `MistHelper.py`.

### Phase: Low (65 task(s))

- [ ] **CMP-017** `MistHelper.py:2941` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `initialize_mist_session`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `initialize_mist_session` in `MistHelper.py`.
- [ ] **CMP-018** `MistHelper.py:2941` - STRUCT-BLOCKS (Structure)
  - Symbol: `initialize_mist_session`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `initialize_mist_session` in `MistHelper.py`.
- [ ] **CMP-019** `MistHelper.py:5602` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `dict_list_as_pretty_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `dict_list_as_pretty_table` in `MistHelper.py`.
- [ ] **CMP-020** `MistHelper.py:6552` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `flatten_dict`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `flatten_dict` in `MistHelper.py`.
- [ ] **CMP-021** `MistHelper.py:7217` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_init_router`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_init_router` in `MistHelper.py`.
- [ ] **CMP-022** `MistHelper.py:7299` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_route_to_polyglot`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_route_to_polyglot` in `MistHelper.py`.
- [ ] **CMP-023** `MistHelper.py:8077` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_all_clients_for_site`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_all_clients_for_site` in `MistHelper.py`.
- [ ] **CMP-024** `MistHelper.py:8283` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_devices`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_devices` in `MistHelper.py`.
- [ ] **CMP-025** `MistHelper.py:8540` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_client_table`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_client_table` in `MistHelper.py`.
- [ ] **CMP-026** `MistHelper.py:8766` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `get_device_identifier`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `get_device_identifier` in `MistHelper.py`.
- [ ] **CMP-027** `MistHelper.py:9651` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_partition_combined_inventory_rows`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_partition_combined_inventory_rows` in `MistHelper.py`.
- [ ] **CMP-028** `MistHelper.py:10274` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_load_port_stats_sites`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_load_port_stats_sites` in `MistHelper.py`.
- [ ] **CMP-029** `MistHelper.py:10697` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_maybe_build_offline_record`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_maybe_build_offline_record` in `MistHelper.py`.
- [ ] **CMP-030** `MistHelper.py:11391` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_operator`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_operator` in `MistHelper.py`.
- [ ] **CMP-031** `MistHelper.py:11758` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_license_records`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_license_records` in `MistHelper.py`.
- [ ] **CMP-032** `MistHelper.py:12756` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `device_stats`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `device_stats` in `MistHelper.py`.
- [ ] **CMP-033** `MistHelper.py:12863` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `devices`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `devices` in `MistHelper.py`.
- [ ] **CMP-034** `MistHelper.py:12908` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `clients`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `clients` in `MistHelper.py`.
- [ ] **CMP-035** `MistHelper.py:13443` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_prompt_model_selection`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_prompt_model_selection` in `MistHelper.py`.
- [ ] **CMP-036** `MistHelper.py:13534` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `export_sites_by_ap_model`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `export_sites_by_ap_model` in `MistHelper.py`.
- [ ] **CMP-037** `MistHelper.py:13754` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `ha_cluster_info`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `ha_cluster_info` in `MistHelper.py`.
- [ ] **CMP-038** `MistHelper.py:14266` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_api_functions`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_api_functions` in `MistHelper.py`.
- [ ] **CMP-039** `MistHelper.py:14530` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_gateway_models`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_gateway_models` in `MistHelper.py`.
- [ ] **CMP-040** `MistHelper.py:14530` - STRUCT-BLOCKS (Structure)
  - Symbol: `_extract_gateway_models`
  - Problem: Function has 8 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_extract_gateway_models` in `MistHelper.py`.
- [ ] **CMP-041** `MistHelper.py:14594` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_get_country_codes_list`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_get_country_codes_list` in `MistHelper.py`.
- [ ] **CMP-042** `MistHelper.py:14620` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_country_codes`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_country_codes` in `MistHelper.py`.
- [ ] **CMP-043** `MistHelper.py:14634` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_normalize_states_data`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-044** `MistHelper.py:14634` - STRUCT-BLOCKS (Structure)
  - Symbol: `_normalize_states_data`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_normalize_states_data` in `MistHelper.py`.
- [ ] **CMP-045** `MistHelper.py:14683` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_filter_to_iso2_country_codes`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_filter_to_iso2_country_codes` in `MistHelper.py`.
- [ ] **CMP-046** `MistHelper.py:14712` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_channel_country_codes`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_channel_country_codes` in `MistHelper.py`.
- [ ] **CMP-047** `MistHelper.py:14881` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_collect_metrics_for_scope`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_collect_metrics_for_scope` in `MistHelper.py`.
- [ ] **CMP-048** `MistHelper.py:15076` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_results`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_results` in `MistHelper.py`.
- [ ] **CMP-049** `MistHelper.py:15456` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `fetch_synthetic_test_stats_with_retry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `fetch_synthetic_test_stats_with_retry` in `MistHelper.py`.
- [ ] **CMP-050** `MistHelper.py:15838` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_dispatch_marvis_choice`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_dispatch_marvis_choice` in `MistHelper.py`.
- [ ] **CMP-051** `MistHelper.py:16180` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `execute`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `execute` in `MistHelper.py`.
- [ ] **CMP-052** `MistHelper.py:16290` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_handle_message`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_handle_message` in `MistHelper.py`.
- [ ] **CMP-053** `MistHelper.py:16381` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_split_arp_text_into_datasets`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_split_arp_text_into_datasets` in `MistHelper.py`.
- [ ] **CMP-054** `MistHelper.py:16876` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_detect_conflicts`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_detect_conflicts` in `MistHelper.py`.
- [ ] **CMP-055** `MistHelper.py:16915` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-056** `MistHelper.py:16915` - STRUCT-BLOCKS (Structure)
  - Symbol: `_check_network_subnet_overlap`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_check_network_subnet_overlap` in `MistHelper.py`.
- [ ] **CMP-057** `MistHelper.py:17266` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute` in `MistHelper.py`.
- [ ] **CMP-058** `MistHelper.py:17266` - STRUCT-BLOCKS (Structure)
  - Symbol: `_execute`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_execute` in `MistHelper.py`.
- [ ] **CMP-059** `MistHelper.py:17353` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_template_selection`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_template_selection` in `MistHelper.py`.
- [ ] **CMP-060** `MistHelper.py:17479` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_show_preview`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_show_preview` in `MistHelper.py`.
- [ ] **CMP-061** `MistHelper.py:18599` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_create_progress_display`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_create_progress_display` in `MistHelper.py`.
- [ ] **CMP-062** `MistHelper.py:18700` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_progress_distribution`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_progress_distribution` in `MistHelper.py`.
- [ ] **CMP-063** `MistHelper.py:18700` - STRUCT-BLOCKS (Structure)
  - Symbol: `_display_progress_distribution`
  - Problem: Function has 7 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_display_progress_distribution` in `MistHelper.py`.
- [ ] **CMP-064** `MistHelper.py:18732` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_ssr_upgrades`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_ssr_upgrades` in `MistHelper.py`.
- [ ] **CMP-065** `MistHelper.py:18807` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrades` in `MistHelper.py`.
- [ ] **CMP-066** `MistHelper.py:18851` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_stored_upgrade`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_stored_upgrade` in `MistHelper.py`.
- [ ] **CMP-067** `MistHelper.py:18879` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_audit_logs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_audit_logs` in `MistHelper.py`.
- [ ] **CMP-068** `MistHelper.py:18955` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_check_site_upgrades`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_check_site_upgrades` in `MistHelper.py`.
- [ ] **CMP-069** `MistHelper.py:19371` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `MistHelper.py`.
- [ ] **CMP-070** `MistHelper.py:19476` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_process_org`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_process_org` in `MistHelper.py`.
- [ ] **CMP-071** `MistHelper.py:19981` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_site_template_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_site_template_wlans` in `MistHelper.py`.
- [ ] **CMP-072** `MistHelper.py:20032` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_is_template_assigned_to_site`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_is_template_assigned_to_site` in `MistHelper.py`.
- [ ] **CMP-073** `MistHelper.py:20049` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_and_filter_org_wlans`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_and_filter_org_wlans` in `MistHelper.py`.
- [ ] **CMP-074** `MistHelper.py:20790` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_wlans`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_wlans` in `MistHelper.py`.
- [ ] **CMP-075** `MistHelper.py:21209` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `audit_log_analysis`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `audit_log_analysis` in `MistHelper.py`.
- [ ] **CMP-076** `MistHelper.py:22799` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_systematic_test_resolve_fast_mode`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_systematic_test_resolve_fast_mode` in `MistHelper.py`.
- [ ] **CMP-077** `MistHelper.py:23319` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_configure_runtime_options`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_configure_runtime_options` in `MistHelper.py`.
- [ ] **CMP-078** `MistHelper.py:23391` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_run_tui_event_loop`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_run_tui_event_loop` in `MistHelper.py`.
- [ ] **CMP-079** `MistHelper.py:23462` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_resolve_cli_site_id`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_resolve_cli_site_id` in `MistHelper.py`.
- [ ] **CMP-080** `MistHelper.py:23698` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_dispatch_main_mode`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_dispatch_main_mode` in `MistHelper.py`.
- [ ] **CMP-081** `MistHelper.py:23719` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_has_meaningful_cli_args`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_has_meaningful_cli_args` in `MistHelper.py`.

