# Research: Upgrade portal journey harness

**Feature**: #3200 | **Date**: 2026-09-23 | **Plan**: [plan.md](plan.md)

Each decision below resolves one design question of the plan. Each decision
names its evidence. The orchestrator research note of 2026-09-23 gives the
starting decision R-01.

## R-01: Simulate the cloud at the operator session object

**Decision**: One `SimulatedMistSession` answers each call of `mist_get`,
`mist_post`, `mist_put`, and `mist_delete`. It sends each URI to one handler
of one `SimulatedOrganization`.

**Rationale**:

- The browser suite registers each operator as
  `identity.OperatorSession(owner, StandInCloudSession(), mode)` in
  `tests/e2e/upgrade_portal/conftest.py:1467-1481`. Each route reads the cloud
  session of the operator from that registry.
- Each `mistapi.api.v1` function builds a URI and calls one of the four
  session methods. `mistapi.get_all` follows `response.next` through
  `mist_get`.
- The shipped code reads `data`, `status_code`, `next`, `headers`, `raw_data`,
  `url`, and `proxy_error` of each answer.
- The destructive-write guard reads `session._MAX_429_RETRIES == 0` and
  `session._session.adapters == {}`. The organization picker reads
  `session.privileges`.
- The SDK functions run with no change. A wrong query key, a wrong device type,
  or a paging defect therefore shows in a journey.

**Alternatives considered**:

- Replace the SDK functions, as `tests/support/rehearsal/cloud.py` does. This
  option skips the URI and the query of each SDK function.
- Serve a loopback copy of the Mist API over HTTP. This option needs a real
  `APISession`, a token, and a host change. SR-003 forbids a token.
- Keep the stand-in services of the browser suite. FR-004 forbids a stand-in
  service.

## R-02: Put the harness in a compliant package

**Decision**: Put the harness code in
`tests/support/upgrade_portal_e2e/harness/`. Move `environment.py` and
`resources.py` into `tests/support/upgrade_portal_e2e/isolation/`. Put the
pytest entry in `tests/integration/upgrade_portal/journeys/`.

**Rationale**:

- On `origin/main`, `tests/support/` holds 6 children. They are
  `__init__.py`, `git_environment.py`, `lock_store_double.py`, `rehearsal/`,
  `thread_scoped_sleep.py`, and `upgrade_portal_e2e/`.
- The plan of spec 2447 counts `__init__.py` as a child. The constitution
  forbids a new direct child of a noncompliant parent.
- `tests/support/upgrade_portal_e2e/` holds 5 children. The move of two
  modules into `isolation/` makes room for `harness/`, and the count stays 5.
- Three modules import the package, and each one imports from the package
  root. They are `tests/e2e/upgrade_portal/conftest.py:60`,
  `tests/contract/upgrade_portal/test_upgrade_routes/test_isolation.py:17`,
  and `tests/unit/upgrade_portal/test_runs/test_isolation.py:20`. The move
  therefore changes no importer.
- `tests/integration/upgrade_portal/` holds 2 children, so a third child is
  compliant. Each directory below `tests/e2e/` is noncompliant.
- The root `harness/` holds `__init__.py` and four subpackages. The fifth
  subpackage of the orchestrator example, `perf`, goes into
  `run/performance.py`. The recorder, the request log, and the ledger make the
  measurements.

**Alternatives considered**:

- `tests/support/upgrade_portal_journeys/` adds a seventh child to
  `tests/support/`. Its five subpackages and `__init__.py` also make 6
  children.
- `tests/e2e/upgrade_portal/journeys/` adds a child to a parent with 17
  children.
- A package with the same name as an existing browser test module moves
  existing tests. FR-082 keeps those tests, and the move conflicts with the
  fix branches.

## R-03: Make the journey clock from the rehearsal clock

**Decision**: `JourneyClock` is a subclass of `RehearsalClock`
(`tests/support/rehearsal/clock.py:28`). The default multiple is 60.

- `now()` gives the start time, plus the scaled wall time, plus the sum of
  each forward move.
- `sleep(seconds)` waits `seconds / multiple` of wall time on a
  `threading.Condition`. A forward move wakes each sleeper.
- `advance(seconds)` adds a forward move. The clock never moves backwards.
- `sleeps()` keeps the record of each sleep for the report.

**Rationale**:

- `RehearsalClock.sleep` adds the interval at once and does not block
  (`clock.py:63-77`). In a live server, the driver would then finish before
  the browser sees a state.
- With a multiple of 60, a settle window of 60 seconds takes 1 wall second.
  The deadline of 1800 seconds takes 30 wall seconds.
- The site locks and the operator sessions keep the wall clock (FR-040).

**Alternatives considered**:

- Use `RehearsalClock` with no change. The sleep of one thread then moves the
  time of each thread.
- Replace `time.time` in the server process. The locks and the sessions then
  lose the wall clock.

## R-04: Fill the four time seats in a journey launcher

**Decision**: `JourneyLauncher` is the value of the `RUN_LAUNCHER` seam. It
builds the same objects as `wiring.start_upgrade_run`
(`src/upgrade_portal/app/wiring.py:1009-1027`). It puts one `JourneyClock`
into the four seats that `tests/support/rehearsal/harness.py:349-364` fills.

