# Quickstart: Webhook config test isolation

## Prerequisites

- Run each command from the repository root, unless a step names another folder.
- Set the `gh` host and token in each shell before a `gh` command. The token value comes from the account variable. Never print it.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Caution: listing all environment variables prints their values. Read one named variable at a time.

- The main checkout holds five modified files that this issue does not change. Do not commit them. Start each branch from `origin/main`.
- Warning: do not create a commit on the branch name `fix/4730-webhook-env-isolation`. Its pull request merged, so a new commit on that name becomes an orphan that no one merges.

## Verification Checks

Each check ID names one verification result. The step column names the procedure that runs it.

| Check | Purpose | Procedure | Expected result |
| - | - | - | - |
| TC-001 | The test passes with `WEBHOOK_ENABLED` unset | Q-8 | `1 passed` |
| TC-002 | The test passes with `WEBHOOK_ENABLED=false` | Q-8 | `1 passed` |
| TC-003 | The whole file passes in both states | Q-8 | Zero failed tests in both runs |
| TC-004 | The negative control fails without the precondition | Q-9 | `1 failed` at the default assertion |
| TC-005 | The follow-up diff names one file | Q-11 | `tests/unit/web_portal/test_webhook_signature.py` only |
| TC-006 | The follow-up changes comments only, and no module-level name changes | Q-11 | Each changed line differs by a trailing comment. Symbol gate exit code 0 |
| TC-007 | The default assertion remains on line 240 | Q-2 | Line `240` |
| TC-008 | Each code line in lines 229 to 240 has an inline comment | Q-11 | Eight of eight non-exempt code lines carry a comment |
| TC-009 | Compile, lint, and format pass | Q-11 | Compile prints nothing. Ruff prints `All checks passed`. Black prints `No file needs a change` |
| TC-010 | The record route resolves to the numbered path | Q-10 | `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation` |
| TC-011 | Issue 4730 is closed and has no `in-progress` label | Q-6 | `CLOSED`, with no `in-progress` label |
| TC-012 | No commit hook override or signing override is set | Q-11 | No `core.hooksPath` value. `commit.gpgsign` is not `false` |
| TC-013 | No changelog fragment is added, and the body gives the reason | Q-11 and Q-12 | No file under `changelog.d/`. The pull request body names the internal-only reason |
| TC-014 | The test quality gate reports no new finding | Q-11 | `gate: 0 new findings vs baseline` |

## Q-0. Reproduce the defect at the pre-fix commit (issue steps 1 to 4)

Run these steps from the repository root. The worktree uses the commit that issue #4730 cites as its reproduction base.

```powershell
git worktree add ..\MistHelper-4730-repro 3964d21d03f9f5717cb8eafb7272ecff21f5362a
cd ..\MistHelper-4730-repro
Remove-Item Env:WEBHOOK_SECRET -ErrorAction SilentlyContinue
$env:WEBHOOK_ENABLED = 'false'
python -m pytest -q tests/unit/web_portal/test_webhook_signature.py::TestAppFactoryWebhookConfig::test_the_factory_stores_an_empty_secret_when_the_variable_is_absent
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
python -m pytest -q tests/unit/web_portal/test_webhook_signature.py::TestAppFactoryWebhookConfig::test_the_factory_stores_an_empty_secret_when_the_variable_is_absent
```

Expected: the first run reports `1 failed`. The error line reads `assert False is True` at `assert app.config["WEBHOOK_ENABLED"] is True`. The second run reports `1 passed`.

Caution: removing a worktree deletes its files. Remove only the worktree that this step created, with `git worktree remove ..\MistHelper-4730-repro`.

## Q-1. Remote blob of the test file

```powershell
$tree = gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" | ConvertFrom-Json
$tree.tree | Where-Object { $_.path -eq 'tests/unit/web_portal/test_webhook_signature.py' } | ForEach-Object { $_.sha }
```

Expected: `bcf0ad12319281ea484e98bba65ff2d544f6b8d3`.

## Q-2. Remote line numbers for the repair and the default (checks TC-007)

