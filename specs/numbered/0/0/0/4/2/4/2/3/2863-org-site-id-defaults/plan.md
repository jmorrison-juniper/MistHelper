# Implementation Plan: Organization and site identifier defaults

**Branch**: `fix/2863-tenant-identifier-validation` (first batch) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/0/4/2/4/2/3/2863-org-site-id-defaults/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Refuse a missing organization or site identifier before each tenant SDK call. The first batch changes only the existing tenant module, one new test file, and one changelog fragment. Later batches add a ratchet guard and repair the state-changing paths. Issue #2863 stays open until every batch lands.

## Technical Context

**Language/Version**: Python 3.15.2. The repository requires Python 3.15 or newer (`.github/copilot-instructions.md:20`, `.specify/memory/constitution.md:278`).

**Primary Dependencies**: `mistapi` 0.64.1 installed, pin `>=0.64.0,<0.65`. `requests` for transport exceptions. `pytest` and `hypothesis` 6.170.17 for tests (`requirements-dev.txt:116`).

**Storage**: None. The change writes no data and adds no schema.

**Testing**: pytest with mocked SDK boundaries and mocked session responses. No live Mist call.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Internal library method in a menu-driven command-line and portal tool.

**Performance Goals**: Zero SDK calls for each refused input.

**Constraints**: No live Mist call, no production store, no container run, no dependency change, and no shared configuration change.

**Scale/Scope**: First batch: six tenant SDK boundaries in one module. Full audit: 110 occurrences in 38 files as reported on 2026-10-06. This count is not reproduced in this record.

## Constitution Check

*Gate: passes before research and after design. The table records the state of each rule.*

| Principle or rule | Gate | Result | Reason |
|-------------------|------|--------|--------|
| I. Five-item rule | No new direct child in a noncompliant folder. | Pass for batch 1. Fail for batch 2, blocked. | `src/mist/access/api/` holds eight children (research RC-36). Batch 1 edits one existing file. `tests/unit/api/` holds four children (RC-37), so one new file reaches five. `tests/guardrails/` holds 79 children (RC-38), so batch 2 cannot add a file there. `.github/` holds 14 children (RC-39). |
| I. Five-item rule, functions | Five parameters or fewer. Twenty-five lines or fewer. | Pass for new code. Debt recorded for existing code. | The new validator methods take at most two parameters. `APITenantFetchUtils.organization_tenants` already spans 35 lines. Batch 1 adds one call line and no new method. |
| II. Class-based architecture | Behavior lives in named classes. No wrapper functions. | Pass | The batch adds `TenantIdentifierValidator` and `TenantNameCollector`. Each class has one subject. |
| III. Safety first | Validate before use. No secret in output. | Pass | Each refusal occurs before its SDK call. The message names the field only. |
| IV. Full deployment pipeline | Local gates, rebase, push, pull request, CI, merge. | Planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run the pipeline. This record does not run it. |
| V. Observability and logging | ASCII only. Structured logs. No secret. | Pass | New messages use ASCII text and `%s` formatting. |
| VI. Inline comments | Each executable line has an inline comment. | Planned | Each changed or new line gets a comment that gives the reason. |
| VII. Action logging | Info before each action. Debug after each action. Error on exception. | Planned | The existing info lines stay. The refusal writes one error record. |
| Python version | Python 3.15 or newer. | Pass after correction | The legacy plan named Python 3.13. This plan corrects it (RC-52, decision D-13). |
| Mist Cloud transport | Each REST request uses a working `mistapi` method. | Pass | The six boundaries use existing `mistapi` functions (RC-41 to RC-46). |
| File paths | Path library or path join only. | Pass | The batch builds no file path. |
| Output backends | Export data through `DataExporter`. | Not applicable | The batch exports no data. |
| Database keys | Natural key defined before a new operation. | Not applicable | The batch adds no endpoint. |
| Data directory | Product output under `data/`. | Pass | The batch writes no product output. |
| Container policy | Compose group and naming for test containers. | Not applicable | No container starts for this record. |
| Security findings | Fix, do not suppress. | Planned | Bandit runs on the changed folder (T-LOCAL-GATES). |
| Specifications | Written for three or more files or two or more classes. | Pass | This record covers the work. |
| Changelog | One unique fragment for each user-visible change. | Pass | One fragment for batch 1 (FR-013). Its name changes to `pr-<number>.md` after the pull request exists (`.github/copilot-instructions.md:451-453`). |

For repository structure and generated files:

- The pull request title uses the Conventional Commits form (`fix(tenant): refuse missing organization and site identifiers`).
- Batch 1 adds one unique changelog fragment. The `changelog.d/` folder holds 335 children (RC-40). That folder is an established process folder, so one unique record is allowed.
- Product output stays under `data/`. Test output uses `tmp_path`.

