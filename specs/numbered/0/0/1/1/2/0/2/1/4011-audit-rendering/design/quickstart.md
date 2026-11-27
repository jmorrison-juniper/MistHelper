# Quickstart: Refactor: isolate audit renderer modules

Use these steps to reproduce the current state and to verify the change. Each step names the task that it supports. Run the commands in PowerShell. Replace `<repo>` with the main checkout path. The worktree path is `..\MistHelper-4011` from the main checkout.

## Prerequisites

- Python 3.15.2 is available through `uv` (row RC-57).
- GitHub CLI is authenticated for the account `jmorrison-juniper`.
- The main checkout is at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` or later.

## Step 1: Show the current layout (T001)

Run these commands in the main checkout. Expect five children at the audit root and five children in the rendering package.

```powershell
Get-ChildItem -LiteralPath '<repo>\src\mist\access\audit' -Force | Where-Object { $_.Name -notlike '__pycache__' } | Select-Object Name
Get-ChildItem -LiteralPath '<repo>\src\mist\access\audit\rendering' -Force | Where-Object { $_.Name -notlike '__pycache__' } | Select-Object Name
Test-Path -LiteralPath '<repo>\src\mist\access\audit\rendering\helpers'
```

The last command prints `False`. The helpers package does not exist yet (row RC-10).

## Step 2: Create the worktree (T002)

```powershell
git -C '<repo>' worktree add '..\MistHelper-4011' -b chore/4011-audit-rendering origin/main
```

## Step 3: Bootstrap the environment (T002)

```powershell
Set-Location -LiteralPath '..\MistHelper-4011'
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

The bootstrap script is at `scripts/bootstrap_worktree.py` (row RC-42). The setup notes are in `documentation/development-setup.md` at lines 32 and 183.

## Step 4: Record the collected test counts (T003)

```powershell
python -m pytest --collect-only -q tests/test_audit_renderer.py tests/unit/marvis/mist/access/audit
```

Save the printed count in the pull request body.

## Step 5: Move the modules and remove the clusters package (T004 to T010)

```powershell
git mv src/mist/access/audit/rendering/_renderer_delta.py src/mist/access/audit/rendering/helpers/_renderer_delta.py
git mv src/mist/access/audit/rendering/_renderer_format.py src/mist/access/audit/rendering/helpers/_renderer_format.py
git mv src/mist/access/audit/rendering/_renderer_time.py src/mist/access/audit/rendering/helpers/_renderer_time.py
git mv src/mist/access/audit/rendering/clusters/_renderer_html.py src/mist/access/audit/rendering/helpers/_renderer_html.py
git mv src/mist/access/audit/rendering/clusters/_renderer_mermaid.py src/mist/access/audit/rendering/helpers/_renderer_mermaid.py
git rm src/mist/access/audit/rendering/clusters/__init__.py
```

Create `src/mist/access/audit/rendering/helpers/__init__.py` with the create tool. Then remove the exact `clusters` folder if a cache folder remains. Caution: remove only the exact `clusters` path.

## Step 6: Edit the imports and docstrings (T011 to T016)

Edit each file with the edit tool. The files and the lines are listed in `plan.md`, section "File change map". Each changed line keeps an inline comment.

## Step 7: Edit the guards and the artifacts, and add the new files (T018 to T026)

Edit the symbol guard rows, the hook guard rows, the seven hook catalog rows, and the #3824 structure test lists. Create the structure guard, the changelog fragment, and the record folder with the create tool.

Stage the explicit paths before any guard run:

```powershell
git add src/mist/access/audit/rendering/helpers/__init__.py tests/guardrails/test_audit_rendering_structure.py changelog.d/issue-4011-audit-rendering.md
```

## Step 8: Run the focused tests and guards (T028)

```powershell
python -m pytest tests/test_audit_renderer.py tests/unit/marvis/mist/access/audit tests/guardrails/test_audit_rendering_structure.py tests/guardrails/test_src_public_symbol_preservation.py tests/guardrails/test_performance_hook_catalog.py tests/guardrails/test_nested_package_structure.py tests/guardrails/test_changelog_fragment_policy.py
```

Each test passes. The structure guard prints the counts 5, 2, and 5.

## Step 9: Run the local gates (T-LOCAL-GATES)

Run each gate in `design/checklists/gates.md` with status `applies`. Record each result in the pull request body.

## Step 10: Commit, push, and open the pull request (T-PR)

Wait for the coordinator to assign the serial slot first. Then run:

```powershell
git -C ..\MistHelper-4011 commit -m "refactor(audit): isolate the audit renderer modules" -m "Closes #4011" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
git -C ..\MistHelper-4011 push --force-with-lease -u origin chore/4011-audit-rendering
```

Open the pull request with the same title and the body `Closes #4011`.

Warning: Do not run `git add -A` or `git add .` in the shared checkout. Those commands stage unrelated files from other sessions.
