# Quickstart: Menu 97 SQLite Write Status

## Prerequisites

1. Open a worktree for branch `fix/4722-sqlite-partial-batch` from `origin/main`. Use a path outside the main checkout.
2. Create the environment in the worktree. Run these commands in order.

```text
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

3. Confirm that PR #4813 merged, or that the owner gave a handover, before you edit `data_exporter.py` or `test_data_exporter.py`.

## Reproduce the Current Defect

The first-batch and later-batch False paths already pass on remote main. Run these tests first.

```text
python -m pytest tests/unit/test_device_events_52w_exporter_extended.py -k "first_write_fails or later_write_fails" -q
```

The partial-batch defect has no test on main yet. After T009 adds TC-10, run it before the change. It must fail with the message that no RuntimeError was raised.

```text
python -m pytest tests/unit/test_device_events_52w_exporter_extended.py -k "real_writer" -q
```

The test sets up the real writer in a temporary folder. It rejects one row of the fourth page with a SQLite trigger on `OrgDeviceEvents_52w`. The trigger rejects the row whose identifier is `rejected-event`. The trigger is created after the first batch writes the table.

## Verify the Change

Run these commands after T006 through T014.

```text
python -m pytest tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py -q
python -m pytest tests/unit/export/test_data_exporter.py -q
python -m pytest tests/unit/test_device_events_52w_exporter_extended.py -q
python -m pytest tests/unit/test_device_events_52w_exporter.py -q
python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py -q
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

## Local Gates

Run each applicable gate. Each command exits 0 when the gate passes.

```text
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
python MistHelper.py --test
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
radon cc src/operations/exporting/export/device_events_52w_exporter.py src/operations/exporting/export/data_exporter.py src/foundation/support/refactors/sqlite_database_writer.py src/foundation/models/dataclasses/export_backend_options.py -j | complexity-gate --max 10
bandit -c pyproject.toml -r src -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
symbol-diff --base origin/main src/operations/exporting/export/device_events_52w_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/data_exporter.py
symbol-diff --base origin/main src/foundation/support/refactors/sqlite_database_writer.py
symbol-diff --base origin/main src/foundation/models/dataclasses/export_backend_options.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4722-partial-batch.md
```

The two `pytest-chunks` commands print one summary line for each shard. The unit shard took 1179.3 seconds in the measurement that `.github/copilot-instructions.md` records.

Do not run these gates for this change: `pip-audit -r requirements.txt` (no requirements change), the Ops portal commands, and the Ops platform command. The pull request body gives the reason for each skipped gate.

## Cleanup

1. Remove the worktree after the merge. Remove the branch after the merge.
2. Do not start a container for these tests. Every test uses `tmp_path` or `monkeypatch`.
3. Do not write to `data/` in the repository. The tests set their own folders.
