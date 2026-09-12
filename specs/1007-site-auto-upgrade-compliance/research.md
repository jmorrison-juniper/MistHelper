# Research 1007 — Hotspot analysis

Detailed decomposition strategy per hotspot function. Each block lists:
- Current baseline (LOC/CC/blocks)
- Root cause of the excess
- Extraction plan with helper names
- Any behavioral invariants to preserve

## `_get_shared_schedule` (HIGH — LOC 61)

- **Root cause**: Two independent prompts (day-of-week + time-of-day) each
  with their own map + error handling all inlined.
- **Extract**:
  - `_prompt_msp_day_of_week(safe_input_fn) -> str | None` — reads day input,
    returns canonical day-name or `None` on operator abort.
  - `_prompt_msp_time_of_day(safe_input_fn) -> str | None` — reads time input,
    normalizes 'any', returns HH:MM string or `None` on abort.
  - Outer `_get_shared_schedule` becomes a 6-line composer.
- **Invariant**: default day is `"any"`, default time is `"02:00"`; abort at
  either prompt returns `None`.

## `_fetch_current_site_settings` (CC 10, blocks 6)

- **Root cause**: 6 sequential `if` guards on the settings payload + two
  optional field pre-fills, all wrapped in a single try/except.
- **Extract**:
  - `_read_site_settings_payload(apisession, site_id) -> dict[str, Any] | None`
    — API call + response-shape guards, returns unwrapped settings dict or
    `None`.
  - `_ingest_auto_upgrade_block(settings, schedule, ...) -> dict[str, str]`
    — pure ingestion of `auto_upgrade` sub-dict into the current-versions
    dict and schedule dict.
- **Invariant**: any exception in the API call or ingestion causes silent
  return (lenient contract) with `logging.debug` trace.

## `_apply_family_selection` (CC 9, LOC 26, blocks 6)

- **Root cause**: three-way branch on `choice` (numeric / empty+current /
  empty+no-current) with a nested loop inside the numeric branch.
- **Extract**:
  - `_apply_family_numeric_choice(idx, custom_versions, ctx) -> None` —
    guard the index, loop the models, print confirmation.
  - `_apply_family_default_choice(custom_versions, ctx) -> None` — Enter path
    (keep-current or skip-family).
- **Invariant**: `_apply_family_selection(choice, custom_versions, ctx)`
  keeps 3-param signature (used by tests).

## `_get_shared_firmware_versions` (CC 8, LOC 51)

- **Root cause**: API fetch + response shape guards + fallback empties +
  interactive selection all inline.
- **Extract**:
  - `_fetch_reference_org_versions(apisession, org_id_str) ->
    list[Any] | None` — API call + guards.
  - `_shared_versions_from_map(model_version_map, safe_input_fn) ->
    dict[str, str] | None` — interactive selection over the map.
- **Invariant**: empty dict returned when fetch fails; `None` returned only
  when operator cancels.

## `_select_versions_interactively` (CC 8, LOC 46, blocks 6)

- **Root cause**: 4-way choice dispatch inside a family loop with
  sub-selects into helpers.
- **Extract**:
  - `_prompt_family_version_choice(family, sorted_versions, safe_input_fn)
    -> str | None` — reads choice, returns raw string or `None` on abort.
  - `_dispatch_family_choice(choice, sorted_versions, model_family_bundle,
    custom_versions) -> bool` — returns `False` on 'q', `True` on any other
    outcome; branches on numeric/empty/invalid inside.
- **Invariant**: 'q' returns `None` from outer function; empty and invalid
  each just skip the family and continue the loop.

## `_execute_msp_mode` (CC 7, LOC 40)

- **Root cause**: linear pipeline (select entities → select firmware →
  select schedule → apply) with `None`-guards after every step.
- **Extract**:
  - `_msp_gather_config(core, msp) -> tuple[list, dict, dict|None] | None`
    — runs the three gather steps, returns triple or `None` on any abort.
  - Outer function becomes: guard-clause + gather + call
    `_msp_confirm_and_apply`.

## `_step3_fetch_available_versions` (CC 7, LOC 27)

- **Root cause**: API call + response guards + assignment + map build +
  count print all inline.
- **Extract**:
  - `_fetch_available_versions_payload(apisession, org_id) -> list[Any] | None`
    — API call + response.data extraction.
  - Outer function stays as ingest + print.

## `_step4_select_versions` (CC 7, LOC 46)

- **Root cause**: pre-fill + family loop with per-family select body.
- **Extract**:
  - `_prefill_current_site_versions(self)` — the two-line pre-fill.
  - `_process_family_selection_loop(self, model_families) -> bool` — the
    for-loop over families with the prompt + apply. Returns `False` on abort.

## `_step6_confirm_and_apply` (LOC 36)

- **Root cause**: summary + optional confirm + build payload + apply +
  final print.
- **Extract**:
  - `_prompt_step6_confirm(safe_input_fn, dry_run) -> bool` — returns
    proceed/cancel.
  - `_apply_step6_settings(self, settings) -> tuple[int, int]` — apply +
    return counts.

## `_apply_auto_upgrade_config` (LOC 33)

- **Root cause**: build settings + label + delegate + report.
- **Extract**:
  - `_build_auto_upgrade_settings(schedule, custom_versions) -> dict`
  - `_report_apply_outcome(success_count, fail_count, dry_run)` — the
    three post-apply prints.

## `_apply_to_all_orgs` (LOC 43)

