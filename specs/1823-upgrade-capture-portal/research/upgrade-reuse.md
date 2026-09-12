# Upgrade Code Reuse Research — Feature 1823

Status: research reference. No source code changed.

This document maps the firmware upgrade code that exists today. It records what the
web portal can reuse and what the web portal must avoid. Every claim below cites a
file and a line number. Statements that are inferences are marked `INFERENCE`.

Line numbers come from the Read and Grep tools. Do not trust PowerShell
`Measure-Object -Line` for these files. That counter reports lower numbers.

---

## 1. Every upgrade entry point

### 1.1 Package inventory

`src/firmware/` holds six files.

| File | Lines |
| --- | --- |
| `src/firmware/__init__.py` | 1 |
| `src/firmware/bulk_ap_upgrader.py` | 2259 |
| `src/firmware/bulk_switch_upgrader.py` | 1096 |
| `src/firmware/firmware_manager.py` | 4084 |
| `src/firmware/org_ap_upgrader.py` | 2804 |
| `src/firmware/site_auto_upgrade.py` | 1780 |

`src/firmware/__init__.py:1` holds only a docstring. The package exports nothing.
Every import must name the full module path.

### 1.2 `src/firmware/firmware_manager.py`

This module is the facade. The command-line menu calls this module. This module
then calls the three worker classes.

Module state:

- `src/firmware/firmware_manager.py:34-37` declares four module globals.
  The names are `msp_privileges`, `apisession`, `org_id`, and `PROGRESS_EMITTER`.
- `src/firmware/firmware_manager.py:49-62` defines `_MistHelperProxy`. The class
  forwards attribute reads to `MistHelper.py` at call time. The proxy breaks a
  circular import. `src/firmware/firmware_manager.py:65` builds the `_MH` instance.
- `src/firmware/firmware_manager.py:116` defines `_bind_module_globals(config)`.
  The function rebinds the four module globals. It reads `sys.modules["__main__"]`
  or `sys.modules["MistHelper"]` at `src/firmware/firmware_manager.py:127`.

Configuration:

- `src/firmware/firmware_manager.py:68-113` defines `FirmwareManagerConfig`. The
  dataclass is frozen. The dataclass carries `apisession`, `org_id`, and six
  optional hook callables.

Class and public methods:

- `src/firmware/firmware_manager.py:134` — `class FirmwareManager`
- `src/firmware/firmware_manager.py:152` — `__init__(self, config: FirmwareManagerConfig) -> None`
- `src/firmware/firmware_manager.py:260` — `check_firmware_upgrade_status(self, scope_choice=None, site_filter=None) -> None`
- `src/firmware/firmware_manager.py:867` — `execute_firmware_upgrade_with_mode_selection(self) -> list[dict[str, Any]] | None`
- `src/firmware/firmware_manager.py:1810` — `execute_switch_firmware_upgrade_with_mode_selection(self) -> None`
- `src/firmware/firmware_manager.py:1930` — `execute_ssr_firmware_upgrade_with_mode_selection(self) -> dict[str, Any] | None`

Selected private methods that matter to the seam:

- `src/firmware/firmware_manager.py:1502` — `_execute_msp_upgrade_plan`
- `src/firmware/firmware_manager.py:1730` — `_bulk_upgrade_ap_firmware_by_site`
- `src/firmware/firmware_manager.py:1753` — `_build_bulk_ap_config`
- `src/firmware/firmware_manager.py:1778` — `_dispatch_bulk_ap_upgrade`
- `src/firmware/firmware_manager.py:1792` — `_execute_status_check`
- `src/firmware/firmware_manager.py:1887` — `_upgrade_switch_firmware_by_gateway_template`
- `src/firmware/firmware_manager.py:2131` — `_select_ssr_upgrade_strategy`
- `src/firmware/firmware_manager.py:2291` — `_is_ssr_inventory_row`
- `src/firmware/firmware_manager.py:2745` — `_call_ssr_upgrade_api`
- `src/firmware/firmware_manager.py:2768` — `_build_ssr_upgrade_body`

`src/firmware/firmware_manager.py:1725` marks `_select_msp_for_upgrade` as
DEPRECATED.

### 1.3 `src/firmware/bulk_ap_upgrader.py`

- `src/firmware/bulk_ap_upgrader.py:26-57` — `BulkAPUpgraderConfig`. The dataclass
  is frozen. Field lines are `org_id` 40, `apisession` 41, `sites_override` 46,
  `dry_run` 47, `safe_input_fn` 52, `check_stop_fn` 53, `fetch_sites_fn` 54,
  `get_csv_path_fn` 55, `check_firmware_status_fn` 56, `get_org_id_fn` 57.
- `src/firmware/bulk_ap_upgrader.py:60` — `class BulkAPFirmwareUpgrader`
- `src/firmware/bulk_ap_upgrader.py:79` — `__init__(self, config: BulkAPUpgraderConfig) -> None`
- `src/firmware/bulk_ap_upgrader.py:146` — `execute(self) -> None`

Phase helpers:

- `src/firmware/bulk_ap_upgrader.py:166` — `_announce_start`
- `src/firmware/bulk_ap_upgrader.py:180` — `_run_discovery_phase`
- `src/firmware/bulk_ap_upgrader.py:201` — `_run_planning_phase`
- `src/firmware/bulk_ap_upgrader.py:218` — `_run_execution_phase`

Step helpers:

