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

## Scenario 1: The self-tests run in the default command

```powershell
.venv\Scripts\python.exe -m pytest tests/integration/upgrade_portal/journeys/test_harness_contract.py -q
```

**Expected result**: Each test passes with no browser and no server. The
shipped readers and the three shipped firmware services run against
`SimulatedMistSession`. The gap list is empty.

## Scenario 2: The journeys skip by default

```powershell
.venv\Scripts\python.exe -m pytest tests/integration/upgrade_portal/journeys -q
```

**Expected result**: Each `journey` item reports `skipped`. The reason names
`UPGRADE_PORTAL_JOURNEYS`.

## Scenario 3: The smoke set gets to the end of the upgrade

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --set smoke
```

**Expected result**:

- `M-ASG` shows the operation status `completed`, and each child shows a
  terminal status.
- `S-ASG` shows the run status `complete`, the verified post-check badge, and
  the new version of each device in the comparison.
- Each case takes less than 3 wall-clock minutes.
- `report.json` shows a write count of 1 for each write key and 0 for each
  trap.
- The exit code is 0.

## Scenario 4: One case for each selection

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --story US1
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --mode single --families AG
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --journey F-UNCERTAIN-M --journey F-UNCERTAIN-S
```

**Expected result**: Each command runs only the matching cases. In the third
command, the uncertain child shows an unknown status. The ledger shows one
write for that child.

## Scenario 5: The browser guard and the date sync

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --journey X-NAV-S
```

**Expected result**: The guard self-test step refuses a host name and an
address literal, and it opens the journey server. The step records each
refusal as a failed request. The age on the progress page agrees with the
journey clock.

## Scenario 6: A seeded defect fails the safety cases

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --story US4 --seed-defect second-child-write
```

**Expected result**: One or more cases fail. The failure names the write key
with a count of 2. Repeat the command with `gateway-on-ap-route` and with
`dropped-option` (SC-013).

## Scenario 7: The full default run, the matrix, and the index page

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --set default --workers 3
```

**Expected result**:

- The run takes less than 60 minutes (SC-010).
- `parity-matrix.md` holds 54 rows, the parity percentage, and one issue for
  each gap. The audit finds zero unmapped controls.
- Open `index.html`. Find a failed step, its screenshot, and its server log
  lines in less than 2 minutes (SC-014).
- `inspection.json` holds one entry for each screenshot.

## Scenario 8: The large fleet and the performance report

```powershell
.venv\Scripts\python.exe -m tests.support.upgrade_portal_e2e.harness.run --set large
```

**Expected result**: `P-LARGE-M` and `P-LARGE-S` each get to the end of the
upgrade in less than 10 minutes. `report.json` ranks the 10 slowest pages and
the 10 slowest API calls for each fleet. Each budget shows `pass`, or
`breach` with an issue number. Each value shows its delta from the earlier
report.

## Scenario 9: CI runs the smoke set

In the Actions tab, start the `Quality Gates` workflow with the
`journey_set` input set to `smoke`.

**Expected result**: The `upgrade_portal_journeys` job passes and uploads the
run directory as an artifact.

## Troubleshooting

- If the server does not get ready, increase
  `UPGRADE_PORTAL_E2E_READY_SECONDS`. Then read `servers/<worker>/server.log`.
- If a step fails with a harness gap, find the call in `report.json` under
  `gaps`. Add the route to the simulated cloud. Do not change the shipped code.
- If a strict `xfail` passes, the fix of its issue is on the branch. Remove the
  issue from the catalog case, and change the matrix row to `parity`.
