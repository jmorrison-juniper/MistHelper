# Implementation Plan: Organization Config Export Refusal

**Branch**: `fix/4707-organization-config-export-refusal` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/3/1/2/4707-organization-config-export-refusal/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The export treats a refused configuration fetch as an empty list. It then saves a bundle and reports completion. The fix adds a fetch outcome for each configuration type. The export writes a bundle only when all six types are verified. The import rejects a bundle that is not verified, and it stops when the destination inventory is not verified. The change stays inside one module and its two unit test modules.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `.github/copilot-instructions.md` line 18 states.

**Primary Dependencies**: `mistapi` 0.64.1. `pyproject.toml` line 29 allows `>=0.64.1,<0.65`, and `requirements.txt` line 129 pins `mistapi==0.64.1`. No dependency changes.

**Storage**: JSON bundle files in `data/`. No database change.

**Testing**: pytest unit tests with mocked sessions and native SDK response objects. No live Mist request.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The change adds no platform-specific code.

**Project Type**: Existing menu operations 58 (export) and 187 (import) in a Python repository.

**Performance Goals**: Request volume does not change for a complete organization. A refused type stops the export after its own page. No retry is added.

**Constraints**: Five-item rule for new code. The module holds 747 lines, and the manager class holds 49 methods before this change. Both are existing debt.

**Scale/Scope**: Six configuration types for one organization per run.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule | Pass | The module gains three top-level names, for five in total: `logger`, `ConfigFetchOutcome`, `ConfigFetchReader`, `BundleVerification`, and `OrgConfigMigrationManager`. The reader holds five methods or fewer. The verifier holds three methods. The manager loses two methods, from 49 to 47. |
| I. Five-item rule, directories | Pass | No file or directory is added under `src/mist/resources/org/`. The directory already holds five tracked children. |
| II. Class-based design | Pass | Behavior sits in `ConfigFetchReader`, `BundleVerification`, and the existing manager class. No wrapper function is added. |
| III. Safety first | Pass | `InputUtils.safe_input` prompts stay. The IMPORT confirmation stays. The new gates stop before any create call. |
| IV. Full pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. A human merges. |
| V. Logging | Pass | Messages use ASCII and `%s` values. No response body or exception text is logged. |
| VI. Inline comments | Pass | Task T009 requires an inline comment on each executable line. |
| VII. Action logging | Pass | Each fetch logs before and after. Each stop logs an error with its context. |
| Mist transport | Pass | Every REST call uses a mistapi function. The change adds no direct HTTP call. No owned WebSocket transport enters. |
| Mist contract evidence | Pass | The spec names the evidence tests for SDK insufficiency, authentication, endpoint parity, failure safety, and redaction. |
| Primary keys | Not applicable | No new endpoint and no new operation. The bundle keys stay unchanged. |
| Output backends | Existing exception | The manager writes the JSON bundle directly. This change does not alter that writer. Complexity Tracking records the debt. |
| Data directory | Pass | Bundles stay in `data/`. Tests use `tmp_path`. |
| Container and Zscaler | Not applicable | No container, compose file, or registry step. |
| Documentation | Pass | The module docstring and the changelog fragment describe the rules. `README.md` and `documentation/operator-guide.md` hold no menu 58 or 187 text (RC-12, RC-13), so they need no edit. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/1/2/4707-organization-config-export-refusal/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      bundle-schema.md
      menu-messages.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/mist/resources/org/
  org_config_migration_manager.py   (modify)
tests/unit/org/
  test_org_config_migration_conflicts.py   (modify)
  test_org_config_migration_workflow.py    (modify)
changelog.d/
  issue-4707-organization-config-export-refusal.md   (add)
