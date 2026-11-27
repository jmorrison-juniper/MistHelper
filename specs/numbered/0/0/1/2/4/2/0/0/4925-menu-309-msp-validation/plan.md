# Implementation Plan: Validate menu 309 with an MSP login

**Branch**: `chore/4925-menu-309-msp-validation` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The MSP scope code, the sign-in code, the console, and the automated tests are on `main` (research rows R-01 to R-93). This change adds no code. It adds three things. It adds the human-only live check for task 5 of issue #4925. It adds the implementer checks that come before the live check. It also adds one documentation fix (decision D-4) and one changelog fragment (decision D-8). One follow-up issue covers the contract mismatch (decision D-5).

## Technical Context

- **Language and version**: Python with the pinned mistapi version in R-72. The pin is `mistapi>=0.64.0,<0.65`.
- **Primary dependencies**: `mistapi>=0.64.0,<0.65` (R-72). This change adds no dependency.
- **Storage**: `data/` holds the run output. This change writes nothing to `data/`. The live check writes the CSV report, the master XML file, and the run folder under `data/`.
- **Testing**: pytest through the local gates table (`.github/copilot-instructions.md` line 61, R-71). The test files and lines are in research section 4.
- **Target platform**: Windows 11, macOS, and Linux (R-73). The owner runs the live check on Windows.
- **Project type**: Python command-line tool with a web portal. The menu and the portal share the code under `src/operations/exporting/ex_hardware_inventory/`.
- **Performance goals**: Stay below 5000 API calls per hour for each API token (R-89, R-90). The owner's estimate of requests per site is unverified (U-01).
- **Constraints**: Menu 309 opens a read-only shell on each switch (R-20). The run needs a typed phrase (R-21, R-22). The run must not retry in a tight loop (4920 FR-039, R-77).
- **Scale and scope**: One MSP login with N organizations. The owner learns N only when the run starts.

## Constitution Check

Each rule has a result and a reason. The constitution text is in `.specify/memory/constitution.md` (R-68).

- **I. Five-Item Rule**: PASS. The record folder sits on the route that base-5 digits of 4925 give (R-66, R-67). Each folder holds five children or fewer. No direct child enters a noncompliant parent.
- **II. Class-Based Architecture**: PASS. The change adds no code.
- **III. Safety-First**: PASS. The change adds no input handling. The phrase prompt uses the existing safe input (`console.py` line 90, R-22). Secrets stay out of the record (FR-015, R-68).
- **IV. Full Deployment Pipeline**: PASS with one stated exception. The pipeline runs in tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. The exception is the pull request keyword `Refs #4925` (decision D-3). The issue stays open until task 5 passes.
- **V. Observability and Logging**: PASS. The change adds no log statement. The quoted console lines are ASCII. The contract `design/contracts/msp-console-lines.md` lists them.
- **VI. Inline Comments**: PASS. The change adds no code. The rule applies to generated code only.
- **VII. Action Logging**: PASS. The change adds no code.
- **Technology constraints**: PASS. No container starts for this change. The live check runs on the owner's own terminal, so no test container is needed. The change writes nothing to `data/`.
- **Development workflow, labels**: PASS. The pull request uses the `chore` type label and the `docs` scope label. The issue keeps its `chore` and `MistHelper.py` labels. Decision D-7 adds `in-progress` and `needs-human-review`.
- **Development workflow, documentation**: PASS. The operator guide change is in the same change (task T009). The STE gate applies (R-74).
- **Development workflow, release notes**: PASS. The change adds one fragment (task T010, decision D-8).
- **Multi-agent git workflow**: PASS. The branch starts from `main`. The implementer checks for overlap with open pull requests before the push (task T-PR).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      msp-console-lines.md
      live-msp-evidence.md
    checklists/
      requirements.md