- `src/firmware/bulk_ap_upgrader.py:236` — `_step1_determine_sites`
- `src/firmware/bulk_ap_upgrader.py:431` — `_step2_discover_aps`
- `src/firmware/bulk_ap_upgrader.py:553` — `_step3_fetch_firmware_stats`
- `src/firmware/bulk_ap_upgrader.py:638` — `_step4_fetch_available_firmware`
- `src/firmware/bulk_ap_upgrader.py:681` — `_step5_select_firmware_versions`
- `src/firmware/bulk_ap_upgrader.py:940` — `_step6_configure_upgrade`
- `src/firmware/bulk_ap_upgrader.py:1101` — `_step7_confirm_upgrade`
- `src/firmware/bulk_ap_upgrader.py:1338` — `_step8_execute_upgrades`

Body builders:

- `src/firmware/bulk_ap_upgrader.py:1539` — `_build_upgrade_body(self, version, device_ids)`
- `src/firmware/bulk_ap_upgrader.py:1556` — `_build_base_upgrade_body`
- `src/firmware/bulk_ap_upgrader.py:1574` — `_augment_body_p2p`
- `src/firmware/bulk_ap_upgrader.py:1580` — `_augment_body_canary`
- `src/firmware/bulk_ap_upgrader.py:1588` — `_augment_body_rrm`
- `src/firmware/bulk_ap_upgrader.py:1598` — `_augment_body_start_time`

### 1.4 `src/firmware/bulk_switch_upgrader.py`

- `src/firmware/bulk_switch_upgrader.py:21-35` — module constants. See section 3.
- `src/firmware/bulk_switch_upgrader.py:38` — `class BulkSwitchFirmwareUpgrader`
- `src/firmware/bulk_switch_upgrader.py:55-61` — `__init__(self, org_id: str, apisession: Any, safe_input_fn: Any, sites_override: list[dict[str, Any]] | None = None) -> None`
- `src/firmware/bulk_switch_upgrader.py:97` — `execute(self) -> dict[str, Any]`
- `src/firmware/bulk_switch_upgrader.py:958` — `_build_upgrade_request(self, device_ids: list[str]) -> dict[str, Any]`
- `src/firmware/bulk_switch_upgrader.py:948` — `_call_upgrade_api(self, site_id, upgrade_request) -> Any`

Warning. This class does not take a config dataclass. This class takes four loose
keyword arguments. The asymmetry blocks a single uniform seam signature. See
section 7.

### 1.5 `src/firmware/org_ap_upgrader.py`

This module holds a fourth upgrade path. The path uses an org-scoped endpoint.

- `src/firmware/org_ap_upgrader.py:3-4` — module docstring names the endpoint.
  The text reads "Uses the upgradeOrgDevices API (POST /api/v1/orgs/{org_id}/devices/upgrade)".
- `src/firmware/org_ap_upgrader.py:20-21` — `OrgAPUpgraderConfig`. The dataclass is
  frozen, uses slots, and is keyword-only.
- `src/firmware/org_ap_upgrader.py:39` — `safe_input_fn: Any | None = None`
- `src/firmware/org_ap_upgrader.py:89` — `class OrgLevelAPFirmwareUpgrader`
- `src/firmware/org_ap_upgrader.py:109` — `__init__(self, **cfg: Any) -> None`
- `src/firmware/org_ap_upgrader.py:2686` — `_create_base_upgrade_body`
- `src/firmware/org_ap_upgrader.py:2726` — `_build_upgrade_body`
- `src/firmware/org_ap_upgrader.py:2679` — the `upgradeOrgDevices` call

### 1.6 `src/firmware/site_auto_upgrade.py`

This module does not start an upgrade. This module writes an auto-upgrade schedule
into site settings.

- `src/firmware/site_auto_upgrade.py:36` — `class SiteAutoUpgradeConfig`
- `src/firmware/site_auto_upgrade.py:85` — `_resolve_configurator_kwargs(cfg) -> SiteAutoUpgradeConfig`
- `src/firmware/site_auto_upgrade.py:111` — `class SiteAutoUpgradeConfigurator`
- `src/firmware/site_auto_upgrade.py:252` — `_apply_auto_upgrade_config(self) -> tuple[bool, int]`
- `src/firmware/site_auto_upgrade.py:272` — `_build_auto_upgrade_settings(self) -> dict[str, Any]`

---

## 2. The request bodies

Four distinct Mist endpoints start or schedule firmware work.

| Endpoint | Scope | Device family | Call site |
| --- | --- | --- | --- |
| `upgradeSiteDevices` | site | AP | `src/firmware/bulk_ap_upgrader.py:1451` and `1529` |
| `upgradeSiteDevices` | site | switch | `src/firmware/bulk_switch_upgrader.py:952` |
| `upgradeOrgDevices` | org | AP | `src/firmware/org_ap_upgrader.py:2679` |
| `upgradeOrgSsrs` | org | SSR gateway | `src/firmware/firmware_manager.py:2761` |
| `updateSiteSettings` | site | any (schedule only) | `src/firmware/bulk_ap_upgrader.py:2079` and `src/firmware/site_auto_upgrade.py:262` |

### 2.1 AP body through `upgradeSiteDevices`

The defaults live in `_init_upgrade_config` at
`src/firmware/bulk_ap_upgrader.py:1008`. The dictionary spans lines 1016 to 1027.

