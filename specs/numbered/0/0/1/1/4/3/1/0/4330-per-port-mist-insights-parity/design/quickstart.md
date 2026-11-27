# Quickstart: Per-port Mist Insights parity in the WAN dashboard

This guide gives the exact steps to reproduce the gap and to verify the change. The steps use mocked responses only. They make no live Mist call and use no production credential.

## Preconditions

1. Open a new worktree for branch `feat/4330-per-port-mist-insights-parity` from `main`.
2. Create the environment with the bootstrap commands in `.github/copilot-instructions.md`, section "Language and environment".
3. Activate the environment with `.venv\Scripts\Activate.ps1`.
4. Do not set `MIST_APITOKEN` or `MIST_API_TOKEN` for these steps.
5. Do not start a container for these steps. The tests run on the host.

## Step 1: Confirm the Remote Baseline

Run each command. Each command reads `main` only. The blob SHA must match the value in `design/research.md`.

```text
gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/portals/wan_dashboard/services/__init__.py?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/portals/wan_dashboard/services/worker.py?ref=main" --jq .sha
gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/portals/wan_dashboard/routes.py?ref=main" --jq .sha
```

The expected values are `11fdc93e4740e0a8c083f4f5ed4106448fa42745`, `084a141c490f3b6bfa4faa8f568fdf3ea090f3c7`, and `d58229ce8f0c15998785f88b3cbf5a7009e15f58`.

## Step 2: Reproduce the Gap

The gap is that no code path writes the per-port keys. Run the route tests. The tests show that the routes return cached data only.

```text
python -m pytest tests/integration/web_portal/wan_dashboard/test_routes.py
```

Then read the three lines that show the gap in `design/research.md`:

- R-03 and R-04 show the cached routes.
- R-05 shows that the routes call no live per-port method.
- R-06 shows that the worker calls no live per-port method.

With an empty cache, the port view shows `unavailable`. No Mist call occurs.

## Step 3: Verify the SDK Contract

Run the contract tests. These tests pin the SDK method, the installed version, the request arguments, and the failure states.

```text
python -m pytest tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py
```

## Step 4: Verify the Helpers and the Budget

```text
python -m pytest tests/unit/wan_dashboard/test_port_insights.py
python -m pytest tests/unit/wan_dashboard/test_worker.py
python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py
python -m pytest tests/integration/web_portal/wan_dashboard/test_services.py
```

Run the admission test only after decision D-12 closes.

## Step 5: Verify the Browser Behavior

```text
python -m pytest tests/e2e/web_portal/test_wan_dashboard_cache_only.py
```

The browser tests use mocked routes. They check the states, the UTC time, the port totals, the overview copy, and the refresh queue.

## Step 6: Run the Local Gates

Run each gate for the changed files. The commands follow the local gates table in `.github/copilot-instructions.md`.

```text
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/interfaces/portals/wan_dashboard src/interfaces/wan_performance --config-file pyproject.toml
python -m pytest tests/unit/wan_dashboard tests/integration/web_portal/wan_dashboard
radon cc src/interfaces/portals/wan_dashboard -j
bandit -c pyproject.toml -r src/interfaces/portals/wan_dashboard -q
pylint src/ --fail-under=9.5
vulture src/interfaces/portals/wan_dashboard --min-confidence 70
symbol-diff --base origin/main src/interfaces/portals/wan_dashboard/services/__init__.py
ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md changelog.d/issue-4330-per-port-mist-insights-parity.md
```

The `radon` command pipes into `complexity-gate --max 10` in the CI gate. Run the pipe on your own machine.

## Step 7: Remove Temporary Output

This change creates no container, no volume, and no network. The tests write output to `tmp_path`. If a test writes output into `test-artifacts/`, remove that folder after the run.

## Expected Results

- Each test command ends with a passing summary line.
- The local gates end with zero findings.
- The remote check IDs in `design/research.md` match the live `main` blob SHAs in Step 1.
