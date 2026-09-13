# Tasks 1007 — site_auto_upgrade.py compliance

Task ordering follows the phase plan. Each task is atomic and gate-testable.

## Phase 1 — Config skeleton

- [ ] T1.1 — Add `SiteAutoUpgradeConfig` frozen slots kw_only dataclass with
  permissive `__post_init__` (validate `org_id` str, `dry_run` bool only).
- [ ] T1.2 — Add `_resolve_configurator_kwargs(cfg: dict) -> SiteAutoUpgradeConfig`.
- [ ] T1.3 — Rewrite `SiteAutoUpgradeConfigurator.__init__` to `def __init__(self, **cfg)`.
- [ ] T1.4 — Add `_apply_config_to_attributes(self)` (6 self.* lines).
- [ ] T1.5 — Add `_reset_workflow_state(self)` (11 self.* lines).
- [ ] T1.6 — Remove `# pylint: disable=too-many-instance-attributes`.

## Phase 2 — execute + MSP mode entry

- [ ] T2.1 — Decompose `execute`: extract `_dispatch_mode`.
- [ ] T2.2 — Remove `# noqa: PLR0913, STRUCT-PARAMS` from `execute`.
- [ ] T2.3 — Decompose `_handle_msp_mode`: extract `_print_msp_mode_banner`,
  `_dispatch_msp_mode_choice`.
- [ ] T2.4 — Decompose `_execute_msp_mode`: extract `_msp_gather_config`.
- [ ] T2.5 — Decompose `_msp_confirm_and_apply`: extract
  `_prompt_msp_final_confirm`, `_apply_msp_config`.
- [ ] T2.6 — Decompose `_apply_to_all_orgs`: extract `_configure_single_msp_org`.
- [ ] T2.7 — Decompose `_msp_select_entities`: extract `_select_msps_or_bail`,
  `_select_orgs_or_bail`.

## Phase 3 — Interactive workflow steps

- [ ] T3.1 — Decompose `_step3_fetch_available_versions`: extract
  `_fetch_available_versions_payload`, `_ingest_available_versions_payload`.
- [ ] T3.2 — Decompose `_step4_select_versions`: extract
  `_prefill_current_site_versions`, `_process_family_selection_loop`.
- [ ] T3.3 — Decompose `_step6_confirm_and_apply`: extract
  `_prompt_step6_confirm`, `_apply_step6_settings`.
- [ ] T3.4 — Decompose `_select_single_site`: extract
  `_prompt_single_site_index`, `_apply_single_site_choice`.
- [ ] T3.5 — Decompose `_fetch_current_site_settings`: extract
  `_read_site_settings_payload`, `_ingest_auto_upgrade_block`.
- [ ] T3.6 — Decompose `_apply_site_indices`: extract
  `_collect_valid_site_choices`, `_report_selected_sites`.
- [ ] T3.7 — Decompose `_apply_family_selection`: extract
  `_apply_family_numeric_choice`, `_apply_family_default_choice`.
- [ ] T3.8 — Decompose `run_msp_mode`: extract `_msp_ensure_versions`.
- [ ] T3.9 — Decompose `_apply_auto_upgrade_config`: extract
  `_build_auto_upgrade_settings`, `_report_apply_outcome`.

## Phase 4 — Module-level helpers

- [ ] T4.1 — Decompose `_get_shared_schedule`: extract
  `_prompt_msp_day_of_week`, `_prompt_msp_time_of_day`.
- [ ] T4.2 — Decompose `_get_shared_firmware_versions`: extract
  `_fetch_reference_org_versions`, `_shared_versions_from_map`.
- [ ] T4.3 — Decompose `_select_versions_interactively`: extract
  `_prompt_family_version_choice`, `_dispatch_family_choice`.
- [ ] T4.4 — Decompose `_msp_get_firmware_config`: extract
  `_prompt_msp_firmware_source_choice`.
- [ ] T4.5 — Decompose `_apply_settings_to_sites`: extract
  `_apply_settings_to_single_site`.