- **Root cause**: per-org loop with configurator build + attribute
  assignment + result accumulation.
- **Extract**:
  - `_configure_single_msp_org(core, org_info, idx, total, shared_schedule,
    shared_versions) -> dict[str, Any]` — the whole per-org body, returns
    the result dict.
- **Invariant**: iteration order preserved; per-org headers preserved.

## `_msp_confirm_and_apply` (LOC 40)

- **Root cause**: summary + confirm + apply + summary all inline.
- **Extract**:
  - `_prompt_msp_final_confirm(safe_input_fn) -> bool`.
  - `_apply_msp_config(core, selected_orgs, shared_schedule, shared_versions)
    -> list[dict[str, Any]]` — banner + delegate + return.

## `_msp_get_firmware_config` (LOC 37)

- **Root cause**: prompt + branch on choice ('2' → manual, else → auto).
- **Extract**:
  - `_prompt_msp_firmware_source_choice(safe_input_fn) -> str | None`.
  - Body becomes 3 lines: prompt + guard + dispatch.

## `_handle_msp_mode` (LOC 31)

- **Root cause**: banner + prompt + branch on mode.
- **Extract**:
  - `_print_msp_mode_banner(dry_run)`.
  - `_dispatch_msp_mode_choice(mode, core, msp, get_org_id_fn)`.

## `_msp_select_entities` (LOC 28)

- **Root cause**: 2-step select with 2 guards + prints.
- **Extract**:
  - `_select_msps_or_bail(select_msps_fn) -> list[Any] | None`.
  - `_select_orgs_or_bail(select_orgs_fn, selected_msps) -> list[dict] | None`.

## `_select_single_site` (LOC 26, CC 5)

- **Root cause**: prompt + numeric validation + index range + apply.
- **Extract**:
  - `_prompt_single_site_index(safe_input_fn, count) -> int | None` — parses
    input to a 0-based index or returns `None` on quit/invalid.
  - `_apply_single_site_choice(self, idx)` — sets selected_sites,
    fetches settings.

## `_apply_site_indices` (LOC 24, CC 6)

- **Root cause**: nested if inside for + subsequent report block.
- **Extract**:
  - `_collect_valid_site_choices(indices, all_sites) -> list[dict]` — pure
    filter.
  - `_report_selected_sites(selected_sites)` — the 5-print preview block.

## `_apply_settings_to_sites` (LOC 36, CC 6)

- **Root cause**: loop + per-site try/except with dry-run branch.
- **Extract**:
  - `_apply_settings_to_single_site(site, settings, apisession, dry_run)
    -> bool` — returns True on success, False on failure. Prints and logs
    the outcome.
- Loop becomes: stop-check → delegate → increment counter.

## `_print_msp_summary` (LOC 33, CC 6)

- **Root cause**: title + dry-run banner + totals + failed listing.
- **Extract**:
  - `_print_msp_summary_header(dry_run)`.
  - `_print_msp_summary_totals(total_orgs, successful_orgs, total_sites,
    dry_run)`.

## `_build_model_version_map` (CC 6)

- **Root cause**: two nested `if`s + a dict-lookup guard.
- **Extract**:
  - `_is_valid_version_entry(entry) -> bool` — predicate.
  - `_record_model_version(map_, entry) -> None`.

## `_build_version_map_from_list` (CC 6)

- Same pattern as `_build_model_version_map`. Reuse the predicates where
  possible (they build different value shapes so keep them distinct).

## `_parse_index_selection` (CC 6)

- **Root cause**: two try/except with three-level nesting on the range branch.
- **Extract**:
  - `_parse_range_part(part) -> set[int]` — returns range set or empty on
    parse fail.
  - `_parse_single_part(part) -> set[int]` — returns singleton or empty.

## `_pick_stable_version` (CC 7)

- **Root cause**: cascade of isinstance/dict/getattr guards.
- **Extract**:
  - `_first_stable_or_none(versions) -> str | None`.
  - `_first_any_version(versions) -> str` — coerces to string.

## `parse_time_input` (CC 7)

- **Root cause**: AM/PM detection + parse + range validate + format all
  linear.
- **Extract**:
  - `_parse_time_markers(time_upper) -> tuple[bool, bool, str]` — returns
    (is_am, is_pm, cleaned).
- Body becomes: guard-empty → markers → parse → apply_ampm → range-check →
  format.

## `run_msp_mode` (CC 6)

- **Root cause**: shared-versions dispatch + version-map fetch fallback.
- **Extract**:
  - `_msp_ensure_versions(self) -> bool` — the shared-versions vs. fetch
    branch.

## `__init__` (LOC 35)

- **Root cause**: 15+ `self.<attr> =` lines + debug log.
- **Extract**:
  - `_apply_config_to_attributes(self, cfg)` — the 6 DI-derived attributes.
  - `_reset_workflow_state(self)` — the 11 workflow-scoped attributes
    (`all_sites`, `selected_sites`, `custom_versions`, `schedule`, etc.).
- Constructor becomes: parse cfg → apply → reset → debug log.

## `execute` (LOC 49)

- **Root cause**: entry log + dry-run banner + build core deps + MSP branch +
  MSP-deps build + dispatch.
- **Extract**:
  - `_build_core_deps_from_kwargs(...) -> SiteAutoUpgradeCoreDeps`.
  - `_dispatch_mode(core_deps, msp_privileges, msp_deps, get_org_id_fn) -> None`.
- Body becomes: log entry → build → dispatch. Params kept unchanged.