| Config key | Default | Line |
| --- | --- | --- |
| `download_strategy` | operator choice, default `canary` | 1017 |
| `reboot_strategy` | operator choice, default `rrm` | 1018 |
| `force` | `False` | 1019 |
| `enable_p2p` | `True` | 1020 |
| `max_failure_percentage` | `7` | 1021 |
| `start_time` | `None` | 1022 |
| `canary_phases` | `[1, 2, 4, 8, 16, 32, 64, 100]` | 1023 |
| `p2p_cluster_size` | `5` | 1024 |
| `p2p_parallelism` | `100` | 1025 |
| `reboot` | `True` | 1026 |

The always-present body fields come from
`src/firmware/bulk_ap_upgrader.py:1563-1572`. The eight fields are
`download_strategy`, `reboot_strategy`, `force`, `enable_p2p`,
`max_failure_percentage`, `reboot`, `version`, and `device_ids`.

Conditional fields:

- `p2p_cluster_size` joins the body only when `enable_p2p` is true
  (`src/firmware/bulk_ap_upgrader.py:1577-1578`).
- `canary_phases` joins the body only when the download strategy or the reboot
  strategy equals `canary` (`src/firmware/bulk_ap_upgrader.py:1583-1586`).
- `rrm_node_order`, `rrm_first_batch_percentage`, and `rrm_max_batch_percentage`
  join the body only when the reboot strategy equals `rrm`
  (`src/firmware/bulk_ap_upgrader.py:1591-1596`).
- `start_time` joins the body only when the operator set a schedule
  (`src/firmware/bulk_ap_upgrader.py:1601-1602`).

The AP body never sends `strategy` and never sends `snapshot`. The AP path splits
the rollout into `download_strategy` and `reboot_strategy`.

Note. `p2p_parallelism` sits in the config at line 1025 but no body builder reads
it. The AP site path drops the value.

### 2.2 Switch body through `upgradeSiteDevices`

`src/firmware/bulk_switch_upgrader.py:958-967` builds the whole body. The body has
exactly six fields and no conditional branches.

| Field | Source attribute | Default | Default line |
| --- | --- | --- | --- |
| `version` | `self.target_version` | `""` until operator selects | 84 |
| `strategy` | `self.upgrade_strategy` | `""` until operator selects | 88 |
| `force` | `self.force_upgrade` | `False` | 89 |
| `reboot` | `self.auto_reboot` | `True` | 90 |
| `snapshot` | `self.take_snapshot` | `True` | 91 |
| `device_ids` | built at line 921 | derived | 921 |

The switch body uses one `strategy` field. The switch body is the only body that
carries `snapshot`. The switch body never carries canary fields, RRM fields, P2P
fields, or `max_failure_percentage`.

### 2.3 Org-scoped AP body through `upgradeOrgDevices`

The base body sits at `src/firmware/org_ap_upgrader.py:2688-2694`.

| Field | Value | Line |
| --- | --- | --- |
| `versions` | `[{"firmware_type": "ap", "version": version}]` | 2689 |
| `models` | `[[model] for model in data["models"]]` | 2690 |
| `strategy` | `self.upgrade_config["reboot_strategy"]` | 2691 |
| `download_strategy` | `self.upgrade_config["download_strategy"]` | 2692 |
| `max_failure_percentage` | `self.upgrade_config["max_failure_percentage"]` | 2693 |

Conditional fields:

- `start_datetime` and `reboot_datetime` (`src/firmware/org_ap_upgrader.py:2696-2705`)
- `all_sites: True` when the operator targets the whole org, otherwise `site_ids`
  (`src/firmware/org_ap_upgrader.py:2707-2712`)
- `canary_phases` (`src/firmware/org_ap_upgrader.py:2714-2717`)
- `enable_p2p`, `p2p_cluster_size` default `5`, `p2p_parallelism` default `100`
  (`src/firmware/org_ap_upgrader.py:2719-2724`)

This body differs from the site AP body in three ways. This body names the field
`strategy` where the site body names it `reboot_strategy`. This body carries a
`versions` list and a `models` matrix instead of `version` and `device_ids`. This
body carries a `firmware_type` discriminator, and the only value in the code is
`"ap"` (`src/firmware/org_ap_upgrader.py:2689`).

### 2.4 SSR body through `upgradeOrgSsrs`

`src/firmware/firmware_manager.py:2775-2783` builds the whole body.

| Field | Value | Line |
| --- | --- | --- |
| `device_ids` | validated device list | 2776 |
| `channel` | `upgrade_config["channel"]` | 2777 |
| `version` | target version | 2778 |
| `strategy` | `upgrade_config["strategy"]` | 2779 |
| `reboot_at` | `-1`, added only when auto reboot is off | 2781-2782 |

The SSR body is the only body with a `channel` field. The SSR body has no `force`,
no `snapshot`, no `reboot` boolean, no canary fields, and no RRM fields. The SSR
path disables reboot with the sentinel value `-1` in `reboot_at`.

### 2.5 Auto-upgrade schedule body through `updateSiteSettings`

`src/firmware/site_auto_upgrade.py:274-280` builds the payload.

| Field | Default | Line |
| --- | --- | --- |
| `enabled` | `True` | 275 |
| `version` | `"custom"` | 276 |
| `day_of_week` | `"any"` | 277 |
| `time_of_day` | `"02:00"` | 278 |
| `custom_versions` | operator map of model to version | 279 |

The caller wraps the payload as `{"auto_upgrade": settings}`
(`src/firmware/site_auto_upgrade.py:264`).

### 2.6 Field-to-family matrix

