# Implementation Plan: API Fetch Failures

**Branch**: `fix/4762-api-fetch-failures` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record route `specs\numbered\0\0\1\2\3\0\2\2\4762-api-fetch-failures`. The route follows the base-5 rule in rows R74 and R75.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Make the two Mist list helpers raise `APIFetchError` on a failed read. Keep the successful output unchanged. Let each optional site lookup log a warning and continue. Let each required read stop with the error.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Section "Language and environment" of `.github/copilot-instructions.md` states the rule.
- **Primary Dependencies**: `mistapi==0.64.1` (row R66). No new dependency.
- **Storage**: Not applicable. The change does not alter persistence.
- **Testing**: pytest modules listed in `tasks.md`.
- **Target Platform**: Windows 11, macOS, and Linux. Section "What this repository is" of `.github/copilot-instructions.md` states the rule.
- **Project Type**: Menu-driven command-line tool with a web portal.
- **Performance Goals**: The number of Mist requests for a successful read does not change. Each later page is requested once.
- **Constraints**: Five-item rule (row R114). No module-level name added (FR-013). Mist calls through mistapi only (row R121). ASCII log text (row R118).
- **Scale/Scope**: Seven source files. One existing unit test module (modified). One new integration test module. One release-note fragment.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (R114) | Pass | The class `APICoreFetchUtils` has five members after the change. The new test module goes to `tests/integration/export/`, which holds two children (R126). It does not go to `tests/integration/`, which holds 26 children (R125). No file is added to `src/mist/access/api/`. |
| II. Class-Based Architecture (R115) | Pass | The helpers stay static methods of `APICoreFetchUtils`. No wrapper function is added. |
| III. Safety-First (R116) | Pass | The change only reads. Warnings carry the org ID and the cause. No credential reaches a log (test I-13). |
| IV. Full Deployment Pipeline (R117) | Pass | The plan runs T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. After T-MERGE, the container build runs on the merged revision. The orchestrator then checks the image revision label and runs the health check. |
| V. Observability and Logging (R118) | Pass | All new log text is ASCII. Info lines come before actions. Debug lines come after them. Errors carry the cause. |
| VI. Inline Comments (R119) | Pass | Each changed line carries an inline comment. Tasks T002 to T009 require the comments. |
| VII. Action Logging (R120) | Pass | Each page request logs info before the request and debug after it. Each caller warning names the action. |
| Technology: mistapi only (R121) | Pass | The helper calls `listOrgSites`, `getOrgInventory`, and `mistapi.get_next`. The change adds no direct HTTP request. |
| Technology: dependencies, containers, and test containers | Pass | No dependency changes. No container starts for this change. |
| Technology: file paths | Pass | The changed code builds no path by string join. |
| Technology: output backends | Pass | No export write path changes. `DataExporter.write_with_format_selection` stays as it is. |
| Technology: data directory | Pass | Each integration test uses `tmp_path` for cache files. No test writes to `data/`. |
| Operational store, export boundary, database keys, container security, Zscaler | Not applicable | The change does not touch a store, a key, a container, or a proxy. |
| Development Workflow: new menu operations | Not applicable | No menu operation is added. |
| Mist Cloud contract rule | Pass | `spec.md` names each mistapi method. Contract tests show the SDK gap (rows R95 and R96) and cover the four contract areas. |

## Architecture

Required read path:

1. A caller invokes `APICoreFetchUtils.all_sites_with_limit` or `APICoreFetchUtils.all_inventory_with_limit`.
2. The helper calls `listOrgSites` or `getOrgInventory`. It passes the response to `_collect_pages`.
3. `_collect_pages` checks each page. It requests later pages through `mistapi.get_next`.
4. On failure, `_collect_pages` raises `APIFetchError`. The error reaches the caller and then the menu dispatcher (rows R59 to R61).

Optional lookup path:

1. A caller invokes a fetch helper inside its own `try` block.
2. On `APIFetchError`, the caller logs one warning, keeps the empty lookup, and continues.
3. Any other exception keeps its current path.

## Design Decisions

Design decisions D-1 to D-13 are in `design/research.md`. Their short forms are:

- D-1: Nest `APIFetchError` in `APICoreFetchUtils` with `RuntimeError` as its base.
- D-2: Page with `mistapi.get_next`.
- D-3: Fail on a status outside 200 to 299, or on a missing status.
- D-4: Fail on an unknown 2xx payload. Return an empty list for a 2xx read with no items.
- D-5: Limit the change to the two helpers and the listed callers.
- D-6: Let required reads propagate `APIFetchError`.
- D-7: Catch only `APIFetchError` in optional lookups.
- D-8: Reference the error through the class that each module already has.
- D-9: Keep the MSP broad catch and raise its log level.
- D-10: Put the integration tests in `tests/integration/export/`.
- D-11: Leave `tests/unit/export/test_site_device_exporter.py` unchanged.
- D-12: Name the release note `issue-4762-api-fetch-failures.md`.
- D-13: Keep the menu dispatcher unchanged.

