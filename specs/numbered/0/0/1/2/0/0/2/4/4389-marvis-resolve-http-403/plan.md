# Implementation Plan: Marvis resolve HTTP 403 handling

**Branch**: `fix/4389-marvis-resolve-403` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root.
Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Menu 270 mode 3 sends one resolve request for each Marvis Action. Mist answered one request with HTTP 403. The client treats the answer as refused and keeps the Mist body. The evidence does not show a client defect. The plan adds three things. It masks identifiers in the refused error text. It stops the run after HTTP 401 or HTTP 403. It adds tests and documentation for the 403 class. The plan does not decide the root cause. A human role check decides the cause.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `pyproject.toml` requires.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`. The local install holds version 0.64.1. No dependency changes.

**Storage**: The results file `data/OrgMarvisActionsResolveResults.csv` is written through `DataExporter.write_with_format_selection`. The SQLite backend and the CSV backend stay unchanged.

**Testing**: pytest with the fake session in `tests/unit/marvis/actions/conftest.py`. Guard tests in `tests/guardrails/`.

**Target Platform**: Windows 11, macOS, and Linux. The product also runs in a Podman container.

**Project Type**: CLI menu operation with a web portal control.

**Performance Goals**: One resolve request for each Marvis Action, paced by `AdaptivePacer`. The stop rule lowers the request count after a refusal.

**Constraints**: ASCII log output. An inline comment on each changed line. Action logging before and after each request. No live Mist call in a test. No new direct child in a noncompliant folder.

**Scale/Scope**: Two source modules, two unit test modules, one guard test module, two documents, and one changelog fragment.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Each rule has a result and a reason. The constitution is version 1.9.0 (`.specify/memory/constitution.md`).

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, folders | Pass | The change adds no direct child. `src/mist/intelligence/marvis/actions/` holds seven direct children on remote `main`. That debt is grandfathered and stays unchanged. |
| I. Function limits | Pass | `resolve` and `_send` keep five logical blocks or fewer, and 25 lines or fewer. A helper method takes the stop reason. |
| II. Class-based design | Pass | Changes stay in `MarvisActionsClient` and `MarvisBulkResolver`. |
| III. Typed confirmation | Pass | `RESOLVE <count>` stays unchanged (`selection.py` line 504 on remote `main`). |
| III. Secrets at the logging boundary | Pass | Masking runs inside `_error_text` before the results file and the log. |
| III. Destructive category | Fail, pre-existing, unchanged | Menu 270 mode 3 is `interactive_safe` (`operation_registry.py` line 347). The constitution counts other changes to the Mist cloud as destructive (line 120). This plan does not change the category. See `analysis.md` item A-1. |
| IV. Full deployment pipeline | Pass | `tasks.md` contains T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. |
| V. ASCII logs and log levels | Pass | The new warning text is ASCII. The result summary uses debug. |
| VI. Inline comments | Pass | Each changed line gets an inline comment. Tasks T008 and T009 require it. |
| VII. Action logging | Pass | The existing info line before each request stays. The refusal warning follows the answer. |
| Mist transport: mistapi only | Pass | The resolve request uses `mist_put`, a mistapi session method. The change adds no direct HTTP call. No endpoint method exists in the pinned SDK for the labs path. |
| Owned WebSocket transport | Not applicable | No WebSocket transport is added. |
| Podman test containers | Not applicable | No container starts for tests. |
| File paths | Pass | No path join changes. |
| Output backends | Pass | `_write_results` keeps `DataExporter.write_with_format_selection`. |
| Data directory | Pass | Results stay under `data/` through the exporter. |
| Database keys | Pass | The `resolveOrgMarvisActions` primary key strategy stays unchanged. No endpoint is added. |
| Testing rules | Pass | New tests use the fake session. No production credential appears in a test. |
| Documentation | Pass | The endpoint report and the operator guide change. A guard test checks the documented statuses. |
| README | Not applicable | `README.md` has no menu 270 entry. The operator guide carries the behavior. |
| Release notes | Pass | One fragment is added under `changelog.d/`. |
| Audience standard | Pass | The warning text names the next step in plain words. |
| SpecKit escalation | Pass | The change touches two classes and more than three files, so this record exists. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/0/0/2/4/4389-marvis-resolve-http-403/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      resolve-refusal.md
    checklists/
      requirements.md
```

