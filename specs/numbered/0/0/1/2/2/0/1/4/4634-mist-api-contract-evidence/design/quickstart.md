# Quickstart: Mist API Contract Evidence for the Cisco Converter

This file gives the exact steps to reproduce the evidence and to run the checks for issue 4634. Run each command from a PowerShell session. Each command reads files or GitHub data. None of the commands writes to Mist. Do not print the value of any environment variable. Refer to a secret by its name only.

The repository path used below is `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

## Step 1: Read the issue facts

1. Set the GitHub host and the account token from the account variable. Do not print the token.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

2. Read the issue fields. The output shows the title, the state, and the labels.

```powershell
gh issue view 4634 -R jmorrison-juniper/MistHelper --json number,title,state,labels,updatedAt
```

Expected: state `OPEN`. The labels include `needs-investigation` and `needs-human-review`.

## Step 2: Confirm the remote state of main

1. Read the commit at the head of main.

```powershell
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
```

Expected at drafting time: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. A later commit can change this value.

2. Read the blob SHA of the bundled OpenAPI JSON file on main.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | select(.path == "documentation/mist-api-openapi31json.json") | .sha'
```

Expected: `5f9f4ce94f812f0e818ee65f99f032118a28f56c`.

3. Confirm that the local file has the same blob SHA. The `hash-object` command without `-w` writes no object.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object documentation\mist-api-openapi31json.json
```

Expected: `5f9f4ce94f812f0e818ee65f99f032118a28f56c`.

## Step 3: Confirm the pinned SDK

1. List the installed mistapi distribution.

```powershell
Get-ChildItem -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages" -Filter "mistapi-*.dist-info" | Select-Object -ExpandProperty Name
```

Expected: `mistapi-0.64.1.dist-info`.

2. Confirm the operation ID and path for one write operation in the bundled JSON file. The file has one line, so the check reads the parsed object.

```powershell
$json = Get-Content -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\documentation\mist-api-openapi31json.json" -Raw | ConvertFrom-Json
$json.paths.'/api/v1/orgs/{org_id}/sites'.post.operationId
```

Expected: `createOrgSite`.

3. Confirm the SDK definition for the same operation. The `Select-String` command reads the file only.

```powershell
Select-String -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py" -Pattern "^def createOrgSite"
```

Expected: line 58, `def createOrgSite(`.

## Step 4: Run the offline contract tests

```powershell
python -m pytest tests\contract\web_portal\cisco_config_converter
```

Expected: 32 tests pass. No socket opens during the run. The run reads no Mist credential variable.

Each negative fixture acts as a control. A reviewer confirms that each negative fixture fails the schema or the allowlist and that its test asserts the rejection. A test that cannot fail is a defect under `AGENTS.md`.

## Step 5: Run the static and style checks

```powershell
python -m ruff check .
python -m black --check .
bandit -c pyproject.toml -r tests\contract\web_portal\cisco_config_converter -q
```

Expected: Ruff reports `All checks passed`. Black reports no file to change. Bandit reports no finding.

## Step 6: Run the changelog guard

```powershell
python -m pytest tests\guardrails\test_changelog_fragment_policy.py
```

Expected: the guard passes with the new fragment `changelog.d\issue-4634-mist-api-contract-evidence.md`.

## Step 7: Run the writing gate on each Markdown file

Run one command for each Markdown file of the record and for the changelog fragment. The example below uses the spec file.

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence\spec.md
```

Expected: the score is 80 or above.

## Step 8: Confirm that no production path changed

Run this command on the feature branch after the commit. The output lists the changed paths against main.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4634" diff --name-only origin/main
```

Expected: no path starts with `src/`. The listed paths match the file-by-file change map in `plan.md`.

## Step 9: Confirm the five-item rule for the record folder

```powershell
(Get-ChildItem -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence" | Measure-Object).Count
```

Expected: `5` (spec.md, plan.md, tasks.md, analysis.md, and design).

## Step 10: Compare the remote check counts

The remote check count appears in three places: `_meta\4634-STATUS.json` (field `remote_checks`), the table in `design\research.md`, and `_meta\4634-summary.md`. Count the table rows and the JSON array entries. Both counts must equal 80.

```powershell
(Get-Content -LiteralPath "C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4634\design\research.md" | Select-String -Pattern '^\| RV-' | Measure-Object).Count
```

Expected: `80`.
