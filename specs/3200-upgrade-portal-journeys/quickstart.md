# Quickstart: Validate the upgrade portal journey harness

**Feature**: #3200 | **Plan**: [plan.md](plan.md)

This guide proves the harness from end to end. It holds commands and expected
results only. The options are in
[harness-command.md](contracts/harness-command.md). The artifacts are in
[report-schema.md](contracts/report-schema.md).

## Prerequisites

- Windows 11, macOS, or Linux, with Python 3.13 in `.venv`.
- The packages of `requirements.txt` and `requirements-dev.txt`.
- Chromium for Playwright.
- No API token, no `.env` credential, and no container. The harness needs
  none.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## Scenario 1: The default command skips the journeys with a reason

```powershell
.venv\Scripts\python.exe -m pytest tests\e2e\upgrade_portal\journeys -q -rxXs --timeout 300
```

**Expected result**: Each `journey` item reports `skipped`. The reason names
`UPGRADE_PORTAL_JOURNEYS`. The command starts no journey server, and it finishes
in less than 5 minutes.

## Scenario 2: The single-site and multi-site journeys complete

```powershell
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1 --keyword "test_start_reaches_a_completed_run or test_family_combination_reaches_a_final_state"
```

**Expected result**:

- One single-site journey reaches the completed run state.
- Each of the seven multi-site family combinations reaches completed child and aggregate states.
- Each server binds to `127.0.0.1` on a free port.
- `summary.json` reports eight passed journeys.
- `index.html`, `journey.json`, and step screenshots are present.
- The exit code is 0.

## Scenario 3: One case for a selection

```powershell
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --keyword "test_family_combination_reaches_a_final_state and ap and not switch and not gateway"
```

**Expected result**: The command runs only the matching AP family journey. Each
unmatched file reports zero selected tests, which the runner accepts.

## Scenario 4: The full journey set

```powershell
$env:UPGRADE_PORTAL_JOURNEYS = "1"
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

**Expected result**: The runner writes `summary.json` and `index.html` under
`test-artifacts/upgrade-portal-journeys/`. The run reports 37 passed and three
expected failures for issues #3222, #4539, and #4540. The full set is opt-in
and does not run in the default CI pytest selection.

## Troubleshooting

- If the server does not get ready, increase
  `UPGRADE_PORTAL_E2E_READY_SECONDS`. Then read the path of the server log in
  the failure message.
- If a step fails, open `index.html`. Then open the screenshot link and
  `journey.json` for the failed journey.
- If a strict `xfail` passes, the fix of its issue is on the branch. Remove the
  issue from the catalog case, and change the matrix row to `parity`.

## Local verification

The following checks ran on macOS with Python 3.13. The simulated cloud and all
portal servers used loopback. The checks used no Mist credential or production store.

```sh
env -u UPGRADE_PORTAL_JOURNEYS .venv/bin/python -m pytest -q -rxXs --timeout 300 tests/e2e/upgrade_portal/journeys
```

**Result**: 54 skipped. Each skip named the opt-in variable.

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

**Result**: 37 passed, 3 xfailed. The runner wrote journey records and
screenshots. The xfails link to issues #3222, #4539, and #4540.

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider tests/contract/upgrade_portal/test_journey_parity_matrix.py tests/contract/upgrade_portal/test_org_upgrade_routes.py::test_checked_switch_with_empty_version_stays_in_the_durable_plan
```

**Result**: 1 passed, 1 xfailed. The matrix contract checked all 54 capability
identifiers. The stored-plan case remains an expected failure for issue #3394.

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/e2e/upgrade_portal/journeys/test_performance_journeys.py
```

**Result**: 2 passed. The report ranks read-only page and API samples by p95.
See [performance-report.md](performance-report.md).

## CI journey job

The CI job waits for the shared E2E gate. It runs the full isolated journey
harness with one worker and a 30-minute job limit.

```sh
python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

The job installs Chromium and uploads the complete
`test-artifacts/upgrade-portal-journeys/` directory as
`upgrade-portal-journeys`. The upload fails when the directory has no files.
The harness uses loopback services and simulated cloud data. It needs no
Mist credential or production store.

The guards check the job settings, the evidence upload, failure reporting, and
the quality-gate inventory. They also test browser shard contracts and the
single-site completion and multi-site refusal journeys.

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/guardrails/test_quality_gate_close_scope.py tests/guardrails/test_upgrade_portal_journey_ci.py tests/guardrails/test_ci_gate_triggers.py::TestCancelledRunStops tests/guardrails/test_e2e_shard_partition.py tests/e2e/upgrade_portal/journeys/test_upj_single_site_journeys.py::TestSingleSiteJourneys::test_start_reaches_a_completed_run tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py::TestMultiSiteOptionsJourneys::test_default_form_refusal_is_in_view
```

Result: 35 passed in 5.33 seconds. Ruff and Black pass on the changed Python
test file.

Run the complete journey suite with this command.

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

Result: 37 passed and 3 expected failures.

Result: 37 passed and 3 xfailed.
