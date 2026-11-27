# Quickstart: Metrics Gateway Core Modules

Run every command from a PowerShell prompt. The commands in sections 2 to 6 run in the new worktree, `..\MistHelper-4009`. Do not run them in the main checkout, because that checkout holds five unrelated modified files.

## 1. Reproduce the problem

1. List the gateway children in the current checkout.

```powershell
Get-ChildItem -LiteralPath src\interfaces\monitoring\metrics_gateway -Force | Where-Object { $_.Name -ne '__pycache__' } | ForEach-Object { $_.Name }
```

Expected result: `__init__.py`, `cache.py`, `catalog.py`, `collector.py`, `prometheus.py`, `samples.py`, `service.py`, `snmp.py`, and `web.py`. The eight modules without `__init__.py` exceed the limit of five.

2. Run the nested guard in the current checkout.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -q
```

Expected result: the test passes. The baseline entry for `src/interfaces/monitoring/metrics_gateway` still records 8 children.

## 2. Prepare the worktree

1. Fetch `main` from the remote.

```powershell
git fetch --no-tags origin main
```

2. Create the worktree and the branch.

```powershell
git worktree add ..\MistHelper-4009 -b chore/4009-metrics-gateway-core origin/main
```

3. Enter the worktree and install the interpreter.

```powershell
Set-Location ..\MistHelper-4009
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

4. If the bootstrap reports a missing C++ build tool on Windows, install the C++ workload first. Then run the bootstrap again.

## 3. Apply the change in this order

1. Create the core folder.

```powershell
New-Item -ItemType Directory -Path src\interfaces\monitoring\metrics_gateway\core
```

2. Move each module with `git mv`. Repeat the command for `catalog.py`, `collector.py`, and `samples.py`.

```powershell
git mv src/interfaces/monitoring/metrics_gateway/cache.py src/interfaces/monitoring/metrics_gateway/core/cache.py
```

3. Create `core/__init__.py`. Its documentation string states the purpose and the five-child reason.
4. Rewrite each import listed in `plan.md`. Add an inline comment to each changed line.
5. Update the MIB generator modules, the contract tests, and the unit tests.
6. Add the guard test, the four `MODULE_PATHS` entries, and the baseline and total changes.
7. Update `documentation/mib_generator.md`, the Observium comment, and the eight hook rows.
8. Regenerate the MIB and the menu pages with the repository tools. Do not edit either output by hand.

```powershell
python MistHelper.py --mib-generate
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
```

9. Review the MIB diff. Only the header path lines may change.

```powershell
git diff -- documentation/mibs/MISTHELPER-MIB.mib
```

10. Add the changelog fragment and copy the reviewed record into the routed folder.

Caution: a regenerated file that changes outside the expected lines needs review before commit. Stop and record the difference in the pull request.

## 4. Verify the change

Run each command after the related task. Each row names the expected result.