| Field | AP site | AP org | Switch | SSR |
| --- | --- | --- | --- | --- |
| `version` | yes | no (uses `versions`) | yes | yes |
| `versions` | no | yes | no | no |
| `device_ids` | yes | no (uses `models` plus scope) | yes | yes |
| `strategy` | no | yes | yes | yes |
| `download_strategy` | yes | yes | no | no |
| `reboot_strategy` | yes | no (maps to `strategy`) | no | no |
| `force` | yes | no | yes | no |
| `reboot` | yes | no | yes | no (uses `reboot_at`) |
| `snapshot` | no | no | yes | no |
| `channel` | no | no | no | yes |
| `max_failure_percentage` | yes | yes | no | no |
| `canary_phases` | conditional | conditional | no | no |
| `rrm_*` | conditional | no | no | no |
| `enable_p2p` and `p2p_*` | conditional | conditional | no | no |
| `start_time` | conditional | no | no | no |
| `start_datetime` and `reboot_datetime` | no | conditional | no | no |
| `all_sites` or `site_ids` | no | conditional | no | no |

---

## 3. The strategies

### 3.1 Access point, download strategy

`src/firmware/bulk_ap_upgrader.py:967` defines `_prompt_download_strategy`. The
table sits at lines 971 to 975.

| Choice | Value | Text |
| --- | --- | --- |
| `1` | `big_bang` | Download all at once - no orchestration |
| `2` | `serial` | Download one device at a time |
| `3` | `canary` | Phased download rollout |

The default is `3`, which selects canary
(`src/firmware/bulk_ap_upgrader.py:981`). The download strategy has no `rrm`
option.

### 3.2 Access point, reboot strategy

`src/firmware/bulk_ap_upgrader.py:987` defines `_prompt_reboot_strategy`. The table
sits at lines 991 to 996.

| Choice | Value | Text |
| --- | --- | --- |
| `1` | `big_bang` | Reboot all at once |
| `2` | `serial` | Reboot one at a time |
| `3` | `canary` | Phased reboot rollout |
| `4` | `rrm` | RRM-aware reboot (AP only - minimizes Wi-Fi disruption) |

The default is `4`, which selects RRM
(`src/firmware/bulk_ap_upgrader.py:1002`). The comment at
`src/firmware/bulk_ap_upgrader.py:991` states that RRM applies to access points
only.

### 3.3 Switch strategy

`src/firmware/bulk_switch_upgrader.py:314` defines `_select_strategy`. The mapping
sits at `src/firmware/bulk_switch_upgrader.py:334`. The constants sit at lines 21
to 23.

| Choice | Constant | Value |
| --- | --- | --- |
| `1` | `STRATEGY_BIG_BANG` | `big_bang` |
| `2` | `STRATEGY_SERIAL` | `serial` |
| `3` | `STRATEGY_CANARY` | `canary` |

The switch path has no default. The loop repeats until the operator enters `1`,
`2`, or `3` (`src/firmware/bulk_switch_upgrader.py:320-327`). The switch path
rejects `rrm`.

Warning. The switch path sends `strategy: canary` with no `canary_phases` field.
The body builder at `src/firmware/bulk_switch_upgrader.py:958-967` never adds
phases. `INFERENCE`: Mist must apply a server-side default. The code sets no
phases.

### 3.4 SSR strategy

`src/firmware/firmware_manager.py:2131` defines `_select_ssr_upgrade_strategy`. The
function returns `"serial"` at line 2146 and `"big_bang"` at line 2150. The SSR
path rejects canary and rejects RRM.

### 3.5 Strategy-to-family matrix

| Strategy | AP download | AP reboot | Switch | SSR |
| --- | --- | --- | --- | --- |
| `big_bang` | yes | yes | yes | yes |
| `serial` | yes | yes | yes | yes |
| `canary` | yes | yes | yes | no |
| `rrm` | no | yes | no | no |

### 3.6 Values that are hard-coded and not configurable

| Value | Setting | Line |
| --- | --- | --- |
| `rrm_node_order = "fringe_to_center"` | AP RRM | `src/firmware/bulk_ap_upgrader.py:1052` |
| `rrm_first_batch_percentage = 2` | AP RRM | `src/firmware/bulk_ap_upgrader.py:1053` |
| `rrm_max_batch_percentage = 10` | AP RRM | `src/firmware/bulk_ap_upgrader.py:1054` |
| `canary_phases = [1, 2, 4, 8, 16, 32, 64, 100]` | AP canary | `src/firmware/bulk_ap_upgrader.py:1023` |
| `p2p_cluster_size = 5` | AP P2P | `src/firmware/bulk_ap_upgrader.py:1024` |
| `p2p_parallelism = 100` | AP P2P | `src/firmware/bulk_ap_upgrader.py:1025` |
| `enable_p2p = True` | AP P2P | `src/firmware/bulk_ap_upgrader.py:1020` |
| `force = False` | AP | `src/firmware/bulk_ap_upgrader.py:1019` |
| `reboot = True` | AP | `src/firmware/bulk_ap_upgrader.py:1026` |
| `ssr_models = ["SSR", "128T"]` | SSR filter | `src/firmware/firmware_manager.py:2941` |
| `reboot_at = -1` | SSR no-reboot sentinel | `src/firmware/firmware_manager.py:2782` |
| `firmware_type = "ap"` | org AP body | `src/firmware/org_ap_upgrader.py:2689` |
| `version = "custom"` | auto-upgrade payload | `src/firmware/site_auto_upgrade.py:276` |
| `day_of_week = "any"` | auto-upgrade default | `src/firmware/site_auto_upgrade.py:277` |
| `time_of_day = "02:00"` | auto-upgrade default | `src/firmware/site_auto_upgrade.py:278` |
| `CACHE_FRESHNESS_HOURS = 24` | switch cache | `src/firmware/bulk_switch_upgrader.py:53` |
| `time.sleep(7)` | status poll wait | `src/firmware/firmware_manager.py:351` |
| `page_size = 25` | status paging | `src/firmware/firmware_manager.py:1307` |

