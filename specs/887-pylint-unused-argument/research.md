# Research: Narrow the pylint W0613 unused-argument suppression

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Date**: 2026-07-29

**Status**: Complete. Every finding holds a final outcome.

This document is the triage record that FR-002 requires. It holds one row for
each measured finding. It also holds the call-site evidence, the cascade
analysis, and the score measurement.

---

## 1. Baseline re-measurement (FR-003)

The team re-measured the baseline in the current working tree.

**Command**:

```powershell
.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n
```

**Tool versions**: pylint 4.0.6, astroid 4.0.4, Python 3.13.3 on Windows.

**Result**: 21 findings. The count matches the spec. Every file and every line
number matches the spec table. The baseline did not drift.

**Decision**: Keep the 21-row site inventory from the spec. No new rows are
needed.

---

## 2. Score measurement and risk evidence

The largest risk is a score drop below the 9.5 threshold. The team measured the
delta on Windows.

**Commands**:

```powershell
.venv\Scripts\python.exe -m pylint src/ --ignore=maps,ssh,ui --exit-zero
.venv\Scripts\python.exe -m pylint src/ --ignore=maps,ssh,ui --enable=W0613 --exit-zero
```

| Condition | Local Windows score |
| - | - |
| Today, `W0613` disabled | 9.77 |
| Simulated, `W0613` enabled | 9.77 |

**Finding**: The 17 gate-visible findings do not move the score at the
reported resolution of 0.01. The measured delta is below 0.01.

**Rationale**: The pylint score divides the message count by the statement
count. The `src/` tree holds a large statement count. Seventeen extra warnings
produce a change smaller than the reported resolution.

**Caution**: This is a Windows measurement. Issue #891 measured a 0.30 gap
between Windows and Linux for the same commit. That gap appeared when the run
included `src/maps`, `src/ssh`, and `src/ui`. This feature keeps the
`--ignore=maps,ssh,ui` flag, so the two runs cover the same package set that
passes today. The gap is therefore expected to be smaller. The team still
treats the Windows number as an estimate only. FR-023 requires a real run on
the Linux runner.

**Decision**: Proceed. Confirm the score with a continuous integration run on
the pushed branch before merge.

**Alternative considered and rejected**: Lower the threshold below 9.5.
FR-024 forbids this action.

**Alternative considered and rejected**: Keep the repository-wide disable and
document the findings only. This action delivers no gate. SC-008 requires the
gate to report a new unused argument on the first run.

---

## 3. Cascade analysis (the main research finding)

Nine of the 21 findings sit at the end of a parameter thread. A caller accepts
the same parameter and passes it down. The caller reads the parameter for no
other purpose.

When the feature removes the parameter from the callee, the caller parameter
becomes unused. Pylint then reports a **new** W0613 finding at the caller. The
new finding did not exist in the baseline.

**Consequence**: An Outcome A change is not always a single-site edit. The
feature must walk the thread up until it reaches a function that reads the
parameter for a real purpose.

**Decision**: Treat each thread as one unit of work. Remove the parameter at
every level of the thread in the same change. Stop at the first level that
reads the parameter.

The table lists every cascade. The "Stops at" column names the function that
reads the parameter for a real purpose.

| Thread | Levels to change | Stops at | Reason the thread stops |
| - | - | - | - |
| `mistapi` in `bulk_ap_upgrader.py` | `_upgrade_version_group`, `_execute_multi_version_upgrade` | `_execute_site_upgrade` | It also calls `_execute_single_version_upgrade`, which uses `mistapi`. |
| `target_org_id` in `version_per_model_fetcher.py` | `_rows_for_model`, `_expand_model_rows` | `fetch` | It uses `target_org_id` for two prefetch calls and for logging. |
| `sitegroup_lookup` in `_ssid_template_phase1.py` | `_resolve_template`, `_resolve_site_wlan` | `_build_site_row` | It reads a dataclass field, not a parameter. Pylint does not report a field. |
| `source` in `address_utils.py` | `_make_api_request`, `_calculate_component_match`, `_calculate_quality_boost`, `_calculate_confidence`, `_parse_geocode_response` | `_geocode_address` | It uses `source` in two debug log calls. |

The `source` thread is the widest. Two of the five methods,
`_calculate_confidence` and `_parse_geocode_response`, are not in the baseline.
They read `source` only to pass it down. They become findings after the leaf
methods change.

