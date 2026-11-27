# Quickstart: Mando pin conflict in the pip-audit gate

Use these steps to reproduce the failure, to confirm the fix, and to verify the merge. Each step names the exact command. Steps 1 to 3 read only.

## Prerequisites

- Read access to `jmorrison-juniper/MistHelper` through the `gh` command.
- A worktree from `main` with a `.venv`, created as `.github/copilot-instructions.md` describes in its environment section.
- A Windows PowerShell session at the worktree root.

## Step 1. Reproduce the failure from the CI log

Set the account variables first.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Read the failed log of the job.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137338084755 --log-failed
```

Expected result: The output holds `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`, and `ERROR: ResolutionImpossible`.

## Step 2. Read the mando pin on the pull request head and on main

Read the pull request head file. The response holds the content in base64.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=e86098cdc2b189d217805b3b4060ef609cbc37af" --jq ".content"
```

Read the main file the same way, with `?ref=main`.

Expected result: Line 179 reads `mando==0.8.2` on the pull request head, and `mando==0.7.1` on main. Line 365 reads `radon==6.0.1` on both.

## Step 3. Read the radon range in the local metadata

Open the file `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` at line 31.

Expected result: The line reads `Requires-Dist: mando (<0.8,>=0.6)`.

## Step 4. Run the dependency lock guard after the change

```powershell
python -m pytest tests/guardrails/test_dependency_lock_file.py
```

Expected result: The five new tests and the existing tests pass. The range test prints the count of pins that it examined.

## Step 5. Run each applicable local gate

Run the commands in the list under T-LOCAL-GATES in `tasks.md`. Each command states its expected result.

## Step 6. Watch the remote checks of the replacement pull request

```powershell
gh pr checks <number> --watch
```

Replace `<number>` with the number of the replacement pull request.

Expected result: The check `pip-audit (CVE scan)` reports success.

## Step 7. Verify main after the merge

Read the latest Quality Gates run on main.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --branch main --limit 1 --json databaseId,conclusion,headSha
```

Read the jobs of that run. Replace `<run id>` with the `databaseId` value from the previous command.

```powershell
gh run view <run id> -R jmorrison-juniper/MistHelper --json jobs
```

Expected result: The job `pip-audit (CVE scan)` reports `success`.

## Step 8. Verify the image revision label (owner host)

Inspect the image that the container build produced.

```powershell
podman image inspect <image reference>
```

Read the `Labels` value for `org.opencontainers.image.revision`.

Expected result: The label equals the merge commit SHA. The label name is the OCI standard name, and the build source is unverified (U-9).