Skills: No skill was loaded. No Podman, Juniper device, or container question applies to this record.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/4/2/4/2/3/2863-org-site-id-defaults/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      tenant-identifier-refusal.md
      ratchet-baseline.md
    checklists/
      requirements.md
      security.md
```

The draft of this record lives in `DRAFT_DIR`. The orchestrator copies it to the route in the table above. The route uses only managed numeric segments (`.specify/memory/constitution.md:57-58`).

### Source Code (repository root)

```text
src/mist/access/api/tenant_fetch.py                         (modify, batch 1)
tests/unit/api/test_tenant_identifier_validation.py         (add, batch 1)
changelog.d/issue-2863-tenant-identifier-validation.md      (add, batch 1, rename at pull request)
tests/guardrails/org_site_identifier_default/               (add, batch 2, blocked)
src/operations/execution/ssid_consolidation/_ssid_template_phase2.py   (modify, batch 3)
src/mist/resources/device/virtual_chassis.py                (modify, batch 4)
src/mist/resources/device/device_reboot_manager.py          (modify, batch 4)
```

## Architecture

The tenant discovery path for menu 120 (service ping) works as follows.

1. `ServicePingManager.execute` calls `_run_workflow` inside a guarded `try` (`src/mist/realtime/websocket/service_ping_manager.py:456-469`).
2. `_prepare_payload` calls `_fetch_all_tenants` before the prompts (`service_ping_manager.py:421-423`).
3. The mixin builds `APITenantFetchUtils` for each call (`src/mist/realtime/websocket/service_ping_discovery.py:84-87`). It calls the four public methods (`service_ping_discovery.py:62-82`).
4. The public methods in `src/mist/access/api/tenant_fetch.py` call the private helpers (lines 71, 107, 143, 167, 305, 321, 337, 356).
5. The helpers call six `mistapi` functions (research RC-41 to RC-46).

The class is also injected into `src/foundation/support/refactors/service_ping_launcher.py:98` and re-exported in `MistHelper.py:3372`. No other direct caller exists in `src/` (search of 2026-11-26).

## Batch Map

| Batch | Scope | Files | Gate | Status |
|-------|-------|-------|------|--------|
| B1 | Tenant boundary refusal. Owner approved on 2026-10-21. | `src/mist/access/api/tenant_fetch.py`, `tests/unit/api/test_tenant_identifier_validation.py`, `changelog.d/issue-2863-tenant-identifier-validation.md` | Standard local gates. Reservation comment first. | Ready after the queue hold clears |
| B2 | Masking-default ratchet and baseline | `tests/guardrails/org_site_identifier_default/test_ratchet.py`, `tests/guardrails/org_site_identifier_default/baseline.json` | Constitution placement fails until remediation. | Blocked (D-14) |
| B3 | SSID site-variable writes. Menu 145, category `interactive`. | `src/operations/execution/ssid_consolidation/_ssid_template_phase2.py`, `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py` | Standard local gates. | Waits for B1 |
| B4 | Virtual chassis conversion (menus 161, 162) and gateway reboot (menu 158). Category `destructive`. | `src/mist/resources/device/virtual_chassis.py`, `src/mist/resources/device/device_reboot_manager.py`, `tests/unit/test_virtual_chassis.py`, `tests/unit/device/test_device_reboot_manager.py` | Standard local gates and human review before merge. | Waits for B1 and human review |
| B5 | Upgrade portal (menu 239). Category `destructive`. | Not listed. The manifest is stale. | New specification required. | Deferred |

Warning: do not start B4 or B5 without human review. A wrong change to a destructive path can start a wrong reboot or conversion.

## Change Map for Batch 1

| Path | Action | Reason |
|------|--------|--------|
| `src/mist/access/api/tenant_fetch.py` | Modify | Add `TenantIdentifierValidator` and `TenantNameCollector`. Route six SDK boundaries through the validator. Replace `_add_valid_name` and `_add_valid_names`. Keep every existing exception handler. |
| `tests/unit/api/test_tenant_identifier_validation.py` | Add | Ten planned test functions (T001, T003, T004, T005). |
| `changelog.d/issue-2863-tenant-identifier-validation.md` | Add | One fragment with one `Fixed` bullet that names issue #2863 (FR-013). |
| `specs/numbered/0/0/0/4/2/4/2/3/2863-org-site-id-defaults/` | Add | This record after review. |
| `src/mist/realtime/websocket/service_ping_discovery.py` | Read only | Existing caller contract (SC-006). |
| `src/mist/realtime/websocket/service_ping_manager.py` | Read only | Existing error path (FR-011). |
| `tests/unit/marvis/standalone/mist/access/api/test_api_tenant_fetch.py` | Read only | Existing tests stay unchanged (SC-006). |
| `tests/unit/marvis/standalone/mist/access/api/test_issue_2971_status_before_count.py` | Read only | Existing tests stay unchanged (SC-006). |

The helper functions `_add_valid_name` and `_add_valid_names` have no caller outside `tenant_fetch.py` (RC-53). Replacing them keeps the top-level name count the same. The module already holds more than five top-level names. That condition is existing debt.

## Validator Contract

`TenantIdentifierValidator` has two static methods. Each method has at most two parameters and at most twenty-five lines.

- `require(value, field)` returns the same string when the string has a non-whitespace character. It raises `ValueError` for every other value. It logs one error record with the field name.
- `resolve(org_id_fn, site_id)` calls the organization resolver first. It validates the organization identifier. It then validates the supplied optional site identifier. It returns the pair `(org_id, site_id_or_none)`.

Each public union method calls `resolve` before any SDK call. Each SDK-calling helper calls `require` before its SDK call. This order makes a refused site identifier cause zero organization SDK calls (FR-004).

## Dependencies

- `mistapi` 0.64.1 (`.venv\Lib\site-packages\mistapi`). Six functions are used. Research RC-41 to RC-46 give their local blob hashes.
- `requests` for `requests.RequestException`.
- `pytest` and `hypothesis` 6.170.17 for tests.
- The parent grant for publication after queue position 30.

## Risks and Mitigations

Warning: do not return an empty result for a refusal. An empty result hides the missing identifier.

| Risk | Mitigation |
|------|------------|
| A caller outside service ping discovery receives a new `ValueError`. | Search of 2026-11-26 found no other direct caller (research RC-31 to RC-34). Test T005 proves the workflow error path. |
| The legacy branch has stale paths and the wrong Python version. | Port the content into the current module. Do not merge the legacy branch. Run tests on Python 3.15.2. |
| A future resolver returns an empty string. `MistHelper.py:3615` uses `or ""`, so the empty value would pass into the discovery object. | Batch 1 refuses the empty value at the tenant boundary. Batch 2 counts the `or ""` form (decision D-10). |
| Destructive paths change behavior. | Batches 4 and 5 keep human review. No `auto-merge` label goes on those pull requests (`AGENTS.md:230-231`). |
| The count of occurrences differs by scan rule. | Batch 2 records its own count at the implementation revision (decision D-9). |
| A concurrent change edits `tenant_fetch.py`. | Post a reservation comment with the current paths first (decision D-12). Seven open pull requests showed no overlap on 2026-11-26. |
| A malformed but non-blank identifier reaches the cloud and returns an HTTP error. | The existing HTTP contract returns an empty result (FR-009). The residual risk is recorded. Batch 2 does not cover it. |

## Rollback Steps

1. For batch 1, revert the single squash commit on `main`.
2. Or restore `src/mist/access/api/tenant_fetch.py` to blob `ba7e74141e32b6d0a4d4edfbeeff618290a9641f`. Then delete the new test file and the changelog fragment.
3. No data migration exists. A refusal writes no cloud data, so no cloud data needs repair.
4. For batches 3 and 4, revert the batch commit. The refusal occurs before each write, so the cloud state does not change.

Caution: keep the recovery branch `recovery/2863-handoff-20261004` and the batch-1 branch until a merged replacement exists (`AGENTS.md:271-276`).

## Complexity Tracking

| Existing debt | Bounded treatment in this plan | Separate remediation |
|---------------|--------------------------------|----------------------|
| `src/mist/access/api/` holds eight children (RC-36). | Add no file. | Group the API modules in a separate change. |
| `APITenantFetchUtils` holds 18 methods, including `__init__` (research RC-22). `organization_tenants` spans 35 lines (`tenant_fetch.py:71-105`). | Add the validator call only. Add no method. | Divide the fetch responsibilities in a separate change. |
| The module `tenant_fetch.py` holds more than five top-level names. | Replace two helper functions with two classes. The count stays the same. | Same separate change. |
| `tests/guardrails/` holds 79 children (RC-38). | Batch 1 adds no file. Batch 2 is blocked. | Remediation issue before batch 2 (D-14). |
| `.github/` holds 14 children (RC-39). | Batch 1 adds no file. | Remediation issue before batch 2 (D-14). |
| `changelog.d/` holds 335 children (RC-40). | Add one unique fragment. | None required. The process-record exception covers unique records. |