---

## 4. Existing ruff suppressions that this feature must resolve

Six parameters already carry a ruff `ARG` suppression. The stated reason is
"signature preserved for tests" or "reserved for future logging".

| File | Parameter | Existing comment |
| - | - | - |
| `_ssid_template_cache.py` | `results` | `# noqa: ARG002 - signature preserved for tests` |
| `_ssid_template_phase1.py` | `sitegroup_lookup` | `# noqa: ARG001 - signature preserved for tests` |
| `address_utils.py` (3 sites) | `source` | `# noqa: ARG002` with a "future logging" reason |
| `address_utils.py` | `debug` | `# noqa: ARG004 - signature preserved for callers passing debug` |

**Decision**: None of these reasons meets the FR-013 bar. FR-013 requires a
specific contract. A test is not an external contract. FR-026 requires the
feature to update any test that calls a changed signature. A future plan for
logging is not a contract either.

**Evidence against the `debug` reason**: The comment claims that callers pass
`debug`. A search of the whole repository found no caller that passes `debug`.
The only callers are four tests, and each test passes two arguments. The stated
reason is factually wrong.

**Action**: These six parameters take Outcome A. The feature removes each
parameter and deletes the now-dead `noqa` comment in the same change.

---

## 5. Triage record (FR-001, FR-002)

The table holds one row for each of the 21 findings. The "Call sites" column
counts the production call sites and the test call sites that need an edit.