```powershell
$encoded = gh api repos/jmorrison-juniper/MistHelper/git/blobs/bcf0ad12319281ea484e98bba65ff2d544f6b8d3 --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($encoded -replace '\s', '')))
$index = $text.IndexOf('monkeypatch.delenv("WEBHOOK_ENABLED"')
($text.Substring(0, $index) -split "`n").Count
$index = $text.IndexOf('assert app.config["WEBHOOK_ENABLED"] is True')
($text.Substring(0, $index) -split "`n").Count
```

Expected: `234`, then `240`.

Production default, blob `0fb25df1732815d18ff30d1823cbbdd30608aed6` (`web_portal/app.py`):

```powershell
$encoded = gh api repos/jmorrison-juniper/MistHelper/git/blobs/0fb25df1732815d18ff30d1823cbbdd30608aed6 --jq .content
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($encoded -replace '\s', '')))
$index = $text.IndexOf('WEBHOOK_ENABLED_CONFIG_KEY, "true"')
($text.Substring(0, $index) -split "`n").Count
```

Expected: `129`.

## Q-3. Sibling references on the tree

Run after the fetch in Q-7 so that `origin/main` is current.

```powershell
git --no-optional-locks grep -n WEBHOOK_ENABLED origin/main -- src web_portal tests
```

Expected: the repair line (234) in the test file, `test_webhook_ingestion.py` line 76, the e2e journey line 415, `native.py` line 190, and `src/foundation/persistence/db/__init__.py` line 69. No other line appears.

## Q-4. CI evidence for main

```powershell
$run = gh run view 45774119357 -R jmorrison-juniper/MistHelper --json conclusion,headSha,jobs | ConvertFrom-Json
$run.conclusion
$run.headSha
$run.jobs | Where-Object { $_.name -match 'root-units' } | ForEach-Object { $_.name + ' ' + $_.conclusion }
```

Expected: `success`, then `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, then `pytest coverage shard (root-units) success`.

## Q-5. Pull request 4843 and ancestry of the merge commit

```powershell
$pr = gh pr view 4843 -R jmorrison-juniper/MistHelper --json state,mergeCommit,files,closingIssuesReferences | ConvertFrom-Json
$pr.state
$pr.mergeCommit.oid
$pr.files | ForEach-Object { $_.path + ' +' + $_.additions + ' -' + $_.deletions }
git fetch --no-tags origin main
git merge-base --is-ancestor 15da34506c7802d81336006ffeacb1e466a31d56 origin/main
$LASTEXITCODE
```

Expected: `MERGED`, then `15da34506c7802d81336006ffeacb1e466a31d56`, then one line `tests/unit/web_portal/test_webhook_signature.py +1 -0`, then `0`. Exit code `0` means the merge commit is an ancestor of `origin/main`. The remote comparison returned `ahead` at authoring time (R-08).

## Q-6. Issue state (after T009 only, check TC-011)

```powershell
$issue = gh issue view 4730 -R jmorrison-juniper/MistHelper --json state,labels | ConvertFrom-Json
$issue.state
$issue.labels | ForEach-Object { $_.name }
```

Expected before T009: `OPEN`, with labels `bug`, `test`, `tests`, and `in-progress`. Expected after T009: `CLOSED`, with no `in-progress` label.

Caution: a closed issue leaves the default issue list. The orchestrator reopens issue 4730 with `gh issue reopen 4730 -R jmorrison-juniper/MistHelper` when a later check fails.

## Q-7. Step A worktree at merged main

