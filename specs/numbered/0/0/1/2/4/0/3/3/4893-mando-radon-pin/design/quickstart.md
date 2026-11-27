# Quickstart: Reproduce and verify issue #4893

Run both environment lines before each `gh` command. The lines select the GitHub account for this repository.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Part 1: Reproduce the failure from the CI logs

All commands in this part are read only.

1. Read the run metadata and the job table for run 45064243269.

   ```powershell
   gh run view 45064243269 -R jmorrison-juniper/MistHelper --json conclusion,headSha,jobs
   ```

   Expected: `conclusion` is `failure`, and `headSha` is `e86098cdc2b189d217805b3b4060ef609cbc37af`.

2. Search the failed-step log for the resolution conflict.

   ```powershell
   gh run view 45064243269 -R jmorrison-juniper/MistHelper --log-failed | Select-String -Pattern 'ResolutionImpossible|mando==0.8.2'
   ```

   Expected: lines that include `Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`.

3. Read the steps of the `mypy (strict)` job.

   ```powershell
   gh api repos/jmorrison-juniper/MistHelper/actions/jobs/137338084785
   ```

   Expected: step `Install dependencies` has conclusion `failure`. Step `Run mypy` has conclusion `skipped`.

4. Read the pins on `main` and on the PR head. Decode the `content` field from base64, then read line 179 and line 365.

   ```powershell
   gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main"
   gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=e86098cdc2b189d217805b3b4060ef609cbc37af"
   ```

   Expected: `main` line 179 is `mando==0.7.1`. The PR head line 179 is `mando==0.8.2`. Line 365 is `radon==6.0.1` in both.

5. Read the radon constraint from the local environment.

   ```powershell
   Select-String -LiteralPath .venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA -Pattern '^Requires-Dist: mando'
   ```

   Expected: line 31 is `Requires-Dist: mando (<0.8,>=0.6)`.

## Part 2: Verify the fix on the changed files

Run these commands from the worktree of branch `fix/4893-mando-radon-pin`.

1. Guard tests, including the four new tests.

   ```powershell
   python -m pytest tests/guardrails/test_dependency_export.py -v
   ```

   Expected: all tests pass. The four tests in class `TestDependencyPinPolicy` appear in the output.

2. Changelog guard.

   ```powershell
   python -m pytest tests/guardrails/test_changelog_fragment_policy.py
   ```

   Expected: all tests pass.

3. Lint and format.

   ```powershell
   python -m ruff check .
   python -m black --check .
   ```

   Expected: `All checks passed`, and no file needs a change.

4. Install the development requirements. The install must finish with no resolution error.

   ```powershell
   python -m pip install -r requirements.txt -r requirements-dev.txt
   ```

   Expected: the command exits with code 0.

5. Type check. The paths come from `MYPY_PATHS` in `.github/workflows/ci.yml` (RC-70).

   ```powershell
   python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
   ```

   Expected: `Success`.

6. Test quality ratchet.

   ```powershell
   test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
   ```

   Expected: `gate: 0 new findings vs baseline`.

7. Markdown grade for each record file and the changelog fragment. Run the command from the repository root after the record is copied into place.

   ```powershell
   Get-ChildItem -LiteralPath specs\numbered\0\0\1\2\4\0\3\3\4893-mando-radon-pin -Recurse -Filter *.md | ForEach-Object { ste-linter --config .ste-linter.toml --min-score 80 $_.FullName }
   ```

   Expected: each file scores 80 or above.

## Part 3: Verify the remote result

1. Watch the checks on the fix PR. The branch name selects the PR.

   ```powershell
   gh pr checks fix/4893-mando-radon-pin -R jmorrison-juniper/MistHelper --watch
   ```

   Expected: every `Quality Gates` job reports success. The `mypy (strict)` job reports success.

2. After the merge, confirm that PR #4888 closed with the closing comment.

   ```powershell
   gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,comments
   ```

   Expected: `state` is `CLOSED`. One comment names the merged PR and the record path.
