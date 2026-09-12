# Spec 1007 — site_auto_upgrade.py Compliance Refactor

## Problem

`src/firmware/site_auto_upgrade.py` currently scores **63.0 / 100 (grade D)**
against the project's coding guidelines. It carries **39 violations**
(1 high, 18 medium, 20 low) across three rule families:

- **STRUCT-LENGTH** (19): functions exceed the 25-line limit — worst offender
  is `_get_shared_schedule` at 61 lines.
- **STRUCT-COMPLEXITY** (17): functions exceed cyclomatic complexity 5 — worst
  offender is `_fetch_current_site_settings` at CC 10.
- **STRUCT-BLOCKS** (3): functions exceed the 5-logical-block limit —
  `_fetch_current_site_settings`, `_apply_family_selection`,
  `_select_versions_interactively`.

Two suppression comments already leak through and must be removed under the
no-suppressions rule:

- `# pylint: disable=too-many-instance-attributes` on class
  `SiteAutoUpgradeConfigurator` (17 instance attributes).
- `# noqa: PLR0913, STRUCT-PARAMS` on `execute()` static entrypoint (9 params).
- `# pylint: disable=too-many-lines` on the module itself.

## Current-state baseline

| Metric | Value |
| - | - |
| File | `src/firmware/site_auto_upgrade.py` |
| LOC | 1487 |
| Executable lines | 748 |
| Functions | 58 |
| Classes | 1 |
| Average CC | 4.4 |
| Max CC | 10 (`_fetch_current_site_settings`) |
| Inline comment coverage | 96.9% |
| Compliance score | 63.0 / 100 |
| Compliance grade | D |
| Total violations | 39 |

Complexity hotspots (CC descending):

| Function | CC |
| - | - |
| `_fetch_current_site_settings` | 10 |
| `_apply_family_selection` | 9 |
| `_get_shared_firmware_versions` | 8 |
| `_select_versions_interactively` | 8 |
| `_execute_msp_mode` | 7 |
| `_step3_fetch_available_versions` | 7 |
| `_step4_select_versions` | 7 |
| `_pick_stable_version` | 7 |
| `parse_time_input` | 7 |

Length hotspots (LOC descending):

| Function | LOC |
| - | - |
| `_get_shared_schedule` | 61 (HIGH) |
| `_get_shared_firmware_versions` | 51 |
| `execute` | 49 |
| `_step4_select_versions` | 46 |
| `_select_versions_interactively` | 46 |
| `_apply_to_all_orgs` | 43 |
| `_msp_confirm_and_apply` | 40 |
| `_execute_msp_mode` | 40 |
| `_msp_get_firmware_config` | 37 |
| `_step6_confirm_and_apply` | 36 |
| `_apply_settings_to_sites` | 36 |
| `__init__` | 35 |
| `_apply_auto_upgrade_config` | 33 |
| `_print_msp_summary` | 33 |
| `_handle_msp_mode` | 31 |
| `_msp_select_entities` | 28 |
| `_step3_fetch_available_versions` | 27 |
| `_select_single_site` | 26 |
| `_apply_family_selection` | 26 |

## Success criteria

1. Compliance analyzer reports **100.0 / 100 (A+)** with **zero violations**
   for `src/firmware/site_auto_upgrade.py`.
2. Every executable line carries a `# WHY:` (or equivalent trailing-hash)
   comment.
3. Every workflow step logs `logging.info(...)` before mutation and
   `logging.debug(...)` after mutation.
4. No suppressions anywhere in the file. Zero `# noqa`, `# type: ignore`,
   `# pragma: no cover`, `# pylint: disable`.
5. `ruff check` clean. `black --check` clean. `mypy --strict` clean.
   `py_compile` clean.
6. All existing unit tests in `tests/unit/test_site_auto_upgrade.py` continue
   to pass without modification (byte-identical test file where possible;
   any signature-affected test callsites must remain semantically equivalent).
7. `MistHelper.py` diff against `main` is **exactly 0 bytes** — the
   `execute(...)` static entrypoint keeps its keyword-arg contract.

## Out of scope

- No behavioral changes: user-visible prompts, print output, and API calls
  remain identical.
- No changes to `src/dataclasses/site_auto_upgrade_deps.py` or
  `src/dataclasses/family_selection_context.py`.
- No changes to `MistHelper.py`.

## Constraints (non-negotiable)

- 5-Item Rule: ≤5 params, ≤5 logical blocks, ≤25 lines/function, CC ≤5,
  nesting ≤4.
- ASCII-only log messages.
- `os.path.join` / `pathlib.Path` for any filesystem path (none currently
  present).
- Byte-identical callsites in `MistHelper.py`.
