# Implementation Plan: Webhook response status

**Branch**: `fix/4718-webhook-log-comments` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record for issue #4718 at `specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

PR #4852 merged the initial-response status gates and their tests. The repair adds the inline comments and debug lines that Principles VI and VII require. It does not change the behavior of the gates. The plan keeps every existing module-level name and class name. It records each structural violation for separate remediation.

## Technical Context

- **Language/Version**: Python 3.15 or newer. `.github/copilot-instructions.md` line 18 begins the section that states this rule (R34).
- **Primary Dependencies**: `mistapi` 0.64.1 within the pin `>=0.64.0,<0.65`, stated at `.github/copilot-instructions.md` line 18. Test dependencies: pytest and requests.
- **Storage**: None for the repair. The tests block SQLite access through the guard in `tests/unit/export/test_org_webhook_deliveries_exporter.py` lines 27 and 28.
- **Testing**: Offline pytest with synthetic native responses. The `block_network` fixture runs for every test.
- **Target Platform**: Windows 11, macOS, and Linux. `.github/copilot-instructions.md` line 8 states the platforms (R87).
- **Project Type**: Command-line menu operation 256. The web portal path is out of scope.
- **Performance Goals**: Zero pagination calls after a rejected initial response (SC-001).
- **Constraints**: Zero socket, DNS, SQLite, or credential-file access during the tests.
- **Scale/Scope**: One exporter module, one reserved unit test module, and the coordinated stable-selection test module. No new source file.

## Constitution Check

The gate is `.specify/memory/constitution.md`. Each row gives the result and the reason. Evidence IDs such as R14 point to the remote table in `design/research.md`.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, hierarchy levels | FAIL | Pre-existing and introduced violations. The test module holds 11 top-level children (R14). PR #4852 added three of them. `deliveries()` spans 32 lines against a 25-line limit (R08). `TestStableWebhookResolver` holds six methods (R19). Remediation RM-1 to RM-3 covers each one. |
| I. Function limits in changed functions | PASS | `_select_webhook_id` keeps 25 lines because the repair adds no line to it (D-4). `_response_status_code` gains one parameter and one debug line inside one logical block. |
| I. Directory children under the numbered route | PASS | The route folder holds one child before the repair. This record reuses that child folder (D-6). |
| II. Class-based architecture | FAIL | Pre-existing. The module-level helper `_response_status_code` (exporter line 25, R02) sits outside a class. PR #4852 changed its body. Remediation RM-4 moves it. |
| III. Safety-first input handling | PASS | The operator selection reads input through `InputUtils.safe_input` (exporter line 92). No log line carries a secret. |
| IV. Full deployment pipeline | PARTIAL | Local gates did not run in this session because rule 2 of the brief forbids them. The PR #4852 rollup shows no failing check. Merge commit b1307510 shows 38 of 38 successful check runs (R74). PR #4852 omitted `Closes #4718` at step 7. Image revision evidence is Unverified (U-4). |
| V. Observability and logging | PASS | Log text is ASCII. Error lines name the organization identifier and the HTTP status. The repair adds no new module, so no structured logging rule applies. |
| VI. Inline comments | FAIL on `main` | Executable lines in the changed functions lack inline comments (R05). Task T009 repairs them. |
| VII. Action logging | FAIL on `main` | No debug line follows the list call or the delivery call (R06, R07). Info lines exist before both calls. Task T010 adds the debug lines. |
| Technology: mistapi interface | PASS | The exporter calls only `mistapi` functions (R76, R77). It sends no direct HTTP request. |
| Technology: primary keys | PASS | The primary key strategy for the delivery endpoint exists (R27). |
| Technology: output backends | PASS | The exporter writes rows through `DataExporter.write_with_format_selection` (exporter line 109). |
| Technology: data directory and file paths | PASS | The exporter writes no path. `DataExporter` owns the output files. The changed lines build no path. |
| Technology: container runtime | N/A | The repair starts no container and publishes no port. The container policy applies only when a container runs (`documentation/container-deployment.md` line 141, R52). |
| Development workflow: new menu operation | N/A | No operation, menu number, or registry entry changes. |
| Development workflow: testing and security | PASS | No skip-list change. The changed test module must pass the test-quality ratchet (U-1). No security finding is suppressed. |
| Documentation | PASS | The README and the operator guide hold no webhook behavior text (R53, R54). No documentation update applies. |
| Release notes | PASS | Fragment `changelog.d/issue-4718-webhook-response-status.md` exists (R20). The repair adds no fragment (D-8). |
| Complexity-driven escalation | PASS | The change spans three or more files. This record is the required specification. |
| Multi-agent git: branch name | PASS | PR #4852 used `fix/4718-webhook-response-failures`. The repair uses `fix/4718-webhook-log-comments`, which matches the branch rule for issue 4718. |
| Multi-agent git: pull request title | PASS | The PR #4852 title `fix(export): reject failed initial webhook responses` passed the Conventional Commits check. |
| Multi-agent git: required labels | PASS | Issue #4718 carries `bug`, `MistHelper.py`, and `in-progress`. |
| Multi-agent git: pull request body | FAIL for PR #4852 | The body says "Refs #4718". The repair pull request body must say `Closes #4718`. |

