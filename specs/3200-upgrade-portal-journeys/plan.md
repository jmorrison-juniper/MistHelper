# Implementation Plan: Upgrade portal journey harness and multi-site parity

**Branch**: `test/3200-upgrade-portal-journeys` | **Date**: 2026-09-23 |
**Spec**: [spec.md](spec.md) | **Issue**: #3200

**Input**: The feature specification in
`specs/3200-upgrade-portal-journeys/spec.md` and the orchestrator research
note of 2026-09-23.

## Summary

The harness drives the shipped portal in a real Chromium browser from the
sign-in to the end of the upgrade. The harness simulates the Mist cloud at the
operator session object. One `SimulatedMistSession` sends each URI of
`mist_get`, `mist_post`, `mist_put`, and `mist_delete` to one
`SimulatedOrganization`. That object holds the fleet state and reads one
accelerated journey clock.

The journey server registers each operator with that session. The server keeps
the record stores inside its process through `build_e2e_overrides`. All other
seams keep their production values. The shipped readers, options builder,
capture collector, `RunDriver`, `AggregateUpgradeService`,
`org_upgrade_service`, and `upgrade_service` therefore run. An unknown URI
gets status 404, and the harness records it as a harness gap.

The plan reuses the journey work of the branch. The branch holds the recorder,
the runner, the markers, and 39 journeys. The plan moves that code into a
compliant package. It then puts each journey on the simulated cloud and
removes each `page.route` call. The research decisions are in
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.13. The shipped browser scripts run with no
change.

**Primary Dependencies**: Flask 3.1 and `mistapi` 0.64 in the portal.
Playwright 1.63, `pytest-playwright` 0.9, pytest 9.1.1, and `pytest-timeout`
2.4 in the harness. The plan adds no dependency.

**Storage**: The process-owned record stores of
`tests/support/upgrade_portal_e2e/records/`. The artifacts go to
`data/test-artifacts/upgrade-portal-journeys/<harness-run-identifier>/`. The
harness uses no ArangoDB, no Redis, and no production store.

**Testing**: pytest collects the journeys. The `journey` marker and the
`UPGRADE_PORTAL_JOURNEYS=1` gate select them. The self-tests of the harness
run in the default pytest command.

**Target Platform**: Windows 11 and Linux. The journey server listens on
`127.0.0.1` only.

**Project Type**: A test harness for a Flask web service. The harness is a
support package and one pytest entry package.

**Performance Goals**: A happy-path journey takes less than 3 minutes. A full
harness run at the default fleet takes less than 60 minutes. A large-fleet
journey takes less than 10 minutes. The page and API budgets are in PR-008.

**Constraints**: Loopback only. No API token, no credential variable, and no
container. No `page.route` and no `context.route`. The Five-Item Rule applies
to each new package, module, and class. The logs use ASCII only.

**Scale/Scope**: 73 journey cases. The catalog holds 14 happy paths, 34 fault
cases, 23 cross-cutting cases, and 2 large-fleet cases. The default fleet holds
2 organizations, 5 sites, 29 devices, and 84 clients. The large fleet holds
about 3,000 devices. The capability inventory holds 54 rows.

No item of the Technical Context stays open. Research R-01 to R-14 resolve
each design question.

## Constitution Check

*GATE: The check passes before Phase 0 research. The check passes again after
the Phase 1 design.*

