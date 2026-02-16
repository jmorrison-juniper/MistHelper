# Menu 115-120 Refactoring Progress

**Goal**: Refactor all functions/methods to comply with 25-line limit per agents.md

**Status Key**: [ ] Not Started | [~] In Progress | [X] Complete | [-] Skipped

---

## Menu 115: switch_to_interactive_login
- [X] `switch_to_interactive_login` (71 lines -> 4 functions: 19, 21, 13, 21 lines)

## Menu 116: OrgLevelAPFirmwareUpgrader
- [ ] `_step1_select_site_scope` (30 lines)
- [ ] `_select_specific_sites` (48 lines)
- [ ] `_parse_selection_input` (32 lines)
- [ ] `_fetch_org_aps` (30 lines)
- [ ] `_fetch_selected_sites_aps` (32 lines)
- [ ] `_step3_fetch_firmware_stats` (42 lines)
- [ ] `_step4_fetch_available_firmware` (36 lines)
- [ ] `_step5_select_firmware_versions` (58 lines)
- [ ] `_step6_configure_upgrade` (34 lines)
- [ ] `_step7_confirm_and_execute` (46 lines)
- [ ] `_execute_dry_run` (32 lines)
- [ ] `_execute_upgrades` (50 lines)

## Menu 117: MSPInventoryExporter
- [ ] `_run` (49 lines)
- [ ] `_process_msp` (45 lines)
- [ ] `_process_org` (61 lines)
- [ ] `_write_results` (37 lines)
- [ ] `_print_summary` (31 lines)

## Menu 118: SiteAutoUpgradeConfigurator
- [ ] `_step2_select_sites` (30 lines)
- [ ] `_select_single_site` (37 lines)
- [ ] `_select_from_list` (54 lines)
- [ ] `_step3_fetch_available_versions` (37 lines)
- [ ] `_step4_select_versions` (84 lines)
- [ ] `_step5_configure_schedule` (58 lines)
- [ ] `_parse_time_input` (50 lines)
- [ ] `_step6_confirm_and_apply` (62 lines)

## Menu 119: ZoneConfigurationAnalyzer
- [ ] `_collect_all_site_settings` (62 lines)
- [ ] `_analyze_engagement_patterns` (77 lines)
- [ ] `_analyze_occupancy_patterns` (62 lines)

## Menu 120: SiteAnalyticsConfigurator
- [ ] `_scan_for_deviations` (51 lines)
- [ ] `_check_deviations` (72 lines)
- [ ] `_compare_engagement` (46 lines)

---

## Session Log

| Date | Menu | Method | Before | After | Notes |
|------|------|--------|--------|-------|-------|
