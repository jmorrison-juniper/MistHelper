# Quickstart: Verify issue #4759

Run the read steps from the main checkout. Run the gate steps and the pull request steps from the feature worktree on branch `docs/4759-two-factor-login-note`. Activate the project environment first with `.venv\Scripts\Activate.ps1`.

Each `gh` command in this file needs the two setup lines before it. The value of the account variable is never printed.

## Step 1. Confirm the old statement on the old blob

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$oldBlob = gh api repos/jmorrison-juniper/MistHelper/git/blobs/f897a85e40ab9c30a0d9bb5e61d2aab9be0fd71e | ConvertFrom-Json
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($oldBlob.content)) -split "`n" | Select-Object -Index 90
```

Expected: line 91 holds the old statement that MistHelper does not handle interactive two-factor flows.

## Step 2. Confirm the corrected note on main

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$note = gh api "repos/jmorrison-juniper/MistHelper/contents/documentation/api/admins/POST_login_two_factor.md?ref=main" | ConvertFrom-Json
$note.sha
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($note.content)) -split "`n" | Select-Object -Index 90
```

Expected: the blob SHA is `98aeb3e81b08c956dc1137f04a833f33220a7bb2`. Line 91 names the interactive login and the SDK call.

## Step 3. Confirm the fragment is absent before T003

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/changelog.d/issue-4759-two-factor-login-note.md?ref=main"
```

Expected before T003: an HTTP 404 response. Expected after the merge: a JSON response for the fragment file.

## Step 4. Confirm no page holds the old statement at HEAD

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n -i "does not handle interactive 2FA" HEAD -- documentation
```

Expected: no output. The exit code is 1.

## Step 5. Confirm the production callers of the SDK login call

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "login_with_return(" HEAD -- src
```

Expected: matches only in `src/mist/access/auth/interactive/login_orchestrator.py` and `src/interfaces/portals/upgrade_portal/app/routes/auth.py`.

## Step 6. Confirm the owner hold state before T-PR

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh issue view 4759 -R jmorrison-juniper/MistHelper --json comments --jq '.comments[-1].url'
```

Expected: the newest comment is an owner instruction that supersedes the hold. If the newest comment is `issuecomment-6904293028`, the hold stays in force. Do not run T-PR.

## Step 7. Run the STE gate on the changed Markdown files

Run this command from the feature worktree root.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation/api/admins/POST_login_two_factor.md documentation/api/admins/POST_login.md changelog.d/issue-4759-two-factor-login-note.md
```

Expected: each file scores 80 or above.

## Step 8. Run the changelog guard

Run this command from the feature worktree root.

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

Expected: no failure. The owner reports one skip for pull request events. That report is unverified (U-1 in `design/research.md`).

## Step 9. Run the regression evidence tests

Run these commands from the feature worktree root.

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -k "test_two_factor_login_resends_credentials_with_installed_sdk or test_success_calls_login_with_return_with_two_factor" -q
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py -k test_prompt_two_factor_returns_trimmed_value -q
```

Expected: all three selected tests pass.

## Step 10. Check open pull request overlap before T-PR

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$openPullRequests = gh pr list -R jmorrison-juniper/MistHelper --state open --limit 200 --json number,files | ConvertFrom-Json
foreach ($pullRequest in $openPullRequests) {
foreach ($changedFile in $pullRequest.files) {
if ($changedFile.path -match 'POST_login|issue-4759') { "pull request $($pullRequest.number) touches $($changedFile.path)" }
}
}
```

Expected: no output.

## Step 11. Check the pull request file list after T-PR

Run this command from the feature worktree, on the feature branch, after the pull request opens.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view --json files --jq '.files[].path'
```

Expected: the fragment file `changelog.d/issue-4759-two-factor-login-note.md` and the files of the record folder `specs/numbered/0/0/1/2/3/0/1/4/4759-two-factor-login-note`. The lines `README.md` and `CHANGELOG.md` do not appear.