| Principle | Result | How the plan meets it |
| - | - | - |
| I. Five-Item Rule | Pass | Each new package holds five children or fewer. The layout adds no child to a noncompliant parent. See [Package layout](#package-layout). |
| II. Class-Based Architecture | Pass | Named classes own each behavior. Examples are `SimulatedMistSession`, `JourneyClock`, `JourneyServer`, `JourneyCatalog`, and `ParityMatrix`. |
| III. Safety-First | Pass | The harness reads no operator input. The typed confirmations, the CSRF check, the owner check, the lock check, and the replay check stay in the shipped path. |
| IV. Full Deployment Pipeline | Pass | The implementation phase runs the pipeline. The orchestrator commits. This plan writes prose only. |
| V. Observability and Logging | Pass | Each request gets one ASCII log line with stable key and value pairs. The harness scans each text artifact for credential values. |
| VI. Inline Comments | Pass | Each new line of code gets an inline comment that tells why. The tasks repeat this rule for each module. |
| VII. Action Logging | Pass | Each action logs `info` before and `debug` after. Each module uses `%s` formats. |
| Python 3.13 and `mistapi` | Pass | The SDK functions run unchanged against the simulated session. No code sends a direct HTTP call to Mist. |
| Test containers | Pass | The harness starts no container (SR-016). |
| File paths and `data/` | Pass | Each path comes from `pathlib.Path`. Each artifact goes below `data/`. |
| Fix over suppress | Pass | The plan adds no suppression. A finding in the harness gets a fix. |

The post-design check gives the same result. The design adds no new
violation. [Complexity Tracking](#complexity-tracking) records the existing
debt that the feature touches.

## Project Structure

### Documentation (this feature)

```text
specs/3200-upgrade-portal-journeys/
├── spec.md              # The specify stage
├── plan.md              # This file
├── research.md          # Phase 0 decisions R-01 to R-14
├── data-model.md        # Phase 1 entities and state transitions
├── quickstart.md        # Phase 1 validation guide
├── contracts/           # Phase 1 interface contracts
│   ├── simulated-cloud.md
│   ├── journey-server.md
│   ├── harness-command.md
│   └── report-schema.md
├── parity-matrix.md     # The harness writes this file in phase 4
├── checklists/
└── tasks.md             # The tasks stage writes this file
```

### Package layout

The directory `tests/support/` holds 6 children on `origin/main`, so it is
noncompliant. The layout therefore adds no child to `tests/support/`. The
harness enters `tests/support/upgrade_portal_e2e/`, which FR-006 names. That
package holds 5 children. Two of its modules move into one new `isolation/`
subpackage, so the package keeps 5 children. Research R-02 gives the evidence
and the rejected options.

```text
tests/support/upgrade_portal_e2e/            # 5 children before and after
├── __init__.py                              # Edit: import the moved modules from isolation
├── isolation/                               # New, 3 children, moved code only
│   ├── __init__.py
│   ├── environment.py                       # git mv from ../environment.py
│   └── resources.py                         # git mv from ../resources.py
├── records/                                 # No change
├── traps/                                   # No change
└── harness/                                 # New, 5 children
    ├── __init__.py
    ├── cloud/                               # Phase 1: the simulated cloud
    │   ├── __init__.py
    │   ├── session.py                       # SimulatedMistSession, SimulatedResponse, UriRouter, WriteShapeCheck, CallLedger
    │   ├── fleets.py                        # FleetBuilder for the default fleet and the large fleet
    │   ├── state/                           # SimulatedOrganization, SimulatedDevice, UpgradeJob, FaultBook
    │   └── handlers/                        # Read handlers, event handlers, upgrade and cancel handlers
    ├── server/                              # Phase 1 and phase 2: the journey server
    │   ├── __init__.py
    │   ├── clock.py                         # JourneyClock and JourneyLauncher (the four time seats)
    │   ├── app.py                           # The child process: app, seams, operators, control
    │   ├── control.py                       # JourneyControl blueprint and RequestLogMiddleware
    │   └── process.py                       # JourneyServer: spawn, owner record, readiness, restart
    ├── journeys/                            # Phase 3: the journeys
    │   ├── __init__.py
    │   ├── catalog.py                       # JourneyCatalog: 73 cases, metadata, selection, smoke set
    │   ├── context.py                       # JourneyContext: browser guard, date sync, viewport, trace
    │   ├── evidence/                        # recorder.py (from evidence.py), checks.py, excerpts.py
    │   └── flows/                           # pages.py, happy.py, faults.py, frame.py
    └── run/                                 # Phase 4 and phase 5: one harness run
        ├── __init__.py
        ├── __main__.py                      # HarnessRunner: the command (from run_journeys.py)
        ├── report.py                        # HarnessReport (schema 1) and IndexPage
        ├── parity.py                        # CapabilityInventory, TestIdAudit, ParityMatrix
        └── performance.py                   # PerformanceReport, BudgetTable, RouteProfile (from perf_profile.py)

tests/integration/upgrade_portal/            # 2 children before, 3 after
└── journeys/                                # New pytest entry package, 5 children
    ├── __init__.py
    ├── conftest.py                          # From the branch: gate, markers, selection options, fixtures
    ├── test_journeys.py                     # One test for each catalog case
    ├── test_harness_contract.py             # Shipped code against the simulated cloud, no browser
    └── test_route_profile.py                # From test_performance_journeys.py
```

Each subpackage in the tree holds five children or fewer. Each new module holds
five top-level symbols or fewer. Each new class holds five methods or fewer.
The tasks stage names the modules of `state/`, `handlers/`, `evidence/`, and
`flows/`. The same limits apply there.

**Structure Decision**: The harness code lives in
`tests/support/upgrade_portal_e2e/harness/`. The pytest entry lives in
`tests/integration/upgrade_portal/journeys/`. Phase 3 removes
`tests/e2e/upgrade_portal/journeys/`, so the feature adds no child to
`tests/e2e/upgrade_portal/`. The narrow edit of
`tests/e2e/upgrade_portal/conftest.py` for `UPGRADE_PORTAL_E2E_READY_SECONDS`
stays.

### Where the branch code goes

| Branch file | New home | Change |
| - | - | - |
| `journeys/evidence.py` | `harness/journeys/evidence/recorder.py` | Move. Add the journey clock times, the log excerpts, the trace, and the checks. |
| `journeys/conftest.py` | `tests/integration/upgrade_portal/journeys/conftest.py` | Move. Keep the gate and the two markers. Add the selection options. |
| `journeys/run_journeys.py` | `harness/run/__main__.py` | Move. Add the run identifier, the report, and the parity matrix. |
| `journeys/perf_profile.py` | `harness/run/performance.py` | Move the profile code into `RouteProfile`. |
| `journeys/test_performance_journeys.py` | `tests/integration/upgrade_portal/journeys/test_route_profile.py` | Move. |
| `journeys/test_upj_*.py`, `journeys/test_*_journeys.py` | `harness/journeys/flows/` and `catalog.py` | Port each step to the simulated cloud. Remove each `page.route` call. |

The journeys file map in research R-10 lists each test function and its catalog
case.

## Build order

Each phase ends with a gate. The next phase starts only after that gate
passes.

### Phase 1: the simulated cloud and the session

1. Move `environment.py` and `resources.py` into `isolation/`. Keep each
   package-root name, so no importer changes.
2. Build `JourneyClock` as a subclass of `RehearsalClock`. It gives scaled wall
   time, an interruptible sleep, and a forward move.
3. Build `SimulatedMistSession` and the route table of
   [simulated-cloud.md](contracts/simulated-cloud.md).
4. Build the default fleet, the device timelines, the upgrade jobs, the fault
   book, and the call ledger.
5. Check each write body against the local OpenAPI 3.1 file.
6. Write `test_harness_contract.py`. It runs the shipped readers and the three
   shipped firmware services against the session, with no server.

**Gate**: The contract tests pass. The ledger shows one write for each planned
write. The gap list is empty for the scripted flows.

### Phase 2: the journey server

1. Build `JourneyServer` on the pattern of `capture_portal_server`. Use the
   owner record, the readiness budget, the server log, and a restart after a
   stop.
2. Build the child app. Use `build_e2e_overrides` for the stores only. Keep the
   cloud seams at their production values. Register each operator with a
   `SimulatedMistSession`.
3. Build `JourneyLauncher`. It fills the four time seats of spec 1992 with one
   `JourneyClock`.
4. Build `JourneyControl` behind the gate variable and a per-run token.
5. Build `RequestLogMiddleware` and the socket guard of the server process.
6. Build the browser guard and the date sync of `JourneyContext`.
7. Port `M-ASG` and `S-ASG` first.

**Gate**: `M-ASG` and `S-ASG` get to the end of the upgrade in less than 3
minutes. Each trap counter reads zero. The guard self-test passes.

### Phase 3: the journeys on the simulated cloud

1. Move the branch files to the homes in the table above.
2. Fill `JourneyCatalog` with the 73 cases and their capabilities.
3. Port each branch journey to `flows/`, and remove each `page.route` call.
4. Add the missing happy paths, fault cases, and cross-cutting cases.
5. Make a strict `xfail` from each catalog issue number.
6. Add the three seeded defects of user story 4.
7. Remove `tests/e2e/upgrade_portal/journeys/`.

**Gate**: The 14 happy paths get to the end, or they fail as a strict `xfail`
that names a known issue. A search finds no `page.route` and no
`context.route` in the harness. Each seeded defect fails one or more journeys.

### Phase 4: the parity matrix and the reports

1. Write `report.json` in schema 1. See
   [report-schema.md](contracts/report-schema.md).
2. Write the index page. Each step shows its screenshot, errors, log lines, and
   trace link.
3. Build the capability inventory C01 to C54 and the `data-testid` audit.
4. Make each status from the journey results. Fail the run for a row that is
   out of date.
5. Write `parity-matrix.md` into the run directory and into the feature
   directory.
6. Write the inspection record template for the screenshot review.

**Gate**: The matrix holds 54 of 54 rows. The audit finds zero unmapped
controls. Each gap names one issue.

### Phase 5: the performance and the scale

1. Build the large fleet and the large site.
2. Add `P-LARGE-M` and `P-LARGE-S`.
3. Collect the server time, the browser timing, and the cloud call count of
   each page and each API call.
4. Rank the 10 slowest pages and API calls for each fleet. Compare each value
   with its budget and with the earlier report.
5. Add the CI job. See [How CI runs the harness](#how-ci-runs-the-harness).
6. Do 5 consecutive full runs on the same code.

**Gate**: Each budget reads `pass`, or `breach` with an issue number. The 5
runs give the same result for each journey.

## How CI runs the harness

- **Marker**: `journey`. The `fresh_server` marker gives a journey its own
  journey server.
- **Gate**: `UPGRADE_PORTAL_JOURNEYS=1`. Without it, each `journey` item
  reports `skipped`. The default pytest job and the E2E smoke job therefore run
  no journey.
- **Command**: `python -m tests.support.upgrade_portal_e2e.harness.run --set smoke`.
  See [harness-command.md](contracts/harness-command.md) for each option.
- **CI job**: Phase 5 adds one job, `upgrade_portal_journeys`, to
  `.github/workflows/ci.yml`. A new workflow file would add a child to a
  noncompliant directory.
- **Pull request**: The job runs the smoke set, `M-ASG` and `S-ASG`. If the pull
  request changes no file below `src/upgrade_portal/`, `src/firmware/`, or the
  harness, the job ends with success and runs nothing.
- **Manual run**: A `workflow_dispatch` input selects `smoke`, `default`,
  `large`, or `all`.
- **Artifacts**: The job uploads the run directory with
  `actions/upload-artifact`.
- **Status**: The job is not a required check. A later issue can make it
  required after 5 stable runs (SC-015).

## Risks

| Rank | Risk | Effect | Mitigation |
| - | - | - | - |
| 1 | `JourneyLauncher` drifts from `wiring.start_upgrade_run`. | The journeys prove a wiring that production does not use. | A contract test compares the class of each dependency with `build_driver_deps`. A follow-up issue can add a clock parameter to the wiring. |
| 2 | The simulated cloud accepts a shape that the live cloud refuses. | The matrix shows false parity. | The write check uses the local OpenAPI 3.1 schemas. The answers follow `seam_shapes.py` and the event rules of spec 1992. The ledger lists each unknown URI. |
| 3 | The shipped code mixes the journey clock and the wall clock. | A page shows a wrong age, or a lock ends early. | Phase 2 makes a list of each time field on a page. The checks compare order, not exact ages. The journey control ends locks and sessions. |
| 4 | A strict `xfail` passes for a different cause. | A new defect hides behind a known issue. | Each gap case asserts the symptom that its issue names. The report shows that symptom. |
| 5 | The package moves conflict with the open fix branches. | Rebases fail, and fix work stops. | Each importer uses the package root, so no importer changes. The move is one small commit at the start of phase 1. |
| 6 | The journeys are not stable across runs. | SC-015 fails, and CI gives noise. | Each step waits for a page condition. Each fleet is fixed. A journey that changes shared state uses `fresh_server`. |
| 7 | The browser guard blocks the journey server or misses an address. | SR-017 fails, or no page opens. | Phase 2 adds a guard self-test for a name, an address literal, and the server. |
| 8 | The simulated cloud is slow at the large fleet. | The report shows a false budget breach. | The ledger records the handler time. The report shows that time next to the server time. |

## Complexity Tracking

The design adds no new violation. This table records the existing debt that
the feature touches.

| Existing debt | Touch | Remediation action |
| - | - | - |
| `tests/support/` holds 6 children. | None. The harness enters a compliant child. | A separate issue can group the upgrade portal support packages. |
| `tests/e2e/upgrade_portal/` holds 17 children. | One narrow edit of `conftest.py`. Phase 3 removes the `journeys/` child of the branch. | A separate issue can split the browser suite. |
| `tests/e2e/upgrade_portal/conftest.py` holds more than five symbols. | The `UPGRADE_PORTAL_E2E_READY_SECONDS` edit only. | The same issue as the row above. |
| `.github/workflows/` holds more than five files, and `ci.yml` holds many jobs. | One new job in `ci.yml`. | A separate issue can split `ci.yml` into reusable workflows. |
| The branch code in `tests/e2e/upgrade_portal/journeys/` holds 10 children and large modules. | Phase 3 moves and splits it. | No debt stays after phase 3. |
| The SpecKit feature directory holds more than five children. | The templates set that layout. | No action. Each feature directory has the same layout. |