```

## Design

### Fetch outcome and reader

`ConfigFetchOutcome` is a frozen dataclass with five fields: `key`, `verified`, `items`, `failure_category`, and `http_status`.

`ConfigFetchReader` holds the session and the dotted-path resolver from the manager. Its `read` method performs these steps for one configuration type:

1. Log an info line that names the type and the organization.
2. Resolve the list function and call it with `limit=1000` and the configured keyword arguments.
3. Verify the response. A status that is not an integer or is a boolean gives `unavailable`. An integer outside 200 through 299 gives `refused` with the status.
4. Read the payload. A list, or a dictionary with a list `results` value, is valid. Any other 2xx payload gives `invalid` with the status.
5. If the response has a `next` value, call `mistapi.get_next` with the session and the response. A `None` result gives `unavailable`. Repeat steps 3 and 4 for that page.
6. Return a verified outcome that holds every object in page order.
7. On an exception, return an `exception` outcome. The log names the type and the exception class name only.

Warning: without a status check, a refused response becomes an empty list, and the bundle looks complete. An operator can then migrate an incomplete configuration.

### Bundle verification

`BundleVerification` holds the class attribute `SCHEMA_VERSION` with the value `"1.1"`. It holds three static methods:

- `fetch_status(outcomes, keys)` returns `verified` for every key of a verified outcome set.
- `unverified_keys(outcomes, keys)` returns each key that is missing or not verified.
- `bundle_problem(metadata, keys)` returns a reason when the schema is not 1.1 or a fetch status is not verified. It returns `None` for a valid bundle.

### Export gate

`export_config` calls `_fetch_all_types`, which returns one outcome for each type. When `unverified_keys` returns any key, the method logs one error with the display names and returns. No file is written and no summary table is printed. Otherwise, `_build_export_bundle` writes schema 1.1 and the fetch status map, and the existing save, summary, and completion steps run.

### Import gates

- `_validate_bundle_structure` keeps its existing metadata and key checks. After the key check, it calls `bundle_problem`. A problem logs the reason and the instruction to run menu 58 again. The method returns `False`.
- `_fetch_existing_objects` calls `_fetch_all_types` for the destination organization. When a key is not verified, it clears the cache, logs the stop message, and returns `False`. Otherwise, it caches the items and returns `True`.
- `import_config` returns before `_execute_import` when `_fetch_existing_objects` returns `False`. The same rule applies to dry-run and live modes.

Warning: an import with an unverified destination can create objects that overlap existing objects. The gate stops this path before the first create call.

### Logging

Messages appear in `contracts/menu-messages.md`. The fetch log uses the same category names as the spec.

## Dependencies

No new package. The change uses `mistapi.get_next`, which `mistapi/__init__.py` line 16 exports in version 0.64.1 (RC-59).

## Risks and mitigations

- **Over-blocking export.** One refused type stops the whole export. Mitigation: the error names the type and the status. The operator fixes the access problem and runs menu 58 again.

  Caution: an organization that refuses one configuration type cannot export a bundle until the access problem is repaired.

- **Over-blocking import.** A destination token without read access stops the import. Mitigation: the stop message names the type and the status. No object is created.
- **Legacy bundles.** Bundles saved before this change lack schema 1.1. Mitigation: the import rejects them with the menu 58 instruction. No migration is attempted.
- **Dynamic SDK call sites.** The SDK compatibility guard limits dynamic call sites. Mitigation: the change keeps one dynamic list call, which replaces the call in `_fetch_config_type`. Task T011 runs the guard.
- **Symbol gate semantics.** The symbol gate states that no module-level name changes. The change adds three top-level names. Mitigation: task T001 captures the baseline. Task T-LOCAL-GATES records the tool output. If the tool fails on added names, stop and report the output. Do not suppress the gate.
- **Mock-only evidence.** No live Mist response confirms the refusal body shape. Mitigation: the tests use native SDK response objects. Analysis U-3 records the gap.

## Revert steps

1. Before merge, close the pull request and delete the branch.
2. After merge, open a new issue. Branch from `main` and revert the squash commit in a new pull request.
3. Restore the previous bundle schema only through the revert pull request. Do not edit `data/` by hand.

## Complexity Tracking

| Existing violation | Why it stays | Remediation action |
| --- | --- | --- |
| `OrgConfigMigrationManager` holds 47 methods after this change, above five | The change removes two methods and adds none. Splitting the class is a larger refactor. | Open a separate issue to split export and import into two classes. |
| `org_config_migration_manager.py` holds 747 lines before this change and grows after it | The fix stays in the existing module because the directory cannot take a new child. | Include the module split in the separate issue above. |
| The manager writes the JSON bundle directly, not through `DataExporter` | The bundle format is outside this fix. | Open a separate issue to route bundle writes through `DataExporter`. |