Only `max_failure_percentage` is promptable among the canary knobs
(`src/firmware/bulk_ap_upgrader.py:1043-1045`). The web portal must expose the
hard-coded values as explicit parameters if operators need to change them.

---

## 4. The SSR and SRX split

### 4.1 The only discriminator

`src/firmware/firmware_manager.py:2291` defines `_is_ssr_inventory_row`. The body
reads:

```python
def _is_ssr_inventory_row(self, gw: dict[str, Any]) -> bool:
    """Return True if the inventory row is SSR-family."""
    if gw.get("type", "") == "ssr":  # WHY: canonical type match
        return True  # WHY: fast-path SSR type
    model = gw.get("model", "")  # WHY: fallback to model pattern
    return "SSR" in model or "128T" in model  # WHY: model-string OR match
```

A second, looser filter sits at `src/firmware/firmware_manager.py:2941`. The line
sets `upgrade_config["ssr_models"] = ["SSR", "128T"]`. The default in
`_run_ssr_site_upgrade_flow` repeats the same list
(`src/firmware/firmware_manager.py:2868`).

### 4.2 SRX has no code path

A case-insensitive search for `srx` across `src/firmware/` returns zero matches.
The word does not appear in any of the six files.

The three gateway inventory reads all pass `type="gateway"` with no vendor filter:

- `src/firmware/firmware_manager.py:2321`
- `src/firmware/firmware_manager.py:2504`
- `src/firmware/firmware_manager.py:2580`

### 4.3 How the SSR call differs from `upgradeSiteDevices`

| Aspect | `upgradeSiteDevices` | `upgradeOrgSsrs` |
| --- | --- | --- |
| Scope | site | org |
| Path arguments | session, `site_id`, body | session, `org_id`, body |
| Call site | `src/firmware/bulk_switch_upgrader.py:952` | `src/firmware/firmware_manager.py:2761` |
| Channel field | absent | required |
| Reboot control | `reboot` boolean | `reboot_at: -1` sentinel |
| Force field | present | absent |
| Snapshot field | present for switch | absent |
| Strategy set | `big_bang`, `serial`, `canary` | `big_bang`, `serial` |
| Version list source | `listOrgAvailableDeviceVersions` | `listOrgAvailableSsrVersions` (`src/firmware/firmware_manager.py:2231`) |

The SSR loop still iterates per site. The loop then calls the org endpoint once for
each site with that site's device list
(`src/firmware/firmware_manager.py:2879-2881`). The scope is org but the batching
is per site.

### 4.4 Verdict on SRX

`INFERENCE`. No SRX-specific upgrade code exists. No code routes a gateway to
`upgradeSiteDevices`. The switch upgrader filters to `type == "switch"` at
`src/firmware/bulk_switch_upgrader.py:898`, so an SRX cannot ride the switch path
today.

Conclusion. The repository has no working SRX upgrade path at all. The portal must
add one. `INFERENCE`: the Mist `upgradeSiteDevices` endpoint accepts SRX device
identifiers in the same shape as switches, because both are Junos devices and both
support `snapshot`. Verify this claim against the Mist API reference before you
build on it. Do not treat it as established repository behavior.

---

## 5. The confirm phrases

| Path | Prompt line | Test line | Required text |
| --- | --- | --- | --- |
| AP, site bulk | `src/firmware/bulk_ap_upgrader.py:1321` and `1323` | `src/firmware/bulk_ap_upgrader.py:1327` | `UPGRADE` |
| AP, facade | `src/firmware/firmware_manager.py:996` | `src/firmware/firmware_manager.py:1000` | `UPGRADE` |
| AP, org level | `src/firmware/org_ap_upgrader.py:2506` | `src/firmware/org_ap_upgrader.py:2513` | `UPGRADE` |
| Switch | `src/firmware/bulk_switch_upgrader.py:770` | `src/firmware/bulk_switch_upgrader.py:777` | `UPGRADE SWITCHES` |
| SSR | `src/firmware/firmware_manager.py:2440` | `src/firmware/firmware_manager.py:2451` | `UPGRADE` |
| MSP continue | `src/firmware/firmware_manager.py:1593` | `src/firmware/firmware_manager.py:1601` | `y` |
| AP multi-version | `src/firmware/bulk_ap_upgrader.py:933` | `src/firmware/bulk_ap_upgrader.py:934` | `y` or `yes`, empty defaults to `y` |
| Auto-upgrade apply | `src/firmware/site_auto_upgrade.py:657` | see module | `y` |

The switch constant `CONFIRM_PHRASE = "UPGRADE SWITCHES"` sits at
`src/firmware/bulk_switch_upgrader.py:24`. Every other phrase is an inline
literal.

The AP site path reads the token with the raw prompt `">>> "`
(`src/firmware/bulk_ap_upgrader.py:1313`).

---

## 6. The interactive coupling

The web portal must avoid every item in this section.

### 6.1 Volume