## Change Map

| Path | Action | Requirements | Task |
| - | - | - | - |
| `src/mist/access/api/api_core_fetch_utils.py` | Modify | FR-001 to FR-008, FR-013 | T002 |
| `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` | Modify | FR-009, FR-014 | T004 |
| `src/mist/intelligence/reports/offline_device_reporter.py` | Modify | FR-009 | T005 |
| `src/operations/exporting/export/site_device_exporter.py` | Modify | FR-009 | T006 |
| `src/operations/exporting/export/sites_by_ap_model_exporter.py` | Modify | FR-009 | T007 |
| `src/operations/exporting/export/org_inventory_exporter.py` | Modify | FR-009, FR-010 | T008 |
| `src/operations/exporting/export/msp_inventory_exporter.py` | Modify | FR-011 | T009 |
| `tests/unit/api/test_api_core_fetch_utils.py` | Modify | FR-001 to FR-008, FR-015 | T001 |
| `tests/integration/export/test_api_fetch_enrichment.py` | Add | FR-009 to FR-012, FR-014, FR-015 | T003 |
| `changelog.d/issue-4762-api-fetch-failures.md` | Add | FR-016 | T010 |

The change does not touch these files:

- `src/interfaces/visualization/ui/prompt_utils.py`. Its existing `RuntimeError` fallback covers the new error (FR-012, rows R30 and R31).
- The firmware modules. Their existing handlers already report the failure (rows R41 to R46).
- `MistHelper.py`. The existing dispatcher handles the new error (rows R59 to R61).
- `tests/unit/export/test_site_device_exporter.py`. Session 79a9bb52 owns it (D-11).

## Dependencies and Ownership

- The two exporter files carry a file-only handoff from the owners of issue 1794. Issue 1794 rebases after this change merges.
- The reserved paths in the issue comments match the change map, except for the test path (D-10).
- No open pull request touches a path in the change map (A-004).

## Design Details

### Fetch helpers

The contract is in `design/contracts/fetch-helpers.md`. The key points are:

- `APICoreFetchUtils.APIFetchError` subclasses `RuntimeError`.
- `_collect_pages` is a static method. It takes the session, the first response, the operation name, and the org ID.
- The class has five members after the change: `APIFetchError`, `all_sites_with_limit`, `all_inventory_with_limit`, `get_api_response_data`, and `_collect_pages`.
- `_collect_pages` keeps the constitution limits (row R114): five parameters or fewer, five blocks or fewer, and 25 lines or fewer.

### Optional lookups

The contract is in `design/contracts/optional-lookups.md`. Each optional lookup logs exactly one warning on failure. It returns the empty value that its caller already expects.

### Operator output

The contract is in `design/contracts/operator-output.md`. It lists each menu or command and its failure output.

## Risks and Mitigations

- R-1: Direct-mode sessions end after a required read fails (D-13). Mitigation: the error names the operation and the cause. The owner reviews the policy after the merge (`analysis.md`, item U-B).
- R-2: A later page has an unknown shape. Mitigation: FR-003 and test U-9.
- R-3: Mocks hide a status defect. Mitigation: the tests build real `mistapi.APIResponse` objects (A-002).
- R-4: The fast path reads runtime cache files. Mitigation: the integration tests point `FilePathUtils.get_csv_path` at `tmp_path` and remove cache hits.
- R-5: The Symbols gate fails on an added name. Mitigation: the nested class (D-1) and SC-005.
- R-6: The test-quality gate rejects the new module. Mitigation: each test module carries HTTP 4xx and HTTP 5xx cases (row R113).
- R-7: Other direct readers keep the empty-result defect. Mitigation: D-5 and the follow-up issue in `analysis.md`.
- R-8: The optional catch hides a real defect at warning level. Mitigation: the catch names only `APIFetchError`, and the warning carries the cause (FR-009, FR-014).

## Rollback

1. Create a branch from `main`. Revert the squash commit on that branch.
2. Open a pull request for the revert. Merge it after the required checks pass.
3. Do not force-push `main`. The revert removes the release note with the code.
4. No data migration, cache change, or configuration change is needed.

## Complexity Tracking

Not applicable. The change adds no direct child to a noncompliant parent (Constitution Check, rule I).

## Documentation Impact

- No operator guide changes. The menu text, the output columns, and the file names do not change.
- The release note under `changelog.d/` (FR-016).
- The docstrings of `APICoreFetchUtils` describe the new contract.