## Architecture

Menu 256 runs this flow.

1. `MistHelper.py` line 4982 binds menu 256 to `OrgWebhookDeliveriesExporter.deliveries` (R26).
2. `deliveries()` (exporter line 119) reads the organization identifier and calls `_select_webhook_id` (line 126).
3. `_select_webhook_id` (line 71) calls `listOrgWebhooks` (line 74). It validates the initial response (lines 75 to 82). It pages the rows (line 83). It asks the operator for one selection (lines 92 and 93).
4. `deliveries()` calls `searchOrgWebhooksDeliveries` inside a `try` block (lines 130 and 134). It validates the initial response (lines 137 to 144). It pages the rows (line 145) and persists them (line 147).
5. `_persist` (line 98) calls `DataExporter.write_with_format_selection` (line 109).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      sdk-initial-response.md
      operator-messages.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/operations/exporting/export/org_webhook_deliveries_exporter.py   (modify)
tests/unit/export/test_org_webhook_deliveries_exporter.py            (modify)
```

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `src/operations/exporting/export/org_webhook_deliveries_exporter.py` | Modify | Add inline comments to the changed executable lines (T009). Add an operation parameter to `_response_status_code`, and one debug line inside it (T010). Pass the call name at the two call sites (T010). |
| `tests/unit/export/test_org_webhook_deliveries_exporter.py` | Modify | Add one parametrized test to `TestWebhookInitialResponse`, which starts at line 298 (T011). |
| `tests/unit/export/test_issue_3188_webhook_id_selection.py` | No change | The status-200 doubles already exist at lines 79, 100, 120, and 125 (R17). |
| `tests/integration/export/test_org_webhook_native_refusals.py` | No change | The native 403, 500, and 503 tests already exist (R15, R16). |
| `tests/e2e/web_portal/test_issue_3188_webhook_control.py` | No change | The browser double already returns HTTP 200 (R22). |
| `changelog.d/issue-4718-webhook-response-status.md` | No change | The release-note fragment already exists (R20). |
| `web_portal/routes/settings.py` | No change | Separate issue (D-1). |
| `specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/` | Replace | This record replaces the eight legacy files. It adds `design/contracts/` and `design/checklists/security.md` (D-6). |

## Dependencies

- `mistapi` 0.64.1 within the pin `>=0.64.0,<0.65`. No change.
- pytest and requests. Existing development dependencies. No change.
- The dependency audit gate does not apply, because no requirement changes.

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| RK-1 | A debug line echoes an untrusted value. | The helper logs the call name and an integer status. For any other value, it logs the fixed text "returned no valid HTTP status". |
| RK-2 | A debug line breaks an existing assertion. The test `test_rejected_status_never_becomes_empty` forbids the words "exported" and "persisted". | `design/contracts/operator-messages.md` lists the forbidden words. T011 runs the whole test module after the change. |
| RK-3 | The record count of `test_absent_status_attribute_is_rejected` changes. That test asserts one record. | The test captures ERROR level only, so the debug line is not captured. T012 runs the test. |
| RK-4 | The reserved test imports `mistapi.__api_response.APIResponse` (line 16), which is a private SDK module. | The SDK pin stays below 0.65. A future SDK change fails the import in the test. |
| RK-5 | A signature change breaks another caller of `_response_status_code`. | T009 requires a repository search for other callers. Other modules define their own helpers with the same name. |
| RK-6 | The web portal path stays defective until the separate issue merges. | The Caution statement in `spec.md`. The separate issue is recommended in RM-5. |
| RK-7 | Principle I violations remain. | This plan records them with remediation actions RM-1 to RM-4. |
| RK-8 | The repair pull request fails a gate that did not run locally. | T-LOCAL-GATES runs each applicable gate before the pull request. |

## Rollback Steps

1. Open a revert pull request for the repair squash commit on `main`. Do not force-push `main`.
2. Caution: a revert of PR #4852 restores the defect in which a missing HTTP status reads as an empty result. Revert PR #4852 only when the repair fails in production.
3. Set `$repo` to the repository path. Run `git -C $repo rev-parse b1307510^1` to find the pre-fix commit. The pre-fix exporter blob is `dff2b4d6a`, from the index line of the PR #4852 diff.
4. Run the offline test set in `design/quickstart.md` after each revert.
5. Keep issue #4718 open until the repair merges.

Warning: never push another commit to branch `fix/4718-webhook-response-failures`. Its pull request is merged, and a later commit becomes orphaned.

## Complexity Tracking

| Violation | Status | Why it stays | Simpler alternative rejected because | Remediation |
| - | - | - | - | - |
| `deliveries()` spans 32 lines (R08) | Grandfathered and touched by PR #4852 | The repair changes comments only, so the line count stays the same. | A split changes control flow and widens the diff beyond FR-006 and FR-008. | RM-1 |
| The test module holds 11 top-level children (R14) | Grandfathered before PR #4852. PR #4852 added three children. | The repair adds no child. | A new class or a new module adds a child or a file. | RM-2 |
| `TestStableWebhookResolver` holds six methods (R19) | Grandfathered and untouched | The repair does not change the class. | A split changes a reserved file beyond the repair. | RM-3 |
| Module-level `_response_status_code` (R02) | Grandfathered and touched by PR #4852 | The repair adds one parameter and one debug line. | Moving the helper into a class changes its call shape and the class method count. | RM-4 |

## Remediation Actions (separate from issue #4718)

- RM-1: Split `deliveries()` into a status gate and a persistence call. Each function must hold 25 lines or fewer. Open a separate issue.
- RM-2: Move `_native_response` (line 51), the `initial_endpoint` fixture (line 64), and `TestWebhookInitialResponse` (line 298) into a nested test package. Open a separate issue.
- RM-3: Split `TestStableWebhookResolver` (line 30) into two classes. Each class must hold five methods or fewer. Open a separate issue.
- RM-4: Move `_response_status_code` (line 25) into a class. Open a separate issue.
- RM-5: Apply the same status gate to `OrgWebhookChoiceProvider._read_webhooks` in `web_portal/routes/settings.py` (lines 46 and 47). Open a separate issue (D-1).
- RM-6: Repair the sibling exporters that default a missing HTTP status to 200 (R31, R32, U-3). Open one issue for each module family (D-11).
- RM-7: Update `documentation/MIST_API_MISSING_ENDPOINTS.md` lines 947 and 948. These lines list both operations as missing (R56). Open a documentation issue.