| No. | Gate | Command | Expected result |
| - | - | - | - |
| 1 | Compile | `python -m py_compile MistHelper.py` | No output |
| 2 | Compile the packages | `python -m compileall -q src\interfaces\monitoring\metrics_gateway src\operations\hardware\mib_generator` | No output |
| 3 | Import smoke, new paths | `python -c "import src.interfaces.monitoring.metrics_gateway.core.cache, src.interfaces.monitoring.metrics_gateway.core.catalog, src.interfaces.monitoring.metrics_gateway.core.collector, src.interfaces.monitoring.metrics_gateway.core.samples"` | Exit status 0 |
| 4 | Import smoke, old path | `python -c "import src.interfaces.monitoring.metrics_gateway.catalog"` | `ModuleNotFoundError`, exit status 1 |
| 5 | Lint | `python -m ruff check .` | `All checks passed` |
| 6 | Format | `python -m black --check .` | No file needs a change |
| 7 | Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| 8 | Targeted tests | Command below | All tests pass |
| 9 | Guardrails | `python -m pytest tests/guardrails -q` | All tests pass |
| 10 | MIB check | `python MistHelper.py --mib-check` | Exit status 0 |
| 11 | Menu drift | `python -m scripts.menu_api_map --check` | Exit status 0 |
| 12 | Symbols, changed files that keep their path | `symbol-diff --base origin/main` followed by each file path listed below | `no module-level name changed`, exit status 0 |
| 13 | Symbols, moved modules | `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py -q` | All tests pass |
| 14 | Old paths | Command below | No output |
| 15 | Complexity | `radon cc src/interfaces/monitoring/metrics_gateway src/operations/hardware/mib_generator -j \| complexity-gate --max 10` | No block above complexity 10 |
| 16 | Security lint | `bandit -c pyproject.toml -r src/interfaces/monitoring/metrics_gateway src/operations/hardware/mib_generator -q` | No output |
| 17 | Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| 18 | Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No output |
| 19 | Docstring style | `pydocstyle src/ wsgi.py web_portal` | No output |
| 20 | Docstring coverage | `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | Coverage 90 percent or above |
| 21 | Citations | `check-citations src tests` | Each citation resolves |
| 22 | STE, changed document | `ste-linter --config .ste-linter.toml --min-score 80 documentation/mib_generator.md` | Score 80 or above |
| 23 | STE, routed record | Command below | Each file scores 80 or above |
| 24 | Markdown links | `markdown-link-check documentation/mib_generator.md documentation/menu-api/interactive-safe.md documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` | No broken link |
| 25 | Test-quality preflight | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | All tests pass |
| 26 | Test-quality gate | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| 27 | Safe sweep | `python MistHelper.py --test` | Each safe operation completes. Mist checks skip without a token. |
| 28 | Full suite, once before the push | Two `pytest-chunks` commands below | One summary line for each shard |
| 29 | Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The CI shards combine to 80 percent or above |

The gates that do not apply are the dependency audit, the Ops portal gate, the Ops platform gate, and the diagram gate. The change edits no requirements file, no portal tree, and no diagram.

Row 8 runs these 13 test modules. The count is the `tests_planned` value in the status file.

```powershell
python -m pytest tests/unit/maps/interfaces/monitoring/metrics_gateway/test_collector.py tests/unit/maps/interfaces/monitoring/metrics_gateway/test_prometheus_and_cache.py tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_and_service.py tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_integration.py tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_mib_generator.py tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_properties.py tests/contract/test_mib_matches_catalog.py tests/contract/test_generated_mib_matches_agent.py tests/guardrails/test_src_domain_structure.py tests/guardrails/test_src_public_symbol_preservation.py tests/guardrails/test_nested_package_structure.py tests/guardrails/test_performance_hook_catalog.py tests/guardrails/test_changelog_fragment_policy.py -q
```

Row 12 runs once for each file below.

- `src/interfaces/monitoring/metrics_gateway/__init__.py`
- `src/interfaces/monitoring/metrics_gateway/prometheus.py`
- `src/interfaces/monitoring/metrics_gateway/service.py`
- `src/interfaces/monitoring/metrics_gateway/snmp.py`
- `src/interfaces/monitoring/metrics_gateway/web.py`
- `src/operations/hardware/mib_generator/__init__.py`
- `src/operations/hardware/mib_generator/assignment.py`
- `src/operations/hardware/mib_generator/mib.py`
- `src/operations/hardware/mib_generator/runner.py`
- `src/operations/hardware/mib_generator/schema.py`

Row 14 prints no output when no old path remains in active text.

```powershell
git grep -n -E "metrics_gateway[./](cache|catalog|collector|samples)" -- ":!specs/1924-failure-evidence" ":!specs/2159-openapi-mib-generator" ":!specs/2448-misthelper-performance-monitoring/research.md" ":!specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv" ":!CHANGELOG.md" ":!changelog.d" ":!specs/numbered/0/0/1/1/2/0/1/4"
```

Row 23 checks each Markdown file of the routed record.

```powershell
Get-ChildItem -LiteralPath specs\numbered\0\0\1\1\2\0\1\4\4009-metrics-gateway-core -Recurse -Filter *.md | ForEach-Object { ste-linter --config .ste-linter.toml --min-score 80 $_.FullName }
```

Row 28 runs two commands. Each command takes a long time on Windows, so start it after the targeted rows pass.

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Caution: a hook row that is unstaged leaves the hook guard red. Stage the four renamed files with `git mv` before row 9 runs.

## 5. Stage, commit, push, and open the pull request

Run these commands only after the coordinator assigns the serial slot and PR #4208 releases the symbol guard file.

1. Stage each path from the change map in `plan.md`. Use one path for each `git add` argument.

```powershell
git add src/interfaces/monitoring/metrics_gateway/core/__init__.py
```

2. Commit with the Conventional Commits subject, the closing line, and the co-author trailer.

```powershell
git commit -m "refactor(metrics-gateway): isolate core modules" -m "Closes #4009" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

3. Push the new branch.

```powershell
git push -u origin chore/4009-metrics-gateway-core
```

4. Write the pull request body to a file outside the repository. The body lists each gate from section 4 and its result. Then open the pull request.

```powershell
gh pr create --base main --head chore/4009-metrics-gateway-core --title "refactor(metrics-gateway): isolate core modules" --body-file ..\pr-body-4009.md
```

## 6. Watch the checks and merge

1. Watch the required checks of the pull request.

```powershell
gh pr checks --watch
```

2. Add the `auto-merge` label only after every required check passes. The orchestrator must authorize the merge first.

3. After the merge, check the menu drift in a worktree of the updated `main`.

```powershell
python -m scripts.menu_api_map --check
```

Caution: deleting a local branch removes its local name. Delete the local branch only after the squash merge appears on `main`. Keep the archive branch `archive/laptop-20261121/jmorrison-juniper-refactor/4009-metrics-gateway-core`.
