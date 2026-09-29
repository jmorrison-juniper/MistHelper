# Quickstart: Validate the upgrade portal journey harness

**Feature**: #3200 | **Plan**: [plan.md](plan.md)

This guide proves the harness from end to end. It holds commands and expected
results only. The options are in
[harness-command.md](contracts/harness-command.md). The artifacts are in
[report-schema.md](contracts/report-schema.md).

## Prerequisites

- Windows 11 or Linux, with Python 3.13 in `.venv`.
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

## Scenario 2: The smoke subset gets to the end of the upgrade

```powershell
$env:UPGRADE_PORTAL_E2E_PORTS="9664,9665,9666,9667,9668,9669"
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1 --keyword "test_selection_reaches_the_capture_page or (test_family_combination_reaches_a_final_state and ap and not switch and not gateway)"
```

**Expected result**:

- One single-site journey reaches the capture page.
- One multi-site AP journey reaches the completed operation state.
- Each server binds to `127.0.0.1` on one port from 9664 through 9669.
- `summary.json` reports two passed journeys.
- The exit code is 0.

## Scenario 3: One case for a selection

```powershell
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --keyword "test_family_combination_reaches_a_final_state and ap and not switch and not gateway"
```

**Expected result**: The command runs only the matching AP family journey. Each
unmatched file reports zero selected tests, which the runner accepts.

## Scenario 4: The full journey set

```powershell
.venv\Scripts\python.exe -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 3
```

**Expected result**: The runner writes `summary.json` and `index.html` under
`test-artifacts/upgrade-portal-journeys/`. The full set is opt-in and does not
run in the default CI pytest selection.

## Troubleshooting

- If the server does not get ready, increase
  `UPGRADE_PORTAL_E2E_READY_SECONDS`. Then read the server log under
  `data/test-artifacts/upgrade-portal/`.
- If a step fails, open `index.html`. Then open the screenshot link and
  `journey.json` for the failed journey.
- If a strict `xfail` passes, the fix of its issue is on the branch. Remove the
  issue from the catalog case, and change the matrix row to `parity`.