| Seat | Shipped object | Value |
| - | - | - |
| 1 | `gate.SettleGate(clock=...)` | `journey_clock.now` |
| 2 | `phase_gate.CloudReconnectReader(session, org_id, EventCatalogue(), clock)` | `journey_clock.now` |
| 3 | `phase_gate.PhaseGateDeps(..., sleep)` | `journey_clock.sleep` |
| 4 | `driver.RunDriverDeps(..., clock)` | `journey_clock` |

The launcher keeps the shipped `CaptureBridge`, `CloudUpgradeSubmitter`,
`CloudStatisticsReader`, heartbeat, and post-check mode. It points
`driver.data_root` at the run directory, as `harness.py:333-334` does.

**Rationale**: The production launcher uses the wall clock. A happy path would
then take more than 30 minutes.

**Alternatives considered**:

- Add a clock parameter to `wiring.build_driver_deps`. This option changes a
  shipped file. A follow-up issue can propose it.

**Drift guard**: A contract test builds the dependencies with
`wiring.build_driver_deps` and with `JourneyLauncher`. The test compares the
class of each dependency.

## R-05: Check each write body against the local OpenAPI file

**Decision**: Load `documentation/mist-api-openapi31json.json` one time at the
start of the server. The file is OpenAPI 3.1.0, API version 2607.1.1, and
loads in 0.14 seconds.

| Call | Request schema | Answer schema |
| - | - | - |
| `upgradeOrgDevices` | `upgrade_org_devices` | `response_upgrade_org_devices` |
| `upgradeSiteDevices` | `upgrade_site_devices` | `response_upgrade_id` |
| `upgradeDevice` | `device_upgrade` | `response_device_upgrade` |
| `upgradeOrgSsrs` | `ssr_upgrade_multi` (requires `device_ids`) | `response_ssr_upgrade` |

A small validator reads `type`, `enum`, `required`, `properties`, `items`,
`minimum`, and `maximum`. A body that breaks the schema gets status 400, and
the answer names the key. A key that the schema does not name goes into the
ledger as a warning, because the schema allows it.

**Rationale**: FR-015 names the documented request shape. The repository holds
no `jsonschema` package, and FR-080 forbids a new dependency.

**Alternatives considered**: Hand-written key lists drift from the documented
shape.

## R-06: Answer an unknown URI with status 404

**Decision**: The router answers an unknown URI with status 404. The ledger
records a harness gap with the method, the path, the query keys, and the step.
The check at the end of each step fails the step and names the call.

**Rationale**: SR-004 needs a failed journey with the name of the call. A
status 404 keeps the shipped error path live. The report lists each gap, so a
gap is never silent. The traps of `tests/support/upgrade_portal_e2e/traps/`
stay active.

**Alternatives considered**:

- An exception inside `mist_get` stops the request thread and hides the page.
- An empty answer with status 200 is silent.

## R-07: Guard the browser without request routes

**Decision**: Start Chromium with a proxy to a closed loopback port. Add a
bypass rule for `127.0.0.1`. Map each other host name to `NOTFOUND` with a
host resolver rule. The recorder records each refusal from the
`requestfailed` event.

**Rationale**:

- FR-007 forbids `page.route` and `context.route`.
- Playwright turns off the HTTP cache when a route is active. The performance
  data therefore stays true only with no route.
- Playwright sends loopback traffic through the proxy unless a bypass rule
  names the host. Phase 2 proves the rule with a self-test. The self-test
  opens a host name, an address literal, and the journey server.

**Alternatives considered**: The socket guard of the server process alone does
not satisfy SR-017.

## R-08: Make the browser date follow the journey clock

**Decision**: Before the first page of each context, call
`page.clock.install` with the journey time. Call `page.clock.set_system_time`
at the start of each step, in each loop of a wait, before each screenshot, and
after each clock move.

**Rationale**: `set_system_time` changes the date and fires no timer. The
browser timers therefore keep the wall pace (FR-039). A loop of 0.5 wall
seconds keeps the date error below 30 journey seconds.

**Alternatives considered**: An init script can scale `Date` with no gap. It
is the fallback if the self-test shows a larger error.

## R-09: Log each request on the server

**Decision**: `RequestLogMiddleware` wraps the shipped WSGI app in the journey
server process. It writes one ASCII line for each request. The line holds the
run, the journey, the step, the method, the path, the status, the server time,
and the cloud call count. The runner sends the journey and the step to the
journey control before each step. One server runs one journey at a time.

A context variable holds the request number. The session ledger reads it, so
each cloud call counts for its request. A call from a driver thread counts as
`background`.

**Rationale**: FR-009 and PR-001 need the journey and the step on the server.
No header goes into a browser request, so FR-007 holds.

**Alternatives considered**:

- Extra headers from the browser context change each browser request.
- The access log of the WSGI server holds no journey and no step.

## R-10: Make one catalog the source of each journey