- [ ] T4.6 — Decompose `_print_msp_summary`: extract
  `_print_msp_summary_header`, `_print_msp_summary_totals`.
- [ ] T4.7 — Decompose `_build_model_version_map`: extract predicate
  `_is_valid_version_entry`.
- [ ] T4.8 — Decompose `_build_version_map_from_list`: same predicate pattern.
- [ ] T4.9 — Decompose `_parse_index_selection`: extract `_parse_range_part`,
  `_parse_single_part`.
- [ ] T4.10 — Decompose `_pick_stable_version`: extract
  `_first_stable_or_none`, `_first_any_version`.
- [ ] T4.11 — Decompose `parse_time_input`: extract `_parse_time_markers`.

## Phase 5 — Suppression removal

- [ ] T5.1 — Remove `# pylint: disable=too-many-lines` from module head.
- [ ] T5.2 — Remove `# pylint: disable=too-many-instance-attributes` (done in T1.6).
- [ ] T5.3 — Remove `# noqa: PLR0913, STRUCT-PARAMS` (done in T2.2).
- [ ] T5.4 — Grep for any `# type: ignore`, `# pragma: no cover`,
  `# pylint: disable` — must return zero hits.

## Phase 6 — Inline WHY comment coverage

- [ ] T6.1 — Ensure every new executable line has a trailing `# WHY:` or
  `# ` explanatory comment.
- [ ] T6.2 — Preserve existing 96.9% coverage on unchanged lines.
- [ ] T6.3 — Add `logging.info` before each mutation/API call and
  `logging.debug` after each mutation.

## Phase 7 — Local gates

- [ ] T7.1 — `python -m py_compile src/firmware/site_auto_upgrade.py`.
- [ ] T7.2 — `ruff check src/firmware/site_auto_upgrade.py`.
- [ ] T7.3 — `black --check src/firmware/site_auto_upgrade.py`.
- [ ] T7.4 — `mypy --strict src/firmware/site_auto_upgrade.py`.
- [ ] T7.5 — `python -m tools.compliance_analyzer --paths src/firmware/site_auto_upgrade.py`
  → must report **100.0 / A+** with **zero violations**.
- [ ] T7.6 — `pytest tests/unit/test_site_auto_upgrade.py -x`.

## Phase 8 — Byte-identity gate

- [ ] T8.1 — `git diff main..HEAD -- MistHelper.py` returns exactly 0 bytes.
- [ ] T8.2 — Save diff evidence to
  `specs/1007-site-auto-upgrade-compliance/artifacts/final_misthelper_diff.txt`.
- [ ] T8.3 — Save callsite evidence to
  `specs/1007-site-auto-upgrade-compliance/artifacts/callsites.txt`.

## Phase 9 — Final artifacts

- [ ] T9.1 — Save final compliance report to
  `artifacts/final_compliance_report.md`.
- [ ] T9.2 — Save `final_ruff.txt`, `final_black.txt`, `final_mypy.txt`,
  `final_py_compile.txt`.
- [ ] T9.3 — Tick every checkbox in this tasks.md.

## Phase 10 — Ship

- [ ] T10.1 — Commit with conventional-commits style message.
- [ ] T10.2 — Push branch `refactor/site-auto-upgrade-compliance` to origin.
- [ ] T10.3 — Open PR against `main` with body summarizing score delta.
- [ ] T10.4 — Watch CI. If failure, iterate.
- [ ] T10.5 — Squash-merge with `--delete-branch`.

## Baseline-violation cross-reference

The 39 violations from
`artifacts/baseline_compliance_report.md` are all subsumed by Phases 1–5:

- STRUCT-LENGTH (19) → Phases 1, 2, 3, 4 decompositions.
- STRUCT-COMPLEXITY (17) → Phases 2, 3, 4 CC-reduction extractions.
- STRUCT-BLOCKS (3) → Phase 3 (`_fetch_current_site_settings`,
  `_apply_family_selection`, `_select_versions_interactively`).

Success gate: **zero** remaining violations across all three rule families.
