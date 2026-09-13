# Requirement Traceability

This record maps each feature requirement to named evidence.
A row is unproven when this review found no named test.

| Requirement | Subject | Evidence type | Test file and test name | State |
| - | - | - | - | - |
| FR-001 | Stale status uses `updated_at` and 24 hours. | unit | tests/unit/upgrade_portal/test_runs/test_staleness.py::test_stale_boundary_uses_exactly_24_hours | PROVEN |
| FR-002 | Terminal checks use `RunStateMachine.TERMINAL`. | unit | tests/unit/upgrade_portal/test_runs/test_staleness.py::test_legacy_terminal_sets_are_removed | PROVEN |
| FR-003 | History shows the last-update age. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py::test_stale_run_has_matching_age_and_badges | PROVEN |
| FR-004 | History shows the stale badge only for stale runs. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py::test_terminal_run_has_age_without_stale_badges | PROVEN |
| FR-005 | The run page uses the same stale decision. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py::test_stale_run_has_matching_age_and_badges | PROVEN |
| FR-006 | Unsafe time values produce `unknown`. | unit | tests/unit/upgrade_portal/test_runs/test_staleness.py::test_unknown_times_fail_closed | PROVEN |
| FR-007 | Display-only age updates do not change eligibility. | browser | tests/e2e/upgrade_portal/test_run_controls/test_stale.py::test_browser_age_update_changes_text_only | PROVEN |
| FR-008 | Only confirmed operator action reconciles a run. | browser | tests/e2e/upgrade_portal/test_run_controls/test_bulk.py::test_stale_stopping_run_reconciles_from_read_only_evidence | PROVEN |
| FR-009 | A stale pre-cloud run moves only to `cancelled`. | unit | tests/unit/upgrade_portal/test_runs/test_reconciliation.py::test_precloud_reconciliation_cancels_without_reading_cloud_evidence | PROVEN |
| FR-010 | A stale `stopping` run moves only to `stopped`. | integration | tests/integration/upgrade_portal/run_controls/test_reconciliation.py::test_complete_stopping_evidence_commits_run_outcome_and_digest_together | PROVEN |
| FR-011 | Reconciliation uses complete safe evidence. | unit | tests/unit/upgrade_portal/test_runs/test_reconciliation.py::test_stopped_reconciliation_outcome_requires_safe_matching_evidence | PROVEN |
| FR-012 | The portal claims `stopped` only with proof. | integration | tests/integration/upgrade_portal/run_controls/test_reconciliation.py::test_complete_stopping_evidence_commits_run_outcome_and_digest_together | PROVEN |
| FR-013 | Incomplete evidence gives `unknown` and no mutation. | unit | tests/unit/upgrade_portal/test_runs/test_reconciliation.py::test_incomplete_stopping_evidence_is_unknown_and_changes_no_run | PROVEN |
| FR-014 | Reconciliation sends no cloud mutation request. | unit | tests/unit/upgrade_portal/test_runs/test_reconciliation.py::test_precloud_reconciliation_cancels_without_reading_cloud_evidence | PROVEN |
| FR-015 | Run mutation and outcome commit together. | integration | tests/integration/upgrade_portal/run_controls/test_reconciliation.py::test_complete_stopping_evidence_commits_run_outcome_and_digest_together | PROVEN |
| FR-016 | A request has 1 through 50 run identifiers. | unit | tests/unit/upgrade_portal/test_runs/test_preview.py::test_request_rejects_an_unsafe_batch_size | PROVEN |
| FR-017 | The server rejects duplicate identifiers. | unit | tests/unit/upgrade_portal/test_runs/test_preview.py::test_request_rejects_duplicate_identifiers_without_deduplication | PROVEN |
| FR-018 | The browser requests preview before phrase entry. | browser | tests/e2e/upgrade_portal/test_run_controls/test_bulk.py::test_bulk_selection_survives_reload_but_requires_a_new_preview | PROVEN |
| FR-019 | Preview removes non-visible identifiers. | unit | tests/unit/upgrade_portal/test_runs/test_preview.py::test_preview_removes_hidden_and_absent_identifiers_and_returns_exact_counts | PROVEN |
| FR-020 | Preview returns exact retained counts. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_preview.py::test_preview_returns_authoritative_selection_counts_phrase_and_token | PROVEN |
| FR-021 | The preview token binds actor, action, scope, order, and counts. | unit | tests/unit/upgrade_portal/test_runs/test_preview.py::test_token_verification_binds_actor_action_scope_order_and_counts | PROVEN |
| FR-022 | Cancel confirmation uses `CANCEL <run-count> RUNS`. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_bulk_preview.py::test_preview_returns_authoritative_selection_counts_phrase_and_token | PROVEN |
| FR-023 | Retry confirmation uses `RETRY <run-count> RUNS`. | unit | tests/unit/upgrade_portal/test_runs/test_preview.py::test_preview_applies_the_current_history_scope | PROVEN |
| FR-024 | Initialization creates ordered placeholders. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_action_initialization_keeps_ordered_unknown_placeholders | PROVEN |
| FR-025 | Each initialized run has one durable outcome. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_finalize_requires_every_item_to_have_one_final_outcome | PROVEN |
| FR-026 | No-mutation results use outcome-only writes. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_outcome_only_write_finalizes_one_claimed_item_and_changes_no_run | PROVEN |
| FR-027 | The portal rechecks permission and lock token. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_bulk_cancel_processes_stable_sites_and_stops_one_site_after_token_loss | PROVEN |
| FR-028 | Guard failure stops later writes for that site. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_bulk_cancel_processes_stable_sites_and_stops_one_site_after_token_loss | PROVEN |
| FR-029 | Blocked site items use the guard-loss reason. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_bulk_cancel_processes_stable_sites_and_stops_one_site_after_token_loss | PROVEN |
| FR-030 | One site failure does not stop another site. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_bulk_cancel_processes_stable_sites_and_stops_one_site_after_token_loss | PROVEN |
| FR-031 | Cancel accepts only current pre-cloud state. | manual | No named refusal test found. Future test must assert a current non-pre-cloud cancel refusal and no run change. | UNPROVEN |
| FR-032 | Cancel sends no cloud request. | integration | tests/integration/upgrade_portal/run_controls/test_performance.py::test_no_cloud_batch_cancels_fifty_runs_under_the_spec_target | PROVEN |
| FR-033 | Cancel mutation and outcome commit atomically. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_atomic_success_changes_the_run_and_outcome_together | PROVEN |
| FR-034 | Retry accepts failed, stopped, or cancelled sources only. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_selects_newest_source_by_time_then_run_id | PROVEN |
| FR-035 | A retry source has valid `updated_at`. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_refuses_an_unknown_source_time | PROVEN |
| FR-036 | Newest retry source uses time then run identifier. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_selects_newest_source_by_time_then_run_id | PROVEN |
| FR-037 | Retry uses the exact option allowlist. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_uses_the_exact_approved_top_level_allowlist | PROVEN |
| FR-038 | Nested options match the current validator fields. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_applies_the_exact_allowlist_and_existing_validator | PROVEN |
| FR-039 | Unknown or invalid options cause deterministic refusal. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_applies_the_exact_allowlist_and_existing_validator | PROVEN |
| FR-040 | Retry validates copied options. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_applies_the_exact_allowlist_and_existing_validator | PROVEN |
| FR-041 | Retry copies targets and approved options only. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_bulk_retry_creates_only_the_newest_source_and_copies_safe_fields | PROVEN |
| FR-042 | Retry drops old pre-checks and unsafe schedule fields. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_retry_policy_applies_the_exact_allowlist_and_existing_validator | PROVEN |
| FR-043 | Retry live check, insert, and outcome commit together. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_atomic_retry_rechecks_the_source_and_live_site_runs | PROVEN |
| FR-044 | Idempotency uses durable actor scope and request key. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_durable_actor_scope_ignores_browser_and_session_values | PROVEN |
| FR-045 | Browser and session identifiers do not define idempotency. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_durable_actor_scope_ignores_browser_and_session_values | PROVEN |
| FR-046 | Another actor receives 404 for another action. | browser | tests/e2e/upgrade_portal/test_run_controls/test_isolation.py::test_response_loss_recovers_by_read_and_preserves_actor_scope | PROVEN |
| FR-047 | The action store uses the composite domain key. | unit | tests/unit/upgrade_portal/test_runs/test_actions.py::test_upgrade_run_actions_strategy_matches_the_data_model | PROVEN |
| FR-048 | The primary-key strategy was added before persistence. | manual | `tests/unit/upgrade_portal/test_runs/test_actions.py::test_upgrade_run_actions_strategy_matches_the_data_model` proves the strategy. No test proves implementation order. | UNPROVEN |
| FR-049 | Same-key same-request replay returns the stored record. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_initialize_returns_the_same_action_for_the_same_request_key | PROVEN |
| FR-050 | Same-key different-request replay returns conflict. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_initialize_rejects_the_same_key_for_different_request_content | PROVEN |
| FR-051 | Replay returns leases and recovery handles claimed items. | integration | tests/integration/upgrade_portal/run_controls/test_recovery.py::test_same_key_active_lease_returns_processing_without_new_work | PROVEN |
| FR-052 | Recovery does not repeat claimed or final items. | integration | tests/integration/upgrade_portal/run_controls/test_recovery.py::test_recovery_resumes_only_pending_items_and_finalizes_every_item | PROVEN |
| FR-053 | Factory overrides install before route registration. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_isolation.py::test_factory_installs_overrides_before_blueprint_registration | PROVEN |
| FR-054 | Browser tests trap all external stores. | unit | tests/unit/upgrade_portal/test_runs/test_isolation.py::test_each_trap_records_and_fails_with_the_contract_message | PROVEN |
| FR-055 | The child environment scrubs credentials and paths. | unit | tests/unit/upgrade_portal/test_runs/test_isolation.py::test_child_environment_scrubs_credentials_paths_and_uses_sentinels | PROVEN |
| FR-056 | The child uses loopback port-1 sentinels. | unit | tests/unit/upgrade_portal/test_runs/test_isolation.py::test_child_environment_scrubs_credentials_paths_and_uses_sentinels | PROVEN |
| FR-057 | Each browser session uses unique resources. | unit | tests/unit/upgrade_portal/test_runs/test_isolation.py::test_resource_allocation_uses_unique_ports_paths_and_identifiers | PROVEN |
| FR-058 | E2E responses include the test run identifier only under overrides. | contract | tests/contract/upgrade_portal/test_upgrade_routes/test_isolation.py::test_e2e_header_is_present_only_for_overrides | PROVEN |
| FR-059 | The complete browser suite runs after isolation controls. | manual | `tests/e2e/upgrade_portal/conftest.py::persistent_store_baseline` wraps the suite. No completed full-suite run record was found. | UNPROVEN |
| FR-060 | ArangoDB is the only authority for action outcomes. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_missing_arango_store_has_no_fallback_path | PROVEN |
| FR-061 | Unavailable ArangoDB fails closed without fallback. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_action_repository_imports_no_fallback_backend | PROVEN |
| FR-062 | Action indexes support actor-scoped reads. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_bootstrap_creates_only_the_action_collection_and_required_indexes | PROVEN |
| FR-063 | Deployment creates and verifies an ArangoDB backup. | manual | `specs/2447-stale-bulk-run-controls/recovery-drill.md` verifies one backup by inspection. No deployment log proves creation before schema work. | UNPROVEN |
| FR-064 | Recovery restore verifies run and action collections. | manual | `specs/2447-stale-bulk-run-controls/recovery-drill.md` gives the restore checks. No isolated restore result was found. | UNPROVEN |
| FR-065 | Action records persist for the lifetime of run records. | manual | `specs/2447-stale-bulk-run-controls/recovery-drill.md` records the retention rule. `rtk git grep -n -i "action cleanup" -- tests src specs` found no source cleanup path. | PROVEN |
| FR-066 | The portal reports success only after durable verification. | integration | tests/integration/upgrade_portal/run_controls/test_actions.py::test_atomic_success_changes_the_run_and_outcome_together | PROVEN |
| FR-067 | The verification matrix covers all requirements. | manual | specs/2447-stale-bulk-run-controls/traceability.md row count review | PROVEN |
| FR-068 | The feature manifest includes all measured feature paths. | manual | feature-files.txt comparison with merge-base diff and status | PROVEN |
| FR-069 | The team claimed the issue and checked overlap first. | manual | No issue claim or overlap evidence found. Future evidence must show the issue claim and overlap check before source edits. | UNPROVEN |
| FR-070 | The staging step uses the explicit manifest. | manual | No staging evidence found. Future evidence must show `git add -A --pathspec-from-file=specs/2447-stale-bulk-run-controls/feature-files.txt`. | UNPROVEN |
| FR-071 | Feature-caused failures stay in this feature. | manual | No failure triage evidence found. Future evidence must show each feature-caused failure and the feature repair. | UNPROVEN |
| FR-072 | Unrelated repairs get an issue first. | manual | No unrelated-failure issue evidence found. Future evidence must show the GitHub issue before any unrelated repair. | UNPROVEN |
| FR-073 | Verification measures both fixed performance workloads. | integration | tests/integration/upgrade_portal/run_controls/test_performance.py::test_no_cloud_batch_cancels_fifty_runs_under_the_spec_target | PROVEN |
| FR-074 | README, operator guide, and changelog update before gates. | manual | `README.md` is modified. No changed `CHANGELOG.md` or operator guide was found in this review. | UNPROVEN |
| FR-075 | Deployment completes the full pull request workflow. | manual | No pull request, CI, merge, image, or deployment evidence found. Future evidence must include each workflow step. | UNPROVEN |
| FR-076 | Tests start no live Morrison House firmware action. | browser | tests/e2e/upgrade_portal/test_run_controls/test_isolation.py::test_each_isolated_response_has_owner_and_zero_hard_trap_counts | PROVEN |

## Summary

- PROVEN requirements: 65
- UNPROVEN requirements: 11

UNPROVEN requirements:

- FR-031: Cancel accepts only current pre-cloud state.
- FR-048: The primary-key strategy was added before persistence.
- FR-059: The complete browser suite runs after isolation controls.
- FR-063: Deployment creates and verifies an ArangoDB backup.
- FR-064: Recovery restore verifies run and action collections.
- FR-069: The team claimed the issue and checked overlap first.
- FR-070: The staging step uses the explicit manifest.
- FR-071: Feature-caused failures stay in this feature.
- FR-072: Unrelated repairs get an issue first.
- FR-074: README, operator guide, and changelog update before gates.
- FR-075: Deployment completes the full pull request workflow.
