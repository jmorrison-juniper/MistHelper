# Quickstart: R0902 and R0903 class design

Run each command from the repository root in Windows PowerShell. Activate the environment first with `.venv\Scripts\Activate.ps1`. Windows keeps `.venv\Scripts\python.exe` (RC-40).

Repository path used below: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

## 1. Confirm the baseline commit

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" rev-parse HEAD
```

Expected: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the `main` commit at authoring time. If the value differs, repeat sections 2 and 4 and update the register in `design\research.md`.

## 2. Reproduce the 25 findings before the change

```powershell
.venv\Scripts\python.exe -m pylint --disable=all --enable=R0902,R0903 --reports=n --score=n --output-format=parseable MistHelper.py src\operations\exporting\juniper_rma\model\service_request.py src\operations\exporting\juniper_rma\settings.py src\operations\exporting\juniper_rma\model\asset.py src\operations\exporting\juniper_rma\api\gateway.py src\operations\exporting\juniper_rma\model\export_rows.py src\operations\exporting\juniper_rma\workflows\correlation.py web_portal\services\operation.py tests\unit\juniper_rma\fixtures\fake_gateway.py tests\unit\juniper_rma\workflows\test_correlation.py tests\unit\juniper_rma\workflows\test_lookups.py
```

Expected: 25 messages, with 9 R0902 and 16 R0903. The output has no message for `fake_gateway.py`.

## 3. Run the targeted tests

Each command must pass after its implementation task. Before the implementation, the new cases fail.

```powershell
python -m pytest tests/unit/juniper_rma/api/test_settings.py
python -m pytest tests/unit/juniper_rma/api/test_gateway.py
python -m pytest tests/unit/juniper_rma/model/test_export_rows.py
python -m pytest tests/unit/juniper_rma/workflows/test_correlation.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

## 4. Verify the register after the change (TS-16)

Repeat the command in section 2.

Expected: 19 messages, with 9 R0902 and 10 R0903. Each message matches one row of the register in `design\research.md`, section 3.1, by file, class, code, and count.

Confirm that no pylint pragma is added to the diff:

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff origin/main -- src tests web_portal
```

Expected: no added line contains `pylint: disable`. Search the printed diff for that text.

## 5. Local gates

Run each command from the Local gates table of `.github\copilot-instructions.md` (RC-33). Run the commands in this order.

```powershell
python -m py_compile src\operations\exporting\juniper_rma\settings.py
python -m py_compile src\operations\exporting\juniper_rma\api\gateway.py
python -m py_compile src\operations\exporting\juniper_rma\model\export_rows.py
python -m py_compile src\operations\exporting\juniper_rma\workflows\correlation.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src/operations/exporting/juniper_rma -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/operations/exporting/juniper_rma -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src\operations\exporting\juniper_rma\settings.py
symbol-diff --base origin/main src\operations\exporting\juniper_rma\api\gateway.py
symbol-diff --base origin/main src\operations\exporting\juniper_rma\model\export_rows.py
symbol-diff --base origin/main src\operations\exporting\juniper_rma\workflows\correlation.py
```

Expected: each command exits 0. `symbol-diff` prints `no module-level name changed` for each file.

Run the two full test shards from the Full tests row of the table:

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Run the test quality ratchet after the local commit. First fetch the base branch:

```powershell
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected: the last line reports `gate: 0 new findings vs baseline`.

Gates that do not apply, with the reason to state in the pull request body:

- Dependency audit: no dependency changes.
- Menu reference: no menu row, handler, or registry entry changes.
- Safe sweep (`python MistHelper.py --test`): no menu wiring changes.
- STE: no file in the STE gate list changes.
- Ops portal and ops platform: no file in those projects changes.

## 6. Scope check

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only origin/main
```

Expected: nine lines. Four are source files, four are test modules, and one is the changelog fragment `changelog.d/issue-4134-r0902-r0903-class-design.md`.