```

### Source Code (existing, read only for this change)

```text
MistHelper.py
src/operations/exporting/ex_hardware_inventory/operation.py
src/operations/exporting/ex_hardware_inventory/console.py
src/operations/exporting/ex_hardware_inventory/scope/resolver.py
src/operations/exporting/ex_hardware_inventory/scope/profile.py
src/operations/exporting/ex_hardware_inventory/run/master_xml.py
src/operations/exporting/ex_hardware_inventory/report/builder.py
src/mist/access/auth/interactive/login_orchestrator.py
src/mist/access/auth/interactive/credential_prompter.py
src/mist/realtime/websocket_streams/web/static/websockets.js
src/mist/realtime/websocket_streams/web/templates/websockets_page.html
```

## File-by-File Change Map

| Path | Action | Reason | Task |
| - | - | - | - |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/spec.md | Add | Feature specification | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/plan.md | Add | Implementation plan | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/tasks.md | Add | Task list and traceability | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/analysis.md | Add | Consistency review | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/research.md | Add | Remote table and decisions | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/data-model.md | Add | Evidence entities | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/quickstart.md | Add | Live check steps | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/contracts/msp-console-lines.md | Add | Console lines contract | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/contracts/live-msp-evidence.md | Add | Counts-only evidence contract | T-PR |
| specs/numbered/0/0/1/2/4/2/0/0/4925-menu-309-msp-validation/design/checklists/requirements.md | Add | Specification quality checklist | T-PR |
| documentation/operator-guide.md | Modify lines 620 to 623 | Remove the unverified refusal sentence (decision D-4) | T009 |
| changelog.d/issue-4925-menu-309-msp-validation.md | Add | One release-note fragment (decision D-8) | T010 |
| MistHelper.py, src/, tests/ | No change | The change adds no code | none |

## Architecture

The live check follows this path through the existing code:

1. The owner starts `python MistHelper.py --login --menu 309`. The launcher reads the flags (R-02, R-03, R-06).
2. `login_orchestrator.py` runs the login. The credential prompter asks for the email (R-39) and the password (R-40). The orchestrator calls the prompter for the 2FA code when Mist requires one (R-41, R-36, R-37). An aborted 2FA prompt clears the session (R-38).
3. `ExHardwareInventoryReport.run` in `operation.py` runs steps 1 to 4 (R-12).
4. `ScopeResolver.resolve` reads the profile with `getSelf` (R-31). It lists each MSP grant (R-25, R-26). It returns MSP scope only when a list returns an organization (R-29).
5. Step 2 previews each organization in scope (R-08, R-09, R-17). An unread organization gets one outcome row (R-07).
6. Step 3 shows the phrase (R-21). The owner types it, or presses Enter to cancel (R-22, R-23).
7. Step 4 runs each organization that has a target (R-10). The run writes the CSV report and the master XML file (R-45, R-48, R-49). A run with no switch writes no file (R-11).
8. The owner reads the counts and posts them in the evidence contract (FR-009).

## Dependencies

- No new dependency. The live check uses the installed SDK that the pin names (R-72).
- The feature code comes from issue #4920 and pull request #4924. Both are complete on `main`.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The 2FA code is wrong or expired | The login ends | Start the command again. The owner types the current code. |
| The MSP list returns HTTP 403 | The scope becomes one organization | Record the cause. Open a new issue (FR-010). |
| Mist limits the requests | An organization is not read | Wait before a new run. Do not retry in a tight loop (R-77). |
| The login session ends during the run | Mist behavior is unverified (U-02) | Record the cause. Start a new login. Use a token for a long run. |
| A secret appears in a run file | A posted secret stays in the history | Stop. Do not post the secret. Remove the run files by name (rollback step 4). |
| The owner selects the wrong scope | Shells open on too many switches | Read the step 1 lines before the phrase. Press Enter to cancel (R-23). |
| The checkout differs from `main` | The evidence does not match the code | Record the checkout SHA. Compare it with `main` (FR-014). |
| The 4920 contract wording differs from the code | The owner expects a different sentence | Use `msp-console-lines.md`, which quotes the code. Open a follow-up issue (decision D-5). |
| No automated test names the MSP sign-in section | The operator guide can drift | The owner live check is the proof. The shell lock guard reads other anchors (U-07). |

## Rollback Steps

1. Record: close the pull request without a merge. If merged, revert the squash commit through a new pull request. The record has no runtime effect.
2. Operator guide: revert the change to lines 620 to 623 in the same pull request.
3. Changelog: remove the fragment in the same pull request.
4. Live check: menu 309 changes no Mist setting, because the shells are read-only (R-20). Remove only the CSV report, the master XML file, and the run folder of that run.

Caution: remove the run files by exact name. Do not delete the whole `data` folder, because it holds other output.

## Contracts

This plan includes the `contracts` folder with two files:

- `msp-console-lines.md` lists the console lines that the owner reads. Each line has its source.
- `live-msp-evidence.md` defines the counts-only evidence that the owner posts.

The CSV and XML contracts stay in the 4920 record (rows R-91 and R-92). This record refers to them. It copies no content from them.
