# Quickstart: Mixed WAN History Summaries

Use these steps to reproduce the defect and to verify the repair. Run the commands in PowerShell from the repository root unless a step names another folder. Each step names its expected result. Write no output to any folder outside the repository worktrees. Scenario 4 only reads remote state.

## Prerequisites

- Windows 11 with PowerShell, `git`, `gh`, and `uv`.
- The `gh` command reads the account token from the `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper` variable. Set `GH_HOST` and `GH_TOKEN` before each `gh` call, as the brief requires.
- Python 3.15.2 through `uv`, as `.github/copilot-instructions.md` lines 28 and 29 describe (remote checks 89 and 90).

## Scenario 1: Reproduce the defect on the parent commit

The parent commit is `07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc` (remote check 45). The parent holds the defect at `summary.py` lines 333 and 338 (remote checks 48 and 49).

1. Fetch the candidate branch.

```powershell
git fetch origin jmorrison-juniper-4200-migrate-mistwanperformance
```

2. Create the candidate worktree in detached mode.

```powershell
git worktree add --detach ..\MistHelper-4794 origin/jmorrison-juniper-4200-migrate-mistwanperformance
```

3. Create the parent worktree in detached mode.

```powershell
git worktree add --detach ..\MistHelper-4794-parent 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc
```

4. Copy the candidate test file into the parent worktree only.

```powershell
git -C ..\MistHelper-4794-parent checkout origin/jmorrison-juniper-4200-migrate-mistwanperformance -- tests/unit/wan_performance/test_calendar_summaries.py
```

5. Run the three regression tests with the candidate venv. Create the venv first with the bootstrap steps in the candidate worktree.

```powershell
Set-Location ..\MistHelper-4794
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
Set-Location ..\MistHelper-4794-parent
..\MistHelper-4794\.venv\Scripts\python.exe -m pytest tests/unit/wan_performance/test_calendar_summaries.py -k "mixed_event_and_ordinary_hours or missing_event_evidence or known_zero_flaps" -q
```

Expected result: three failures.

- The mixed-hour test raises `KeyError: 'flap_count'` from `_complete`.
- The missing-evidence test reports zero flaps and zero minutes.
- The known-zero test reports zero minutes.

If an import fails, record the module name. A missing module means the parent is not a complete base. Use Scenario 3 with the candidate test file instead.

6. Remove the parent worktree. Caution: removing a worktree deletes its folder. The parent holds no unsaved work.

```powershell
Set-Location ..\MistHelper-4794
git worktree remove ..\MistHelper-4794-parent
```

## Scenario 2: Verify the repaired head

Run these commands in the candidate worktree.

```powershell
Set-Location ..\MistHelper-4794
python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q
python -m pytest tests/e2e/web_portal/test_wan_performance_live.py -k renders_missing_evidence_as_unknown -q
```

Expected result: each command reports zero failures.

## Scenario 3: Run the issue reproduction on the candidate

The issue reproduction has five steps. The mixed-hour test performs the same steps in `tests/unit/wan_performance/test_calendar_summaries.py`.

| Issue step | Test lines | Action |
| - | - | - |
| 1. Load the committed modules | 1 to 15 | Import the summary, measurement, and offline preview modules. |
| 2. Create the event hour | 226 to 234 | Set `up_minutes` 60, `down_minutes` 0, and `flap_count` 0. |
| 3. Build with the event hour only | 243 to 247 | Read the daily summary. |
| 4. Create the poll hour | 235 to 241 | Set only `rx_bps` 100. |
| 5. Build with both hours | 243 to 247 | Read the daily summary. |

Expected result after the repair: `LinkEventSummary(1, 1, 24, 60, 0, 0, 100)`. Before the repair, step 5 raises `KeyError: 'flap_count'`.

## Scenario 4: Check the remote state (read only)

