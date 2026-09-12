# Contract: Signature changes

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Date**: 2026-07-29

This file is the authoritative list of every signature that the feature
changes. A function signature is an internal interface. This contract records
the shape before the change and the shape after the change. It also names every
call site that must change in the same task.

A row marked **cascade** is not in the measured baseline. Pylint reports it only
after the level below it loses the parameter. Section 3 of `research.md`
explains the rule.

Warning: a removal in group 4, group 7, and group 8 shifts a positional
argument. If you drop the parameter and leave a call site unchanged, the
remaining arguments bind to the wrong parameters. Change the signature and every
call site in the same edit.

---

## Group 1. `src/capture/packet_capture.py`

| Item | Value |
| - | - |
| Before | `def _multi_ap_gather_params(self, ap_macs: list[str]) -> dict[str, Any] \| None:` |
| After | `def _multi_ap_gather_params(self) -> dict[str, Any] \| None:` |
| Call site | `packet_capture.py:1018`, `self._multi_ap_gather_params(ap_macs)` becomes `self._multi_ap_gather_params()` |
| Tests to update | None |
| Cascade | None. The caller still passes `ap_macs` to `_multi_ap_confirm_and_launch`. |

---

## Group 2. `src/firmware/bulk_ap_upgrader.py`

| Item | Value |
| - | - |
| Before | `def _upgrade_version_group(self, site_id: str, site_name: str, version: str, version_info: dict[str, Any], mistapi: Any) -> None:` |
| After | Drop the final parameter `mistapi`. |
| Call site | `bulk_ap_upgrader.py:1479` |
| Tests to update | `tests/unit/test_bulk_ap_upgrader.py:1724` |

**Cascade level 1**

| Item | Value |
| - | - |
| Before | `def _execute_multi_version_upgrade(self, site_id: str, site_name: str, site_data: dict[str, Any], mistapi: Any) -> None:` |
| After | Drop the final parameter `mistapi`. |
| Call site | `bulk_ap_upgrader.py:1399`, inside `_execute_site_upgrade` |
| Tests to update | `tests/unit/test_bulk_ap_upgrader.py:1702` |

**Stop condition**: `_execute_site_upgrade` keeps its `mistapi` parameter. It
also calls `_execute_single_version_upgrade`, which uses `mistapi`.

---

## Group 3. `src/firmware/org_ap_upgrader.py`

| Item | Value |
| - | - |
| Before | `def _display_org_list(self, orgs: list[Any], msp_name: str) -> None:` |
| After | `def _display_org_list(self, orgs: list[Any]) -> None:` |
| Call site | `org_ap_upgrader.py:617` |
| Tests to update | None |
| Cascade | None. The caller still passes `msp_name` to `_collect_org_selection` and to the error log. |

---

## Group 4. `src/inventory/inventory_summary/version_per_model_fetcher.py`

Warning: `target_org_id` is the first positional parameter in both functions.
Every call site passes it positionally.

| Item | Value |
| - | - |
| Before | `def _rows_for_model(target_org_id: str, model_row: dict, switch_records: list[dict], gateway_records: list[dict]) -> list[dict]:` |
| After | Drop the first parameter `target_org_id`. |
| Call site | `version_per_model_fetcher.py:25` |
| Tests to update | `tests/unit/inventory/test_version_per_model_fetcher_wave3.py` lines 117, 123, 129, 136, and 142 |

**Cascade level 1**

| Item | Value |
| - | - |
| Before | `def _expand_model_rows(target_org_id: str, model_rows: list[dict], switch_records: list[dict], gateway_records: list[dict]) -> list[dict]:` |
| After | Drop the first parameter `target_org_id`. |
| Call site | `version_per_model_fetcher.py:72`, inside `fetch` |
| Tests to update | `tests/unit/inventory/test_version_per_model_fetcher_wave3.py:320` |