**Decision**: `JourneyCatalog` holds the 73 cases. Each case holds the
identifier, the story, the mode, the family combination, the fault, and the
fleet. It also holds the server mode, the capabilities, the expected errors,
the step limit, and the issue. `test_journeys.py` holds one test with one
parameter for each case. The `conftest.py` makes the marks from the catalog.

The branch markers `journey` and `fresh_server` stay. The gate
`UPGRADE_PORTAL_JOURNEYS=1` stays. A strict `xfail` comes from the issue of
the case.

**Rationale**: A module holds five top-level symbols or fewer. One test
function for each journey breaks that limit. One catalog feeds the tests, the
selection, and the parity matrix.

| Branch test | Catalog case |
| - | - |
| `test_upj_multisite_journeys.py::test_family_combination_reaches_a_final_state` | `M-A` to `M-ASG` |
| The options checks of `test_upj_multisite_journeys.py` (#3206, #3207, #3223) | The options step of `M-*` |
| The confirm checks of `test_upj_multisite_journeys.py` (#3221, #3222) | The confirm step of `M-ASG` |
| `test_running_operation_*` (#3220), `test_completed_operation_offers_no_cancel` (#3225) | `M-ASG`, `F-LOCK-M`, `F-CANCEL-M` |
| `test_second_start_on_busy_sites_*`, `test_busy_site_refusal_*` (#3224) | `F-LOCK-M` |
| `test_multisite_journeys.py`, each test with `page.route` | `X-MODE-M`, `X-NAV-M`, `F-DOUBLE-M`, `F-REPLAY-M`, `F-CANCEL-M`, `F-OWNER-M` |
| `test_upj_single_site_journeys.py` | `S-ASG`, `X-HISTORY-S`, `X-COMPARE-S`, the device fault cases |
| `test_single_site_journeys.py::test_single_site_operator_journeys` | `S-ASG`, `F-STOP-S` |
| `test_performance_journeys.py` | `test_route_profile.py` |

**Alternatives considered**: One test function for each journey repeats the
metadata and breaks the module limit.

## R-11: Make the parity matrix from the spec inventory

**Decision**: The inventory C01 to C54 of the spec is the authority (FR-070).
Phase 4 maps each row P-01 to P-40 of the branch matrix to one or more C rows.
Each issue number of the branch matrix becomes a hand-kept gap issue (FR-074).
`TestIdAudit` reads each `data-testid` value of the shipped templates of each
mode. It maps each value to one capability. A value that the template builds
from a variable maps by its fixed prefix.

**Rationale**: FR-074 needs a status from the journey results. The branch
matrix uses different words and different rows.

**Alternatives considered**: A hand-written matrix cannot show a row that is
out of date (FR-075).

## R-12: Measure without a wait

**Decision**:

| Measure | Source |
| - | - |
| The server time (PR-001) | The request log line of R-09 |
| The page timing (PR-002) | The Navigation Timing entry that the recorder reads |
| The API call timing (PR-003) | `request.timing` of each `requestfinished` event |
| The cloud call count (PR-004) | The ledger count for each request |
| The status polls (PR-005) | The request log lines of the two status paths |

The report gives the 50th percentile, the 95th percentile, the maximum, and
the sample count. It uses the nearest-rank method. `BudgetTable` holds the
budgets of PR-008 and each named budget of PR-009 with its cause. The report
compares each value with the newest earlier report of the same fleet.
`RouteProfile`, the `cProfile` code of the branch, runs only on request for a
breach.

**Alternatives considered**: A HAR file is large and can hold credential
values. `pytest-benchmark` is a new dependency.

## R-13: Run the harness in CI as one new job

**Decision**: Phase 5 adds the job `upgrade_portal_journeys` to
`.github/workflows/ci.yml`. The job runs the smoke set on a pull request that
changes the portal, the firmware services, or the harness. A
`workflow_dispatch` input selects a larger set. The job is not a required
check.

**Rationale**: The directory `.github/workflows/` holds more than five files,
so a new workflow file adds a child to a noncompliant parent. The E2E smoke job
has a 15-minute budget, and its store services are of no use to the harness.

**Alternatives considered**: A nightly schedule on `ci.yml` runs each gate. A
later issue can add a schedule after 5 stable runs (SC-015).

## R-14: Run the workers as child processes

**Decision**: The runner starts one child pytest process for each worker. Each
worker has its own journey server, run identifier, port, artifact directory,
and fleet. The default is 3 workers.

**Rationale**: The repository holds no `pytest-xdist`. A serial run of the
default catalog takes about 100 minutes, by the time limit of each class of
case. With 3 workers, the run stays below the budget of 60 minutes.

**Alternatives considered**: One shared server for all journeys lets the state
of one journey change the result of the next journey.

## Known product defects

The plan fixes no product defect. Separate fix branches own #3203 to #3217
and #3220 to #3225. A journey that meets one of these defects is a strict
`xfail` that names the issue. The journey server sets
`ORG_UPGRADE_WRITES_ENABLED` to `True` in its own process only (FR-010). That
setting does not repair #3203.

The orchestrator note reports a wiring import of `src.upgrade_portal.mistapi`,
which does not exist. A search of `src/upgrade_portal/` finds no such import
text. If a journey meets that failure, the journey records the call and the
issue.
