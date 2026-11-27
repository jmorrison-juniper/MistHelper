# Quickstart: Menu 243 Result File Not Found

## 1. Preconditions

- Create a worktree outside the repository path for branch `fix/4036-menu-243-preview-test`. Make the change in that worktree.
- Use synthetic files only. No live Mist call is needed.
- For a new worktree, run the bootstrap from the repository instructions, then activate the environment.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## 2. Reproduce the reported layout

This step proves that the browser test can fail. Use the scratch worktree at `..\misthelper-red-4036`.

1. Create the scratch worktree from the branch. Do not reuse the repository path.
2. Add the two-part table route from line 77 of commit `2a48cee`. Make it call the existing `preview_table` helper.
3. Copy the test module from the branch into the scratch worktree.
4. Run the browser module.

```powershell
python -m pytest tests/e2e/web_portal/test_operation_results_table.py -q
```

Expected result: the nested preview assertion fails with HTTP 404.

Caution: The scratch worktree contains a changed route. Remove it after the run with `git worktree remove` so no other work uses it.

## 3. Verify the change on the branch

Run each command in the branch worktree. Each command must exit 0.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests/unit/web_portal/test_preview_row_order.py -q
python -m pytest tests/e2e/web_portal/test_operation_results_table.py -q
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py -q
python -m pytest tests/guardrails/test_process_folder_structure.py -q
symbol-diff --base origin/main tests/e2e/web_portal/test_operation_results_table.py
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4036-menu-243-preview-test.md
```

Run the STE command for each changed Markdown file in the record folder as well.

Full unit shards are not required for this change. The changed test file sits in `tests/e2e`, which neither `pytest-chunks` command reads.

## 4. Live check after merge

This check runs on the deployed product container at the merged revision. It confirms the symptom that the issue reports. Complete the steps in order.

1. Confirm the image revision. The expected value is the merged commit SHA.

```powershell
podman inspect misthelper-app --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'
```

2. Copy the ledger folder outside the repository.

Caution: Menu 243 rewrites `data/mib_generator/oid_assignments.json`. Keep the copy until the live check passes. The copy restores the prior content if the run changes it.

```powershell
Copy-Item -Recurse -LiteralPath "data\mib_generator" -Destination "..\misthelper-4036-backup"
```

3. Open the operations page of the deployed portal on port 8055. Run menu 243 and wait for the status Complete.
4. Confirm that the output list names only `mib_generator/oid_assignments.json`.
5. Open the Results panel. Confirm that ledger rows appear and that no `Could not read the results` text appears.
6. Request the download route for `mib_generator/allowlist.json` and for `mib_generator/oid_assignments.json`. Confirm HTTP 200 for each request.
7. Capture a screenshot of the Results panel. Post the revision, the output list, the two download status codes, and the screenshot on issue #4036.
8. If the panel shows `File not found`, stop. Post the request path and the server log lines on a new issue. Leave issue #4036 open.

After step 7 passes, the orchestrator closes issue #4036.