**Stop condition**: `fetch` keeps `target_org_id`. It uses the value for
`_prefetch_switches`, for `_prefetch_gateways`, for `_append_bulk_rows`, and for
two log calls.

---

## Group 5. `src/maps/_maps_clone.py`

| Item | Value |
| - | - |
| Before | `def _confirm_clone(self, source_map: dict, new_name: str, source_zones_count: int, clone_payload: dict) -> bool:` |
| After | Drop the final parameter `clone_payload`. |
| Call site | `_maps_clone.py:352` |
| Tests to update | None |

Caution: `src/gateway/template_config.py` holds a different method with the same
name and a different signature. Tests in
`tests/unit/test_template_config.py` target that other method. Do not change
them.

---

## Group 6. `src/maps/maps_manager.py`

Warning: `site_name` is the first positional parameter.

| Item | Value |
| - | - |
| Before | `def _render_site_maps_table(site_name: str, maps: list) -> None:` |
| After | `def _render_site_maps_table(maps: list) -> None:` |
| Call site | `maps_manager.py:559` |
| Tests to update | None |
| Cascade | None. The caller `list_site_maps` still prints `site_name` and logs it. |

---

## Group 7. `src/site/address_audit/address_resolver.py`

Warning: `candidates` is the fourth parameter of five. Removing it shifts
`query`.

| Item | Value |
| - | - |
| Before | `def _combine(self, internal, osm, ui, candidates: ResolveCandidates, query: str) -> ResolverResult:` |
| After | Drop `candidates`. The parameter `query` moves into the fourth slot. |
| Call site | `address_resolver.py:83`, `self._combine(internal, osm, ui, candidates, query)` becomes `self._combine(internal, osm, ui, query)` |
| Tests to update | None |

---

## Group 8. `src/ssh/runtime/app_runner.py`

| Item | Value |
| - | - |
| Before | `def _prompt_for_commands(env_cmds: list[str], csv_cmds: list[str]) -> list[str]:` |
| After | `def _prompt_for_commands() -> list[str]:` |
| Call site | `app_runner.py:262` |
| Tests to update | None |
| Cascade | None. The caller `_resolve_commands` still tests both lists in an `if` block. |

This group resolves two findings, because the site holds two unused parameters.

---

## Group 9. `src/ssid_consolidation/_ssid_template_cache.py`

| Item | Value |
| - | - |
| Before | `def _offer_resume(self, phase: int, results: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:` |
| After | `def _offer_resume(self, phase: int) -> tuple[bool, list[dict[str, Any]]]:` |
| Call sites | `_ssid_template_phase2.py:238`, `_ssid_template_phase3.py:276`, `_ssid_template_phase45.py:610` |
| Tests to update | `tests/unit/test_ssid_template_consolidation.py:2027` |

Every call site passes a literal empty list today.

Note: the manager class reaches this method through `__getattr__` proxy
delegation. No base class fixes the signature.

Note: `tests/unit/test_ssid_template_consolidation.py` lines 3283 and 3339 use
`patch.object(mgr, "_offer_resume", ...)`. A patch by name survives a signature
change. Do not edit those two lines.

Also delete the dead comment `# noqa: ARG002 - signature preserved for tests`.

---

## Group 10. `src/ssid_consolidation/_ssid_template_phase1.py`

| Item | Value |
| - | - |
| Before | `def _resolve_template(site, template_lookup, sitegroup_lookup) -> tuple[dict[str, Any] \| None, str]:` |
| After | Drop the final parameter `sitegroup_lookup`. |
| Call site | `_ssid_template_phase1.py:289` |
| Tests to update | `tests/unit/test_ssid_template_consolidation.py` lines 423, 434, and 445 |

**Cascade level 1**

| Item | Value |
| - | - |
| Before | `def _resolve_site_wlan(site, target_ssid: str, template_lookup, sitegroup_lookup) -> tuple[...]:` |
| After | Drop the final parameter `sitegroup_lookup`. |
| Call site | `_ssid_template_phase1.py:351`, inside `_build_site_row` |
| Tests to update | None |

