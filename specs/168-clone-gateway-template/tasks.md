# Tasks: Menu 194 — Clone Device Config to New Gateway Template

**Feature**: Clone Device Config to New Gateway Template  
**Branch**: `feat/168-clone-gateway-template`  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Date**: 2026-06-08

---

## Phase 1: Setup

- [X] T001 Verify `src/gateway/` directory exists; create it with `src/gateway/__init__.py` if missing (`src/gateway/__init__.py`)
- [X] T002 Confirm `src/gateway/__init__.py` is empty (module marker only, no imports)

---

## Phase 2: Foundational — Module Scaffolding

- [X] T003 Create `src/gateway/device_template_cloner.py` with module-level docstring, imports (`logging`, `mistapi.api.v1.orgs`, `mistapi.api.v1.sites`), and `STRIP_FIELDS` frozenset constant listing all device-specific metadata fields to exclude from the template payload (`src/gateway/device_template_cloner.py`)
- [X] T004 Define `KEEP_FIELDS` frozenset constant in `src/gateway/device_template_cloner.py` listing all config fields to retain (`additional_config_cmds`, `bgp_config`, `dhcpd_config`, etc.) (`src/gateway/device_template_cloner.py`)

---

## Phase 3: User Story 1 — Core Implementation

**Story Goal**: A NOC engineer can select a gateway device, strip its metadata, and clone it into a new org-level gateway template.

**Independent Test Criteria**: `_build_template_payload()` returns correct keys; `_strip_metadata()` removes all STRIP_FIELDS; unit tests pass without API credentials.

- [X] T005 [US1] Implement `DeviceConfigTemplateClonerManager.__init__()` accepting `apisession`, `org_id`, `input_fn`, `get_csv_path_fn`, `save_data_fn`, `check_and_generate_csv_fn`; store all as instance attributes with inline comments explaining each dependency (`src/gateway/device_template_cloner.py`)
- [X] T006 [US1] Implement `_select_site()` method: call `listOrgSites`, log before/after with site count, present numbered menu, return selected site dict (`src/gateway/device_template_cloner.py`)
- [X] T007 [US1] Implement `_select_gateway_device(site_id)` method: call `listSiteDevices` with `type="all"`, filter to `type == "gateway"`, log before/after, present numbered menu, return selected device dict (`src/gateway/device_template_cloner.py`)
- [X] T008 [US1] Implement `_fetch_device_config(site_id, device_id)` method: call `getSiteDevice`, log before call with site_id and device_id, log after with field count, return raw device dict (`src/gateway/device_template_cloner.py`)
- [X] T009 [US1] Implement `_fetch_existing_template_names()` method: call `listOrgGatewayTemplates`, log before/after, return set of existing template name strings for uniqueness validation (`src/gateway/device_template_cloner.py`)
- [X] T010 [US1] Implement `_prompt_template_meta(device_model, existing_names)` method: prompt for type (`standalone`/`spoke`), prompt for name with uniqueness validation loop, prompt for model override (default = device_model); return `(name, ttype, model)` tuple; all prompts use `input_fn` (`src/gateway/device_template_cloner.py`)
- [X] T011 [US1] Implement `_build_template_payload(device_config, name, ttype, model)` method: dict comprehension excluding STRIP_FIELDS and None values, inject `name`, `type`, and `gateway_matching` block with `match_model`; every line commented with WHY (`src/gateway/device_template_cloner.py`)
- [X] T012 [US1] Implement `_confirm_creation(name, ttype, model)` method: display summary of pending operation, prompt user to type `CREATE` (exact case) using `safe_input` pattern via `input_fn`; return bool; log confirmation result (`src/gateway/device_template_cloner.py`)
- [X] T013 [US1] Implement `_create_template(payload)` method: call `createOrgGatewayTemplate`, log before with payload name/type, log after with new template ID; return new template dict; raise on API error (`src/gateway/device_template_cloner.py`)
- [X] T014 [US1] Implement `_export_result(template)` method: build single-row list, call `check_and_generate_csv_fn` with `api_function_name="createOrgGatewayTemplate"`, log before/after export; print success summary with template ID and name (`src/gateway/device_template_cloner.py`)
- [X] T015 [US1] Implement `run()` method: orchestrate `_select_site` → `_select_gateway_device` → `_fetch_device_config` → `_fetch_existing_template_names` → `_prompt_template_meta` → `_confirm_creation` (abort if not confirmed) → `_build_template_payload` → `_create_template` → `_export_result`; wrap in try/except with `logging.error` on failure (`src/gateway/device_template_cloner.py`)

