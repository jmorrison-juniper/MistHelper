# Quickstart: Port the routed layout and the git extension to Spec Kit 1.4.3

This file gives the exact steps to reproduce the defects and to verify the change for issue #4873. Run every command from the repository root unless a step says otherwise. Use the `.venv` of the main checkout, as `copilot-instructions.md` requires for a new worktree.

## 1. Prepare the environment

Warning: the branch `chore/4873-routed-git-extension` already exists in the worktree `MistHelper-4873-git-extension`. Reuse that worktree only after the orchestrator approves. Deleting that worktree removes the local commit `76b920fbc`. Run the next command only when the branch does not exist.

```powershell
git worktree add ..\MistHelper-4873-routed-git-extension -b chore/4873-routed-git-extension origin/main
```

Change into the worktree and bootstrap the environment.

```powershell
Set-Location ..\MistHelper-4873-routed-git-extension
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Confirm that `pwsh` version 7 is on the path.

```powershell
pwsh -NoProfile -Command "$PSVersionTable.PSVersion"
```

## 2. Select the record without writing the pointer

Use the environment variable for every dry run. Do not change `.specify/feature.json`.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "specs\numbered\0\0\1\2\3\4\4\3\4873-routed-git-port"
```

Record the pointer state before the runs.

```powershell
git --no-optional-locks status --short .specify/feature.json
```

## 3. Reproduce defect F-02 (the 1.0.0 git script)

The 1.0.0 script reads only the direct children of `specs\`. Run its dry run.

```powershell
.specify\extensions\git\scripts\powershell\create-new-feature.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

The `FEATURE_NUM` value does not count the records under `specs\numbered\`. Compare it with the highest number in that tree.

```powershell
Get-ChildItem -LiteralPath specs\numbered -Directory -Recurse | Where-Object { $_.Name -match '^\d{3,}-' } | ForEach-Object { $_.Name } | Sort-Object | Select-Object -Last 5
```

## 4. Check the routed core (FR-001 to FR-005)

Run the routed core dry run. `SPEC_FILE` must contain `specs\numbered\`.

```powershell
.specify\scripts\powershell\create-new-feature.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

Run the three read-only setup scripts. Each must exit 0 and print JSON. The script `update-agent-context.ps1` writes the agent context file, so this quickstart does not run it.

```powershell
.specify\scripts\powershell\check-prerequisites.ps1 -Json
.specify\scripts\powershell\setup-plan.ps1 -Json
.specify\scripts\powershell\setup-tasks.ps1 -Json
```

Confirm that the pointer did not change (SC-006).

```powershell
git --no-optional-locks status --short .specify/feature.json
```

The command must print nothing.

## 5. Check the git 1.0.8 scripts (FR-008 to FR-011)

Run the PowerShell 1.0.8 dry run after T007. Read `FEATURE_NUM`.

```powershell
.specify\extensions\git\scripts\powershell\create-new-feature-branch.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

Run the bash 1.0.8 dry run on macOS or Linux after T008. Read `FEATURE_NUM`. The value must match the PowerShell value (SC-004).

```bash
.specify/extensions/git/scripts/bash/create-new-feature-branch.sh --json --short-name "routed-check" "routed check"
```

Run the core dry run that follows the git dry run. Its `SPEC_FILE` must hold `specs\numbered\` (FR-011).

```powershell
.specify\scripts\powershell\create-new-feature.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

## 6. Confirm the adopted tree against upstream (FR-010)

Read the upstream blob SHAs at tag `v1.4.3`. Each adopted file must match its blob (see `research.md` rows R-072 to R-077).

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$upstreamTree = gh api "repos/github/spec-kit/git/trees/v1.4.3?recursive=1" | ConvertFrom-Json
$upstreamTree.tree | Where-Object { $_.path -like "extensions/git/*" } | ForEach-Object { $_.sha + " " + $_.path }
```

Read the registry and the manifest state after T011 and T012.

```powershell
git --no-optional-locks diff --stat -- .specify/extensions/.registry .specify/integrations
```

## 7. Run the guard tests (one command for each file)

```powershell
python -m pytest tests/guardrails/test_routed_core_port.py
python -m pytest tests/guardrails/test_spec_route_contract.py
python -m pytest tests/guardrails/test_specify_gitignore_keeps_feature_json.py
python -m pytest tests/guardrails/test_routed_git_extension_port.py
python -m pytest tests/guardrails/test_integration_local_rules.py
python -m pytest tests/guardrails/test_process_folder_structure.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

The `test_spec_route_contract.py` symlink case can fail on a host without the Windows symlink privilege. Record that failure with its cause in the PR body (existing rule from part 1).

## 8. Run the local gates that apply

```powershell
python -m ruff check .
python -m black --check .
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
```

Record each gate that does not apply, with its reason, in the PR body. The reasons are in `plan.md`, in the Constitution Check and in `analysis.md`.

## 9. Read the integration status (SC-001)

Run the Specify CLI status command. This record did not run it (U-1). Save its output in the PR body.

```powershell
specify integration status
```

The output must name no managed file without a documented local rule.

## 10. Remove the scratch data

Remove any scratch fixture under `test-artifacts\`. The folder is git-ignored. Do not run a prune command on a shared host.

```powershell
Remove-Item -LiteralPath test-artifacts\routed-fixture -Recurse -Force -ErrorAction SilentlyContinue
```
