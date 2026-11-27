# Gates Checklist: Refactor: isolate audit renderer modules

Each row names one local gate from the Local gates table of `.github/copilot-instructions.md` (row RC-54, lines 50 to 76). The status column is `applies` when the gate covers a changed file. The status column is `not applicable` when no changed file falls under the gate. The task T-LOCAL-GATES runs each row with status `applies`.

| Gate | Status | Command | Expected result |
|------|--------|---------|-----------------|
| Compile | applies | `python -m py_compile MistHelper.py`, then `python -m py_compile` for each changed Python file | No output |
| Lint | applies | `python -m ruff check .` | `All checks passed` |
| Format | applies | `python -m black --check .` | No file needs a change |
| Types | applies | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` (paths from row RC-41, line 93) | `Success` |
| Tests | applies | `python -m pytest tests/test_audit_renderer.py tests/unit/marvis/mist/access/audit` | All tests pass |
| Full tests | applies | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`, then `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard |
| Coverage | applies (CI confirms it) | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The shards combine at 80 percent or above |
| Test quality | applies | Preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. After the local commit: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | applies | `radon cc src/mist/access/audit -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | applies | `bandit -c pyproject.toml -r src/mist/access/audit -q` | No finding at any severity |
| Dependency audit | not applicable | None | No dependency changes |
| Code quality | applies | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | applies | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` (paths from row RC-41, line 101) | No finding |
| Docstrings | applies | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` (paths from row RC-41, lines 104 and 107) | No violation, and coverage at 90 percent or above |
| Menu reference | applies | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` (row RC-43) | No changed file after the run |
| Symbols | applies | `symbol-diff --base origin/main src/mist/access/audit/rendering/renderer.py` | `no module-level name changed`, exit code 0 |
| STE | applies to each new Markdown file | `ste-linter --config .ste-linter.toml --min-score 80` with each new Markdown file | Each file scores 80 or above |
| Markdown links | applies to each new Markdown file | `markdown-link-check` with each new Markdown file | No broken link |
| Ops portal | not applicable | None | No file under `ops-portal/` changes |
| Ops platform | not applicable | None | No file under `mist-ops-platform/` changes |
| Safe sweep | applies | `python MistHelper.py --test` | Each safe operation completes. The Mist checks skip without a token. |
| Guardrails | applies | `python -m pytest tests/guardrails` | All tests pass |
| Import smoke | applies | `python -c "import src.mist.access.audit.rendering.renderer, src.mist.access.audit.rendering.helpers._renderer_delta, src.mist.access.audit.rendering.helpers._renderer_format, src.mist.access.audit.rendering.helpers._renderer_time, src.mist.access.audit.rendering.helpers._renderer_html, src.mist.access.audit.rendering.helpers._renderer_mermaid"`, then `python -c "__import__('src.mist.access.audit.rendering.clusters._renderer_html')"` | The first command exits 0. The second command raises `ModuleNotFoundError`. |
| Resolver | not applicable | None | No audit module string exists in `source_dependency_resolver.py` (row RC-45) |
| Old paths | applies | `git grep -n "access.audit._renderer_\|access.audit.renderer\|rendering._renderer_\|rendering.clusters\|audit/_renderer_\|rendering/_renderer_\|rendering/clusters" -- ":!specs"` | Hits appear only in the allowlist of `design/contracts/structure-guard.md` |

## Checks that are not commands

| ID | Check | Covers |
|----|-------|--------|
| C-01 | `git -C <worktree> diff --name-only origin/main` lists only the paths in `plan.md`, section "File change map". | FR-015, FR-016 |
| C-02 | The old-path command finds only the allowlisted files. | FR-006, SC-002 |
| C-03 | The import smoke command passes, and the retired import fails. | FR-004, FR-006, FR-007 |
| C-04 | The symbol command prints `no module-level name changed`. | FR-012 |
| C-05 | A reviewer reads each changed line. Each executable line has an inline comment. | FR-019 |
| C-06 | The record folder holds five children at its root, and `design/` holds five children. | FR-021 |
| C-07 | The STE and Markdown link gates pass for each new Markdown file. | FR-014, FR-021 |
| C-08 | The coordinator confirms the serial slot in writing before the pull request opens. | FR-020 |
| C-09 | `plan.md` and `design/contracts/python-imports.md` state the `__module__` changes and the unchanged logger set. | FR-013 |

Caution: The old-path command reports hits in the historical records under `specs/`. The command excludes `specs/` for that reason. Review each hit before the commit.