| File | Lines | `print()` calls | Input calls |
| --- | --- | --- | --- |
| `src/firmware/bulk_ap_upgrader.py` | 2259 | 190 | 19 |
| `src/firmware/bulk_switch_upgrader.py` | 1096 | 134 | 10 |
| `src/firmware/firmware_manager.py` | 4084 | 435 | 19 |
| `src/firmware/org_ap_upgrader.py` | 2804 | 324 | 19 |
| `src/firmware/site_auto_upgrade.py` | 1780 | 188 | 13 |
| Total | 12023 | 1271 | 80 |

The upgrade code prints on average once every ten lines. A line-by-line removal of
the terminal calls is not practical. The seam must sit below the printing layer.

### 6.2 The `builtins.input` fallbacks

Three classes fall back to the built-in `input` when no injected function is
present.

- `src/firmware/firmware_manager.py:165` —
  `self._safe_input_fn: SafeInputFn = config.safe_input_fn or input`
- `src/firmware/bulk_ap_upgrader.py:107` —
  `self._input_fn = config.safe_input_fn or input`
- `src/firmware/org_ap_upgrader.py:157` and `172-176` —
  `self._config.safe_input_fn or self._default_safe_input`, which delegates to
  `InputUtils.safe_input`

`src/firmware/bulk_switch_upgrader.py:59` takes `safe_input_fn` as a required
positional-or-keyword argument with no default. That class cannot fall back.

Caution. A web request that reaches any of the first three fallbacks will block on
a terminal read or raise `EOFError`. The web portal must never construct these
classes without an input function.

### 6.3 The `InputInterceptor` the portal must not use

`web_portal/services/input_hook.py:16` defines `InputInterceptor`.

- `web_portal/services/input_hook.py:32-33` replaces `builtins.input` with
  `cls._patched_input`.
- `web_portal/services/input_hook.py:24` holds a `threading.local()` store.
- `web_portal/services/input_hook.py:46` raises `EOFError("Web input queue exhausted")`
  when the queue empties.
- `web_portal/services/input_hook.py:60-72` defines the `web_input_context`
  context manager.

The interceptor answers prompts from a fixed script. The portal cannot script a
firmware upgrade reliably, because prompt order changes with inventory. The seam in
section 7 removes the need for the interceptor on the upgrade path.

### 6.4 Terminal reads by file

Access point site upgrader
(`src/firmware/bulk_ap_upgrader.py`): lines 355, 391, 832, 933, 981, 1002, 1043,
1059, 1067, 1074, 1086, 1313.

Switch upgrader (`src/firmware/bulk_switch_upgrader.py`): lines 204, 240, 322, 344,
358, 376, 675, 690, 739, 771.

Facade (`src/firmware/firmware_manager.py`): lines 996, 1593, 1849, 1984, 2047,
2070, 2141, 2163, 2183, 2352, 2445.

Org access point upgrader (`src/firmware/org_ap_upgrader.py`): lines 1514, 1592,
2123, 2165, 2506.

Auto-upgrade configurator (`src/firmware/site_auto_upgrade.py`): lines 350, 381,
458, 581, 622, 623, 657.

### 6.5 Process-wide mutable state

This is the largest hazard for a multi-request web server.

- `src/firmware/firmware_manager.py:34-37` declares four module globals.
- `src/firmware/firmware_manager.py:116` rebinds those globals on every
  `FirmwareManager` construction.
- `src/firmware/firmware_manager.py:1736-1741` saves and restores the global
  `apisession` around a bulk access point upgrade.
- `src/firmware/firmware_manager.py:1797-1803` saves and restores the global
  `apisession` around a status check.

Warning. Two concurrent web requests that target different organizations will
corrupt each other's session and organization identifier. The save-and-restore
blocks are not thread safe. The seam must not touch module globals.

### 6.6 Other assumptions about a human

- `src/firmware/firmware_manager.py:351` — `time.sleep(7)` between status polls.
- `src/firmware/firmware_manager.py:889` — a progress emitter bound to menu
  identifier `"90"`.
- `src/firmware/bulk_switch_upgrader.py:52` — a relative cache path,
  `data/cached_org_devices_versions_switch.csv`. A web worker with a different
  working directory will miss the cache.
- `src/firmware/bulk_ap_upgrader.py:1313` — a bare `">>> "` prompt with no context
  string.

---

## 7. The proposed seam

### 7.1 Principle

Split each upgrader into three layers. Keep the terminal layer where it is. Extract
the middle and the bottom.

1. Prompt layer. Stays in `src/firmware/`. Reads from the operator. Builds a
   request object.
2. Plan layer. Moves to the new module. Takes a request object. Returns a plan
   object. Performs read-only API calls and pure computation.
3. Invoke layer. Moves to the new module. Takes a plan object. Posts to Mist.
   Returns a result object. Prints nothing and reads nothing.

The web portal calls layers two and three. The command line keeps all three.

### 7.2 Proposed module

Create `src/firmware/upgrade_service.py`.

The module must import nothing from `MistHelper.py`. The module must declare no
module-level mutable state. The module must contain no `print` call and no `input`
call.

### 7.3 Proposed data classes

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class UpgradeRequest:
    """One operator intent, free of terminal input."""
    family: str            # "ap" | "switch" | "ssr" | "srx"
    scope: str             # "site" | "org"
    org_id: str
    target_ids: tuple[str, ...]   # site ids, or org id when scope is org
    version: str
    options: UpgradeOptions


