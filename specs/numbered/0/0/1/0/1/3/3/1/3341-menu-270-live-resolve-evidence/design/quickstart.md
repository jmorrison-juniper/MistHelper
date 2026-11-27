# Quickstart: Menu 270 Live Resolve Acceptance Evidence

This guide has two parts. Part 1 runs the offline checks, and any operator can run it. Part 2 is the live check, and only the repository owner can run it.

## Part 1: Offline Checks

Prerequisites: a Windows 11 workstation and the repository root as the working folder.

If the worktree has no `.venv`, run the bootstrap command first (research row 31).

```powershell
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
```

Activate the environment and run the offline tests.

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests\unit\marvis\actions -q
```

Expected result: every test passes. The 22 tests of the test set live in `test_client.py`, `test_operation.py`, `test_selection.py`, and `test_portal_contract.py`. `tasks.md` lists each one.

Check the endpoint report for the stale sentence. Run this command before T003. It prints one line. Run it again after T003. It prints nothing.

```powershell
Select-String -Path documentation\marvis-actions-api-endpoints.md -Pattern 'no live resolve request was sent'
```

## Part 2: Owner-Only Live Check

### Preconditions

All of these conditions must hold before the first answer:

1. The owner approves one named lab organization and one named Marvis Action in writing. The approval appears in issue #3341.
2. The lab organization holds one open Marvis Action of the approved topic.
3. Issue #4389 names a cause for the HTTP 403 response, or the owner approves a new run in writing after the 2026-10-21 refusal (FR-008).
4. The owner's Mist access is configured outside the repository. Do not write a credential in a file or in the issue.

Warning: a live check that causes an outage cannot be undone. Stop the run if any device or site outside the approved action could change.

### Run the Live Check

1. Start the menu with `python MistHelper.py`. Choose menu `270`.
2. Answer the mode prompt with `3`.
3. Answer the category and subcategory prompts so that the preview lists one action. If the preview lists more than one action, stop. Do not type a confirmation.
4. Answer the resolution code prompt with `suggested`. The approved attempt of 2026-10-21 used this code (issue comment IC_kwDOQltU8c8AAAABeBNT3g).
5. Answer the comment prompt with the text that the approval names. Leave it blank when the approval names no text.
6. At the confirmation prompt, type `RESOLVE 1` exactly. Any other text sends no request (FR-003).
7. At the acknowledge prompt, press Enter with no text. The alarm step stays unanswered (FR-004).
8. Wait for the run to finish. Read the summary line in the console.

Caution: the live check changes the status of one Mist Marvis Action. You can set the action back to Open in the Mist UI.

### Read the Results

Read the results file. This command reads the file and changes nothing.

```powershell
Import-Csv data\OrgMarvisActionsResolveResults.csv | Select-Object uuid, outcome, http_status, verified_status, message
```

Expected result: one row. The row shows outcome `resolved`, an HTTP 2xx status, and a closed verified status.

Read the run log for the request line. This command reads the log and changes nothing.

```powershell
Select-String -Path data\script.log -Pattern 'Sending the resolve request'
```

Expected result: one info line that names request 1 of 1. The HTTP status line may be absent at the default log level (unverified item U-4). The results file is the primary record.

### Decide the Next Step

| Outcome in the results file | Next step |
| - | - |
| `resolved`, HTTP 2xx, closed verified status | Record acceptance in issue #3341 (T005). Then add the accepted date to the endpoint report (T006). |
| `error` | Record the HTTP status and the message in issue #3341. Do not retry. Keep the cause with issue #4389. |
| `sent_unverified` | Check the action in the Mist UI. Record the result. This outcome does not count as acceptance. |
| `not_sent` | The stop signal ended the run before the request. Record it. Do not retry without new approval. |
| `skipped` | The action has no row key, so no request went out. Record it. Do not retry without new approval. |

Caution: a resolved action can be set back to Open in the Mist UI. Record the undo in issue #3341 with the date and the result.

## Part 3: Checks for the Documentation Change

Run these checks after T003 and before the pull request.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation/marvis-actions-api-endpoints.md
markdown-link-check documentation/marvis-actions-api-endpoints.md
python -m pytest tests\unit\marvis\actions -q
```

Expected result: the STE score is 80 or above, the link check reports no broken link, and the tests pass.

Confirm that the registry file is unchanged (FR-013). This command prints nothing when the file is unchanged.

```powershell
git diff --stat -- src/foundation/support/utils/operation_registry.py
```
