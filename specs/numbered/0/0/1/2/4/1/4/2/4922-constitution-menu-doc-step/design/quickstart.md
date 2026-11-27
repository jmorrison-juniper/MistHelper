# Quickstart: Menu step names the generated pages

Run each command from the worktree root in PowerShell. Activate the worktree environment first with `.venv\Scripts\Activate.ps1`.

## 1. Reproduce the stale text

```powershell
Select-String -LiteralPath .specify\memory\constitution.md -Pattern 'Update README'
Select-String -LiteralPath .github\copilot-instructions.md -Pattern 'menu table in'
```

Expected output: line 352 of the constitution, and line 242 of the rule file.

## 2. Run the new guard cases before the change

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -k menu_step_and_version_record
```

Expected result: five failed cases, one for each of `menu-step`, `readme-bullet`, `rule-file-step`, `footer-version`, and `sync-report`.

## 3. Apply the change

Apply tasks T003 to T007 in `tasks.md`. Each edit uses the exact text in `plan.md`.

## 4. Run the verification commands

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m pytest tests/guardrails/test_websocket_transport_constitution.py
python -m ruff check .
python -m black --check .
symbol-diff --base origin/main tests/guardrails/test_changelog_fragment_policy.py
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
ste-linter --config .ste-linter.toml --min-score 80 .specify/memory/constitution.md
```

Expected results:

- Each pytest run exits with code 0.
- Ruff prints `All checks passed`.
- Black reports that no file needs a change.
- Symbol-diff prints `no module-level name changed`.
- The first ste-linter run scores each listed file at 80 or above.
- The second ste-linter run measures the constitution only. It records the score in the pull request body. It does not gate CI.

Run the Full tests shard from the Full tests row. It covers `tests\guardrails` and the other readers of the constitution:

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: one summary line for each shard, with no failed chunk.

## 5. Run the test quality check

Run the preflight before the commit. The commands come from the Test quality ratchet section of `.github/copilot-instructions.md`.

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Run the required check after the commit and before the push:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected output: the line `gate: 0 new findings vs baseline`.

## 6. Read the pull request checks

Read-only. Set `PR_NUMBER` to the number that `gh pr create` returns.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr checks $PR_NUMBER -R jmorrison-juniper/MistHelper
```

## 7. Gates that do not apply

| Gate | Reason |
| --- | --- |
| Compile | The change does not touch `MistHelper.py`. |
| Types | `tests/` is outside `MYPY_PATHS` (`ci.yml` line 93). |
| Safe sweep | The change alters no operation. |
| Coverage | The command measures `src` only. |
| Complexity | The command reads a package. The change adds no package code. |
| Security lint | The command reads a package. The change adds no package code. |
| Dependency audit | The change alters no dependency. |
| Code quality | The command reads `src/` only. |
| Dead code | `VULTURE_PATHS` excludes `tests/` (`ci.yml` line 101). |
| Docstrings | `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` exclude `tests/` (`ci.yml` lines 104 and 107). |
| Menu reference | The change alters no registry entry, menu, or generated page. |
| Ops portal | The change touches no file under `ops-portal/`. |
| Ops platform | The change touches no file under `mist-ops-platform/`. |