| # | File | Line | Function | Parameter | Gate sees it | Outcome | Justification | Call sites |
| - | - | - | - | - | - | - | - | - |
| 1 | `src/capture/packet_capture.py` | 911 | `PacketCaptureManager._multi_ap_gather_params` | `ap_macs` | Yes | A | The body calls three prompt helpers. None of them needs the AP list. The sibling helpers `_multi_ap_print_summary` and `_multi_ap_build_payload` do use the list, so the parameter is a copy-paste leftover. | 1 production, 0 test |
| 2 | `src/firmware/bulk_ap_upgrader.py` | 1487 | `BulkAPFirmwareUpgrader._upgrade_version_group` | `mistapi` | Yes | A | The deeper helper `_invoke_upgrade_api` performs a lazy `import mistapi` of its own. The threaded module is dead. Cascades one level to `_execute_multi_version_upgrade`. | 2 production, 2 test |
| 3 | `src/firmware/org_ap_upgrader.py` | 675 | `OrgLevelAPFirmwareUpgrader._display_org_list` | `msp_name` | Yes | A | The body prints the org list and the selection help. It never names the MSP. The caller already prints the MSP name in the step banner. | 1 production, 0 test |
| 4 | `src/inventory/inventory_summary/version_per_model_fetcher.py` | 188 | `VersionPerModelFetcher._rows_for_model` | `target_org_id` | Yes | A | The method dispatches on `device_type` and reads only the prefetched record lists. The org id is no longer needed after the prefetch refactor. Cascades one level to `_expand_model_rows`. | 2 production, 6 test |
| 5 | `src/maps/_maps_clone.py` | 149 | `_MapsClone._confirm_clone` | `clone_payload` | No | A | Verified in the spec. The method prints a plan and prompts for confirmation. It never reads the payload. | 1 production, 0 test |
| 6 | `src/maps/maps_manager.py` | 532 | `MapsManager._render_site_maps_table` | `site_name` | No | A | The table header prints the map count and the column titles only. The caller already prints the site name before the call, so the operator does not lose information. | 1 production, 0 test |
| 7 | `src/org/org_synthetic_probes_manager.py` | 1619 | `_build_probe_set` | `vlan_ids` | Yes | B | Verified in the spec. The docstring documents a back-compat promise to the caller. VLAN scoping belongs on the `tests[]` row, not on the `custom_probes` definition. | 0 |
| 8 | `src/site/address_audit/address_resolver.py` | 93 | `AddressResolver._combine` | `candidates` | Yes | A | Verified in the spec. The body delegates to `_pick_tier_winner` and `_resolve_validated`. Neither helper needs the candidate list. The parameter sits fourth of five, so the removal shifts `query`. | 1 production, 0 test |
| 9 | `src/ssh/runtime/app_runner.py` | 265 | `AppRunner._prompt_for_commands` | `env_cmds` | No | A | The caller reaches this line only after both lists tested empty. The caller passes two empty lists. The body prompts the operator and ignores both. | 1 production, 0 test |
| 10 | `src/ssh/runtime/app_runner.py` | 265 | `AppRunner._prompt_for_commands` | `csv_cmds` | No | A | Same evidence as row 9. Both parameters are always empty at the single call site. | 1 production, 0 test |
| 11 | `src/ssid_consolidation/_ssid_template_cache.py` | 193 | `_SsidTemplateCacheCluster._offer_resume` | `results` | Yes | A | All three production call sites pass a literal empty list. The body loads the prior results from disk instead. The manager reaches this method through `__getattr__` proxy delegation, so no base class fixes the signature. | 3 production, 1 test |
| 12 | `src/ssid_consolidation/_ssid_template_phase1.py` | 121 | `_resolve_template` | `sitegroup_lookup` | Yes | A | The scope check `_template_applies_to_site` reads `site["sitegroup_ids"]` directly. The lookup map is never needed. Cascades one level to `_resolve_site_wlan`. | 2 production, 3 test |
| 13 | `src/ssid_consolidation/_ssid_template_phase45.py` | 267 | `_build_template_config` | `resolutions` | Yes | **C** | See section 6. The operator answers a deviation prompt for each cluster and parameter. The answers never reach the template. | Do not remove |
| 14 | `src/utils/address_utils.py` | 494 | `AddressUtils.apply_business_context_rules` | `debug` | Yes | A | No caller in the repository passes `debug`. The parameter carries a default value, so the removal cannot raise a `TypeError` at any caller. | 0 production, 4 test |
| 15 | `src/utils/address_utils.py` | 902 | `NominatimValidator._make_api_request` | `source` | Yes | A | The body builds the query parameters and retries the request. It never reads `source`. Part of the five-level `source` thread. | 1 production, 4 test |
| 16 | `src/utils/address_utils.py` | 947 | `NominatimValidator._calculate_component_match` | `source` | Yes | A | The body scores address parts against the display name. It never reads `source`. Part of the five-level `source` thread. | 1 production, 3 test |
| 17 | `src/utils/address_utils.py` | 977 | `NominatimValidator._calculate_quality_boost` | `source` | Yes | A | The body sums two boost helpers. It never reads `source`. Part of the five-level `source` thread. | 1 production, 3 test |
| 18 | `src/websocket/manager.py` | 318 | `WebSocketManager._on_open` | `websocket_connection` | Yes | B | Verified in the spec. The `websocket-client` library calls the callback with the connection as the first argument. | 0 |
| 19 | `src/websocket/manager.py` | 323 | `WebSocketManager._on_message` | `websocket_connection` | Yes | B | Same library protocol as row 18. | 0 |
| 20 | `src/websocket/manager.py` | 336 | `WebSocketManager._on_error` | `websocket_connection` | Yes | B | Same library protocol as row 18. | 0 |
| 21 | `src/websocket/manager.py` | 343 | `WebSocketManager._on_close` | `websocket_connection` | Yes | B | Same library protocol as row 18. | 0 |

### Outcome totals

| Outcome | Count | Rows |
| - | - | - |
| A, remove the parameter | 15 | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17 |
| B, keep with a narrow suppression | 5 | 7, 18, 19, 20, 21 |
| C, a real defect | 1 | 13 |
| **Total** | **21** | |

Zero findings stay unassigned. SC-001 is satisfied by this table.

---

## 6. Outcome C detail, row 13

**Site**: `src/ssid_consolidation/_ssid_template_phase45.py:267`,
`_build_template_config`, parameter `resolutions`.

**The chain**:

1. `_phase4_preflight` calls `_resolve_deviations`. That function prompts the
   operator once for each deviating cluster and parameter.
2. `_resolve_deviations` records each answer in `resolutions`, keyed by the
   cluster name and the parameter name.
3. `_phase4_preflight` passes `resolutions` to `_build_all_template_configs`.
4. `_build_all_template_configs` passes `resolutions` to
   `_build_template_config`.
5. `_build_template_config` never reads `resolutions`. It calls
   `_cluster_deviation_params` instead, and it writes a
   `{{MISTHELPER_<PARAM>}}` placeholder for each deviating parameter.

**Evidence**: A search of the whole module found 15 uses of the name
`resolutions`. Every use belongs to the build-and-pass chain above. No code
writes `resolutions` to a file. No code reads a value out of the map.