---

## Phase 4: User Story 2 — MistHelper.py Integration

**Story Goal**: Menu 194 is reachable from the interactive menu and direct `--menu 194` invocation; all routing goes through the delegation stub.

**Independent Test Criteria**: Delegation stub instantiates `DeviceConfigTemplateClonerManagerImpl` and calls `.run()` without executing any business logic itself; `--menu 194` reaches the stub.

- [X] T016 [US2] Add `DeviceConfigTemplateClonerManager` delegation stub class to `MistHelper.py`: `__init__` stores `apisession`, `org_id`, and all helper fn references; `run()` imports `DeviceConfigTemplateClonerManagerImpl` from `src.gateway.device_template_cloner` and delegates; inline comments on every line (`MistHelper.py`)
- [X] T017 [US2] Add `createOrgGatewayTemplate` PK strategy entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in `MistHelper.py` with `type: natural_pk`, `primary_key: ["id"]`, `indexes: ["org_id", "name"]` (`MistHelper.py`)
- [X] T018 [US2] Add menu 194 entry to the dispatcher dict in `MistHelper.py`: key `194`, value calls `DeviceConfigTemplateClonerManager(...).run()`; follow the exact pattern used by the nearest destructive menu operation (`MistHelper.py`)

---

## Phase 5: Documentation & Release

- [X] T019 Update `README.md`: increment operation count from 161 to 162 in all locations (header count, mindmap, pie chart, architecture-overview); add row for Menu 194 in the Destructive operations table (`README.md`)
- [X] T020 Update `CHANGELOG.md`: add new version entry `26.06.08` with description "Add Menu 194 — Clone Device Config to New Gateway Template" under `### Added` (`CHANGELOG.md`)

---

## Phase 6: Quality Gates

- [X] T021 Run `python -m py_compile src/gateway/device_template_cloner.py` — must produce no output (`src/gateway/device_template_cloner.py`)
- [X] T022 Run `python -m py_compile MistHelper.py` — must produce no output (`MistHelper.py`)
- [X] T023 Run `python -m ruff check src/gateway/device_template_cloner.py MistHelper.py` — must pass clean with zero violations
- [X] T024 Run `python -m black --check src/gateway/device_template_cloner.py MistHelper.py` — must pass; auto-fix with `black` if needed, then re-check

---

## Dependencies

```text
T001 → T002 → T003 → T004
T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015
T015 → T016 → T017 → T018
T018 → T019 → T020
T020 → T021 → T022 → T023 → T024
```

T006–T014 within Phase 3 can be worked in any order since each is an independent method; T015 (`run()`) must come last within Phase 3.

---

## Parallel Execution Opportunities

| Parallel Group | Tasks | Condition |
| - | - | - |
| Phase 3 helpers | T006, T007, T008, T009, T010, T011, T012, T013, T014 | All independent helper methods; T015 waits for all |
| Phase 5 docs | T019, T020 | Independent of each other; both require T018 complete |
| Phase 6 lint | T021, T022, T023, T024 | Run sequentially (T021/T022 first to catch syntax before lint) |

---

## Implementation Notes

- **Inline comments**: Every executable line in `device_template_cloner.py` and the delegation stub in `MistHelper.py` must have a same-line comment explaining WHY, not just WHAT. No exceptions.
- **Action logging**: `logging.info("...")` BEFORE every API call; `logging.debug("...")` AFTER with result count or summary. Never log raw API responses (may contain sensitive data).
- **Confirmation string**: `CREATE` (exact case, no trailing spaces). If user input does not match, log `"Operation cancelled - confirmation failed"` and return early.
- **No new dependencies**: Only `mistapi`, `logging`, and stdlib are permitted.
- **ASCII logs only**: No Unicode or emoji in any log string.
- **File paths**: Use `os.path.join()` in any path construction.
- **MVP scope**: All 24 tasks are required for a complete, shippable operation. There is no partial delivery path for this feature.