Set the environment before each `gh` command.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$repairSha = 'd7a706d71cf13661cf33e5b4a96ddafd79b6b67b'
$headSha = '843be63bc837513b4442dae69da9f0db922e0ed1'
$range = $repairSha + ([string][char]46) * 3 + $headSha
gh api "repos/jmorrison-juniper/MistHelper/compare/$range" --jq ".status"
gh api repos/jmorrison-juniper/MistHelper/commits/15c69b1176f7ae7c24e010aba3d29915ef228610 --jq ".sha"
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,isDraft,mergeable,mergeStateStatus,headRefName --jq ".state"
```

Expected results:

- The compare command prints `ahead`, which means the repair commit is an ancestor of the candidate head (remote check 44).
- The commit command returns HTTP 422 (remote check 46).
- The PR command prints `OPEN` (design/research.md, Linked work).

## Scenario 5: Run the local gates

Run each applicable gate in the candidate worktree. Read `MYPY_PATHS` from the candidate `.github/workflows/ci.yml`, not from memory.

```powershell
python -m py_compile src\interfaces\wan_performance\domain\summary.py tests\unit\wan_performance\test_calendar_summaries.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
radon cc src\interfaces\wan_performance\domain -j | complexity-gate --max 10
bandit -c pyproject.toml -r src\interfaces\wan_performance -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc src/interfaces/wan_performance/domain/summary.py
ste-linter --config .ste-linter.toml --min-score 80 <each Markdown file in the record>
```

The full test shards use the two `pytest-chunks` commands at `.github/copilot-instructions.md` lines 87 and 88 (remote check 93).

### Gate map

| Gate | Applies | Reason | Remote check |
| - | - | - | - |
| Compile | Yes | Changed Python files | 91 |
| Lint | Yes | Changed Python files | 91 |
| Format | Yes | Changed Python files | 91 |
| Types | Yes | Changed `src/` files | 26 |
| Tests | Yes | Changed test module and e2e check | 91 |
| Full tests | Yes | Changed test module | 93 |
| Safe sweep | No | No menu operation changes | 91 |
| Coverage | Yes | Changed `src/` code | 91 |
| Test quality | Yes | Changed test module | 92 |
| Complexity | Yes | Changed `src/` code | 91 |
| Security lint | Yes | Changed `src/` code | 91 |
| Dependency audit | No | No dependency change | 91 |
| Code quality | Yes | Changed `src/` code | 91 |
| Dead code | Yes | Changed `src/` code | 27 |
| Docstrings | Yes | Changed `src/` code | 28 and 29 |
| Menu reference | No | No menu change | 91 |
| Symbols | Yes | Changed `summary.py`, base is the parent commit | 91 |
| STE | Yes | Changed Markdown in the record | 5 |
| Ops portal | No | No change under `ops-portal/` | 91 |
| Ops platform | No | No change under `mist-ops-platform/` | 91 |

The Symbols base is the parent commit because main lacks `summary.py` (remote check 37).

## Scenario 6: Deliver the repair (T-PR)

Caution: a force push rewrites the candidate branch history. Record the old head `843be63bc837513b4442dae69da9f0db922e0ed1` in a pull request comment before the push.

```powershell
Set-Location ..\MistHelper-4794
git fetch origin main
git rebase origin/main
git push --force-with-lease origin HEAD:jmorrison-juniper-4200-migrate-mistwanperformance
```

If the rebase reports conflicts over 20 lines, run `git rebase --abort`, then stop and report the blocker (decision D-9).

Edit the PR body so it holds `Closes #4794` and keeps `Refs #4200` without a closing keyword. Use a body file outside the repository.

```powershell
gh pr edit 4208 -R jmorrison-juniper/MistHelper --body-file <body file outside the repository>
```

## Expected Results Summary

| Check | Expected |
| - | - |
| Parent reproduction | Three failures, with `KeyError: 'flap_count'` in the mixed-hour case |
| Repaired head unit tests | Zero failures |
| Repaired head e2e check | Zero failures |
| Five-step reproduction | `LinkEventSummary(1, 1, 24, 60, 0, 0, 100)` |
| Symbols gate | `no module-level name changed`, exit code 0 |
| Lint gate | `All checks passed` |
| STE gate | Each Markdown file scores 80 or more |