@dataclass(frozen=True, slots=True, kw_only=True)
class UpgradeOptions:
    """Every knob the four bodies accept. Absent values stay None."""
    strategy: str | None = None
    download_strategy: str | None = None
    reboot_strategy: str | None = None
    force: bool = False
    reboot: bool = True
    snapshot: bool | None = None
    channel: str | None = None
    max_failure_percentage: int | None = None
    canary_phases: tuple[int, ...] | None = None
    rrm_node_order: str | None = None
    rrm_first_batch_percentage: int | None = None
    rrm_max_batch_percentage: int | None = None
    enable_p2p: bool | None = None
    p2p_cluster_size: int | None = None
    p2p_parallelism: int | None = None
    start_time: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpgradeTarget:
    """One site plus the devices at that site that share a version."""
    site_id: str
    site_name: str
    version: str
    device_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class UpgradePlan:
    """The full set of API calls the request will make."""
    request: UpgradeRequest
    targets: tuple[UpgradeTarget, ...]
    call_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class UpgradeOutcome:
    """One posted call and its response."""
    site_id: str
    upgrade_id: str | None
    status_code: int
    device_count: int
    error: str | None = None
```

Every class holds at most a handful of fields and needs no method. The Five-Item
Rule applies to functions, not to dataclass fields.

### 7.4 Proposed function signatures

```python
def build_body(request: UpgradeRequest, target: UpgradeTarget) -> dict[str, Any]:
    """Return the exact JSON body for one API call."""


def plan_upgrade(session: Any, request: UpgradeRequest,
                 inventory: Sequence[dict[str, Any]]) -> UpgradePlan:
    """Group devices into targets and count the calls. No network writes."""


def invoke_upgrade(session: Any, plan: UpgradePlan,
                   dry_run: bool = False) -> tuple[UpgradeOutcome, ...]:
    """Post every target in the plan. Return one outcome per target."""


def classify_gateway(row: dict[str, Any]) -> str:
    """Return 'ssr' or 'srx' for one gateway inventory row."""