The route `0/0/1/2/0/0/2/4` is the base-5 form of issue 4389. The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` uses the same rule.

### Source Code (repository root)

| Path | Action | Change |
| - | - | - |
| `src/mist/intelligence/marvis/actions/client.py` | Modify | `_error_text` (lines 305 to 310) masks UUIDs, token values, and email addresses. Mask patterns are class attributes. |
| `src/mist/intelligence/marvis/actions/operation.py` | Modify | `MarvisBulkResolver.resolve` (lines 228 to 252) stops after HTTP 401 or 403. `_send` (lines 277 to 292) writes the refusal warning. `REFUSAL_STATUSES` is a class attribute. |
| `tests/unit/marvis/actions/test_client.py` | Modify | Add resolve tests to `TestResolveRequest` (line 358). Add masking tests. |
| `tests/unit/marvis/actions/test_operation.py` | Modify | Add run-level tests to `TestResolve` (line 416). Cover the stop rule, the warning, and the regression case. |
| `tests/guardrails/test_marvis_actions_portal_exposure.py` | Modify | Add a guard test. It checks that both documents name HTTP 401 or HTTP 403, and that the code constant matches. |
| `documentation/marvis-actions-api-endpoints.md` | Modify | Update "Response of the resolve", the `not_sent` row of the outcome table, and "Permissions". |
| `documentation/operator-guide.md` | Modify | Update the menu 270 paragraph that describes mode 3. |
| `changelog.d/issue-4389-marvis-resolve-403.md` | Add | One release-note fragment. |

No file is deleted. The results columns stay the same.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `src/mist/intelligence/marvis/actions/` holds seven direct children (grandfathered) | Existing module layout from issue 3299. | Moving files is a separate refactor (issue 4008 covers alarm modules). This plan adds no child to the folder. |

## Dependencies

- No new package and no version change. The pin `mistapi>=0.64.0,<0.65` stays.
- The gates use tools from `requirements-dev.txt`. Those tools are `symbol-diff`, `ste-linter`, `test-quality-analyzer`, `complexity-gate`, and `pytest-chunks`.

## Architecture

```text
Menu 270 mode 3 -> MarvisResolveWorkflow.resolve_open_actions -> MarvisBulkResolver.resolve
  -> MarvisBulkResolver._send -> MarvisActionsClient.resolve_action -> mistapi mist_put
  -> HTTP answer
       2xx:      status and empty error text, then verify read
       401/403:  masked error text, then stop rule, then later rows not_sent
       other:    masked error text, then the run continues
  -> results file through DataExporter
```

The masking step belongs to the client. The stop rule belongs to the resolver. The client returns the status and the text. The resolver decides whether the run continues. This split keeps the Mist transport in one class.

## Decisions

The decisions are recorded in `design/research.md` with alternatives, reasons, and risks. Summary:

- D-1: Keep the resolve request contract.
- D-2: Mask identifiers in the error text.
- D-3: Stop mode 3 after HTTP 401 or HTTP 403.
- D-4: Keep the menu 270 category. File a separate issue.
- D-5: Add no pre-flight role check in this change.
- D-6: Use mock sessions in every test.
- D-7: The credential policy for mode 3 runs needs a human decision.
- D-8: Mark the cause of HTTP 403 as unverified in the documents.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The stop rule halts a run for one action-specific refusal. | Some Marvis Actions stay open until a later run. | The results file marks each unsent row. The warning names the status. |
| Masking hides a useful identifier. | A reader lacks one value. | The status and the reason text stay. The masking rule is in the contract file. |
| The labs contract changes. | The request fails for another reason. | Existing tests pin the path and the body. |
| The cause stays unknown. | Mode 3 stays blocked for some tokens. | The quickstart lists the role check. Decision D-7 needs a human answer. |
| The category conflict remains. | The constitution and the registry disagree. | `analysis.md` item A-1 recommends a separate issue. The needs-human-review label stays. |
| Another change edits the same files. | A merge conflict. | No open pull request touches these paths. Check again before T-PR. |

## Rollback Steps

1. Revert the squash commit on `main` through a pull request.
2. The results file format does not change, so no data migration runs.
3. Rows written by the stop rule keep the `not_sent` outcome. A reader handles those rows as before.