```powershell
git fetch --no-tags origin main
git worktree add ..\MistHelper-4730-verify origin/main
cd ..\MistHelper-4730-verify
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Caution: the bootstrap installs packages and downloads Chromium. Run it only in the new worktree.

## Q-8. Checks TC-001 to TC-003 in step A

Run these commands in `..\MistHelper-4730-verify`.

```powershell
Remove-Item Env:WEBHOOK_SECRET -ErrorAction SilentlyContinue
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
python -m pytest tests/unit/web_portal/test_webhook_signature.py::TestAppFactoryWebhookConfig::test_the_factory_stores_an_empty_secret_when_the_variable_is_absent -q
```

Expected TC-001: `1 passed`.

```powershell
$env:WEBHOOK_ENABLED = 'false'
python -m pytest tests/unit/web_portal/test_webhook_signature.py::TestAppFactoryWebhookConfig::test_the_factory_stores_an_empty_secret_when_the_variable_is_absent -q
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
```

Expected TC-002: `1 passed`.

```powershell
$env:WEBHOOK_ENABLED = 'false'
python -m pytest tests/unit/web_portal/test_webhook_signature.py -q
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
python -m pytest tests/unit/web_portal/test_webhook_signature.py -q
```

Expected TC-003: both runs report zero failed tests.

## Q-9. Check TC-004 negative control in step A

In the verification worktree, delete line 234 of `tests/unit/web_portal/test_webhook_signature.py`. That line is `monkeypatch.delenv("WEBHOOK_ENABLED", raising=False)`. Then run:

```powershell
$env:WEBHOOK_ENABLED = 'false'
python -m pytest tests/unit/web_portal/test_webhook_signature.py::TestAppFactoryWebhookConfig::test_the_factory_stores_an_empty_secret_when_the_variable_is_absent -q
Remove-Item Env:WEBHOOK_ENABLED -ErrorAction SilentlyContinue
git restore -- tests/unit/web_portal/test_webhook_signature.py
```

Expected: `1 failed`. The failing assertion is `app.config["WEBHOOK_ENABLED"] is True`.

Caution: the negative control edits a tracked file. The `git restore` command returns the file to its committed state. Run the restore before any commit.

## Q-10. Check TC-010 record route

```powershell
. .specify\scripts\powershell\spec-route.ps1
Resolve-SpecFeaturePath -SpecsDir specs -BranchName 4730-webhook-env-isolation -Number 4730
```

Expected: `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation`. The route script defines functions only (lines 4 to 118).

## Q-11. Step B checks on the follow-up branch

Create the worktree from `origin/main` with the follow-up branch name. Replace `<NEW-ISSUE>` with the number from T008.

```powershell
git worktree add ..\MistHelper-<NEW-ISSUE>-webhook-comments -b chore/<NEW-ISSUE>-webhook-test-comments origin/main
```

Add the inline comments (T010) with the edit tool. Then run:

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
symbol-diff --base origin/main tests/unit/web_portal/test_webhook_signature.py
```

Expected TC-009 and TC-006: compile prints no output. Ruff prints `All checks passed`. Black prints `No file needs a change`. The symbol gate prints `no module-level name changed` with exit code 0.

```powershell
git diff --name-only origin/main HEAD
git diff -U0 origin/main HEAD -- tests/unit/web_portal/test_webhook_signature.py
git config --show-origin --get core.hooksPath
git config --show-origin --get commit.gpgsign
```

Expected TC-005: the name list holds only `tests/unit/web_portal/test_webhook_signature.py`. Expected TC-006: each changed line differs from the original line only by a trailing inline comment. Expected TC-012: the `core.hooksPath` read returns nothing. The `commit.gpgsign` read returns nothing or `true`, and never `false`.

Expected TC-013: the name list holds no file under `changelog.d/`.

Expected TC-008: each code line in lines 229 to 240 carries a comment on the same line. Read the lines with the command below. Lines 231, 232, 236, and 238 are exempt.

```powershell
Get-Content -LiteralPath tests\unit\web_portal\test_webhook_signature.py -TotalCount 240 | Select-Object -Skip 228
```

Expected TC-014: run the test quality gate. Its output holds the line `gate: 0 new findings vs baseline`.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

## Q-12. Pull request, checks, and merge

Push the follow-up branch and create the pull request with the title and the body that T-PR lists. Use the commit trailer that this session requires.

```powershell
git push -u origin chore/<NEW-ISSUE>-webhook-test-comments
gh pr create -R jmorrison-juniper/MistHelper --base main --head chore/<NEW-ISSUE>-webhook-test-comments --title "chore(tests): add inline comments to the webhook config test"
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
```

Use the number that `gh pr create` returns for `<number>`.

The orchestrator authorizes the merge. After every check passes, the executor adds the auto-merge label and the orchestrator confirms the squash merge.

```powershell
gh pr edit <number> -R jmorrison-juniper/MistHelper --add-label auto-merge
```

Warning: do not bypass the commit hooks. Do not use `--no-verify` or change `core.hooksPath`. A bypassed commit cannot show that the checks passed.