```

Each signature takes at most three parameters. Each body must stay at or below 25
lines and 5 blocks. Split `build_body` into one private helper per family to keep
the block count low. Use the existing shape at
`src/firmware/bulk_ap_upgrader.py:1539-1602` as the model, because that code
already splits a base builder from four augment helpers.

Move `classify_gateway` from `src/firmware/firmware_manager.py:2291`. Extend it to
return `"srx"` instead of a bare `False`.

### 7.5 Call sites that would change

| Call site | Change | Risk |
| --- | --- | --- |
| `src/firmware/bulk_ap_upgrader.py:1539-1602` | Delete six methods. Call `build_body`. | Low. Pure functions with clear inputs. |
| `src/firmware/bulk_ap_upgrader.py:1442-1458` and `1515-1537` | Replace the two post helpers with one `invoke_upgrade` call. | Medium. Two call sites, two counter updates. |
| `src/firmware/bulk_switch_upgrader.py:948-967` | Delete both methods. Call the new module. | Low. Twenty lines, no branches. |
| `src/firmware/firmware_manager.py:2745-2783` | Replace with `invoke_upgrade`. | Medium. Error classification at lines 2720-2743 must move or stay. |
| `src/firmware/firmware_manager.py:2291` | Move to `classify_gateway`. | Low. Six lines. |
| `src/firmware/org_ap_upgrader.py:2686-2735` | Delete five methods. Call `build_body`. | Medium. The org body shape differs most. |

### 7.6 Blast radius

Rating: **medium**.

Reasons for the rating:

- The change touches four files in `src/firmware/` plus one new file.
- The change does not touch the prompt code, so the operator-visible strings stay
  byte-identical.
- The change does not touch `src/firmware/site_auto_upgrade.py` at all.
- Existing tests cover the body builders. The relevant files are
  `tests/unit/test_bulk_ap_upgrader.py`, `tests/unit/test_bulk_switch_upgrader.py`,
  `tests/unit/test_org_ap_upgrader.py`, `tests/unit/test_site_auto_upgrade.py`, and
  seven files under `tests/unit/firmware/`.
- The refactor is mechanical. Each moved method is small and pure.

Suggested order:

1. Land `src/firmware/upgrade_service.py` with `build_body` and `classify_gateway`
   only. Point the four existing body builders at it. Ship that alone.
2. Land `plan_upgrade` and `invoke_upgrade`. Point the post helpers at them.
3. Build the portal route on top. Never touch the prompt layer.

Step one alone unblocks the portal for body construction. Step one does not change
`MistHelper.py`.

---

## 8. The hot file risk

Rule: only one open pull request may modify `MistHelper.py` at a time.

### 8.1 What `MistHelper.py` holds today

- `MistHelper.py:169-170` — the `__all__` entries `"FirmwareManager"` and
  `"FirmwareManagerConfig"`.
- `MistHelper.py:494-497` — the import of `FirmwareManager` and
  `FirmwareManagerConfig`.
- `MistHelper.py:498-500` — the import from `src.firmware.org_ap_upgrader`.
- `MistHelper.py:501` — the import from `src.firmware.site_auto_upgrade`.
- `MistHelper.py:3364-3378` — `_build_firmware_manager(session, target_org_id)`.
  The factory builds `FirmwareManagerConfig` with eight arguments.
- `MistHelper.py:3381` — `_build_org_ap_upgrader(**overrides)`.
- `MistHelper.py:3836-3838` — menu 137, the status check.
- `MistHelper.py:3899-3901` — menu 154, the access point upgrade.
- `MistHelper.py:4014-4016` — menu 155, the switch upgrade.
- `MistHelper.py:4026-4028` — menu 156, the SSR upgrade.

Menu numbers and text come from `documentation/menu_reference.md:174`, `191`,
`192`, and `193`.

### 8.2 Verdict

`MistHelper.py` **does not need to change** for the seam in section 7.

Reasons:

- The new module `src/firmware/upgrade_service.py` sits below the classes that
  `MistHelper.py` imports. The imports at `MistHelper.py:494-501` stay valid.
- The factory at `MistHelper.py:3364` builds `FirmwareManagerConfig`. Section 7
  does not change that dataclass.
- The four menu lambdas call public methods that keep their names and their
  signatures.
- The web portal imports `src/firmware/upgrade_service.py` directly. The portal
  never imports `MistHelper.py`.

### 8.3 If a change becomes unavoidable

Keep the change to two lines. Add the new module to `__all__` near
`MistHelper.py:169`. Do nothing else in that file. Do not touch
`_build_firmware_manager`. Do not touch the menu registry.

Caution. A new portal menu entry does need a classification row in
`src/utils/operation_registry.py`. That file is not `MistHelper.py`, so the
hot-file rule does not apply. Add the row or the guardrail test fails.

---

## 9. Virtual chassis

### 9.1 The firmware code ignores virtual chassis

A search across `src/firmware/` for `virtual_chassis`, `vc_mac`, `vc_role`,
`member_count`, and `is_vc` returns no functional match. Only three hits exist and
all three use the word "members" in an unrelated sense. Two are family header text
at `src/firmware/site_auto_upgrade.py:1098` and
`src/firmware/site_auto_upgrade.py:1665`. One is a list-index comment at
`src/firmware/org_ap_upgrader.py:823`.

The switch upgrader fetches devices with
`listSiteDevices(self.apisession, site_id, type="switch")` at
`src/firmware/bulk_switch_upgrader.py:885`. The call passes no `vc` argument. The
filter at `src/firmware/bulk_switch_upgrader.py:898` keeps rows where
`d.get("type") == "switch"`.

`INFERENCE`. Mist returns one logical row for a virtual chassis when the caller
omits `vc`. The switch upgrader therefore sends the virtual chassis identifier, not
the member identifiers. That is correct behavior for an upgrade, because Junos
upgrades a virtual chassis as a unit. The code achieves the correct result by
accident, not by design. No comment in the file mentions virtual chassis.

### 9.2 Where the repository does handle virtual chassis

The inventory and export code handles virtual chassis in detail.

- `src/api/api_core_fetch_utils.py:61-62` calls `getOrgInventory` with `vc=True`.
  The comment states "vc=True includes all physical VC member devices".
- `src/export/org_inventory_exporter.py:87` passes `vc=True`. The comment records
  the difference in row counts, "6186 vs 3224 logical".
- `src/export/org_inventory_exporter.py:169-170` writes two raw files, one with
  `vc: True` and one with `vc: False`.
- `src/export/org_inventory_exporter.py:207` names the synthetic virtual chassis
  MAC prefix `020003*`.
- `src/export/org_inventory_exporter.py:216-217` builds the set of virtual chassis
  parent MAC values from the `vc_mac` field. The code then finds shells with no
  physical member.
- `src/export/org_inventory_exporter.py:560-597` inherits a site identifier from
  the virtual chassis parent. Physical members carry `vc_mac` but carry no
  `site_id`.
- `src/export/org_device_stats_exporter.py:477` exports virtual chassis statistics,
  including stacking cable information.
- `src/device/_utility_commands_cluster.py:67-69` and
  `src/device/_utility_commands_clear.py:128-129`, `236-237`, `287` accept an
  optional `node` value. The comments state that the value targets one member of a
  virtual chassis.

### 9.3 What the portal must do

For upgrade:

- Fetch switches with `vc` omitted or set to false. Send the logical device
  identifier. Never send member identifiers. Sending both starts two upgrades on
  the same hardware.
- Report member count from a separate `vc=True` fetch if the operator needs it. The
  key is `vc_mac` on each physical member
  (`src/export/org_inventory_exporter.py:216`).

For capture:

- A capture must reach every member. Use `vc=True` to enumerate members
  (`src/api/api_core_fetch_utils.py:61`).
- Skip rows whose MAC starts with `020003`. Those rows are synthetic virtual
  chassis placeholders with no hardware
  (`src/export/org_inventory_exporter.py:207`).
- A member row carries no `site_id`. Resolve the site through the `vc_mac` parent
  (`src/export/org_inventory_exporter.py:580-581`).
- Pass the `node` argument when a command must target one member
  (`src/device/_utility_commands_cluster.py:67-69`).

Warning. Upgrade and capture need opposite views of the same fleet. Upgrade needs
the logical view. Capture needs the physical view. Do not share one inventory fetch
between the two features.

---

## 10. Summary of risks for the portal

1. Four different request bodies exist. No shared builder exists today.
2. No SRX upgrade path exists. The portal must add one and must verify the API
   contract first.
3. Module globals in `src/firmware/firmware_manager.py` are not thread safe.
4. Three classes fall back to `builtins.input`. A web request will hang or raise.
5. The switch upgrader takes loose keyword arguments while the others take config
   dataclasses.
6. RRM knobs and canary phases are hard-coded and not reachable through a prompt.
7. Virtual chassis handling is absent from the firmware code and lives only in the
   export code.
8. The switch firmware cache uses a relative path and will miss under a web
   worker.