**Why this is a defect**: The operator answers an interactive prompt for each
deviation. The answers change nothing. The generated template holds a
placeholder in every case. The prompt therefore misleads the operator.

**Action (FR-015, FR-018)**: Do not delete the parameter. Deleting it hides the
defect and removes the seam that the fix needs. Add a site-local
`# pylint: disable=W0613` comment. The reason names the companion issue and
states that the parameter stays until the fix lands.

**Companion issue (FR-017)**: File an issue with the title
"Phase 4 discards the operator deviation resolutions". Use the labels `bug` and
`MistHelper.py` scope equivalent for `src/ssid_consolidation`. The issue body
holds the five-step chain above.

**Rationale for the minimal action**: The correct fix reads a resolved value
out of `resolutions` and writes the concrete value into the config instead of
the placeholder. That change alters the generated Mist template. It needs its
own specification, its own tests, and its own operator review. It is larger
than this feature.

---

## 7. Companion issues and observations

| Source | Observation | Required action |
| - | - | - |
| Row 13 | Phase 4 discards the operator deviation resolutions. | File an issue. FR-017 requires it. |
| Row 5 | The maps clone confirmation prints a static capability list. The text does not describe the real payload. | File an issue. The spec requires it. Do not redesign the text. |
| Row 12 cascade | After the change, `_build_sitegroup_lookup` and the `_SiteLookups.sitegroup_lookup` field have no reader. The module also re-exports `_build_sitegroup_lookup` for back-compat. | File an issue. Removal of a dataclass field and a public re-export is dead-code work, and the Out of Scope list excludes it. |

---

## 8. Outcome B suppression text

FR-011 requires a site-local comment. FR-013 requires a specific contract. The
table holds the exact reason text for each Outcome B site.

| Row | Reason text |
| - | - |
| 7 | `# pylint: disable=W0613 - back-compat contract with the caller. VLAN scope belongs on the tests[] row.` |
| 18 | `# pylint: disable=W0613 - websocket-client library passes the connection to on_open.` |
| 19 | `# pylint: disable=W0613 - websocket-client library passes the connection to on_message.` |
| 20 | `# pylint: disable=W0613 - websocket-client library passes the connection to on_error.` |
| 21 | `# pylint: disable=W0613 - websocket-client library passes the connection to on_close.` |
| 13 | `# pylint: disable=W0613 - kept as the seam for issue <N>. Phase 4 must apply this map.` |

Each comment names a specific contract or a specific issue. No comment uses a
generic phrase.

---

## 9. Positional-shift check (FR-008, FR-009)

FR-008 forbids a removal that shifts another positional argument into the wrong
slot. The team checked every Outcome A call site.

| Risk class | Rows | Finding |
| - | - | - |
| The parameter is last in the signature | 1, 2, 3, 5, 9, 10, 11, 12, 14, 15, 16, 17 | The removal cannot shift a later argument, because no later argument exists. Rows 9 and 10 empty the signature. |
| The parameter is first or in the middle | 4, 6, 8 | Every call site passes the parameter positionally. Every call site must drop it in the same edit. Row 4 sits first of four. Row 6 sits first of two. Row 8 sits fourth of five and shifts `query`. |

Section 5 names every call site for rows 4, 6, and 8. The signature contract
repeats them with a warning.

No caller passes any Outcome A parameter by keyword. FR-009 is satisfied.

Row 14 carries a default value. FR-009 needs a keyword check for that row. No
caller passes `debug` at all, so no keyword call site exists.

---

## 10. Decisions summary

| Decision | Rationale | Alternative rejected |
| - | - | - |
| Resolve each parameter thread as one unit. | A partial removal creates a new finding at the caller. | Fix only the reported line. This leaves the gate red. |
| Treat "signature preserved for tests" as insufficient. | FR-013 requires a specific contract. FR-026 requires a test update. | Convert the ruff `noqa` into a pylint disable. This keeps dead parameters. |
| Keep row 13 and file an issue. | FR-015 forbids a delete. The defect must stay visible. | Delete `resolutions`. This hides a real operator-facing defect. |
| Change `pyproject.toml` last. | An early change turns the gate red for every open branch. | Change the configuration first. This blocks the whole team. |
| Confirm the score on the Linux runner. | Issue #891 measured a 0.30 platform gap. | Accept the local Windows score. FR-023 forbids this. |
