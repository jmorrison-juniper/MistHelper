# Implementation Plan: Menu 270 Live Resolve Acceptance Evidence

**Branch**: `docs/3341-menu-270-live-resolve-evidence` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record at `specs\numbered\0\0\1\0\1\3\3\1\3341-menu-270-live-resolve-evidence\`. The route is the base-5 value of 3341, padded to eight digits. Research rows 36 and 37 hold the route script facts.

## Summary

Issue #3341 requires one live resolve request. The request must return HTTP 2xx, outcome `resolved`, and a closed verified status. Mist refused the one approved request on 2026-10-21 with HTTP 403. The resolve path, its typed gate, and its offline tests exist on `main`. This plan corrects the endpoint report and records the owner-only live check. It makes no code change. A code change waits for the cause in issue #4389.

## Technical Context

**Language/Version**: Python 3.15 or newer. The language section of `.github\copilot-instructions.md` names this rule (research row 32).

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`. The installed package is 0.64.1 (research row 51). The pin appears in the same language section (research row 32).

**Storage**: `data\OrgMarvisActionsResolveResults.csv`, written by the results writer (research row 13) through the shared exporter. The `data\` folder holds product output (research row 52). The results endpoint has a natural key strategy (research row 24).

**Testing**: pytest. The offline tests live in `tests\unit\marvis\actions\`.

**Target Platform**: The owner runs the live check on a Windows 11 workstation.

**Project Type**: Command-line menu with a web portal. The registry comment states that the operations portal runs safe and interactive_safe rows (research row 4).

**Performance Goals**: Not applicable. The live check changes one action. No throughput target applies.

**Constraints**: A resolve request changes Mist Cloud data. The live check must cause no outage (FR-011).

**Scale/Scope**: One Marvis Action for each live run. No batch run is in scope.

## Constitution Check

Source: `.specify\memory\constitution.md`. Principle III is at research row 33, and the mistapi rule is at research row 34.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one folder under the managed route. Each folder holds five children or fewer. No code hierarchy changes. |
| II. Class-Based Architecture | Pass | No code changes. No wrapper or function is added. |
| III. Safety-First | Pass, with an open decision | The typed gate, which requires RESOLVE followed by the count, exists (research row 17). The category question stays open as D-5, which is a human decision. |
| IV. Full Deployment Pipeline | Pass | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the documentation change. The live check is owner evidence, not a pipeline step. |
| V. Observability and Logging | Pass | The change adds no logging. The results file records the HTTP status, the outcome, and the verified status. |
| VI. Inline Comments | Pass | The change adds no code. Any changed code block must carry inline comments before merge. |
| VII. Action Logging | Pass | The change adds no code. Existing logging writes an info line before each resolve request and a debug line after the call (research row 7). |
| Technology: mistapi | Pass, with a note | mistapi 0.64.1 holds no method for the `labs` paths (research row 50). The call uses `APISession.mist_put` (research row 43), which is a mistapi method. No raw HTTP client is used. Decision D-6 records the choice. |
| Technology: owned WebSocket transport | Not applicable | No WebSocket flow is in scope. |
| Technology: Podman test containers | Not applicable | The offline tests and the owner live check run on the local virtual environment. No container starts. |
| Technology: file paths | Pass | The change adds no path code. |
| Technology: output backends | Pass | The results file uses the shared exporter through the results writer (research row 13). |
| Technology: database keys | Pass | The results endpoint has a natural key strategy (research row 24). |
| Technology: data directory | Pass | The results file belongs under `data\`. |
| Development: new menu operations | Not applicable | No menu operation is added. |

## Architecture

No architecture changes. The resolve path has four steps.

```text
Menu 270 row (research row 1)
  -> mode 3 branch (research row 14)
  -> typed prompts and request body (research rows 15 to 17)
  -> resolve_action and one mist_put call (research rows 6 and 7)
  -> mistapi APISession.mist_put (research row 43)
  -> verify read and verdict (research row 12)
  -> results file (research rows 8 and 13)
```

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\0\1\3\3\1\3341-menu-270-live-resolve-evidence\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      resolve-put.md
      results-csv.md
      menu-270-prompts.md
      live-evidence-record.md
    checklists\
      requirements.md
      live-check.md
      docs-change.md
```

### Source Code

No source code changes. The modules and tests that implement mode 3 stay as they are on `main`.

## File Change Map

| Action | Repository path | Change |
| - | - | - |
| Modify | `documentation/marvis-actions-api-endpoints.md` | Line 13 names mistapi 0.64.1. Line 582 is replaced with the 2026-10-21 attempt. A live-attempt section states the date, HTTP 403, outcome `error`, the open status, and issue #4389. |
| Add | `specs/numbered/0/0/1/0/1/3/3/1/3341-menu-270-live-resolve-evidence/` | The record. It holds 14 files: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, three design files, four contract files, and three checklist files. |

Unchanged: `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, `src/mist/intelligence/marvis/actions/*.py`, `tests/unit/marvis/actions/*.py`, and `changelog.d/`. The changelog stays unchanged because the change alters no user-visible behavior.

## Dependencies

No new package is added. The pinned mistapi range stays unchanged. Issue #4389 is a dependency for acceptance only.

## Risks and Mitigations

| Risk | Mitigation |
| The owner runs the resolve on the wrong action. | The filter must show one action. The preview count must read 1. The owner types nothing when the count differs (FR-002, FR-003). |
| HTTP 403 repeats after a retry. | No retry occurs until issue #4389 names a cause (FR-008). |
| Mist changes the beta labs path or body. | The offline tests fail on a changed path or body (research rows 20 and 22). The owner repeats the live check on approval. |
| Mist closes the action between preview and request. | The outcome is `error` or `sent_unverified`. The owner records the result and does not retry. |
| The endpoint report drifts again. | Tasks T003 and T006 change the report with a check. The owner evidence record contract fixes the fields. |
| The category conflict stays unresolved. | D-5 is a human decision. FR-013 keeps the current row until the owner decides. |
| The debug HTTP line is absent from `data\script.log`. | The `http_status` column in the results file is the primary record. The quickstart reads that column first (analysis item A-7). |

## Rollback Steps

1. Revert the squash commit of the documentation pull request on `main`. The change touches one document and one record folder. No runtime behavior changes.
2. Caution: a live resolve request changes one Mist Marvis Action. Set the action back to Open in the Mist UI to undo the change.
3. Record the undo in issue #3341 with the date and the result.