**Stop condition**: `_build_site_row` passes `lookups.sitegroup_lookup`. That is
a dataclass field, not a parameter. Pylint does not report a field.

Also delete the dead comment `# noqa: ARG001 - signature preserved for tests`.

Do not remove the `_SiteLookups.sitegroup_lookup` field. Do not remove
`_build_sitegroup_lookup`. Both become dead after this change. A companion issue
records that work, because the module re-exports the function for back-compat.

---

## Group 11. `src/utils/address_utils.py`, the `debug` parameter

| Item | Value |
| - | - |
| Before | `def apply_business_context_rules(mist_result, comparison_result, debug: bool = False) -> str:` |
| After | Drop the final parameter `debug`. |
| Call sites | None. No caller in the repository passes `debug`. |
| Tests to update | None. Each of the four tests passes two arguments already. |

Also delete the dead comment
`# noqa: ARG004 - signature preserved for callers passing debug`. The comment
states a claim that no call site supports.

---

## Group 12. `src/utils/address_utils.py`, the `source` thread

This is the widest thread. Five methods lose the parameter. Change all five in
one task.

| Level | Before | After | Call site |
| - | - | - | - |
| Leaf | `def _make_api_request(self, address_string: str, source: str) -> Any \| None:` | Drop `source`. | `address_utils.py:1058` |
| Leaf | `def _calculate_component_match(self, address_parts: list[str], display_name: str, source: str) -> float:` | Drop `source`. | `address_utils.py:1017` |
| Leaf | `def _calculate_quality_boost(self, result: dict[str, Any], source: str) -> float:` | Drop `source`. | `address_utils.py:1018` |
| Cascade | `def _calculate_confidence(self, result: dict[str, Any], address_parts: list[str], source: str) -> float:` | Drop `source`. | `address_utils.py:1035` |
| Cascade | `def _parse_geocode_response(self, response: Any, address_parts: list[str], source: str) -> dict[str, Any]:` | Drop `source`. | `address_utils.py:1061` |

**Stop condition**: `_geocode_address` keeps `source`. It uses the value in two
`logging.debug` calls in the exception path.

**Tests to update** in `tests/unit/test_address_utils.py`: lines 728, 734, 740,
744, 751, 773, 778, 790, 798, 806, 813, 819, 827, and 844. Read the whole
`NominatimValidator` test class before you edit. The list above holds the calls
that the search found. Run the test file after the edit to catch any call that
the search missed.

Also delete the three dead `# noqa: ARG002` comments.

---

## Group 13. Outcome B sites, no signature change

These five sites keep the parameter. Add the comment only.

| File | Line | Function |
| - | - | - |
| `src/org/org_synthetic_probes_manager.py` | 1619 | `_build_probe_set` |
| `src/websocket/manager.py` | 318 | `WebSocketManager._on_open` |
| `src/websocket/manager.py` | 323 | `WebSocketManager._on_message` |
| `src/websocket/manager.py` | 336 | `WebSocketManager._on_error` |
| `src/websocket/manager.py` | 343 | `WebSocketManager._on_close` |

Section 8 of `research.md` holds the exact comment text for each site.

---

## Group 14. Outcome C site, no signature change

| File | Line | Function | Parameter |
| - | - | - | - |
| `src/ssid_consolidation/_ssid_template_phase45.py` | 267 | `_build_template_config` | `resolutions` |

Warning: Do not remove this parameter. FR-015 forbids the removal. The
parameter is the seam that the future fix needs. Add the comment that names the
companion issue.

---

## Summary of the change surface

| Measure | Count |
| - | - |
| Functions that lose a parameter | 19 |
| Of those, cascade functions not in the baseline | 5 |
| Production call sites to edit | 17 |
| Test call sites to edit | 24 |
| Sites that gain a suppression comment | 6 |
| Dead `noqa` comments to delete | 6 |
