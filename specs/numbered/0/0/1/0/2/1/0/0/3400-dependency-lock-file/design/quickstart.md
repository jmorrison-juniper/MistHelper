# Quickstart: Tracked Dependency Lock File

This quickstart lists the commands that reproduce the current state and verify each slice. Run the local commands only in an implementation worktree after the bootstrap. This authoring step runs none of them.

## 1. Read the remote state

Read the commit of `main` and the blob of `uv.lock`. Both commands are read-only.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | select(.path == \"uv.lock\") | .path + \" \" + .sha"
```

At the time of this record, the commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The blob of `uv.lock` is `5445b4eb382dc9f6dd5c351ba40c521f01f93165`.

## 2. Check the overlap before each slice

List the open pull requests and their files. This command is read-only.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr list -R jmorrison-juniper/MistHelper --state open --json number,title,files --limit 100
```

If a listed file matches a path that your slice changes, wait for that pull request. Do not start the slice.

## 3. Run the guard commands for each slice

Run the verification command of each task in `tasks.md`. The guard commands are these:

```powershell
python -m pytest tests/guardrails/test_dependency_declaration_parity.py
python -m pytest tests/guardrails/test_dependency_lock_file.py
python -m pytest tests/guardrails/test_dependency_export.py
python -m pytest tests/guardrails/test_dependency_lock_workflow.py
python -m pytest tests/guardrails/test_container_build_trigger.py
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py
pip-audit -r requirements.txt
```

Each guard prints the count of files, records, or cases that it examined. A guard that cannot read its input fails. Read the printed count before you accept a pass (AGENTS.md, Tests section).

## 4. Regenerate the exports after a lock change

Run these commands from the repository root after a declaration change and a lock refresh:

```powershell
uv lock
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
```

For the ops export, which applies after task T018, run these commands:

```powershell
Push-Location mist-ops-platform
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
Pop-Location
```

## 5. Check the image after approval

The image freeze check runs in `.github/workflows/container-build.yml` after a dispatch that the user approves. Read the step output in that workflow run. Do not start a local test container with a bare `podman run`. The repository instructions require each test container to join the compose group.

## 6. Check the style of the record and the documents

Run the STE command from the Local gates table on the instruction files:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
```

Run the same tool on the record files:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/plan.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/tasks.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/analysis.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/research.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/data-model.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/quickstart.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/contracts/lock-install-contract.md specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/checklists/requirements.md
```

## 7. Check the folder structure

Count the direct children of each new folder. The record folder holds five children or fewer. The `design` folder holds five children or fewer. Each `contracts` and `checklists` folder holds five files or fewer.
