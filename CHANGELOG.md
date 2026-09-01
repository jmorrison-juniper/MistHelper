# Changelog

All notable changes to MistHelper are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version format: `YY.MM.DD.HH.MM` (UTC timestamp).

## [Unreleased]

### Add the release train and the schedule of a session smart router

- **Added**: The options page offers the release train of a session smart
  router. The control names the three words that the router schema holds, which
  are alpha, beta, and stable. Only the router schema reads a channel, so the
  page hides the control unless the run upgrades a router. Issue #2157.
- **Added**: The options page offers the moment that the firmware download
  begins. Each cloud schema of the three holds the field, so the control shows
  for every device type. Before this change the portal held the rule and
  offered no control at all.
- **Added**: The plan warns when a run upgrades two routers or more under a
  single wave. Two routers of one site may share the wide area link, and one
  wave reboots the pair at once. The portal names the risk and keeps the order
  that the operator chose.
- **Added**: The confirmation page reports the release train, the download
  moment, and the reboot moment before the firmware moves.
- **Changed**: The note of the separate window for a reboot now states the rule
  of a router. That schema holds no reboot flag, so a no on the reboot control
  sends the value that disables the reboot of the router.

### Expose the advanced firmware upgrade controls of the cloud schema

- **Added**: The portal now offers every remaining upgrade field of the cloud
  schema. The new controls are the phase list of a staged
  upgrade and the failure limit of each phase. They are the failure
  percentage of the whole run and a separate window for the reboot of a
  switch and a gateway. They are the serial strategy and the radio strategy
  with its five settings. They are the three settings for a download between
  access points. They are the force flag and the vendor stable build. Before
  this change an operator who needed one of these fields had to leave the
  portal and call the cloud by hand. Issue #2156.
- **Added**: The page hides a control that the selection does not read. The
  radio settings reach an access point only. The settings for a download
  between access points reach an access point only. The separate window for
  a reboot reaches a switch and a gateway only. The phase list reaches the
  staged strategy only.
- **Added**: The confirmation page names each advanced control that the run
  submits, and it names no control that keeps the cloud default.
- **Added**: The plan warns when the radio strategy misses the switches and
  the gateways of a mixed run. It also warns that the stable build ignores
  every version that the device table shows.
- **Fixed**: The save call of the options dropped the schedule and every
  advanced choice when no site inventory answered. That path stored three
  fields by hand instead of the whole option record. It now maps the body
  through the one module that owns every rule. Both paths store the same
  record, and both refuse the same bad value.
- **Fixed**: A refusal of the separate reboot window named the start time.
  The refusal now names the reboot control, so the operator opens the control
  that holds the fault.

### Show the saved plan warning list on the confirm page

- **Fixed**: The confirm page shows the same list of warnings that the
  options page saved, for example the access-point reboot warning. Before
  this change, the options-save call answered a warning list but never wrote
  it onto the run record. The confirm page reads a fresh record with no
  warning list at all, so it always showed "The plan found no warning," even
  when a real warning applied. The confirm page is the last page before
  firmware moves, so a hidden warning was a safety gap. Issue #2003.

### Retire the duplicate continuous-loop menu number

- **Removed**: Menu 152 ran the same `DataCollectionManager.continuous_loop`
  action as menu 151, under a vaguer description. One of the two
  descriptions could not be true for both numbers. Menu 152 is retired. Menu
  151 keeps the accurate description. It stays the one number for this
  action. `RETIRED_MENU_NUMBERS` in
  `tests/guardrails/test_menu_number_uniqueness.py` records the gap. The
  guardrail still catches a new, unexplained gap, and it refuses a future
  reuse of 152.
- **Changed**: The generated menu reference, the README menu tables, and the
  architecture diagram now show one `continuous_loop` operation. Each one
  also shows the corrected total of 240 operations.

### Link the open run that an already-running refusal names

- **Added**: The capture page's already-running-upgrade refusal now shows the
  open run identifier as a link to its live view (`/runs/<run_id>`). Before
  this change the identifier was plain text, and an operator had to copy it
  by hand. The site-lock-holder refusal keeps showing its address as plain
  text alone, because that value comes from another operator and must never
  reach `innerHTML`. The link is a real anchor element, built through
  `createElement`, never a concatenated string.

### Fix the E2E stand-in cloud session's crash on the site inventory page

- **Fixed**: The browser test fixture's stand-in cloud session had no
  `mist_get` method. Every browser test that opened the site inventory page
  then met a 500 fault. The stale-firmware check (issue #2006) started
  reading device versions through that session, and the stand-in never grew
  a method for it. The stand-in now answers the one read that check needs.
  Every other cloud call still fails fast, as the class always intended.

### Report a lost run write and a lost tracker write instead of discarding them

- **Fixed**: The upgrade driver now reads the result of `write_run`. A write
  that never reaches the store logs the fact. The record then moves to the
  failed state, the same rule `write_capture` already applies to a capture.
  One retry writes the failed state to the store. A second failure only logs,
  because the driver must never recurse through its own failure path.
- **Fixed**: `write_tracker` now catches a disk fault and returns `None`
  instead of raising. The tracker is a convenience for restart recovery. The
  upgrade already reached the cloud by the time the driver writes the tracker.
  A lost tracker write now only logs. It never fails a run whose firmware
  write is already underway on real hardware.

### Group the local stack under one project and drop the unused Ollama container

- **Removed**: The local compose stack no longer builds or starts an Ollama
  container. No file under `src/` used it. The only other Ollama references
  are in the standalone `scripts/mist_ideas_*` tools. Those tools connect to
  an external Ollama fleet through `OLLAMA_SERVERS`. They do not read this
  compose file. Issue #2167 records the finding.
- **Changed**: `compose.yml` now sets an explicit project name. This is the
  same pattern that the fiber-planner project uses. Every service now joins
  one pod in Podman. Before this change, the project name came from the
  current folder name. A worktree checkout could then start a separate pod
  instead of the shared one.

### Restore confirmed upgrade starts

- **Fixed**: A run that adopts a verified pre-check capture now moves to the
  confirmation stage when its upgrade plan is saved. The portal sends the
  upgrade after the operator confirms it.
- **Changed**: A run that cannot start now names the recovery step. The run
  page links to the saved upgrade options. Manual refresh now confirms that the
  displayed state is current.

### Show useful wired-client identity data

- **Display (Changed)**: The wired-client table now uses `hostname` and falls
  back to `last_hostname`. It shows the manufacturer and no longer shows the
  VLAN number.

### Render capture result tables after automatic refresh

- **Fixed**: A capture page now reloads once when polling first finds a verified
  capture. The reload renders the stored device, wired-client, and
  wireless-client rows. A page that already rendered its tables does not reload.

### Show capture results and firmware targets in the portal

- **Fixed**: The capture page now opens the stored capture after the portal starts
  it. The completed capture tables now load on that page.
- **Added**: The site inventory now marks a reported firmware version that differs
  from its safe target. The target uses the configured version when available.
  Otherwise, the portal uses the highest compatible model version.

### Restore SSR firmware version choices in the capture portal

- **Fixed**: The portal now reads Session Smart Router versions from the Mist
  SSR endpoint. It offers the returned versions for each SSR model in a site.

### Restore capture collection in the container

- **Fixed**: The container image now includes the `scripts` package. The capture
  collector can import the Zscaler city metadata helper during startup.

### Browser token and safe device selection

- **Added**: The capture portal accepts a browser API token only when it started
  without an environment token. The portal reads a safe token name for the
  session audit and never stores, shows, or logs the token value.
- **Added**: Operators can select all supported device types, one device type,
  or several device types for an upgrade plan. The capture still includes every
  device.
- **Added**: The options page marks known firmware versions that differ from
  the safe target. A compatible configured target takes priority. Otherwise,
  the portal uses the highest compatible model version.

### Restore capture portal browser controls

- **Fixed**: The portal JavaScript now initializes correctly. Site lock, capture,
  and upgrade option controls now attach to the page.
### Use safe type-specific firmware targets in the capture portal

- **Defaults (Added)**: The upgrade capture portal now selects the numerically
  highest compatible firmware version for each access point, switch, and gateway
  type. Each device uses the type target when compatible. Otherwise, it uses its
  own highest compatible version.
- **Configuration (Added)**: `CAPTURE_DEFAULT_AP_VERSION`,
  `CAPTURE_DEFAULT_SWITCH_VERSION`, and `CAPTURE_DEFAULT_GATEWAY_VERSION` can
  set a type target. The portal ignores an unavailable value and uses the safe
  fallback.
- **Controls (Changed)**: The options page now has separate access point, switch,
  and gateway selectors. The retired all-device selector is removed.
- **Discovery (Fixed)**: Version discovery now sends the Mist device type and
  model. Mist otherwise defaults the version request to access points.

### The capture portal waited on serial cloud calls and raced on the tracker (issue #2090)

- **Strategy (Applied)**: `documentation/python-parallelism-matrix.md` decides the
  tool for each case. Every hot path of the portal waits on a network, so the
  bottleneck is input and output. The matrix answers that case with a bounded
  thread pool and warns against a process pool, because the payload is a
  multi-megabyte document and the pickle cost is larger than the gain. No change
  raises the cloud call count, so the hourly call budget is unchanged.
- **Defect (Fixed)**: `capture/extras.py` made four cloud calls one after another
  inside the tier 3 call group. Each call walks every page, so a large site paid
  the sum of four page walks. `tests/unit/upgrade_portal/test_performance.py`
  credited that group with one page of latency, because its fake answered the
  whole group in one call. The code was about four times slower than its own
  documented model and no test could see it.
- **Fan-out (Added)**: `runtime/pools.py` grows `BoundedFanOut`. It runs a small
  set of named blocking calls at one time, never wider than
  `CAPTURE_WORKER_TARGET`, and returns one answer for each name. A call that
  raises answers with None, so one fault never loses the other answers.
- **Capture (Faster)**: the four tier 3 reads now run at one time. The tier 3
  group costs the longest page walk instead of the sum of four.
- **Stop (Faster)**: `upgrade/stop.py` cancelled each upgrade plan one at a time,
  and each plan costs two cloud calls. A run holds up to one plan for each device
  family, so a stop waited for six round trips before the last plan reached the
  cloud. Every second of that wait is a second in which one more device can start
  to write firmware, and FR-038d forbids an interrupt of a write. The cancels now
  run at one time.
- **Race (Fixed)**: `upgrade/driver.py` `write_tracker` read `ActiveUpgrades.json`,
  dropped one row, appended a row, and wrote the whole file with no lock. The plan
  allows six runs at one time and each run owns a driver thread, so two threads
  could interleave and lose one run row. An operator then saw no record of a run
  that was still writing firmware. A process-wide re-entrant lock now holds the
  read and the write together.
- **Atomic (Added)**: the tracker write lands through a neighbor file and one
  rename, so a reader never meets a half-written file. Windows refuses to rename a
  file that another handle holds open, so the reader takes the same lock and both
  the read and the rename try again after a short pause.
- **Waste (Removed)**: `capture/assembly.py` `stamp_size` ran four whole JSON
  serializations of a multi-megabyte document every time. The number settles after
  two or three rounds. The loop now stops the moment the number repeats, which is
  what `capture/store.py` already did.
- **Model (Repaired)**: the performance model now drives the real
  `extras.collect_extras` with counted cloud calls and reads the four tier 3
  tallies apart from the call group tallies. Five new tests pin the call count at
  four, pin the group cost at one page, and prove the model reports four times the
  cloud time for a group that runs its calls in order.
- **Tests (Added)**: 18 tests. Each concurrency test uses a barrier, which
  releases only when every party arrives, so it passes under a fan-out and times
  out under a loop. A value test alone could not tell the two apart.
- **Not Changed (Explained)**: the settle gate poll still makes its two reads in
  order. The round already sleeps 20 seconds and the round count is capped, so a
  faster round buys nothing and the gate is safety critical. The comparison
  counters still walk the delta list once for each count, because the list holds
  at most 250 devices and 5000 clients and five passes cost about one millisecond.

### Remove the unused noqa directives and gate the rule (issue #1792)

- **Defect (Fixed)**: 310 `# noqa` directives suppressed nothing. A stale
  directive hides the next real finding on the same line, and it tells a reader
  that a problem exists where none does. `ruff check . --fix` removed all 310.
- **Gate (Added)**: `RUF100` joins `select` in `pyproject.toml`. The rule reports
  a directive that suppresses nothing, so the count stays at zero and a reader
  can trust that every remaining directive answers a real finding.
- **Comments (Restored)**: the ruff fix removes the whole trailing comment when
  the reason runs on directly after the code, so
  `except Exception:  # noqa: BLE001 - the SDK raises bare Exception` lost its
  reason. This project requires a reason on every executable line, so a repair
  pass read the base revision of each changed file and put 121 lost reasons back
  as plain comments. No line lost its reason.
- **Count (Explained)**: the earlier attempt on this issue removed 287
  directives. `main` has moved since then, so the sweep was measured again
  against the current tree and it now reports 310. A rebase of the old sweep
  would have left the 23 newer directives in place, and the new gate would then
  have failed on the very branch that added it.
- **Formatting (Applied)**: `src/export/org_inventory_exporter.py` and
  `src/firmware/firmware_manager.py` needed black after the sweep, because the
  shorter lines let black rejoin two wrapped calls.
- **Sweep safety (Verified)**: the four checks of the sweep policy pass.
  `py_compile` reports no output for all 107 changed files. `ruff check .`
  reports `All checks passed`. `mypy src/ MistHelper.py wsgi.py` reports
  `Success: no issues found in 387 source files`. `tools.symbol_diff` reports
  `no module-level name changed` and exits 0. The count of deleted lines that
  are not comments is zero.
### Read one organization security intelligence profile (spec 635, issue #1148)

- **Gap (Closed)**: MistHelper exported the whole SecIntel profile list through
  `listOrgSecIntelProfiles`, and that list view holds the summary fields only.
  An operator who reviewed one profile had to open the Mist portal to read the
  full body. Menu **240** now reads one profile through `getOrgSecIntelProfile`
  (`GET /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}`).
- **Prompt (Chosen)**: the endpoint needs a profile UUID. A junior engineer
  cannot be expected to know a UUID, and a typed UUID invites a typing error.
  The exporter therefore reads the profile list first, prints a numbered table,
  and asks for a number. The operator never types a UUID.
- **Response shape (Explained)**: the endpoint returns one object and it is not
  paginated, so `OrgSecIntelProfileExporter._fetch` reads `response.data`.
  `mistapi.get_all` would return nothing useful for this call.
- **Primary key (Added)**: `getOrgSecIntelProfile` joins
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` as a `natural_pk` on `id`, with indexes on
  `org_id` and `name`. A repeat read of the same profile therefore upserts
  instead of writing a duplicate row.
- **Category (Assigned)**: menu 240 is `interactive_safe`. The operation reads
  only, and it needs an org and a profile choice, so it runs under
  `--testinteractive` and not under `--test`.
- **Tests (Added)**: `tests/unit/export/test_org_sec_intel_profile_exporter.py`
  holds 23 tests. They pin the paging call, the rejection of a malformed list
  entry, the numbered prompt with every cancel path, the `response.data` read
  with four wrong body shapes, the flatten step, the exact operationId that
  reaches the writer, and the promise that an SDK error returns to the menu
  instead of ending the session. Every Mist call is mocked.

### Menu 238 was allocated twice, so the portal moved to menu 239 (issue #2065)

- **Defect (Fixed)**: `main` gave menu 238 to the MSP license export, which is
  `interactive_safe`. This branch gave menu 238 to the upgrade capture portal,
  which is `destructive`. Each branch passed the registry guardrail on its own,
  because that check compares `menu_actions` against the registry inside one
  branch and never reads the merge base.
- **Safety (Explained)**: the two entries disagreed on the category, and the
  category decides whether an automated run may execute the option. Had the
  merge kept the portal action under the `interactive_safe` row from `main`,
  `python MistHelper.py --testinteractive` would have started the firmware
  upgrade portal on port 8056 during a normal test pass. That is the one outcome
  the destructive classification exists to prevent.
- **Renumber (Applied)**: `listMspLicenses` reached `main` first, so it keeps
  menu 238. The upgrade capture portal moves to menu **239** and keeps its
  `destructive` category. The `--capture-portal` flag is unchanged.
- **Merge (Resolved)**: pull request #1825 reported `DIRTY`, so 80 commits of
  portal work could not reach `main`. This commit merges `origin/main` into the
  branch and resolves all six conflicts: `MistHelper.py`,
  `src/utils/operation_registry.py`, `README.md`, `CHANGELOG.md`, and the two
  generated menu references.
- **Counts (Corrected)**: the registry now holds 240 entries, numbered 0 to 239.
  `interactive_safe` reads 71 and covers 235-238. `destructive` reads 42 and
  covers 154-187, 189-191, 194, 206-208, and 239.
- **Guardrail (Added)**: `tests/guardrails/test_menu_number_uniqueness.py` holds
  6 tests. They refuse a duplicate key, a gap in the numbering, and two numbers
  that answer one action. They also pin the portal to `destructive` and pin menu
  238 to the MSP license export, so a later branch that takes 238 back fails at
  once.
- **Finding (Recorded)**: the new guardrail found that menus 151 and 152 both
  call `DataCollectionManager.continuous_loop` with no argument that tells them
  apart, while each advertises different work. Issue #2066 tracks the repair.
  The pair sits in `KNOWN_SHARED_ACTIONS` so the guardrail still catches a new
  duplicate while that one waits.

### The capture page shows the stored size of a finished capture (issue #2063)

- **Defect (Fixed)**: the capture detail page reported `Stored size in bytes: 0`
  beside the word `Verified` for a capture that was stored and complete. The
  history page and the database both held the true size for the same document,
  so one page disagreed with the other two.
- **Cause (Found)**: the template reads `stored_size_bytes` from the context
  root. `status_body` removes that field, because `STATUS_FIELDS` does not name
  it and the poll contract carries no size, and `page_context` never set it
  separately. The browser filled the gap with one extra read of the whole
  capture in `loadStoredSize`, but `refreshCaptureStatus` calls that read only
  when a poll answers `verified`. A capture that ended before the page opened
  never polls, so the value stayed at the template default of zero.
- **Fix (Applied)**: `page_context` now renders `stored_size_bytes` at the first
  paint, and `stored_page_fields` carries the value for a capture that the
  portal reads back from the store. The page no longer depends on the second
  browser read, which stays as a refinement for a capture that finishes while
  the page is open.
- **Reading (Hardened)**: `stored_size_of` turns an absent value, a null, and a
  value the page cannot read into zero, so an older document renders rather than
  raising.
- **Tests (Added)**: `tests/unit/upgrade_portal/test_capture_stored_size.py`
  holds 17 tests. They cover the page fields, the whole status record, the merge
  order, every unreadable value, the page context, and the rule that the poll
  body must still drop the size. Five were verified red first against the old
  code.
- **Verification (Measured)**: both stored captures were opened after a portal
  restart, which guarantees no live progress record exists. The page rendered
  39472 and 15494 bytes, matching the database and the history page. Before the
  fix the same two pages rendered 0.

### Every capture failed, because the write name and the read name differed (issue #2061)

- **Defect (Fixed)**: no capture could ever be stored. The portal collected the
  data correctly, wrote it to ArangoDB successfully, and then declared the write
  failed. Both tier 2 and tier 3 failed the same way, and the page showed every
  collection phase as `done` beside the sentence "The portal could not store the
  capture."
- **Cause (Found)**: `src/upgrade_portal/capture/store.py` held two names for one
  thing. It wrote through `CAPTURE_OPERATION = "upgradeCaptureWrite"` and read
  back through `CAPTURE_COLLECTION = "upgrade_captures"`.
  `DataExporter.write_with_format_selection` hands the operation name to
  `DatabaseRouter.write`, which hands it to `ArangoWriter.write` as the
  collection name. `ArangoWriter._ensure_collection` then creates the collection
  when it is absent. Nothing translates the name on the way, so every capture
  created and filled a collection named `upgradeCaptureWrite`, and the read-back
  looked in an empty `upgrade_captures` and reported `document_absent`.
- **Evidence (Measured)**: the two failed captures of the report were found in
  the wrong collection under the exact keys from the log.
  `upgradeCaptureWrite` held 2 documents while `upgrade_captures`,
  `upgrade_runs`, and `capture_for_run` each held 0. The `data/` directory held
  21 capture backup files, so the fault predates the report.
- **Fix (Applied)**: each operation name is now bound to its collection name,
  `CAPTURE_OPERATION = CAPTURE_COLLECTION` and `RUN_OPERATION = RUN_COLLECTION`.
  The second name is gone, so the two cannot drift again. The matching keys in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` move with them and keep `natural_pk` on
  `capture_id` and `run_id`.
- **Why no gate caught it**: every readiness signal was green while every
  capture failed. The storage bootstrap creates the three collections the portal
  reads and reports `collections=3, indexes=7, database_available=True`, and
  `GET /readyz` answered `{"database":"ok","redis":"ok"}`. Neither one exercises
  the write path, and the write path never used those collections.
- **Tests (Added)**: `test_the_write_name_equals_the_read_name` asserts the two
  names are one value for both targets, and
  `test_no_stale_write_endpoint_name_returns` refuses either retired name in the
  strategy table. The first test was verified red against the old constants: it
  reported 2 failures before the fix and passes after it.
- **Verification (Measured)**: both tiers were run against a live site after the
  fix and both reached the verified state.

  | Tier | Key | State | Stored bytes |
  | - | - | - | - |
  | 2 | `cap-b4e8473a...-01` | `verified` | 15494 |
  | 3 | `cap-434b67ea...-01` | `verified` | 39472 |

  The page reads "Capture progress verified 100%" and "The portal read the
  capture back and the record matches." `upgrade_captures` holds 2 documents and
  `capture_for_run` holds 2 edges.
- **Migration (Done)**: the stray `upgradeCaptureWrite` collection held two
  captures that never left the `writing` state. Both keep a CSV backup under
  `data/`, so the collection was dropped without data loss.

### The portal checks its dependencies and repairs a stopped one (issue #2059)

- **Defect (Fixed)**: the portal started, logged "ready for the port 8056", and
  served the sign-in page while the document store answered nothing. The
  operator signed in, picked a site, and only then met a 503, because
  `acquire_site_lock` fails closed. The fault appeared three pages after its
  cause. `GET /readyz` already reported the gap, but it answers JSON for an
  orchestrator and no page showed the result.
- **Preflight (Added)**: `src/upgrade_portal/runtime/dependencies.py` probes
  every service the portal needs and returns one report. The sign-in page renders
  the report, so the operator reads the state, the address, and the next action
  on the first page.
- **Probe depth (Stated)**: each probe opens a TCP connection and closes it, so
  it answers one question: does a service listen. It signs in to nothing,
  because the page must render fast and must render before the portal holds a
  credential. The panel names `/readyz` for the deeper reading that also writes
  to both stores.
- **Auto-start (Added)**: `src/upgrade_portal/runtime/containers.py` reads the
  state of one named container and starts it. A stopped container is the common
  workstation fault and the one case the portal can repair. The module creates
  nothing, pulls nothing, and removes nothing, so a missing container stays
  missing and the report names the compose command instead. `CAPTURE_AUTOSTART`
  turns the behavior off, and `compose.yml` sets it to `0` inside the container,
  because a container cannot start its sibling.
- **Command safety (Kept)**: every runtime call passes an argument list and no
  shell, the runtime path comes from `shutil.which`, each container name passes
  a pattern that refuses a leading hyphen and every shell character, and each
  call carries a timeout.
- **Name collisions (Fixed)**: `compose.yml` named two containers `arangodb` and
  `redis-stack`. Those names belong to no project, so another project took them
  first. A container named `truck-arangodb` from a different project held port
  8529 on the test workstation, and the portal read that foreign database as its
  own store. It reached a real server, received 401, and reported its own store
  unreachable. Every service, container, network, and volume now carries the
  `misthelper-` prefix.
- **Ports (Moved)**: a vendor default is the port every other project also
  publishes. ArangoDB moves from 8529 to 9529, Redis from 6379 to 9379, the
  Insight UI from 8001 to 9526, and Ollama from 11434 to 9530. Each service binds
  the new port inside the container as well, so each health check names the port
  its client tool would otherwise guess. Ports 2200, 8055, and 8056 do not move,
  because none is a vendor default and each already sits in the required range.
- **Network (Pinned)**: the project network takes the subnet `172.31.240.0/24`
  and an explicit name. A bridge with no subnet takes the next free range from
  the runtime pool, and two projects can receive the same range. The test host
  showed this: the old network held `10.89.0.0/24` from the pool.
- **Migration (Required)**: the renamed containers use renamed volumes, so a
  fresh ArangoDB holds no `misthelper` database. Create the database once, and
  the portal then builds its three collections and seven indexes on the next
  start. The old `arangodb-data` and `redis-data` volumes are left in place, so
  no data is deleted by the rename.
- **Tests (Added)**: 69 tests. `tests/unit/upgrade_portal/test_containers.py`
  holds 26 and covers the name guard, the runtime search, every reported state,
  and every failure path. `tests/unit/upgrade_portal/test_dependencies.py` holds
  30 and covers the probe, the switch, and every reading the page can show.
  `tests/guardrails/test_compose_naming_policy.py` holds 13 and fails when a
  later edit reintroduces a generic name, a vendor default port, or a bridge
  with no subnet. No test runs a container.
- **Verification (Measured)**: the renamed stack was started on the test host.
  Both containers report healthy, the network holds the pinned subnet, and the
  storage bootstrap reported `database_available=True` with 3 collections and 7
  indexes. `GET /readyz` answered `{"database":"ok","redis":"ok"}`. With
  `misthelper-redis` stopped, one load of the sign-in page started the container
  and rendered the state `started`.

### Add the upgrade capture portal, menu 238 (issue #1823)

- **Menu 238 (Added)**: `Upgrade Capture Portal` starts a web server and prints a
  clickable link. The flag `--capture-portal` starts the same server without the
  menu. Spec 1823.
- **New package (Added)**: `src/upgrade_portal/`. It sits outside `web_portal/`,
  which ruff and mypy exclude, so every gate covers the new code.
- **Port (Added)**: `CAPTURE_PORT`, default 8056. The portal takes its own port,
  so it never fights the other portal in a container or on a shared desktop.
- **Server (Added)**: Gunicorn on Linux and Waitress on Windows. Windows ships no
  `fcntl`, and `gunicorn.util` imports `fcntl`, so Gunicorn cannot start there.
- **Bind address (Added)**: the portal binds the loopback address on a desktop.
  It binds every address only inside a container, where the port map is the only
  way in.
- **Capture (Added)**: one capture records the firmware, the device state, and
  the client counts of one site. The operator picks a standard tier or a full
  tier. Every capture writes to ArangoDB, to a CSV file under `data/`, and to the
  browser as a table. The page offers the CSV as a download.
- **Upgrade (Added)**: the portal reuses the bulk firmware tools through a new
  seam, `src/firmware/upgrade_service.py`. The operator types `CONFIRM` to unlock
  the start control, and types `STOP` to cancel the devices not yet started.
- **Settle logic (Added)**: the portal watches the device events of the site
  every 20 seconds. It waits for the reconnect message, then waits one more
  minute before the post-upgrade capture. Access points and clients wait for the
  switches, and everything waits for the gateways.
- **Comparison (Added)**: the compare page shows the two captures side by side
  and adds a statistics summary. The page offers that summary as a CSV download.
- **Site lock (Added)**: Redis holds one lock for each site, so two operators
  never work one site at the same time. An operator signs in with a work email
  address, and the lock pairs that address with the browser. One operator can
  therefore hold several sites in several tabs. An abandoned session frees the
  site after a five minute cooldown. Any operator can read a site and download
  its data without a lock.
- **Lost lock (Added)**: a lost lock never fails a run. The portal submits the
  upgrade to the cloud, and the cloud then owns the work. The banner states that
  the upgrade continues in the cloud and that the devices still reboot.
- **Theme (Added)**: the navigation holds a theme picker, and the portal now
  reads the choice. The picker is a GET form, because the content security
  policy blocks an inline script, so the page reloads with `?theme=<name>`. One
  context processor reads that argument for every page. Before this the picker
  rendered, accepted a choice, reloaded the page, and changed nothing, so the
  brand theme was unreachable. A name the portal does not ship reads as the
  neutral theme, so no operator input reaches a file path.
- **History (Added)**: the portal keeps every capture without an expiry, and it
  records the stored size of each one. An operator can return a week later and
  read the same comparison.
- **Storage (Added)**: ArangoDB is the primary store, with collections
  `upgrade_captures` and `upgrade_runs` and the edge `capture_for_run`. Redis
  holds the site lock alone. CSV files under `data/` are the fallback.
- **Tests (Added)**: 2548 unit and contract tests under
  `tests/unit/upgrade_portal/` and `tests/contract/upgrade_portal/`. Statement
  coverage of the package is 94.67 percent.
### Export the MSP licenses through menu 238 (issue #1260)

- **Gap (Closed)**: the Mist endpoint `listMspLicenses`
  (`GET /api/v1/msps/{msp_id}/licenses`) had no menu entry. An operator who
  manages an MSP had to write custom code to read the license entitlement, the
  usage counters, and the subscription records.
- **Menu (Added)**: menu 238 runs the export. The registry classifies it
  `interactive_safe`, because it reads only and it prompts for an MSP ID. The
  `--testinteractive` run therefore includes it, and the `--test` run skips it.
- **Class (Added)**: `src/export/msp_license_exporter.py` holds
  `MSPLicenseExporter`. It prompts through `InputUtils.safe_input`, calls the
  SDK once, and writes through `DataExporter.write_with_format_selection`, so
  the CSV, SQLite, and ArangoDB backends all work.
- **Response shape (Explained)**: the endpoint returns one aggregate object, not
  a list. The object holds four counter maps, one `licenses` array, and one
  `amendments` array. The endpoint is not paginated, so the exporter reads
  `response.data` instead of running `mistapi.get_all`.
- **Two files (Chosen)**: the exporter writes `MSPLicenses_<msp>_summary.csv`
  and `MSPLicenses_<msp>_details.csv`. One wide row would hold one column for
  each subscription field, so the column count would change every time the MSP
  buys or retires a subscription. Two files keep both schemas stable. The
  detail file carries a `record_type` column, because a subscription record and
  an amendment record share the same field names.
- **Primary keys (Added)**: `ENDPOINT_PRIMARY_KEY_STRATEGIES` gains
  `listMspLicenses` as a `natural_pk` on `msp_id` and `listMspLicensesDetails`
  as a `natural_pk` on `id`. Both are natural keys, so a repeat run upserts and
  writes no duplicate row.
- **Shared prompt (Extracted)**: `InputUtils.prompt_msp_id` now holds the MSP
  identifier prompt. Menu 237 carried its own copy inside `CountExporter`, and a
  second copy in the new exporter made Pylint report duplicate code. One method
  keeps the prompt text, the trim, and the abort rule identical across both MSP
  menus. `CountExporter._prompt_msp_id` is deleted, not delegated, because the
  project forbids a wrapper.
- **Tests (Added)**: `tests/unit/export/test_msp_license_exporter.py` holds 22
  tests. They cover the abort path, the non-dict body, both row builders, the
  malformed-array guards, the empty result, the error handler, both primary-key
  entries, and the menu wiring. `tests/unit/utils/test_input_utils_wave9.py`
  gains 4 tests for the shared prompt, including the EOF path. Every Mist call
  is mocked, so no test reaches the live cloud.
- **Documentation (Updated)**: `documentation/menu_reference.md` and
  `documentation/wiki/Menu-Reference.md` were regenerated. The README operation
  counts were stale at menu 234, because menus 235 to 237 reached `main` without
  a README update. The counts now read 238 entries plus Exit, and the menu table
  lists 235 through 238.
### Count and report the dropped server-sent events (issue #1924, instance 3)

- **Defect (Fixed)**: `PortalEventBus._enqueue_event` in
  `web_portal/services/event_bus.py` held two silent loss paths. The first
  `queue.get_nowait()` removed the oldest event to free a slot, and the closing
  `except Full: pass` discarded the new event. Neither path kept a record.
- **Reader risk (Explained)**: an operator watching the live operation feed saw
  an incomplete record of a run and received no indication that a gap existed.
  Issue #1924 names this shape: a failure path that erases its own evidence.
- **Counters (Added)**: `_evicted_event_count` and `_rejected_event_count`
  separate the two loss paths. The `dropped_event_count` property and the
  `drop_stats()` method expose them to a test and to an operator.
- **Rate limit (Chosen)**: the bus logs the first drop at WARNING, then doubles
  the threshold before each later report. A full queue overflows again on the
  next event, so one line for each drop would flood the log. Issue #1766
  already records that noise dilutes the WARNING level in this project.
- **Summary (Added)**: `stop()` reports the final drop total one time, because
  the growing threshold can leave the last drops unreported.
- **Live feed (Changed)**: the heartbeat event now carries a `dropped_events`
  count, so the operator sees the gap in the stream without opening a log.
- **Lock safety (Verified)**: `publish()` is the only caller and it already
  holds `self._lock`. `threading.Lock` is not reentrant, so the counters take
  no further lock and the property reads them without one.
- **Tests (Added)**: `tests/unit/web_portal/test_event_bus.py` holds 5 new
  tests. They pin the drop counter, the eviction order, the first WARNING, the
  bounded line count across a 500-event burst, and the stop summary.

### Run the quality gates on every pull request (issue #1952)

- **Defect (Fixed)**: `.github/workflows/ci.yml` started on a pull request that
  targeted `main` only. A pull request against any other base ran no gate. Ruff,
  Black, mypy, pytest, the coverage gate, Bandit, pip-audit, Pylint, Radon,
  Vulture, and both docstring gates all stayed silent.
- **Evidence (Measured)**: pull request #1890 targets
  `feat/1823-upgrade-capture-portal`. It reported 0 successful checks and 0
  failed checks, while every pull request against `main` reported 17 to 19. The
  pull request was closed and reopened to force a new run. The count stayed at
  zero, which rules out a missed event.
- **Reader risk (Explained)**: the pull request also reported a `CLEAN` merge
  state. `CLEAN` means no required check is failing. A reviewer reads an empty
  check list as safe, and the correct reading is unmeasured.
- **Trigger (Changed)**: the `pull_request` trigger now carries no branch
  filter, so a pull request against any base runs every gate.
- **Cost control (Kept)**: the `push` trigger stays pinned to `main`. A push run
  on every branch would repeat the pull request run and add no signal.
- **Tests (Added)**: `tests/guardrails/test_ci_gate_triggers.py` holds 5 tests.
  They pin the absent branch filter and the narrow push trigger. The tests were
  verified red first. They report 2 failures against the old workflow and 5
  passes against the new one.

### The ops-portal CI gate now blocks a merge (issue #1852)

- **Defect (Fixed)**: the `ops_portal` job ran `typecheck`, `lint`, and `test`
  with `continue-on-error: true`. Each step failed on a configuration defect,
  so each step reported a result and blocked nothing. The `ops_portal` job is
  the only gate that reads the TypeScript source and the npm dependency tree.
  The whole `ops-portal/` application therefore had no enforcing check.
- **Type check (Fixed)**: `tsconfig.json` set the deprecated `baseUrl` option,
  and TypeScript 6 refuses it. The option is deleted. The `paths` map resolves
  relative to the config file, so the `@/*` alias still works. `vite.config.ts`
  carries its own alias, so the build is unchanged.
- **Broken imports (Fixed)**: the `baseUrl` error stopped TypeScript before it
  read any file, so three broken imports in `src/router.tsx` stayed hidden.
  The router loaded `@/pages/config/TimeTravelPage`, `RevisionsPage`, and
  `BaselinesPage`, and none of the three files existed. Three `/config` routes
  and the `time-travel` route pointed at nothing. The three pages are added.
  Each one reads the existing `configQueries` API layer.
- **Lint (Fixed)**: the project shipped `.eslintrc.cjs`, and eslint 10 reads
  `eslint.config.js` only, so eslint found no configuration and exited
  non-zero. A flat `eslint.config.js` replaces it. Each plugin supplies its own
  flat configuration, so the file needs no `FlatCompat` shim.
- **Lint findings (Fixed)**: the working lint step found four errors that had
  reached `main`. `src/hooks/useTelemetry.ts` declared a never reassigned
  binding with `let`. `src/pages/deploy/TemplatesPage.tsx` held three labels
  with no associated control, which a screen reader cannot read. Each label now
  wraps its control.
- **Tests (Added)**: the project shipped no test, and vitest exits non-zero
  when it finds no test. `vitest.config.ts` and
  `src/components/ConfirmationDialog.test.tsx` add 12 tests. The suite covers
  the confirmation dialog, which is the safety gate for every destructive
  action in the portal.
- **Dialog crash (Fixed)**: the first test run proved that
  `ConfirmationDialog` threw "Passing props on Fragment" and never rendered.
  The component passed `as={Fragment}` to the Headless UI dialog, and a
  Fragment cannot carry the ref and the aria attributes that the dialog sets.
  Seven call sites guard a destructive action with this dialog. The prop is
  removed.
- **Dependencies (Added)**: `@eslint/js`, `globals`, `jsdom`, and
  `@testing-library/dom` are added as dev dependencies. The lint configuration
  and the test environment need them. `npm audit` still reports zero
  vulnerabilities.
- **Gate (Changed)**: `.github/workflows/ci.yml` drops `continue-on-error` from
  all three steps. A type error, a lint error, and a failing test now each stop
  a merge.
- **Flag (Unchanged)**: `npm ci` keeps `--legacy-peer-deps`. Both
  `eslint-plugin-jsx-a11y` 6.10.2 and `eslint-plugin-react` 7.37.5 cap their
  eslint peer range below the installed eslint 10.7.0, and both are the newest
  published releases. The workflow comment records the measurement.

### Warning: the web portal now refuses a remote client by default (issue #1933)

- **Warning: read this before you upgrade.** This entry changes a shipped
  default. A running portal can stop answering a remote browser after the
  upgrade. Set `PORTAL_ALLOWED_IPS` before you upgrade, and no operator loses
  access. The startup log names the setting and gives an example value.
- **Defect (Fixed)**: the web portal has no user authentication. The address
  allowlist is the only access control it has. `PORTAL_ALLOWED_IPS` shipped
  empty, and `SecurityMiddleware._register_ip_allowlist` read an empty value as
  "accept every source address". A portal that reached a network therefore
  served every page, every data browser table, and every operation to any
  caller who reached the port. No credential was needed.
- **Fallback (Added)**: an empty `PORTAL_ALLOWED_IPS` value no longer opens the
  portal. `SecurityMiddleware._build_fallback_allowlist` picks a closed set of
  networks that fits the run mode. Outside a container the portal serves the
  loopback ranges `127.0.0.0/8` and `::1/128` only. The operator who starts the
  portal keeps access.
- **Container case (Added)**: inside a container the portal serves the private
  ranges only. These are the two loopback ranges, `10.0.0.0/8`,
  `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `fe80::/10`, and
  `fc00::/7`. A container must bind every interface to answer a published port,
  so a loopback rule would make every container unreachable. This fallback
  blocks a direct path from the public internet. It does not replace a real
  allowlist. Set `PORTAL_ALLOWED_IPS` on a container that faces a shared
  network.
- **Opt-out (Added)**: `PORTAL_ALLOW_PUBLIC_ACCESS` restores the old open
  behavior. The portal accepts `1`, `true`, `yes`, and `on`. Every other value
  keeps the portal shut, so a typing slip cannot open it. The portal writes a
  warning to the log at every startup while the setting is true, so an audit
  finds the choice.
- **Startup message (Added)**: each fallback writes one warning. The message
  names the served scope, names `PORTAL_ALLOWED_IPS`, gives the example value
  `10.20.30.0/24,192.168.1.5`, and names the opt-out setting. The message is
  ASCII only.
- **Precedence (Unchanged)**: a configured `PORTAL_ALLOWED_IPS` value still
  wins. The fallback ranges never widen an explicit allowlist.
- **Tests (Added)**: `tests/unit/web_portal/test_portal_access_control_default.py`
  adds 24 tests. Twelve of them failed before the fix. The proof case sends a
  request from the public address `203.0.113.10` to a portal with no allowlist
  and expects 403.
- **Documentation (Changed)**: `deploy/.env.example` states the fallback, the
  container ranges, and the opt-out.

### Stop the ZTP password from reaching a stored stream (issue #1735)

- **Defect (Fixed)**: `src/device/_utility_commands_action.py` printed the live
  ZTP password to stdout on every call of menu 144. CodeQL alert 173 reported
  clear-text logging of sensitive data. Three paths stored the value. The first
  path is an SSH session transcript on container port 2200. The second path is a
  shell redirect such as `MistHelper.py > run.txt`. The third path is a planned
  print-to-logging migration under issue #886.
- **Terminal gate (Added)**: `_stdout_is_terminal()` calls `sys.stdout.isatty()`
  before the print. The value now reaches a live terminal only. A stream that
  lacks `isatty`, and a stream that raises on the call, both count as unsafe.
- **Warning order (Added)**: the reveal path writes the warning first, the label
  and the value second, and the copy guidance last. The operator reads the risk
  before the screen holds the value. Clause C-4 of
  `specs/1034-codeql-cleartext-logging/contracts/credential_console.md` states
  that rule.
- **Withheld notice (Added)**: a redirect, a pipe, and a recorded session now
  receive a four-line notice. The notice states the decision and the reason. The
  notice also gives two other sources for the value. The notice never holds the
  value.
- **Comment (Changed)**: the old comment claimed the value could not reach a
  file, and the code did not enforce that claim. The new docstring states the
  review date 2026-08-22, the reason, the migration rule, and the next review
  trigger.
- **Migration rule (Added)**: `TestZtpCredentialMigrationRule` parses the source
  of the three helpers. The test fails when a `logging` call appears next to the
  credential. The rule now lives in a test, so a lost comment cannot drop it.
- **Tests (Added)**: `tests/unit/test_device_utility_commands.py` gains 17 cases.
  They prove that a terminal stdout prints the value. They prove that the
  warning reaches the screen before the value. They prove that a pipe stdout
  prints the value nowhere. They prove that no log record holds the value in
  either mode. They also prove that the empty-payload path and the error path
  keep their old behavior.
- **Divergence from spec 1034 (Noted)**: clause C-2 of the console contract asks
  for `sys.stdout.write()` instead of `print()`. This change keeps `print()` and
  blocks the issue #886 migration with an `ast` guard test. Spec 1034 is unbuilt
  at 0 of 67 tasks, and `CredentialConsole` does not exist yet.
### Replace the obfuscated all-interfaces bind in the web portal launcher (issue #1711)

Version 26.08.23.01.26

- **Defect (Fixed)**: `_launch_web_portal()` built the bind address with
  `".".join(("0",) * 4)`. The expression produced the string `0.0.0.0`, and the
  only purpose of the expression was to hide that literal from bandit rule B104.
  The project standard forbids a shortcut that silences a real finding. A
  suppression comment records the decision and the reason. A join expression
  records nothing.
- **Bind address (Changed)**: the new function `_resolve_web_portal_host()` holds
  the decision. It returns the value of `WEB_HOST` when the operator sets that
  variable. Without that variable it returns `0.0.0.0` inside a container and
  `127.0.0.1` on a workstation. The old code bound to all interfaces on every
  platform, so a workstation run exposed the portal to the local network.
- **Container test (Changed)**: the all-interfaces bind now depends on
  `EnvironmentUtils.is_running_in_container()`. A container needs the external
  bind, because the container network maps the port from outside. The container
  port map controls the exposure.
- **Suppression (Added)**: the assignment carries `# nosec B104`, and the three
  comment lines above it state the container condition and the reason. Bandit
  reports no issue and no warning for the file.
- **Tests (Added)**: `tests/unit/test_web_portal_bind_address.py` holds 8 cases.
  They prove the loopback default, the container all-interfaces bind, the
  `WEB_HOST` override in both states, the fallback for an empty `WEB_HOST` value,
  and that the join expression is gone from the script.

### Scan the Redis keyspace in batches instead of blocking it (issue #1882)

- **Defect (Fixed)**: `RetentionManager.check_redis_retention` ran the Redis
  `KEYS` command with the pattern `*.avg_1h`. The pattern starts with a
  wildcard, so Redis compared every key in the keyspace. Redis serves commands
  on one thread, so the whole server stalled for the length of each scan. The
  background sweep thread repeated the stall every 6 hours by default.
- **`SCAN` loop (Added)**: the check now drives a cursor loop. Each round trip
  sends `SCAN <cursor> MATCH *.avg_1h COUNT 500`. Redis returns one bounded
  batch and then serves other clients, so no single command holds the thread.
- **Memory (Changed)**: the loop adds the length of each batch to a running
  total and drops the batch. The process never holds the whole key set. The old
  code returned a list of every matching key only to read its length.
- **Upper bound (Added)**: `REDIS_SCAN_MAX_KEYS` stops the loop after 100000
  scanned keys. The sweep then logs the new `redis_retention_scan_capped`
  warning with the partial count and returns it. The cost of one sweep stays
  fixed as the keyspace grows.
- **Contract (Unchanged)**: the method still returns an `int` key count. It
  still logs a warning and returns 0 when the Redis call raises.
- **Tests (Added)**: `tests/unit/db/test_retention_redis_scan.py` holds 10
  cases. A fake client records every command it receives. The cases prove the
  code issues `SCAN`, never issues `KEYS`, sends `MATCH` and a bounded `COUNT`,
  follows the cursor until it returns to 0, accepts a cursor that arrives as
  bytes, and stops at the upper bound against an endless keyspace.

### Run the real rollback when a post-check fails (issue #1887)

- **Defect (Fixed)**: `_execute_scheduled_job` set the job status to
  `ROLLED_BACK` after a failed post-check, but no restore ran. The new
  configuration stayed on the live network devices. The operator read the status,
  believed the network held the previous configuration, and started no manual
  repair. The audit trail recorded a rollback that never happened.
- **Configuration backup (Added)**: the workflow now reads the live configuration
  of every target before the push and keeps the snapshots for the whole job.
- **Restore on a failed post-check (Added)**: a failed post-check now pushes the
  captured snapshot back to each device through `RollbackService`.
- **Install result (Fixed)**: the workflow now reads the install result. A failed
  install stops the workflow and starts the restore. The post-check no longer
  runs after a failed install.
- **Honest job status (Changed)**: the status comes from the real restore
  outcome. `rolled_back` means that every device holds the previous
  configuration again. The new value `rollback_failed` means that one or more
  devices did not restore.
- **`auto_rollback_on_failure` (Fixed)**: the workflow now reads this payload
  field. If the value is false, the status is `failed` and no restore runs. The
  workflow never reports `rolled_back` when no restore ran.
- **Tests (Added)**: `mist-ops-platform/tests/unit/worker/test_deploy_rollback.py`
  covers the post-check failure, the failed install, the disabled rollback
  switch, an incomplete restore, the happy path, and the pre-check failure.
- **Test setup (Added)**: `mist-ops-platform/tests/conftest.py` supplies a
  stand-in for `src.shared.config`, because the root `.gitignore` pattern
  `config/` keeps that package out of git and every clean checkout fails to
  import the worker modules.

### Add a graceful shutdown path to the web portal (issue #1861)

- **Defect (Fixed)**: nothing called `PortalEventBus.stop()` or shut down the
  `OperationExecutor` thread pool. A restart sent `SIGTERM`, Gunicorn killed the
  worker, an in-flight operation aborted mid-run, and the heartbeat thread
  leaked past the worker exit.
- **Heartbeat thread (Changed)**: `PortalEventBus._heartbeat_loop` now waits on
  a `threading.Event` instead of `time.sleep(30)`. `stop()` sets the event, so
  the thread exits within a bounded join instead of up to 30 seconds later.
  A second `stop()` call is a no-op, so a duplicate shutdown signal is safe.
- **Operation pool (Added)**: `OperationExecutor.shutdown()` waits for every
  in-flight run's future, up to a bounded grace period, then closes the thread
  pool. A second `shutdown()` call is a no-op.
- **Shutdown wiring (Added)**: `WebPortalApp.create_app` registers one
  `atexit` hook through `WebPortalApp._register_shutdown_hook`. Gunicorn never
  runs `if __name__ == "__main__"`, so the hook calls the new
  `WebPortalApp.shutdown_app` function, which stops the event bus and drains
  the operation pool. `shutdown_app` is idempotent, so a duplicate call at
  process exit does not raise.
- **Grace period (Added)**: `PORTAL_OPERATION_SHUTDOWN_GRACE_SECONDS` defaults
  to 30 seconds. `deploy/.env.example` documents it.
  `container/scripts/start.sh` reads the same value for the Gunicorn
  `--graceful-timeout` flag, so Python and Gunicorn agree on the drain time.
- **Container cleanup (Changed)**: `container/scripts/start.sh` `cleanup()` now
  waits for Gunicorn and sshd to exit, bounded by the grace period plus a
  10-second margin, then sends `SIGKILL` if a process still runs. The old code
  sent one `kill` signal and returned right away, so it never confirmed a
  drain.
- **Quadlet timeout (Changed)**: `deploy/misthelper.container` sets
  `TimeoutStopSec=60`, so systemd waits long enough for the bounded shutdown
  chain to finish before it forces a kill.
- **Tests (Added)**: `tests/unit/web_portal/test_portal_graceful_shutdown.py`
  holds 9 tests. They prove the heartbeat thread ends after `stop()`, that
  `OperationExecutor.shutdown()` closes the pool and waits for a short
  in-flight run, that `WebPortalApp.shutdown_app` stops both the event bus and
  the operation executor for a real app, and that every shutdown path is safe
  to call twice. `tests/e2e/conftest.py` now tears its session-scoped Flask app
  down through `shutdown_app`, so the long-lived test fixture no longer leaks
  its own heartbeat thread.
### Report the real Mist status from list_all_entities (issue #1884)

- **Defect (Fixed)**: `MistEndpointService.list_all_entities` built its result
  with the hardcoded status `200`. A Mist API failure therefore reached the
  caller as a success. `_extract_list` then turned the error body into one data
  record, so the inventory sync wrote a site row with a random identifier and an
  empty name. The sync ledger recorded that run as a success of one site. The
  drift check compared the live configuration against that row, so every real
  site looked like a drift.
- **Status code (Changed)**: `_paginate` now returns the rows and the last
  response. `list_all_entities` reads the real status from that response through
  `_wrap`. On a failure the result holds the Mist error body and no data records.
- **Error body (Changed)**: `_extract_list` returns an empty list for a body that
  is not a list. The old `[data] if data else []` fallback is gone, so an error
  body can never become a data record.
- **Page cap (Kept)**: `main` already caps the page loop at `MAX_PAGINATION_PAGES`
  and already stops a repeated cursor through `_accept_cursor` (issue #1903). This
  branch therefore adds no second cap and no second repeat guard. `_paginate` keeps
  the rate limiting and the 429 retry of `_invoke_with_protection` (issue #1886)
  and only changes its return value to carry the last response.
- **Inventory sync (Changed)**: `_sync_sites` and `_sync_devices` now call
  `_read_records`, which reads `result.success` before it reads `result.data`. A
  failure raises the new `MistSyncError`, so the service writes no row and the
  sync ledger records the run as a failure with the Mist error text.
- **Tests (Added)**: `mist-ops-platform/tests/unit/mist/test_list_status.py`
  holds 11 cases. They prove a failed page reports a failure, that an error body
  never becomes a data record, that a repeated cursor stops the loop, that the
  page cap stops the loop, that a page which stays at 429 reports the failure
  once the retries run out, and that a failed list writes no site row and no
  device row.

### Add a real readiness probe and keep the health endpoint cheap (issue #1863)

- **Defect (Fixed)**: the `/health` endpoint returned the fixed text `healthy` on
  every call. It never tested write access to the data directory, which is the
  one resource with a documented failure. A portal that could not write a single
  output file still reported a good state, so no monitor saw the fault.
- **`/health` (Changed)**: the route is now a liveness probe. It reports the
  process state and the uptime. It reads no disk and it opens no network
  connection, so a blocked resource cannot slow the reply down. The response
  keeps the word `healthy`, so an existing monitor still matches.
- **`/ready` (Added)**: the route tests every resource the portal needs. It
  writes and deletes one temporary file in the data directory, it opens the
  SQLite database read-only when the file exists, and it reads the Mist API
  session state without a network call.
- **Failure report (Added)**: `/ready` returns code 503 when a check fails, and
  the body names each failed check under `failed_checks`. The body also carries
  a detail line for each check, so the operator learns how to repair it.
- **Quadlet probe (Added)**: `deploy/misthelper.container` now sets `HealthCmd=`
  against `/ready`, with an interval of 30 seconds, a timeout of 5 seconds,
  3 retries, a start period of 20 seconds, and `HealthOnFailure=restart`. A
  wedged portal now restarts, because `Restart=always` alone could not see it.
- **Tests (Added)**: `tests/unit/web_portal/test_dashboard_readiness.py` holds 14
  cases. They prove `/ready` returns 503 for a read-only data directory, that the
  body names the failed check, that `/ready` returns 200 when the directory is
  writable, and that `/health` answers while every disk call raises.
- **SQLite query (Changed)**: the database check runs
  `SELECT count(*) FROM sqlite_master`. That query reads a real page, so SQLite
  validates the file header. The first version ran `SELECT 1`, which answers from
  memory. A corrupt database therefore passed the check on the Linux build of
  SQLite, and the test caught the miss only in CI.
- **Deferred**: the `Containerfile`, the `Dockerfile`, and `compose.yml` still
  need a probe. Open pull request #1825 owns those three files today.

### Cap the output file list in a web portal run record (issue #1870)

- **Gap (Fixed)**: issue #1860 bounded `log_messages` and `debug_messages`, and
  it left `run["output_files"]` without a cap. One per-site export appends one
  distinct name for each site, so deduplication does not bound that list.
- **Output files (Changed)**: `output_files` is now a `collections.deque` with a
  `maxlen`. The deque drops the oldest name, so the operator still sees the most
  recent output.
- **Dropped count (Added)**: `dropped_output_file_count` counts every name the
  cap discarded. `_run_to_dict` and `_run_to_summary` report the count next to
  `dropped_log_count`.
- **Setting (Added)**: `PORTAL_RUN_OUTPUT_FILES_MAX` defaults to 500. An
  unusable value falls back to the default and logs a warning, which matches the
  three settings issue #1860 added. `deploy/.env.example` documents it.
- **Read boundary (Changed)**: `_run_to_dict` and `_publish_complete` copy the
  deque into a list, so the JSON response and the SSE event still encode.
- **Tests (Added)**: `tests/unit/web_portal/test_operation_output_files_cap.py`
  holds 11 tests. They cover the cap, the newest-name order, the duplicate name
  rule, the dropped count in the response, the two read boundaries, the default
  cap, and the warning for an unusable setting.

### Repair the container health probe command and add the compose probe (issues #1863, #1881)

- **Defect (Fixed)**: `deploy/misthelper.container` ran the probe with
  `curl --fail --silent --show-error`. The image installs `ca-certificates`,
  `openssh-server`, and `sudo` only, so the image holds no curl binary. The
  probe therefore failed on every call, and `HealthOnFailure=restart` restarted
  a healthy container in a loop.
- **Quadlet probe (Changed)**: `HealthCmd` now runs the Python interpreter that
  already runs the application. The command reads `WEB_PORT` and calls `/ready`.
  A non-200 response raises `HTTPError`, the command exits non-zero, and the
  runtime marks the container unhealthy.
- **Container probe (Added)**: `Containerfile` and `Dockerfile` define a
  `HEALTHCHECK` that calls `/ready` with the same Python command. A Quadlet
  build can drop the instruction when the image uses the OCI format, so the
  unit states the command as well.
- **Compose probe (Added)**: the `misthelper` service in `compose.yml` now
  carries a `healthcheck` block. It matches the pattern the ArangoDB service
  and the Redis service already use.
- **Readiness endpoint (Superseded)**: pull request #1893 landed the `/health`
  and `/ready` split for issue #1863 first. This change keeps that version of
  `web_portal/routes/dashboard.py` and supplies the container probe only.
- **Tests (Added)**: `tests/unit/test_container_health_probe.py` holds 12 tests.
  They prove that no probe command calls curl, that every probe targets
  `/ready`, and that the Quadlet unit keeps its timing keys and its restart key.

### Bound the web portal operation run registry (issue #1860)

- **Defect (Fixed)**: `OperationExecutor` kept every run in memory forever, and
  each run appended one dictionary for every log record the operation emitted.
  The portal runs as one long-lived Gunicorn worker, so the memory only rose
  until an out-of-memory kill interrupted a write to the data directory.
- **Run log (Changed)**: `log_messages` and `debug_messages` are now a
  `collections.deque` with a `maxlen`. The deque drops the oldest entry, so one
  high-volume run cannot fill the worker memory.
- **Dropped count (Added)**: `dropped_log_count` counts every entry the cap
  discarded. `_run_to_dict` and `_run_to_summary` report the count, so the
  operator sees that the portal truncated the run log.
- **Registry cap (Added)**: `OperationExecutor._prune_runs` keeps the most
  recent finished runs and drops the rest. It also drops a finished run that
  passed the retention period. It never evicts a pending or a running
  operation, and it follows the `PortalEventBus._cleanup_stale_subscribers`
  pattern.
- **Settings (Added)**: `PORTAL_RUN_LOG_MAX_ENTRIES` defaults to 2000,
  `PORTAL_RUN_HISTORY_MAX` defaults to 50, and `PORTAL_RUN_RETENTION_SECONDS`
  defaults to 3600. An unusable value falls back to the default and logs a
  warning. `deploy/.env.example` documents all three.
- **Tests (Added)**: `tests/unit/web_portal/test_operation_run_registry_caps.py`
  holds 11 tests. They cover the registry cap, the per-run log cap, the
  protection of an active run, the retention period, the dropped count in the
  response, and the fallback for an unusable setting.
### Store an opaque session id and unblock the auth event loop (issues #1859, #1858)

- **Cookie (Fixed)**: the `mist_session` cookie held the raw Mist API token. A
  reader of that cookie gained the full Mist privileges of the operator, outside
  this application and outside its audit log. The cookie now holds an opaque
  identifier that `secrets.token_urlsafe(32)` produces.
- **Token storage (Added)**: `SessionStore` in
  `mist-ops-platform/src/shared/services/session_store.py` keeps the Mist token in
  a server-side record. The record uses Redis when Redis answers, and a
  process-local map when Redis does not answer. `_extract_token` reads the token
  from that record, so no route reads a token from a client.
- **Secure flag (Added)**: the cookie now sets `Secure` and `HttpOnly`. The new
  `SESSION_COOKIE_SECURE` setting defaults to a true value. Set the value to
  `false` only for local work over plain HTTP.
- **Logout (Fixed)**: `DELETE /api/v1/auth/session` now deletes the server-side
  record. A logout therefore ends the session, which the old code could not do.
- **Event loop (Fixed)**: the Mist `/api/v1/self` lookup ran inside an `async def`
  dependency and blocked the event loop for one round trip to `api.mist.com`. The
  lookup now runs in a worker thread through `anyio.to_thread.run_sync`.
- **Verification cache (Fixed)**: the privilege cache was never active, because
  both call sites passed `redis=None`. The auth middleware now caches the
  verification result on the session record for 5 minutes, so a repeat request
  makes no second call to Mist.
- **Cache key (Changed)**: the Redis privilege key derived from `hash(token)`,
  which Python randomizes for each process. The key now derives from a SHA-256
  digest, so it stays stable across every worker and across a restart.
- **Status codes (Changed)**: an unreachable Mist API now returns 503 through the
  new `MistApiUnavailableError`. Only a token that Mist rejects returns 401. A
  transient upstream fault no longer logs every operator out.
- **Settings (Added)**: `mist-ops-platform/src/shared/config/settings.py` supplies
  the `AppSettings` object that six modules already imported. Every default value
  lives in a module constant, because a `slots` dataclass turns a class attribute
  into a descriptor instead of the default value.
- **Tests (Added)**:
  `mist-ops-platform/tests/unit/api/test_session_security.py` holds 18 tests. They
  prove the cookie differs from the token, the cookie carries `Secure`, a deleted
  identifier returns 401, the lookup runs off the event loop, and a second request
  inside the cache period makes no second upstream call. The suite reports
  18 passed, and the wider `tests/unit` run reports no new failure.

### Bind the web portal IP allowlist to the peer address (issue #1857)

**Warning:** This entry contains a breaking change. If you run the portal behind
a reverse proxy and you set `PORTAL_ALLOWED_IPS`, the portal answers 403 to every
client after this upgrade. The allowlist now reads the socket peer address, which
is the address of the proxy. Set `PORTAL_TRUSTED_PROXIES` to the address of the
proxy, or to the CIDR range that holds the proxy, before you upgrade. A portal
that runs without a proxy needs no action.

- **Defect (Fixed)**: `SecurityMiddleware._get_client_ip` read the
  client-supplied `X-Forwarded-For` header and fed that value into the
  `PORTAL_ALLOWED_IPS` check. No reverse proxy sits in front of the portal, so a
  blocked caller reached every portal operation with one extra header.
- **Peer address (Changed)**: `SecurityMiddleware._get_peer_ip` returns
  `request.remote_addr`, and the allowlist judges that address. A caller cannot
  forge the socket peer address.
- **PORTAL_TRUSTED_PROXIES (Added)**: this new setting names the reverse proxy
  addresses that the portal trusts. The default value is empty. The portal reads
  the forwarded header only when the peer address matches an entry. An entry is
  a plain address or a CIDR range.
- **Forwarded entry (Changed)**: `SecurityMiddleware._resolve_client_ip` reads
  the rightmost entry of the header, because that entry is the address the
  trusted proxy observed. A caller controls every entry to its left.
- **Audit trail (Changed)**: the block message now names the client address and
  the peer address, so the record always holds the real source.
- **PortalConfigLoader.parse_networks (Added)**: this shared parser replaces
  `_parse_allowed_ips`. It reads both settings and names the setting in every
  log message. It reports the position of an invalid entry, not the text of that
  entry, because an environment value can hold a secret.
- **Documentation (Added)**: `deploy/.env.example` documents
  `PORTAL_ALLOWED_IPS` and `PORTAL_TRUSTED_PROXIES` in one section.
- **Tests (Added)**: `tests/unit/web_portal/test_config_ip_allowlist.py` holds 15
  cases. A forged header from a blocked peer returns 403. The same header from a
  trusted proxy peer sets the client address.
### Remove the spawned Edge profile directory on teardown (issue #1862)

- **Defect (Fixed)**: the address audit spawned a debuggable Edge into a new
  temporary profile directory on every run in auto mode. The teardown path
  stopped the process and left the directory on disk. The path was a local
  variable, so no later code could find it. An Edge profile that completed a
  Mist login holds the cache, the cookies, and the local storage of that
  session, so every run leaked one directory of session material.
- **SpawnedBrowser (Added)**: `src/site/address_audit/ui_geocoder.py` holds a
  frozen dataclass with a `process` field and a `profile_dir` field.
  `spawn_debuggable_browser` returns it, so the caller owns both.
- **Teardown (Changed)**: `MistUIGeocoder._terminate_spawned` stops the browser,
  waits for the exit, then removes the profile directory. Edge holds a file lock
  on the profile until the process exits. A stop that passes the 10-second
  budget leads to a kill, and the removal then runs.
- **Safety (Added)**: a failed removal logs a WARNING and never raises, and
  `close()` stays idempotent. One DEBUG line names the removed path, so an
  operator can confirm the cleanup.
- **Tests (Added)**: `tests/unit/site/address_audit/test_ui_geocoder_profile_cleanup.py`
  holds nine cases that use a fake process object, so no test starts a browser.

### Stop the gitignore rule that hid a source package and a security finding (issue #1778)

- **Defect (Fixed)**: line 244 of `.gitignore` held an unanchored `config/` rule.
  That rule matched every nested directory of that name, so it hid the source
  package `mist-ops-platform/src/shared/config/` from git and from every
  scanner. Eight tracked modules import that package, and none of it was
  tracked.
- **Ignore rules (Changed)**: `/config/` and `/configs/` now carry a leading
  slash, so each rule matches the repository root only. The four negation lines
  that undid the over-broad rule are gone, because they became inert.
- **Source package (Added)**: `__init__.py`, `constants.py`, and `settings.py`
  of `mist-ops-platform/src/shared/config/` now enter git. Pull request #1905
  force-added the same three modules, so this change keeps that version of each
  module and removes the ignore rule that made the force-add necessary.
- **B104 (Fixed)**: the `api_host` default was `0.0.0.0`, which binds the API to
  every interface. Bandit reported it as a MEDIUM `hardcoded_bind_all_interfaces`
  finding that no gate could see. The current settings module defines no bind
  address, so the finding is gone. A guard test fails again if a bind-all default
  returns.
- **Suppression (Removed)**: the inert `# noqa: S104` note is gone. The root
  ruff configuration does not select the `S` family, and bandit reads `# nosec`
  only, so that note suppressed nothing and misled a reader.
- **Tests (Added)**: `tests/unit/test_config_package_tracked.py` holds six cases.
  They read text only, so they need no optional dependency. They fail again if
  an unanchored rule returns, if the package leaves the checkout, if a field
  default binds to every interface, or if an inert `# noqa: S` note returns.

### Route the Starlink status line through the GPS precision control (issue #1838)

- **Defect (Fixed)**: `StarlinkStatusWidget._status_part_location` built its
  status line with a hardcoded `:.4f` format on the latitude and on the
  longitude. That path never called `_format_gps_coordinate`, so it ignored both
  the `GPS_PRECISION_DECIMALS` default and the operator opt-in that issue #1737
  added. Four decimal places locate a driveway, and the line reaches stdout,
  where a redirect or a recorded SSH session can capture it into a support
  bundle.
- **Cause (Recorded)**: pull request #1834 fixed the two paths that CodeQL
  reported as alert 190 and alert 191. Both sat in `_dump_diagnostics_location`.
  CodeQL never flagged the status line, so the alert-scoped triage never reached
  it. The module then held two different rules for one value.
- **Status line (Changed)**: the method now calls `_format_gps_coordinate` for
  each coordinate. One rule governs every coordinate the module prints. The
  default rounds to about 100 meters, and `STARLINK_DASHBOARD_EXACT_GPS` returns
  the exact value through this path too.
- **Delivery (Recorded)**: pull request #1849 landed the code change and the
  test cases first. This entry records the fix in the changelog, because #1849
  merged without one. The source and the tests here match the merged version.
- **Tests (Added)**: four cases in
  `tests/unit/test_starlink_dashboard_startup_and_gps.py`. Three prove the
  behavior of the status line: it rounds on a default run, it returns the exact
  pair after the opt-in, and it returns `None` when the terminal reports no
  location. The fourth scans the module source and fails when any coordinate
  format field states a literal decimal count, so a new caller cannot reopen the
  same gap. All three behavior tests fail against the unfixed source. All 11
  tests in the file pass against the fix.

### Replace the assert runtime guards in the SSH package (issue #1720)

- **Defect (Fixed)**: four runtime guards used `assert`. The interpreter removes
  every `assert` when it runs with `-O`, so each guard disappeared in an
  optimized run and the code continued past a condition that must stop it.
- **Guards (Changed)**: `ShellExecutor.execute`, `EnhancedSSHRunner._execute_direct`,
  `_exec_with_pty`, and `_exec_without_pty` now raise `ValueError` from an
  explicit `if` check. This copies the pattern that issue #889 established.
- **Suppressions (Removed)**: the `# nosec B101` comments are gone, because the
  rule no longer fires. Those comments had hidden the guards from the triage
  scan of issue #889.
- **Message (Added)**: `_NO_ACTIVE_CONNECTION_MSG` holds one message per module,
  so the two packages report the same words.
- **Tests (Changed)**: the two cases that expected `AssertionError` now expect
  `ValueError` and match the message. All 180 SSH tests pass under `python` and
  under `python -O`.

### Re-probe a database backend that recovered after boot (issue #1830)

- **Defect (Fixed)**: `DatabaseRouter` latched the ArangoDB, Redis TimeSeries,
  and Redis JSON availability flags in `__init__` and never probed again. A
  backend that recovered after boot stayed unused for the life of the process,
  and a backend that died after boot was still reported as healthy.
- **Re-probe (Added)**: `DatabaseRouter._reprobe` answers the live state of one
  backend. It reconnects when the backend is marked down and the back-off window
  expired. `RECONNECT_WINDOW_SECONDS` holds that window at 30 seconds, so one
  dead backend costs at most one connect attempt per window.
- **health_check (Changed)**: it now returns the re-probed state instead of the
  boot-time flags. A `/health` endpoint therefore reports a recovered backend as
  available without a restart.
- **Write path (Changed)**: `_write_arango`, `_write_redis`, `_write_redis_json`,
  and `ingest_stats_batch` re-probe before they fall back to CSV. An export that
  starts before the database container finishes its start sequence now reaches
  the database once it answers.
- **Write failure (Changed)**: a write that raises marks its backend as
  unavailable and logs `backend_lost`. The health report then matches what the
  write path observes.
- **Resource leak (Fixed)**: `close()` never closed the Redis JSON writer, and a
  reconnect never closed the writer it replaced. Both paths now release the
  handle first.
- **Tests (Added)**: `TestRouterReprobe` and `TestRouterCloseRedisJson` in
  `tests/unit/test_router.py`. All seven new cases fail against the pre-fix
  router.
### Route polyglot writes by host reachability, not by the container boundary (issue #1824)

- **Fixed**: `DataExporter._is_standalone_mode` returned true whenever
  MistHelper ran outside a container. Every ArangoDB and Redis write was
  dropped on a workstation. `DatabaseRouter._csv_fallback` answered
  `success=True`, so the loss left no trace in the log.
- **Changed**: the decision now follows a TCP reachability probe against the
  configured `ARANGO_HOST` and `REDIS_HOST`. MistHelper writes to the polyglot
  backend whenever one of the two answers, inside or outside a container.
- **Added**: `src.db.polyglot_hosts_unreachable` runs the probe and records
  both verdicts through the `polyglot_host_probe` structured log event. The
  probe uses a TCP connect, not a DNS lookup, because a hostname can resolve
  while no service listens. The timeout is 0.5 seconds for each host.
- **Added**: `DataExporter._standalone_probe` caches the verdict for the life
  of the process, so an export pays the probe cost one time.
- **Added**: one `WARNING` at the fallback point names the dropped polyglot
  write and the two environment variables that fix it.
- **Unchanged**: `MISTHELPER_STANDALONE` still forces the mode. The
  `--standalone` flag still sets that variable.
- **Tests (Added)**: `TestPolyglotHostProbe` in `tests/unit/test_standalone.py`
  and the rewritten `TestIsStandaloneMode` in
  `tests/unit/export/test_data_exporter.py`.

### Add five organization-scoped search operations, menus 230 to 234 (issues #1386, #1385, #1383, #1382, #1379)

- **Menu 230 (Added)**: `searchOrgWirelessClientSessions`. Spec 878, issue #1386.
- **Menu 231 (Added)**: `searchOrgWirelessClientEvents`. Spec 877, issue #1385.
- **Menu 232 (Added)**: `searchOrgWanClients`. Spec 875, issue #1383.
- **Menu 233 (Added)**: `searchOrgWanClientEvents`. Spec 874, issue #1382.
- **Menu 234 (Added)**: `searchOrgSystemEvents`. Spec 879, issue #1379.
- **New module (Added)**: `src/export/org_search_exporter.py`. It mirrors
  `SiteSearchExporter` for the organization scope. Every one of these endpoints
  takes a session and an organization and returns a paginated row set, so one
  shared helper runs the resolve, fetch, and persist sequence.
- **Category (Added)**: these five are `safe`, not `interactive_safe`, because
  they resolve the organization from the cached context rather than prompting
  for a site. The `--test` run therefore covers them.
- **Primary keys (Unchanged)**: all five operationIds already had a strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`, so this change adds none.
- **Tests (Added)**: `tests/unit/export/test_org_search_exporter.py`. The
  per-menu bindings are checked by a parametrized case, so each entry is proven
  to call its own endpoint and write its own file.

### Add five site-scoped search operations, menus 225 to 229 (issues #1401, #1393, #1391, #1396, #1412)

- **Menu 225 (Added)**: `searchSiteOspfStats` searches the OSPF neighbor
  statistics for a site. Spec 893, issue #1401.
- **Menu 226 (Added)**: `searchSiteDeviceLastConfigs` searches the last device
  configurations for a site. Spec 885, issue #1393.
- **Menu 227 (Added)**: `searchSiteDeviceConfigHistory` searches the device
  configuration history for a site. Spec 883, issue #1391.
- **Menu 228 (Added)**: `searchSiteDiscoveredSwitches` searches the discovered
  switches for a site. Spec 887, issue #1396.
- **Menu 229 (Added)**: `searchSiteZoneSessions` searches the zone sessions for a
  site. Spec 904, issue #1412.
- **Zone type prompt (Added)**: `searchSiteZoneSessions` puts a zone type in the
  URL path, so menu 229 asks for one before it calls the endpoint. The SDK
  accepts only `zones` and `rssizones`. A wrong value returns 404 rather than an
  empty result, so the prompt rejects anything else before any request goes out.
  An empty answer means `zones`. The chosen value also appears in the output
  filename, which keeps the two zone families in separate artifacts.
- **Shared helper (Changed)**: `_run_site_search` accepts an optional
  `extra_args` tuple. Menu 229 is the only caller that needs it today. Every
  other menu entry is unchanged.
- **Primary keys (Unchanged)**: all five operationIds already had a strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`, so this change adds none.
- **Tests (Added)**: the parametrized binding table covers the four plain
  entries. Menu 229 has its own tests for the default value, the explicit
  `rssizones` value, the rejected value, and the fact that a bad zone type stops
  the flow before the operator is asked to pick a site.

### Add five more site-scoped search operations, menus 220 to 224 (issues #1411, #1408, #1392, #1394, #1403)

- **Menu 220 (Added)**: `searchSiteWirelessClientEvents` searches the wireless
  client events for a site. Spec 903, issue #1411.
- **Menu 221 (Added)**: `searchSiteWanClients` searches the WAN clients for a
  site. Spec 900, issue #1408.
- **Menu 222 (Added)**: `searchSiteDeviceEvents` searches the device events for a
  site. Spec 884, issue #1392.
- **Menu 223 (Added)**: `searchSiteDevices` searches the devices for a site.
  Spec 886, issue #1394.
- **Menu 224 (Added)**: `searchSiteRogueEvents` searches the rogue access point
  events for a site. Spec 895, issue #1403.
- **Shared helper (Changed)**: `src/export/site_search_exporter.py` gained five
  more thin menu entries. The prompt, fetch, and persist sequence is unchanged,
  because every one of these endpoints takes a session and a site and returns a
  paginated row set.
- **Primary keys (Unchanged)**: all five operationIds already had a strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`, so this change adds none.
- **Tests (Added)**: the parametrized binding table in
  `tests/unit/export/test_site_search_exporter.py` covers the five new entries.
  Each entry is proven to call its own endpoint and write its own file, so the
  shared helper cannot silently point two menus at one endpoint.

### Add five site-scoped search operations, menus 215 to 219 (issues #1387, #1388, #1389, #1390, #1405)

- **Menu 215 (Added)**: `searchSiteAlarms` searches the alarms for a site. Spec
  879, issue #1387.
- **Menu 216 (Added)**: `searchSiteAssets` searches the tracked assets for a
  site. Spec 880, issue #1388.
- **Menu 217 (Added)**: `searchSiteBgpStats` searches the BGP peer statistics for
  a site. Spec 881, issue #1389.
- **Menu 218 (Added)**: `searchSiteCalls` searches the call quality records for a
  site. Spec 882, issue #1390.
- **Menu 219 (Added)**: `searchSiteSkyatpEvents` searches the Sky ATP security
  events for a site. Spec 897, issue #1405.
- **New module (Added)**: `src/export/site_search_exporter.py`. The five
  endpoints take the same arguments and return the same shape, so one shared
  helper runs the prompt, fetch, and persist sequence. Each menu entry supplies
  only the SDK callable and the naming. That avoids five copies of the same code.
- **Primary keys (Unchanged)**: all five operationIds already had a strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`, so this change adds none.
- **Tests (Added)**: `tests/unit/export/test_site_search_exporter.py`. The
  per-menu bindings are checked by a parametrized case, so each entry is proven
  to call its own endpoint and write its own file. The shared branches are
  covered once.

### Add five site-scoped read operations, menus 210 to 214 (issues #1416, #1417, #1418, #1419, #1406)

- **Menu 210 (Added)**: `getSiteAssetsOfInterest` exports the BLE beacons that
  match an Asset or an AssetFilter for a site. Spec 670, issue #1419.
- **Menu 211 (Added)**: `getSiteAssetFilter` reads one asset filter by
  identifier. Spec 668, issue #1418.
- **Menu 212 (Added)**: `getSiteAsset` reads one asset by identifier. Spec 667,
  issue #1417.
- **Menu 213 (Added)**: `getSiteApplicationList` exports the applications a site
  recognizes for WxLAN tag rules. Spec 666, issue #1416.
- **Menu 214 (Added)**: `searchSiteSystemEvents` searches the system events for a
  site. Spec 898, issue #1406.
- **New modules (Added)**: `src/export/site_asset_exporter.py`,
  `src/export/site_application_list_exporter.py`, and
  `src/export/site_system_events_exporter.py`. Every operation is read-only and
  writes through `DataExporter.write_with_format_selection`, so the CSV, SQLite,
  and ArangoDB backends all work.
- **Primary keys (Added)**: `getSiteAssetFilter`, `getSiteAsset`, and
  `getSiteApplicationList` gained a strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`. `getSiteAssetsOfInterest` and
  `searchSiteSystemEvents` already had one, so this change reuses it.
- **Wrong SDK module paths (Fixed)**: the source specs named a mistapi module
  that does not exist for `getSiteApplicationList` and `searchSiteSystemEvents`.
  The real modules are `mistapi.api.v1.sites.wxtags` and
  `mistapi.api.v1.sites.events`. Issue #1757 tracks the same defect across 245
  other endpoint specs.
- **Tests (Added)**: `tests/unit/export/test_site_asset_and_events_exporters.py`
  covers the happy path, the empty result, the declined site prompt, the blank
  identifier, and the API error path for all five operations.

### Stop writing partial API token values to the log (issue #1710)

- **Token previews (Changed)**: `_redact_tokens()` now returns a count in the
  form `2 token(s) found, values hidden`. It no longer builds the
  `first4...last4` preview. Six log call sites that built the same preview
  inline now print a positional label instead. The call sites sit in
  `_check_token_rate_limit()` and in the token availability loop. They run at
  DEBUG, INFO, and WARNING level, so a normal run wrote 8 characters of a live
  credential into `data/script.log` before this change.
- **Token identity (Changed)**: `_check_token_rate_limit()` takes a third
  argument named `label`. The caller passes a secret-free identifier such as
  `2/3`. An operator still tells one token from another by that position, which
  the per-token log lines already carried.
- **No hash of a secret (Security)**: an earlier draft of this work hashed each
  token with SHA-256. CodeQL raised `py/weak-sensitive-data-hashing` at high
  severity, because SHA-256 is not a computationally expensive hash for
  credential material. The final change removes the hash and passes no token
  into any digest function. No secret now reaches a hash, a log, or a report.
- **Why this matters (Security)**: a log file travels with a support bundle, and
  menu 101 builds a support package for each site. A reader of that bundle must
  never see a credential fragment. Eight characters also reduce the search space
  for an attacker who already holds part of a token.
- **CodeQL follow-up (Recorded)**: this change clears the 2 alerts that
  `py/clear-text-logging-sensitive-data` reported in `MistHelper.py`. The query
  reports 19 more alerts in five other files, which this change does not touch.
  Those need their own triage.
- **Tests (Added)**: added `TestTokenPreviewCarriesNoSecret` to
  `tests/unit/test_credential_preflight.py`. The tests assert the count message,
  the empty list case, a clean probe log, and a distinct label for each token in
  the availability loop. Each test also asserts that neither the leading 4
  characters nor the trailing 4 characters of a token reach the output.
- **Tests (Changed)**: `test_no_raw_token_leaks_in_failure_message` no longer
  accepts the `first4...last4` preview. It now asserts the count message and
  that no leading or trailing token character appears.

### Reconcile the speckit records with the merged work (issues #1667, #1668, #891)

- **Spec 1025 (Fixed)**: marked tasks T024, T025, T026, and T027 complete. The
  code for both fixes sits on `main` today. The dedup set sits at line 862 of
  `src/org/org_synthetic_probes_manager.py` and the single load time call site
  sits at lines 2715 to 2721. The `NOTE(1025-US2)` comment sits at lines 1697
  to 1698. The two test files report 107 passed. Task T039 stays open, because
  it needs a live organization. Issues #1667 and #1668 are ready to close.
- **Spec 1033 (Fixed)**: reopened tasks T003, T004, T005, and T006. The record
  claimed that User Story 1 shipped, but pull request #1723 reverted that edit
  before the merge. The pylint ignore flag still sits at line 303 of
  `.github/workflows/ci.yml`. The record now states the revert and the measured
  backlog of 683 pylint messages in `src/maps`, `src/ssh`, and `src/ui`. Issue
  #891 holds that work.
- **Spec 1033 (Added)**: closed tasks T017 through T028 and T030 through T034
  with the evidence from pull request #1723 and pull request #1726.
- **CodeQL counts (Corrected)**: replaced the stale claim of 0 alerts for both
  removed queries. A read of `refs/heads/main` on 2026-08-04 reports 0 alerts
  for `py/stack-trace-exposure` and 21 open alerts for
  `py/clear-text-logging-sensitive-data`. Issue #1710 owns the fix for the 21
  alerts.
- **Spec 1032 (Fixed)**: marked task T052 complete against merged pull request
  #1717. Task T044 stays open, because it needs a second reviewer.
- **Spec status headers (Changed)**: replaced the `Draft` status in specs 1025
  through 1033 with the real delivery state and the merged pull request number.
  A reader can now tell a planned feature from a shipped feature without a
  search of the pull request history.

### Add menu operation 209 for getSiteBeacon (issue #1420, spec 671)

- **New endpoint workflow (Added)**: added `SiteClientExporter.get_site_beacon`
  and menu option `209` to execute
  `mistapi.api.v1.sites.beacons.getSiteBeacon` with safe prompts for `site_id`
  and `beacon_id`.
- **Persistence contract (Added)**: normalized single-record payloads to a
  list and persisted via
  `DataExporter.write_with_format_selection(..., api_function_name="getSiteBeacon")`
  using deterministic filenames per site/beacon pair.
- **Resilience (Added)**: applied adaptive retry/backoff behavior for 429
  responses via `RateLimitingUtils.get_rate_limited_delay` before retrying.
- **Registry and key strategy (Added)**: registered menu option `209` as
  `interactive_safe` in `OperationRegistry` and added `getSiteBeacon`
  natural-key strategy (`id`) to
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- **Tests (Added)**: added unit coverage for prompt validation, happy path,
  empty payload, 429 retry, and non-429 failure handling; added integration
  menu dispatch smoke test for option `209`.

### Lower the vulture confidence floor to 70 (issue #892)

- **Dead code floor (Changed)**: lowered the vulture confidence floor from 90 to
  70 in `.github/workflows/ci.yml`. The file holds that value at two sites. Line
  35 is the `workflow_call` input default and line 51 is the `env` fallback.
  Both sites now read `'70'`. A caller that uses `workflow_call` therefore runs
  the same floor as a pull request.
- **Measurement (Recorded)**: this checkout reports 0 findings at confidence 90,
  0 at 80, 0 at 70, and 306 at 60. The floor stops at 70, because the step from
  70 to 60 crosses a false positive cliff. Issue #1703 removes the dynamic
  `mh.*` lookup that drives most of that rate. A later slice re-measures
  confidence 60 after that issue lands.
- **Repeat delivery (Fixed)**: the entry below this one recorded the same change
  for pull request #1723, but that change never reached `main`. The revert of
  the issue #891 work restored the whole `ci.yml` file, which silently undid
  this floor change in the same file. The squash merge still read `Closes #892`
  and closed the issue. This entry records the real delivery, on a branch that
  carries this issue alone.

### Resolve the Redis time-series entity identifier from a fallback list (issue #990)

- **Entity identifier (Fixed)**: `RedisTimeSeriesWriter` read the entity
  identifier from one field only. A record that omitted that field landed under
  the text `unknown`. Many unrelated records then shared one time-series key.
  The writer now walks the ordered fallback list `device_id`, `site_id`,
  `org_id`, `mac`, `id` when the strategy field holds no usable value.
- **Existing keys (Unchanged)**: a record that carries a usable value in the
  strategy field produces the same key as before. The key still holds three
  parts that a colon separates. The text `unknown` stays as the final fallback,
  because `RedisJSONWriter._build_key` depends on a stable key length.
- **Usable value (Added)**: a new test accepts the number `0` as an identifier.
  A plain truth test rejected `0` and sent the record to the fallback list.
- **Resolution summary (Added)**: each extraction call emits one debug event
  that reports three counts. The counts name the records that used the strategy
  field, a fallback field, and the sentinel. The writer emits no log line for a
  single record, so a large export produces one summary line.

### Remove the vulture and CodeQL gate silencers (issues #892, #893)

- **Pylint scope (Attempted and reverted)**: the removal of
  `--ignore=maps,ssh,ui` from the pylint step was tried and reverted, because it
  fails the gate on Linux. A Windows checkout with pylint 4.0.6 reports 806
  messages and a score of 9.77 with the flag, and 1339 messages and a score of
  9.71 without it. Both Windows runs exit 0. The `ubuntu-latest` runner reports
  **9.41** for the same commit, which falls below the `--fail-under=9.5`
  threshold and exits 30. See pull request #1723 for the failing run. The flag
  stays in place. Issue #891 now carries the correct measurement and the real
  remaining work, which is to raise the Linux score above 9.5 before the flag
  can come off. A local run is not a safe proxy for this gate.
- **Dead code floor (Attempted and lost)**: this entry claimed that the vulture
  confidence floor moved from 90 to 70. The claim is wrong. The change never
  reached `main`. The revert of the pylint work restored the whole `ci.yml`
  file, and that revert undid this floor change too, because both changes edit
  the same file. The `ci.yml` change that pull request #1723 delivered is nine
  added comment lines and no deleted line. The squash merge still read
  `Closes #892` from the first commit message and closed the issue. The entry at
  the top of this release records the real delivery. The lesson is that a
  file level revert reverts every change in that file, so a partial revert needs
  a line level edit.
- **CodeQL exclusions (Removed)**: deleted the whole `query-filters` block from
  `.github/codeql/codeql-config.yml`. The block excluded
  `py/clear-text-logging-sensitive-data` and `py/stack-trace-exposure`. The
  first exclusion carried an eight line rationale that claimed the tool never
  logs an actual secret. Issue #1710 contradicts that claim, because it found a
  partial API token value in `data/script.log`. The second exclusion carried no
  rationale at all. This work deletes the key itself, because an empty
  `query-filters` key parses as `null` and a `null` value can stop the whole
  analysis. The file now holds the `name` key alone.
- **CodeQL result (Recorded)**: the CodeQL analysis on pull request #1723
  completed successfully with both exclusions removed, and the code scanning
  API reported **0 alerts** for the merge reference at that time. A later read
  of `refs/heads/main` on 2026-08-04 reports the true post merge counts, because
  the default branch analysis runs after the merge. `py/stack-trace-exposure`
  reports **0 alerts**, so its verdict is `clean` and its removal stays.
  `py/clear-text-logging-sensitive-data` reports **21 open alerts** across six
  files, so its verdict is `real` and its removal also stays. The counts are
  `src/site/address_audit/address_resolver.py` 10, `src/capture/packet_capture.py`
  4, `MistHelper.py` 2, `src/ssh/ssh_runner_manager.py` 2, `starlink_dashboard.py`
  2, and `src/device/_utility_commands_action.py` 1. Issue #1710 owns the fix for
  these 21 alerts. The removal of the exclusion is what made them visible, which
  is the outcome that this work wanted. Any future proposal to restore an
  exclusion must carry a review record that states the review date, the evidence
  link, the reason, and the next review trigger.
- **Gate comments (Added)**: the pylint step and the dead code step each hold a
  new comment. The comment states the review date, the measurement, and the
  condition that starts the next review. The pylint comment records the Linux
  and Windows score difference, so the next reader does not repeat the mistake.
- **Out of scope (Note)**: `.github/quality-gates-portable.yml` is a template
  copy for other repositories. It still holds the confidence value `'90'` at
  two sites. GitHub never runs that file in this repository, so this work
  leaves it unchanged.

### Drop the bandit `-ll` severity suppression and clear all 54 findings (issue #889)

- **Security gate (Changed)**: removed `-ll` from the bandit step in
  `.github/workflows/ci.yml`. The command is now
  `bandit -c pyproject.toml -r .`. The flag had hidden every finding below
  MEDIUM severity from both the report and the exit code, so a LOW finding
  could never fail the build.
- **Finding triage (Fixed)**: cleared all 54 in-scope findings across 21 files.
  The split is 15 real fixes and 39 annotated suppressions. No suppression is
  bare. Each one names the rule and states why the finding is a false positive.
  Rules cleared: B101 (18), B105 (11), B603 (9), B110 (7), B404 (4), B607 (3),
  B107 (1), and B606 (1).
- **Assert removal (Fixed)**: converted 7 asserts that guarded real behavior
  into runtime checks that raise. An assert disappears under `python -O`, which
  had made `validate_template` a silent no-op in that mode.
- **Silent exception handlers (Fixed)**: five `try`/`except`/`pass` blocks now
  log the error, so it no longer disappears without a trace. One of the five
  also narrowed its catch to `(redis_lib.RedisError, OSError, ValueError)`. The
  other four keep a broad catch, because a unit test proves a documented
  fail-open contract at each one. The remaining two findings in this group took
  an annotated suppression.
- **Executable resolution (Changed)**: `starlink_dashboard.py` and
  `tools/compliance_analyzer/engine.py` now resolve an executable through
  `shutil.which` before they run it, which removes the partial-path risk.
- **Measurement note**: a local Windows run still reports 51 findings. Every one
  sits in `tools/test_quality_analyzer/fixtures/` or in an untracked file.
  `[tool.bandit].exclude_dirs` already excludes the fixture path, but a Windows
  scan does not match it, because bandit compares the configured forward-slash
  path against a backslash path. A clean CI checkout reports zero.

### Remove both pip-audit `--ignore-vuln` entries after review (issue #890)

- **CVE suppression review (Removed)**: deleted `--ignore-vuln CVE-2026-4539`
  and `--ignore-vuln PYSEC-2025-183` from the pip-audit step in
  `.github/workflows/ci.yml`. A run of `pip-audit -r requirements.txt` with no
  ignore flags reports "No known vulnerabilities found" against the current
  dependency set, which resolves cryptography 49.0.0 and PyJWT 2.13.0. Both
  packages are transitive, and cryptography arrives through paramiko. Neither
  suppressed identifier fires any longer, so both entries were dead weight that
  could have masked a future finding under the same identifier.
- **Review policy (Added)**: the replacement comment states the review date and
  the evidence, and it requires three facts before anyone adds a new
  `--ignore-vuln` entry. Those facts are the date of the review, a link to the
  upstream tracker, and the condition that triggers the next review.

### Set STE precedence over caveman compression and add an `ste-writing` skill (issue #1714)

- **Writing standards (Changed)**: added the same precedence block to every
  file that states a caveman rule or a Simplified Technical English rule.
  Simplified Technical English now outranks caveman compression in every
  conflict. Caveman keeps its cut of filler, pleasantries, and hedging, and
  loses the permission to drop an article, to write a fragment, or to swap a
  synonym. Files changed: `.github/copilot-instructions.md`,
  `.github/instructions/caveman.instructions.md`, `agents.md`, `CLAUDE.md`,
  and `documentation/ASD-STE100_writing-guide.md`.
- **Caveman default level (Changed)**: the default level moves from `full` to
  `lite`. The `lite` level is the only level that keeps the articles and the
  complete sentences that Simplified Technical English Rules 4.5 and 4.2
  require.
- **Agent skill (Added)**: `.github/skills/ste-writing/SKILL.md` holds the
  eight core rules, the repair for each of the 13 linter rule identifiers, the
  three-part warning structure, and the self-check command. Before this change,
  the 700-line writing guide loaded only when an agent chose to open it.
- **Verification**: every changed Markdown file passes
  `python -m tools.ste_linter --min-score 80`.

### #887 slice 4/N: drop `capture` from pydocstyle `match-dir` exclusion (issue #887)

- **Pydocstyle scope narrowing (Changed)**: removed `capture` from the
  `[tool.pydocstyle].match-dir` negation list in `pyproject.toml`. Audit
  confirmed `src/capture/` (13 files) already reports zero Google-style
  violations, so the entry was dead weight; CI now enforces Google-style
  docstrings on the subtree going forward. Continues the #887 workstream of
  shrinking the pydocstyle exclusion list one subtree at a time; next slice
  targets `websocket` (15 files).

### #887 slice 3/N: drop `inventory` from pydocstyle `match-dir` exclusion (issue #887)

- **Pydocstyle scope narrowing (Changed)**: removed `inventory` from the
  `[tool.pydocstyle].match-dir` negation list in `pyproject.toml`. Audit
  confirmed `src/inventory/` (8 files) already reports zero Google-style
  violations, so the entry was dead weight; CI now enforces Google-style
  docstrings on the subtree going forward. Continues the #887 workstream of
  shrinking the pydocstyle exclusion list one subtree at a time; next slice
  targets `capture` (13 files).

### #887 slice 1/N: drop `troubleshooting` from pydocstyle `match-dir` exclusion (issue #887)

- **Pydocstyle scope narrowing (Changed)**: removed `troubleshooting` from
  the `[tool.pydocstyle].match-dir` negation list in `pyproject.toml`.
  Audit confirmed `src/troubleshooting/` (4 files: `__init__.py`,
  `interactive_test_runner.py`, `marvis_troubleshoot_utils.py`,
  `troubleshoot_utils.py`) already reports zero Google-style violations
  under `pydocstyle --convention=google`, so the exclusion was dead weight.
  `pydocstyle src/` remains clean after the regex change.

### #886 Phase 2 slice 108/N: retire `print()` in `src/export/site_anomaly_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 28 `print()` calls in
  `src/export/site_anomaly_exporter.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. The
  `Export Site Anomaly Events:` banner routes through `logger.info`;
  operator-abort notices (`! No site selected. Exiting.`,
  `! No device selected. Exiting.`, `! No client selected. Exiting.`,
  `! No potential anomaly metrics found ...`, per-metric/per-client
  `! 0 ... exported ... (no data available)` notices, and per-metric
  `! Error retrieving ...` notices) route through `logger.warning`;
  `! Error exporting site/device/client anomaly events` operator notices
  route through `logger.error` (paired with the existing `logger.exception`
  stack-trace logs); informational `! No <metric> ... available` notices
  route through `logger.info`. Pre-existing `logging.info`/`logging.warning`/
  `logging.error`/`logging.exception` calls across `site_anomaly_events`,
  `device_anomaly_events`, `client_anomaly_events`,
  `_discover_site_anomaly_metrics`, `_fetch_one_anomaly_metric`,
  `_export_anomaly_data`, `_anomaly_collect_metrics`, and `_anomaly_export`
  were rebound to the module-scoped `logger` for namespace consistency;
  intentional `logging.getLogger(<mistapi_logger_name>)` reads used by
  `_anomaly_suppress_mistapi_loggers`/`_anomaly_restore_loggers` were
  preserved verbatim. Test suite migrated 16 assertions from
  `capsys.readouterr().out` to `caplog.text` with explicit
  `caplog.set_level(..., logger="src.export.site_anomaly_exporter")`.

### #887 slice 8/N: drop `export` from pydocstyle `match-dir` exclusion (issue #887)

- **Quality gate (Changed)**: removed `export` from the
  `[tool.pydocstyle] match-dir` negation regex in `pyproject.toml`, so
  `src/export/` (34 files) is now scanned by `pydocstyle
  --convention=google`. Audit surfaced 13 D205/D212/D415 violations
  across 3 files, all fixed:
  - `src/export/const_definitions_exporter.py:25` — D212 on
    `ConstDefinitionsExporter` class docstring; moved summary onto the
    first line so the multi-line summary starts immediately after the
    opening quote.
  - `src/export/org_inventory_exporter.py` — 4 sites: D212+D415 on the
    `OrgInventoryExporter` class docstring (line 48) and D205+D212 on
    `inventory` (line 73), `devices` (line 97), and
    `gateways_with_site_info` (line 673). Reflowed each so the summary
    ends with a period on the first line, followed by a blank line and
    the extended description.
  - `src/export/site_anomaly_exporter.py:32` — D212+D415 on the
    `SiteAnomalyExporter` class docstring; collapsed the header line
    onto the first line and added the terminating period.
  This is the final pydocstyle slice under #887; `match-dir` still
  excludes `capture`, `inventory`, and `troubleshooting`, which are
  tracked as separate follow-ups.

### #887 slice 5/N: drop `websocket` from pydocstyle `match-dir` exclusion (issue #887)

- **Quality gate (Changed)**: removed `websocket` from the
  `[tool.pydocstyle] match-dir` negation regex in `pyproject.toml`, so
  `src/websocket/` is now scanned by `pydocstyle --convention=google`.
  Audit surfaced two D107 (missing `__init__` docstring) violations,
  both fixed:
  - `src/websocket/polling/message_router.py:45` — `MessageRouter.__init__`
    now documents why the five constructor args are packed into the frozen
    `_RouterCtx` holder (immutable snapshot, cheaper attribute access,
    stays within the project's argument-count limits).
  - `src/websocket/polling/result_collector.py:121` — `ResultCollector.__init__`
    documents the four-arg `WebSocketManager` wiring (results dict, its
    lock, logger, debug flag) and why they collapse into the frozen
    `_CollectorDeps`.
  Next slice (6/N) targets `site` (17 files) per the #887 slicing plan.

### #887 slice 6/N: drop `site` from pydocstyle `match-dir` exclusion (issue #887)

- **Quality gate (Changed)**: removed `site` from the `[tool.pydocstyle]
  match-dir` negation regex in `pyproject.toml`, so `src/site/` is now
  scanned by `pydocstyle --convention=google`. Audit surfaced 4 violations
  across 2 files, all fixed:
  - `src/site/bulk_radius_wlan_config_manager.py:31` — D212 (multi-line
    summary must start on the first line); reflowed the class docstring
    so the summary sits directly after the opening quote.
  - `src/site/address_audit/audit_engine.py:678` — D205/D209/D415 in
    `_classify`; split the summary from the parenthetical exclusion note
    into a separate paragraph and moved the closing quote to its own line.
  Next slice (7/N) targets `gateway` (21 files) per the #887 slicing plan.

### #887 slice 2/N: drop `analytics` from pydocstyle `match-dir` exclusion (issue #887)

- **Pydocstyle scope narrowing (Changed)**: removed `analytics` from the
  `[tool.pydocstyle].match-dir` negation list in `pyproject.toml`. Added
  Google-style docstrings to `TelemetryEmitter.__init__`,
  `TelemetryEmitter.__enter__`, and `TelemetryEmitter.__exit__` in
  `src/analytics/telemetry_emitter.py` (previously the only three D107/D105
  violations in the subtree). Post-fix `pydocstyle --convention=google
  src/analytics/` reports zero violations across all 7 files, so the subtree
  is now enforced by CI going forward. Continues the #887 workstream of
  shrinking the pydocstyle exclusion list one subtree at a time; next slice
  targets `inventory` (8 files).

### #887 slice 7/N: drop `gateway` from pydocstyle match-dir exclusion (issue #887)

- **Docstring quality (Changed)**: dropped `gateway` from the
  `[tool.pydocstyle] match-dir` negation regex so 21 `src/gateway/**.py`
  files are now scanned under the Google convention. Fixed 4 pre-existing
  violations across 2 files:
  - `src/gateway/wan2_migration_manager.py:137` — D212 on
    `WAN2MigrationManager` class docstring (reflowed summary onto the
    opening `"""` line).
  - `src/gateway/wan_probe_device_override_manager.py:76` — D212 on
    `WANProbeDeviceOverrideManager` class docstring (same fix).
  - `src/gateway/wan_probe_device_override_manager.py:110` — D212 + D415
    on `configure` classmethod docstring (reflowed summary and added
    terminal period after `"(DESTRUCTIVE)"`).
  Post-audit `pydocstyle --convention=google src/gateway/` reports 0
  violations. Next slice 8/N targets `export` (34 files); after that the
  match-dir negation drops back to `tests|\\.` only, closing the
  pydocstyle strand of #887.

### #886 Phase 2 slice 107/N: retire `print()` in `src/gateway/device_template_cloner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 27 `print()` calls in
  `src/gateway/device_template_cloner.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Operator
  banners, site/gateway selection prompts, template-selection listings, and
  success notices route through `logger.info`; empty-list notices
  (`No sites found`, `No gateway devices found`), retry prompts on empty or
  duplicate template names, and invalid hardware-selection messages route
  through `logger.warning`; clone failure notices (device-config fetch
  failure, template-creation failure, unexpected-exception handler) route
  through `logger.error`. Pre-existing `logging.info`/`logging.warning`/
  `logging.error` audit-trail calls throughout the module were rebound to
  the module-scoped `logger` for namespace consistency. Each converted call
  carries the standard `# WHY: preserve operator notice verbatim; route
  through logger for capture/redirection.` comment above the emission.
- **Test migration (Changed)**:
  `tests/unit/gateway/test_device_template_cloner_extended.py` swapped 10
  `capsys`-based stdout assertions to `caplog` with
  `caplog.set_level(<level>, logger="src.gateway.device_template_cloner")`
  scoping so operator-facing notices are captured from the logger channel
  the code now emits on. `tests/unit/gateway/test_device_template_cloner.py`
  contained no `capsys` references and needed no changes. All 58 tests
  across the two files remain green.
### #886 Phase 2 slice 106/N: retire `print()` in `src/refactors/serial_cc/start_site_scan_capture.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 26 `print()` calls in
  `src/refactors/serial_cc/start_site_scan_capture.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Intro
  banner, band/bandwidth menus, loop-mode menu, summary block, and
  conflict-cancel notice use `logger.info`; validation notices
  (`! Invalid channel`, `! Invalid bandwidth`, `! Invalid <label>`,
  `! WARNING` conflict lines) use `logger.warning`. Pre-existing
  `logging.debug`/`logging.info`/`logging.warning`/`logging.error` calls
  across `_select_band`, `_prompt_channel`, `_select_bandwidth`,
  `_prompt_bounded_int`, `_build_payload`, `_list_existing_captures`,
  `_confirm_conflict_override`, `_select_ap`, `_finalize_and_run`, and
  `execute` were rebound to the module-scoped `logger` for namespace
  consistency.

### #886 Phase 2 slice 105/N: retire `print()` in `src/maps/_plotly_viewer.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 26 `print()` calls in
  `src/maps/_plotly_viewer.py` with the pre-existing module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Dash-import
  failure notices (`Dash not available`, install hint) route through
  `logger.warning`; interactive-viewer banner lines, Dash startup banner,
  KeyboardInterrupt/stop notice, and static-HTML fallback path notices
  (`! Map saved to:`, `! Opening in browser...`, `! Creating static HTML
  map...`) route through `logger.info`; the Dash server `except Exception`
  operator notice routes through `logger.error` (paired with the existing
  `logger.exception` stack-trace log). Each converted call carries the
  standard `# WHY: preserve operator notice verbatim; route through logger
  for capture/redirection.` comment above the emission.
- **Namespace rebind (Changed)**: 21 pre-existing `logging.info` /
  `logging.debug` / `logging.warning` / `logging.exception` calls scattered
  through the file (mesh links, virtual/BLE beacon counts, browser auto-open
  trace, Dash import trace, background image validation, device orientation
  debug, Dash startup / stop / error, static map save/browser-launch trace)
  were rebound to the module-scoped `logger` so all lifecycle diagnostics
  share the `src.maps._plotly_viewer` namespace and can be filtered as one
  unit.

### #886 Phase 2 slice 104/N: retire `print()` in `src/device/_utility_commands_selection.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 26 `print()` calls in
  `src/device/_utility_commands_selection.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Banner and
  row output uses `logger.info`; validation notices (`!`, `[WARNING]`) use
  `logger.warning`. Two pre-existing `logging.error`/`logging.debug` calls
  were rebound to the module-scoped `logger` for namespace consistency.
- **Test channel switch (Changed)**: converted `capsys`-based assertions
  covering `_validate_device_type`, `_select_site_and_device`,
  `_print_interface_list`, `_get_interface_selection`, and
  `_select_network_from_device` to `caplog` scoped at
  `src.device._utility_commands_selection`; other tests continue to use
  `capsys` where they exercise helpers outside this module.

### #886 Phase 2 slice 103/N: retire `print()` in `src/analytics/site_inventory_health_analyzer.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 26 `print()` calls in
  `src/analytics/site_inventory_health_analyzer.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. The module
  is a collection of `@staticmethod` display helpers, so a module logger is
  the correct fit (no `self.logger` available). All 26 sites route through
  `logger.info` because they emit operator-facing report banners, section
  headers, per-site totals, and sample listings for the site-inventory
  health report — none are validation warnings or errors. Each converted
  call carries the standard `# WHY: preserve operator notice verbatim; route
  through logger for capture/redirection.` comment above the emission.
  Pre-existing `logging.info(...)` audit-trail lines were left untouched.
- **Test migration (Changed)**:
  `tests/unit/analytics/test_site_inventory_health_analyzer.py` swapped
  `capsys` for `caplog` in `test_analyze_exits_when_org_missing`, pinning
  the capture to the SUT logger via
  `_MODULE_LOGGER = "src.analytics.site_inventory_health_analyzer"` and
  `caplog.at_level(logging.WARNING, logger=_MODULE_LOGGER)`. All 4 tests
  remain green with no behavioural drift.
- **Compliance**: ruff T201/T203 clean on the module; `black`, `ruff`, and
  `pytest tests/unit/analytics/test_site_inventory_health_analyzer.py`
  (4 passed) all green locally.

### #886 Phase 2 slice 102/N: retire `print()` in `src/capture/client_pcap_downloader.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 23 `print()` calls in
  `src/capture/client_pcap_downloader.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. The class
  `ClientPacketCaptureDownloader` does not hold `self.logger`, so a module
  logger was introduced immediately after the `_OUTPUT_ROOT` constant. Step
  banners, table headers, per-row summary lines, and per-file "Downloaded"
  status route to `logger.info`; input-validation notices (invalid row
  number, out-of-range row, bad MAC) route to `logger.warning`; API fetch
  failures and HTTP/transport download errors route to `logger.error`.
  Column-formatted table output was preserved by converting f-string
  alignment specifiers (`{x:>4}`, `{x:<32}`) to `%`-format equivalents
  (`%4d`, `%-32s`). Each converted call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` comment.
- **Tests**: no test migration required — the existing suite
  (`tests/unit/capture/test_client_pcap_downloader.py`, 28 tests) does not
  use `capsys`; all assertions rely on `MagicMock` / `patch` and continue
  to pass after the migration.
- **Rationale**: Menu 197's client packet-capture downloader is an
  interactive four-step wizard; operator-facing progress, validation, and
  download-outcome text needs to flow through the logging pipeline so it
  is captured to disk and can be redirected in headless/batch contexts.
  This slice removes another 23 `T201` violations from `src/` without
  changing user-visible output content.

### #886 Phase 2 slice 101/N: retire `print()` in `src/refactors/serial_cc/start_site_client_capture_wireless.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 25 `print()` calls in
  `src/refactors/serial_cc/start_site_client_capture_wireless.py` with a
  module-scoped `logger = logging.getLogger(__name__)`. The service class
  exposes only `@staticmethod` / `@classmethod` entry points and therefore
  has no `self.logger` to inject, so a module logger was the appropriate
  choice. All emissions are `%`-style deferred to satisfy G004, and each
  converted call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` comment.
- **Level assignment (Changed)**: banner and prompt-header lines (intro
  banner, client/AP option menus, loop-mode header, capture-summary block)
  now emit at `logger.info`; validation misses ("no client MAC provided",
  "invalid MAC", "invalid `<int>`", range violations) emit at
  `logger.warning`. No error/debug channels are used in this module.
- **Format-string constants (Changed)**: the four module-level `_INVALID_*_MSG`
  constants were tightened from f-style `{value}` placeholders to `%s`
  placeholders so the logger call sites can pass positional arguments and
  keep formatting deferred.
- **Tests (Unchanged)**: `tests/unit/serial_cc/test_start_site_client_capture_wireless.py`
  exercises the flow via `MagicMock` on the manager and prompt helpers, so
  no `capsys` → `caplog` migration was required. All 3 tests remain green.
### #886 Phase 2 slice 100/N: retire `print()` in `src/websocket/polling/completion_detector.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 20 `print()` calls in
  `src/websocket/polling/completion_detector.py` with the injected
  `self.logger` (a `logging.Logger` supplied via `__init__`, so no
  module-scoped logger is added). All emissions are `%`-style deferred to
  satisfy G004. Of the 20 prints, 15 were duplicates that sat directly
  alongside pre-existing `self.logger.debug(...)` calls emitting the same
  content — those prints were deleted and the surviving logger calls were
  left in place. The remaining 5 standalone diagnostic prints in
  `_trace_generic_scan`, `_trace_service_ping`, `_trace_mac_missing_header`,
  `_trace_mac_idle_pending`, and `_trace_arp_patterns` were converted to
  `self.logger.debug(...)` with the standard `# WHY: preserve operator
  notice verbatim; route through logger for capture/redirection.` comment.
  Level assignment is uniformly DEBUG because every call site is gated by
  the detector's `debug_mode` flag and emits low-level scan tracing rather
  than user-visible status.
- **Test migration (Changed)**:
  `tests/unit/websocket/polling/test_completion_detector.py` dropped the
  `capsys` fixture from ~30 helper-level tests covering the generic-scan,
  ping-statistics, service-ping, MAC-table, and ARP-table strategies, and
  now asserts on `caplog.text` after
  `caplog.at_level(logging.DEBUG, logger=_LOGGER_NAME)` where
  `_LOGGER_NAME = "test.completion_detector"` matches the name passed into
  the injected logger by the test's `_make_detector` factory. Each debug-OFF
  test asserts `caplog.text == ""` (helper silent); each debug-ON test
  asserts the expected substring is present. Non-debug tests (strategy
  chain, count helpers, parse helpers, integration paths) are unchanged.
- **Compliance**: ruff T201/T203 clean on the module; `black`, `ruff`, and
  `pytest tests/unit/websocket/polling/test_completion_detector.py` (88
  passed) all green locally.

### #886 Phase 2 slice 99/N: retire `print()` in `src/refactors/data_directory_checker.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 20 `print()` calls in
  `src/refactors/data_directory_checker.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. The four
  `_print_*` helpers were reclassified per severity: `_print_error_header`
  and `_print_error_footer` (banner + path + impact sentence + closing
  separator, 6 sites) route to `logger.error`; `_print_container_guidance`
  (10 sites) and `_print_local_guidance` (4 sites) route to `logger.info`
  because they emit operator remediation steps rather than errors. Each
  converted call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` comment. Module
  and class docstrings were updated to reflect that operator-facing output
  now flows through the stdlib `logging` root logger (per #886) instead of
  raw `print()`.
- **Test migration (Changed)**: `tests/unit/refactors/test_data_directory_checker.py`
  dropped the `capsys` fixture from the three `_handle_permission_error`
  branches (local guidance, container guidance, podman-marker container
  detection) and now asserts on `caplog.text` after
  `caplog.at_level(logging.INFO, logger="src.refactors.data_directory_checker")`.
  All 9 tests remain green with no behavioural drift.

### #886 Phase 2 slice 98/N: retire `print()` in `src/network/routing_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 20 `print()` calls in
  `src/network/routing_utils.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and level-appropriate `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Banners /
  progress notices (`-> Executing...`, `-> Establishing WebSocket...`,
  `-> WebSocket connected...`, `-> WebSocket connection closed`,
  `-> Proceeding with standard command`) route through `logger.info`;
  connection/subscription/no-data warnings (`! Failed to establish...`,
  `! Failed to subscribe...`, `! No <label> data received`, `Available result
  keys: ...`) route through `logger.warning`; operator error banner
  (`! WebSocket ... operation failed: ...`) routes through `logger.error`;
  every `[DEBUG] ...` trace routes through `logger.debug`. Each converted
  call carries the standard `# WHY: preserve operator notice verbatim; route
  through logger for capture/redirection.` comment above the emission. The 7
  existing tests in `tests/unit/test_routing_utils.py` were migrated from
  `capsys` to `caplog` with `caplog.set_level(logging.<LEVEL>,
  logger="src.network.routing_utils")`; all remain green.

### #886 Phase 2 slice 97/N: retire `print()` in `src/gateway/_wan2_variable_device.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 19 `print()` calls in
  `src/gateway/_wan2_variable_device.py` with a module-scoped
  `logger = logging.getLogger(__name__)` and `logger.info(...)` emissions using
  `%`-style deferred formatting to satisfy G004. All 19 sites are step banners
  (Step 7 header, optimization/fetch progress notices, apply/revert-mode
  headers, no-devices / found-devices / intro / summary / fast-mode /
  sequential-mode banners), so every conversion maps to `logger.info`.
  Preserved implicit-concatenation strings were merged into single format
  arguments. Each converted call carries the standard `# WHY: preserve
  operator notice verbatim; route through logger for capture/redirection.`
  comment above the emission. Existing 101 tests in
  `tests/unit/test_wan2_variable.py` remain green (no `capsys` assertions
  targeted these prints).

### #886 Phase 2 slice 96/N: retire `print()` in `src/device/_utility_commands_websocket.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 19 `print()` calls in
  `src/device/_utility_commands_websocket.py` with module-scoped `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Level
  heuristic: banner/session/streaming/results notices map to `logger.info`;
  no-response / no-session / connect-fail / subscribe-fail / no-results /
  cancelled notices map to `logger.warning`; command-failed and streaming-
  failed error paths map to `logger.error`. Each converted call carries the
  standard `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` comment above the emission.
- **Test migration (Changed)**: migrated 12 `capsys` assertions in
  `tests/unit/test_device_utility_commands.py` to `caplog` against
  `_WS_LOGGER = "src.device._utility_commands_websocket"` so the assertions
  follow the emissions across the print→logger boundary.

### #886 Phase 2 slice 95/N: retire `print()` in `src/websocket/manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 18 `print()` calls in
  `src/websocket/manager.py` with module-scoped `logger.*` emissions using
  `%`-style deferred formatting to satisfy G004. Level heuristic: credential
  missing/timeout warnings map to `logger.warning`; connection/subscription
  failures map to `logger.error`; `[DEBUG]` gated echoes map to `logger.debug`;
  success/status banners map to `logger.info`. Every migrated line carries the
  standard verbatim WHY comment. Also removed a redundant `self.logger.debug`
  call in `_debug_log_sub` that duplicated the module-level `logger.debug`
  (same logger object → double emission).
- **Tests (Changed)**: migrated 24 tests in
  `tests/unit/websocket/test_manager.py` from `capsys` to `caplog`, with a
  module-level `_MANAGER_LOGGER = "src.websocket.manager"` constant driving
  `caplog.set_level(logging.DEBUG, logger=_MANAGER_LOGGER)` calls. Preserved
  targeted `patch.object(...)` sites that validate specific logger call
  interactions (root `logging.error`, instance `self.logger.warning/error/info`).
  71/71 unit tests pass.

### #886 Phase 2 slice 94/N: retire `print()` in `src/ssh/runtime/app_runner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 18 `print()` calls in
  `src/ssh/runtime/app_runner.py` with module-scoped `logger.*` emissions
  using `%`-style deferred formatting. Added
  `logger = logging.getLogger(__name__)` alongside the pre-existing
  `import logging`. Level heuristic: `.env`/CLI parameter hints in
  `_print_param_hints` and the `_resolve_commands` CSV-loaded banner map
  to `logger.info`; soft-fail notices in `_resolve_password`
  (password missing), `_validate_hosts` (invalid hosts + proceeding
  banner), `_validate_commands` (invalid commands + proceeding banner),
  `_run_multi_host` (thread-count clamp), and the `KeyboardInterrupt`
  branch of `run` map to `logger.warning`; hard-fail notices in
  `_validate_hosts` (no valid hosts remaining), `_check_required_params`
  (missing parameters), `_prompt_for_commands` (no commands specified),
  `_validate_commands` (no valid commands remaining), `_finalize_preflight`
  (invalid username), `_build_request` (no commands to execute), and the
  fatal-error branch of `run` map to `logger.error`. Each migrated call
  carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for capture/redirection.`
  annotation and preserves the exact user-visible text operators grep on.
  f-string interpolation was converted to positional `%s`/`%d` arguments
  to keep the file G004-clean.
- **Tests**: no `capsys` assertions target the migrated prints; the two
  vestigial `capsys` parameters in `tests/unit/test_ssh_runner.py`
  (`TestParseHostList.test_invalid_hosts_filtered`,
  `TestParseHostList.test_max_100_hosts`,
  `TestParseCommandList.test_max_50_commands`) belong to the
  `HostListParser` / `CommandListParser` suites and are untouched.
- **Gates**: `python -m black src/ssh/runtime/app_runner.py`,
  `python -m ruff check src/ssh/runtime/app_runner.py`, and
  `python -m pytest tests/unit/test_ssh_runner.py` (168 passed) all
  green.

### #886 Phase 2 slice 93/N: retire `print()` in `src/refactors/serial_cc/site_client_insights.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 18 `print()` calls in
  `src/refactors/serial_cc/site_client_insights.py` with module-scoped
  `logger.*` emissions using `%`-style deferred formatting to satisfy G004.
  Converted 11 `_MSG_*_TMPL` constants from `str.format()` `{name}` placeholders
  to positional `%s` / `%d` conversions so logger arguments defer formatting
  until the record is emitted. Level heuristic: banners, preview rows, refresh
  notices, per-metric progress, export-success counts, and confirmed selections
  map to `logger.info`; empty-list / invalid-index / invalid-MAC / skip-empty /
  no-metrics user warnings map to `logger.warning`; the top-level export
  exception branch in `_run_collect_and_export` maps to `logger.error`.
  Behavior otherwise unchanged.

### #886 Phase 2 slice 92/N: retire `print()` in `src/export/org_export_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 18 `print()` calls in
  `src/export/org_export_utils.py` with module-scoped `logger.*` emissions
  using `%`-style deferred formatting to satisfy G004. Level heuristic:
  banner/status/count/completion notices map to `logger.info`; empty-data
  and no-org guards map to `logger.warning`; error-handler paths map to
  `logger.error`. Each converted call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` comment above the emission.
- **Test migration (Changed)**: migrated 5 `capsys` assertions in
  `tests/unit/export/test_org_export_utils.py` to `caplog` against
  `LOGGER_NAME = "src.export.org_export_utils"` so the assertions follow
  the emissions across the print→logger boundary.

### #886 Phase 2 slice 91/N: retire `print()` in `src/export/site_device_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 18 `print()` calls in
  `src/export/site_device_exporter.py` with module-scoped `logger.*` emissions
  using `%`-style deferred formatting to satisfy G004. Level heuristic: empty-
  data / filter-miss / no-VC-payload user notices map to `logger.warning`;
  banners, per-site export counts, and VC summary lines map to `logger.info`;
  fetch/export exception branches in `device_stats`, `devices`, and
  `_export_vc_for_device` map to `logger.error`. Behavior otherwise unchanged.
- **Test capture migration (Changed)**: converted the 13 `capsys`-based stdout
  assertions in `tests/unit/export/test_site_device_exporter.py` to
  `caplog`-based assertions targeting `LOGGER_NAME = "src.export.site_device_exporter"`
  so the suite exercises the migrated logger pipeline; all 37 tests pass.

### #886 Phase 2 slice 90/N: retire `print()` in `src/device/_utility_commands_show.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 17 `print()` calls
  in `src/device/_utility_commands_show.py` with module-scoped `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Level
  heuristic: the "Destination host is required." validation-failure branch
  in `traceroute` maps to `logger.warning`; the 16 remaining "-> Fetching …"
  / "-> Running …" / "-> Monitoring …" / "-> Testing …" operator-progress
  banners across `traceroute`, `show_ospf_neighbors`, `show_ospf_interfaces`,
  `show_ospf_database`, `show_ospf_summary`, `resolve_dns`,
  `monitor_traffic`, `run_top`, `show_session`, `show_service_path`,
  `show_bgp_summary`, `show_arp_table`, `show_dhcp_leases`, `show_dot1x`,
  `show_evpn_database`, and `cable_test` map to `logger.info`. Three
  f-strings (traceroute host, monitor_traffic port, cable_test port) were
  rewritten to `%s` deferred formatting. Each converted call carries the
  standard `# WHY: preserve operator notice verbatim; route through logger
  for capture/redirection.` inline comment so future auditors can trace the
  origin.
- **Tests (Changed)**: migrated the `TestTraceroute.test_early_return_no_host`
  assertion in `tests/unit/test_device_utility_commands.py` from `capsys`
  stdout to `caplog.at_level("WARNING", logger="src.device._utility_commands_show")`
  + `assert "required" in caplog.text`. Full 194-test module passes locally
  under the new fixture.

### #886 Phase 2 slice 89/N: retire `print()` in `src/gateway/gateway_export_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 16 `print()` calls in
  `src/gateway/gateway_export_utils.py` with module-scoped `logger.*`
  emissions using `%`-style deferred formatting. Added
  `logger = logging.getLogger(__name__)` alongside the pre-existing
  `import logging` and paired `logging.error/warning` calls that already
  wrapped several of the migrated prints. Level heuristic: cache-status
  hits/misses in `_prime_management_ip_caches`, the 5-line completion
  banner in `_emit_management_ip_summary`, and the banner/step lines in
  `management_ips` and `templates` map to `logger.info`; the
  `"No gateway templates found for this organization."` operator notice
  (paired with the existing `logging.warning`) maps to `logger.warning`;
  the "Required CSV file not found" error notice (paired with the
  existing `logging.error`) maps to `logger.error`. Each migrated call
  carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for capture/redirection.`
  annotation and preserves the exact user-visible text operators grep on.
- **Test migration**: converted the two `capsys` assertions in
  `tests/unit/gateway/test_gateway_export_utils_extended.py` (banner +
  completion lines for `_emit_management_ip_summary`; empty-template
  warning for `templates`) to `caplog.at_level(...)` reads against the
  module logger. Full module suite: 62/62 green.

### #886 Phase 2 slice 81/N: retire `print()` in `src/ssh/runtime/interactive_mode.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 15 `print()` calls
  in `src/ssh/runtime/interactive_mode.py` with module-scoped `logger.*`
  emissions using `%`-style deferred formatting to satisfy G004. Level
  heuristic: interactive banner, separator, and status line ("Starting SSH
  session ...") route to `logger.info`; validation errors ("X  Hostname is
  required", "X  Port must be between 1 and 65535", "X  Timeout must be a
  valid number", etc.) and the empty-password abort message route to
  `logger.warning`. Each converted call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` inline comment so future auditors can trace the
  origin. Module-scoped `logger = logging.getLogger(__name__)` was added
  alongside the pre-existing `logging.info/debug` audit calls.
- **Tests (Unchanged)**: existing `TestInteractiveMode` suite (5 tests) in
  `tests/unit/test_ssh_runner.py` continues to pass unmodified; the suite
  asserts on boolean return values and `SingleCommandRunner.run` mock
  invocations rather than captured stdout, so no capsys→caplog migration
  was required.

### #886 Phase 2 slice 79/N: retire `print()` in `src/device/_utility_commands_clear.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 15 `print()` calls
  in `src/device/_utility_commands_clear.py` with module-scoped
  `logger.*` emissions using `%`-style deferred formatting to satisfy
  G004. Level heuristic: `>> …` progress lines and `[OK]` results map
  to `logger.info`; `[!] … failed:` handlers map to `logger.error`;
  "cancelled" / "… required" user-facing operator notices map to
  `logger.warning`. Each converted call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` inline comment so future auditors can trace the
  origin.
- **Tests (Changed)**: migrated 12 tests in
  `tests/unit/test_device_utility_commands.py` from `capsys` stdout
  assertions to `caplog` log-record assertions
  (`caplog.at_level(logging.LEVEL)` + `assert "…" in caplog.text`).
  Full 194-test module passes locally under the new fixtures.

### #886 Phase 2 slice 51/N: retire `print()` in `src/ssh/connection/connector.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 14 `print()` calls in
  `src/ssh/connection/connector.py` with `self.logger.*` emissions (or the
  new module-scoped `logger.*` for the `@staticmethod _paramiko_available`
  call sites that cannot access `self`), using `%`-style deferred
  formatting to satisfy G004. Added a module-scoped `logger =
  logging.getLogger(_LOGGER_NAME)` alongside the existing `_LOGGER_NAME =
  "ssh_runner_v2"` constant so the two static-method emissions land on the
  same unified SSH logger the rest of the class uses. Level heuristic:
  `>>` preflight banner and `[OK]` / `[INFO]` status lines map to
  `logger.info`; `[ERROR]` prefixed failure notices (`_fail_input`,
  paramiko-missing hint pair in `_paramiko_available`, host key enrollment
  failure, DNS resolution error, connection timeout, bad host key, auth
  failure, untrusted host key, generic SSH error, unexpected error) map to
  `logger.error`. Preserved: the pre-existing `import logging`,
  `logging.getLogger(_LOGGER_NAME)` fallback getter in `__init__`, the
  `logging.Logger` type annotations, and the `_LOGGER_NAME` constant.
  Each migrated call carries the standard `# WHY: preserve operator
  notice verbatim; route through logger for capture/redirection.`
  annotation and preserves the exact user-visible text operators grep on.
- **Test migration (Changed)**: none. `tests/unit/ssh/test_connector.py`
  and `tests/unit/test_ssh_host_key_tofu.py` were grepped for
  `capsys|capfd|readouterr` — no matches, so no stdout-based assertions
  needed conversion to `caplog`.
- **Rationale**: brings `src/ssh/connection/connector.py` into compliance
  with the module-by-module rollout of Ruff `T201` (`print()` retirement)
  tracked in issue #886. Routing through `self.logger` on the unified
  `"ssh_runner_v2"` logger keeps SSH connection lifecycle output
  capturable, redirectable, and consistent with the rest of the SSH
  runner v2 stack.

### #886 Phase 2 slice 88/N: retire `print()` in `src/capture/_packet_capture_tcpdump.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 16 `print()` calls
  in `src/capture/_packet_capture_tcpdump.py` with module-scoped
  `logger`-based emissions. Added `import logging` and
  `logger = logging.getLogger(__name__)` at module top. 15 calls became
  `logger.info(...)` (menu banner, section headers, filter items,
  filter-applied confirmations, custom-expression prompts, capture-format
  selector); the one validation-fallback message
  (`"\n! Invalid choice, using no filter"`) became `logger.warning(...)`.
  All argument interpolation uses `%`-style deferred formatting to
  satisfy G004. Each converted call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation.
- **No test migration needed**: existing
  `tests/unit/test_packet_capture.py::TestTcpdumpExpressionSelection`
  and `TestCaptureFormatSelection` assert only on return values via
  mocked `_get_input_utils`, not on stdout — the 256-test file passes
  unchanged.

### #886 Phase 2 slice 87/N: retire `print()` in `src/site/address_audit/audit_engine.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 5 `print()` calls
  in `src/site/address_audit/audit_engine.py` with `logger`-based emissions
  using `%`-style deferred formatting to satisfy G004. Also converted the
  14 module-level `logging.<level>(...)` calls to the new module-scoped
  `logger = logging.getLogger(__name__)` handle added at the top of the
  file. Preserved the six `logging.<Class>` type references
  (`logging.Filter`, `logging.LogRecord`, `logging.Handler`,
  `logging.StreamHandler`, `logging.FileHandler`) plus the
  `logging.getLogger()` root-logger lookup inside
  `_AddressAuditConsoleFilter`, since those are class references, not log
  emission calls. Each replaced `print()` carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation.
- **No test migration needed**: existing address-audit tests do not assert
  on captured stdout for the migrated lines, so no capsys→caplog rewrite
  was required.

### #886 Phase 2 slice 49/N: retire `print()` in `src/network/_routing_utils_payload.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 14 `print()` calls in
  `src/network/_routing_utils_payload.py` with `logger.debug` / `logger.info`
  / `logger.warning` emissions using `%`-style deferred formatting to
  satisfy G004. Added a module-scoped `logger = logging.getLogger(__name__)`
  at import time (the module previously used `logging.error(...)` against
  the root logger). Level heuristic: `[DEBUG]` prefixed diagnostics
  (`_post_device_command` POST URL, `_log_response_debug` HTTP status/body,
  `_invoke_ssr_route_api` mistapi request trace, `_log_ssr_response_debug`
  response type/data trace, and the `_extract_ssr_session_id` `[DEBUG]
  SSR Route Command Response` line) map to `logger.debug`; user-facing
  status lines (SSR/SRX device notice in `_invoke_ssr_route_api`, generic
  `Failed to execute SSR route command:` fallback in
  `_handle_ssr_api_error`, and the two positive-path `SSR route command
  executed successfully` / `Response received:` lines in
  `_extract_ssr_session_id`) map to `logger.info`; failure-path notices
  (`Error executing SSR route command:`, `SSR route command may have
  failed:`, and `No response data from SSR route command` in
  `_extract_ssr_session_id`) map to `logger.warning`. The pre-existing
  `logging.error("SSR route response is not a dict: %s", ...)` call in
  `_handle_ssr_api_error` was converted to `logger.error(...)` for module
  consistency. `traceback.print_exc()` was intentionally left untouched
  (not a `T201` target). Each migrated call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation and preserves the exact user-visible
  text and indentation operators grep on.
- **Test migration (Changed)**: `tests/unit/test_routing_utils.py` added
  `import logging` and migrated two `capsys.readouterr().out`-based
  assertions to `caplog` under
  `caplog.at_level(..., logger="src.network._routing_utils_payload")`:
  `TestExecuteSsrRouteCommand.test_api_exception` now asserts
  `"Error executing SSR route command"` in `caplog.text` at `WARNING`;
  `TestExecuteForwardingTableCommandDebug.test_debug_output` now asserts
  the `[DEBUG] POST URL` + `[DEBUG] HTTP Response Status` pair in
  `caplog.text` at `DEBUG`, with a `capsys.readouterr()` drain retained
  to consume stray parent-module stdout that is not part of this slice's
  migrated output. Full unit suite green: `pytest tests/unit/ -q` reports
  `8529 passed` (exit 0); black and ruff clean on both changed files.
- **Rationale**: brings `src/network/_routing_utils_payload.py` into
  compliance with the module-by-module rollout of Ruff `T201` (`print()`
  banned) and prepares the file for the eventual global flip in
  `pyproject.toml`.

### #886 Phase 2 slice 48/N: retire `print()` in `src/maps/_maps_matplotlib.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 14 `print()` calls in
  `src/maps/_maps_matplotlib.py` with `logger`-based emissions using
  `%`-style deferred formatting to satisfy G004. The module already declared a
  module-scoped `logger = logging.getLogger(__name__)`. Level heuristic:
  operator status lines ("Loading sites...", "Loading maps for site:",
  "Loading map:", "Found N sites", the matplotlib "Displaying map..." UX
  cue, the standalone-viewer banner title/subtitle plus the `=` rules,
  the "Launching viewer anyway" guidance, and the entity-count summary)
  map to `logger.info`; the two `[!]` fallback notices ("No sites found
  in organization" and "No maps found for site") map to `logger.warning`.
  Each replaced call carries the standard `# WHY: preserve operator
  notice verbatim; route through logger for capture/redirection.`
  annotation. `_print_banner` was whole-block rewritten so the top and
  bottom `=` rules pass the separator as a `%s` positional arg rather
  than embedding `"=" * _BANNER_WIDTH` in the format string.
  `_print_entity_counts` collapses its three concatenated f-strings into
  a single `logger.info(..., devices, zones, clients)` invocation. No
  test files import `_maps_matplotlib` and no capsys assertions target
  its output, so no test migration was required.

### #886 Phase 2 slice 86/N: retire `print()` in `src/maps/_maps_backup.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 4 `print()` calls in
  `src/maps/_maps_backup.py` with `logger`-based emissions using `%`-style
  deferred formatting to satisfy G004. The module already had a module-scoped
  `logger = logging.getLogger(__name__)`. The three summary lines in
  `_print_summary` (backup saved header, image line, summary counts) now go
  through `logger.info`; the exception-path CLI warning in
  `backup_map_geometry` now goes through `logger.warning`. Each replaced call
  carries the standard "preserve operator notice verbatim; route through
  logger for capture/redirection" WHY comment. No test files import
  `_maps_backup` directly and no capsys assertions target its output, so no
  test migration was required.

### #886 Phase 2 slice 85/N: retire `print()` in `src/maps/_maps_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the sole `print()` call in
  `src/maps/_maps_utils.py` (the CSV-save confirmation line
  `   Data saved to: <filepath>` emitted by
  `write_data_with_format_selection`) with a `logger.info` emission using
  `%`-style deferred formatting to satisfy G004. The module already declared
  `logger = logging.getLogger(__name__)` at line 17, so no logger import
  changed. Converted the shared `_PRINT_SAVED_TMPL` module constant from a
  `{filepath}` `str.format` template into the `%s` deferred-format
  equivalent (`"   Data saved to: %s"`) so the logger call passes the
  path as a positional arg (`logger.info(_PRINT_SAVED_TMPL, filepath)`),
  keeping the exact user-visible text and leading indent verbatim. The
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation.
- **No test migration needed**: `_maps_utils` has no `tests/` coverage that
  imports the module or asserts on captured stdout from
  `write_data_with_format_selection`. Ruff clean; black clean;
  `pytest tests/unit/maps/ -q` passes existing suite unchanged.

### #886 Phase 2 slice 84/N: retire `print()` in `src/export/org_inventory_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 12 `print()` calls in
  `src/export/org_inventory_exporter.py` with `logger.info(...)` emissions
  using `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)` (module previously imported
  `logging` for its `save_raw_json` helper but had no module logger).
  Level heuristic: all twelve migrated sites are operator-visible status
  lines (raw-JSON summary counts, VC-shell dashboard-parity note, menu 25
  section headers, weekly/summary/master output paths and row counts,
  device/gateway export confirmations, and the two "All Devices with Site
  and Address Info" / "Gateways with Site and Address Info" banners), so
  each maps to `logger.info`. Two helper docstrings updated from "Print" to
  "Log" to match the new emission channel: `_emit_vc_shell_dashboard_diff`
  and `_print_combined_inventory_summary` (function names left unchanged
  to avoid churn in call sites). Each migrated call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation.
- **Test migration (Changed)**: `tests/unit/test_org_inventory_exporter_helpers.py`
  migrated six `capsys.readouterr().out` assertions to `caplog.text` under
  `caplog.at_level(logging.INFO, logger="src.export.org_inventory_exporter")`.
  The affected tests cover `_emit_vc_shell_dashboard_diff` (three-line
  dashboard-parity note), `_log_combined_inventory_vc_summary` (silent
  path + emits-dashboard-note path), `_print_combined_inventory_summary`
  (weekly / summary / master output naming), and the flatten/sort/export
  device + gateway helpers. The "stays silent" assertion inverted from
  `capsys.readouterr().out == ""` to `"provisioned VC shells" not in
  caplog.text`, preserving the original behavioural contract now that the
  module writes to the logger instead of stdout.
- **Rationale**: brings `src/export/org_inventory_exporter.py` into
  compliance with the module-by-module rollout of Ruff `T201` (`print()`
  banned) and prepares the file for the eventual global flip in
  `pyproject.toml`.

### #886 Phase 2 slice 83/N: retire `print()` in `src/maps/_flask_viewer.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 8 `print()` calls in
  `src/maps/_flask_viewer.py` with `logger`-based emissions using `%`-style
  deferred formatting to satisfy G004. The module already had a module-scoped
  `logger = logging.getLogger(__name__)` at line 23 (used by route handlers)
  so no new imports were required. Six banner emissions in
  `_print_flask_viewer_banner` (separator, title, separator, server URL
  f-string, table-driven `_BANNER_LINES` loop, trailing separator) migrated
  to `logger.info(...)`; the `KeyboardInterrupt` branch of `_run_flask_server`
  migrated to `logger.info("\n\nFlask map viewer stopped by user")` and the
  broad-exception fallback migrated to `logger.warning("\n! Error running
  map viewer: %s", e)`. Each migrated call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation and preserves the exact byte layout
  operators grep on. The `_print_flask_viewer_banner` docstring updated
  from "Print the pre-launch..." to "Emit the pre-launch..." to reflect
  the migration; the function name is retained to avoid churning the one
  call site in `launch_flask_viewer`.
- **Test migration (Changed)**: none. No tests import or assert on
  `_flask_viewer`, `_print_flask_viewer_banner`, `launch_flask_viewer`, or
  `_run_flask_server` (grep across `tests/` returned zero matches).

### #886 Phase 2 slice 80/N: retire `print()` in `src/websocket/polling/result_combiner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 11 `print()` calls in
  `src/websocket/polling/result_combiner.py` with `logger`-based emissions
  using `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)` that coexists with the pre-existing
  per-request `request.logger` mirror calls (the caller-supplied structured
  logger continues to receive the info/debug lines it always has; the new
  module logger only carries the ten verbatim `[DEBUG] ...` diagnostic
  lines and the single `[DEBUG] WARNING: Final result is empty` notice
  that were previously written to stdout). Level heuristic: `debug` for
  the header trio (segment count, wait time, checks performed), the
  trailer preview block (length, fields, first/last 150 chars,
  session-complete banner, `"=" * 60` separator), and the per-segment
  trace line emitted only when `debug_mode and len(segments) > 5`;
  `warning` for the empty-payload sentinel. Each migrated call carries the
  standard `# WHY: preserve operator notice verbatim; route through
  logger for capture/redirection.` annotation, preserves the `[DEBUG]`
  prefix and `%r`/`%s`/`%d`/`%.2f` format specifiers, and continues to
  respect the `_VERBOSE_SEGMENT_THRESHOLD = 5` guard.
- **Test migration (Changed)**: `tests/unit/websocket/polling/test_result_combiner.py`
  migrated 7 tests from `capsys` to `caplog` with
  `_MODULE_LOGGER = "src.websocket.polling.result_combiner"` filter —
  three in `TestMergeSegments` (verbose-off with debug off, verbose-off
  at/below threshold, verbose-on above threshold) and four in
  `TestAbsorbRawChunk` (missing raw key, empty raw string, verbose trace
  index, verbose-off suppression). Each test asserts on
  `caplog.records` filtered by `r.name == _MODULE_LOGGER` and keeps
  `capsys.readouterr().out == ""` as a belt-and-suspenders guard that no
  stray stdout writes crept back in. Pre-existing tests that assert on
  the per-request logger via
  `caplog.set_level(..., logger="test.result_combiner")` are unchanged.
- Ruff clean; black clean;
  `pytest tests/unit/websocket/polling/test_result_combiner.py` = 34 passed.

### #886 Phase 2 slice 78/N: retire `print()` in `src/device/arp_command_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 11 `print()` calls in
  `src/device/arp_command_manager.py` with `logger`-based emissions using
  `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)`. Level heuristic mirrors the
  operational intent of each notice: `info` for the WebSocket-subscription
  banner (` Subscribing to WebSocket stream...`), the trigger-success
  notice (`! ARP command triggered. Session ID: <sid>`), the received-output
  header (`\n  ARP Output Received:\n`), the debug-mode full-table dump,
  the non-debug row-count summary (`! ARP output received with N rows.`),
  and the CSV write-success line (`! Saved N rows to <path>`); `warning`
  for the missing-credentials operator notice
  (` Mist host or API token not found in session or environment.`) and the
  empty-payload notice (` No ARP output received for this session.`);
  `error` for the trigger-failure status/response body pair
  (`! Failed to trigger ARP command: <status>` + response text) and the
  CSV-export exception notice (`! Failed to export ARP output to CSV: <e>`).
  Each migrated call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for capture/redirection.`
  annotation and preserves legacy `!`/`  `/`\n` prefixes verbatim in the
  format string.
- **Test migration (Changed)**: `tests/unit/device/test_arp_command_manager.py`
  migrated seven `capsys`-based assertions to `caplog` using a shared
  `_LOGGER_NAME = "src.device.arp_command_manager"` constant with
  `caplog.set_level(<LEVEL>, logger=_LOGGER_NAME)` gating and
  `any("<needle>" in r.getMessage() for r in caplog.records)` matching.
  Removed the vacuous `or True` assertion from
  `test_debug_prints_full_table` (the migration surfaces the debug table
  through the logger, so the fallback tautology is no longer needed and the
  `table.get_string.assert_called_once()` check now stands on its own).
  Suite result: 54 passed, ruff clean, black clean.

### #886 Phase 2 slice 77/N: retire `print()` in `src/analytics/data_collection_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 11 `print()` calls in
  `src/analytics/data_collection_manager.py` with `logger`-based emissions
  using `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)` (the module previously used only
  bare `logging.info/error` calls; the new logger routes the former print
  notices for capture/redirection while pre-existing action logs remain on
  the root `logging.*` API). Level heuristic: `info` for the three-line
  continuous-loop startup banner (` Starting continuous data collection
  loop...`, `   This will collect core organizational data every 5
  seconds`, `   Press CTRL+C to stop or create 'stop_loop.txt' file`), the
  per-iteration header (`\n  Loop iteration N - TIMESTAMP`), each
  exporter-step banner (`  Collecting site list...`, etc.), the
  successful-loop tally (`  Loop N completed successfully`), and the
  final `  Continuous data collection loop ended.` notice; `warning` for
  the KeyboardInterrupt notice (`\n  Continuous data collection loop
  stopped by user.`) and the per-iteration cycle-failure pair (`  Error
  in loop N: ...`, `  Continuing to next iteration...`); `error` for the
  fatal continuous-loop failure (`! Fatal error in continuous loop: ...`).
  Each migrated call carries the standard `# WHY: preserve operator
  notice verbatim; route through logger for capture/redirection.`
  annotation and preserves the exact original string (leading `\n`,
  double-space indentation, `! ` prefix) verbatim in the format string.
- **Test migration (capsys → caplog)**: migrated six assertions in
  `tests/unit/analytics/test_data_collection_manager.py` from
  `capsys.readouterr().out` to `caplog.records` with
  `caplog.set_level(logging.INFO|WARNING|ERROR,
  logger="src.analytics.data_collection_manager")`, matching the level of
  the migrated call under test. All 17 tests in the file pass.
- **No dead-code cleanup this slice**: no unused helpers or constants were
  produced by the migration; every migrated string is inlined at its call
  site. Ruff T20 clean on the target file; black clean; ruff full clean.

### #886 Phase 2 slice 76/N: retire `print()` in `src/ssh/batch/multi_host_runner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 10 `print()` calls in
  `src/ssh/batch/multi_host_runner.py` with `logger.info(...)` emissions
  using `%`-style deferred formatting to satisfy G004. The class already
  passed a `logger: logging.Logger` parameter into every staticmethod, so
  no module-scoped logger addition was required — the migration routed all
  former print notices through the caller-supplied logger. All migrated
  lines are `info`-level (startup banner `\n>> Starting SSH execution on
  N hosts (T threads)`, the multi-host execution summary block with
  `[STATUS] EXECUTION SUMMARY`, `Total hosts:`, `Successful: N [OK]`,
  `Failed: N [ERROR]`, the `Per-host logs:` hint, the optional
  `[OK] Successful hosts:` / `[ERROR] Failed hosts:` blocks, and the
  final `Multi-host execution completed: S/T successful` tally). Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation and
  preserves legacy prefixes, brackets, and leading `\n` newlines verbatim
  in the format string.
- **Dead-code cleanup**: removed the now-unused `_STARTUP_TEMPLATE`
  module-level constant (it used Python `{count}`/`{threads}` format
  tokens incompatible with `%`-style logger substitution, and after
  inlining the format string it had no remaining callers).
- **No test migration needed**: no dedicated `test_multi_host_runner.py`
  exists; cross-referencing tests in `tests/unit/ssh/` and
  `tests/unit/test_ssh_runner.py` do not assert on any of the migrated
  strings (existing `capsys` fixtures target `HostListParser` /
  `CommandListParser`, not `MultiHostRunner`). Ruff T20 clean on the
  target file; black clean; ruff full clean;
  `pytest tests/unit/ssh/ tests/unit/test_ssh_runner.py` = 359 passed.

### #886 Phase 2 slice 75/N: retire `print()` in `src/site/address_audit/address_corrector.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 10 `print()` calls in
  `src/site/address_audit/address_corrector.py` with `logger`-based emissions
  using `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)` (the module previously used only
  bare `logging.debug/info/warning` calls; the new logger routes the former
  print notices while pre-existing action logs remain on the root
  `logging.*` API). Level heuristic: `info` for the `No correctable
  addresses to push.` notice, the `--- Address write-back: N site(s) to
  review ---` banner, the safety warning, the per-site `Site:` / `BEFORE:`
  / `AFTER:` triple, the `  PUSHED.` confirmation, and the final
  `Write-back complete: P pushed, S skipped, F failed.` tally; `warning`
  for the two failure inline notices `  FAILED: <exc>` and
  `  FAILED: Mist rejected the update (check token permissions).`. Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation and
  preserves legacy prefixes and whitespace (`  FAILED:`, `  PUSHED.`,
  leading `\n` on banner/tally) verbatim in the message string.
- **No test migration needed**: `tests/unit/site/address_audit/test_address_corrector.py`
  asserts on outcome objects (`CorrectionOutcome.action`, `.error`), never
  on captured stdout — 10/10 tests pass unchanged. Ruff T20 clean on the
  target file; black clean; ruff full clean.

### #886 Phase 2 slice 74/N: retire `print()` in `src/websocket/diagnostics/common.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/websocket/diagnostics/common.py` with `logger`-based emissions using
  `%`-style deferred formatting to satisfy G004. Added a module-scoped
  `logger = logging.getLogger(__name__)` (the module previously used only
  bare `logging.debug/info/warning` calls; the new logger routes the former
  print notices while pre-existing action logs remain on the root
  `logging.*` API). Level heuristic: `info` for `[DEBUG] POST URL`,
  `[DEBUG] Headers`, `[DEBUG] HTTP Response Status/Body` (still gated by
  the CLI `debug_mode` flag), and for the `OTHER AVAILABLE FIELDS` header
  and per-field value lines; `warning` for `! Failed to issue`,
  `! Response:`, and `! No session ID returned` operator errors. Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation and
  preserves legacy prefixes (`[DEBUG]`, `!`, `OTHER AVAILABLE FIELDS:`)
  verbatim in the message string.
- **Test migration (Changed)**: migrated 8 tests in
  `tests/unit/websocket/diagnostics/test_common.py` from `capsys` to
  `caplog` using `caplog.set_level(<LEVEL>, logger="src.websocket.diagnostics.common")`
  and a `_messages()` helper that joins `caplog.records` for substring
  matching. 14/14 tests pass; ruff T20 clean; ruff full clean; black clean.

### #886 Phase 2 slice 73/N: retire `print()` in `src/ssh/shell_execution/shell_executor.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/ssh/shell_execution/shell_executor.py` with `logger`-based emissions
  using `%`-style deferred formatting to satisfy G004. Instance methods use
  the existing `self.logger` (info for `[STATUS] completed`, `[TIMEOUT]`,
  `[OK]` result summaries, and `!? channel closed`; warning for `[TIMEOUT]
  killing`, `[TIMEOUT] force closing`, and `- Attempt N failed` retry notice).
  The staticmethod `_maybe_print_drain_progress` cannot access `self`, so a
  new module-scoped `logger = logging.getLogger(__name__)` was added to route
  its `warning`-level drain-progress notice. Each migrated call carries the
  standard `# WHY: preserve operator notice verbatim; route through logger
  for capture/redirection.` annotation and preserves the legacy operator
  prefixes verbatim in the message string (`[STATUS]`, `[TIMEOUT]`, `[OK]`,
  `X `, `!? `, `- `).
- **Verification (Changed)**: 12/12 tests in `tests/unit/ssh/test_shell_executor.py`
  pass; ruff T20 clean; ruff full clean; black clean. No `capsys`/`readouterr`
  assertions in the shell_executor test file required migration (the file
  never asserted on `print()` output).

### #886 Phase 2 slice 72/N: retire `print()` in `src/ssh/config/env_loader.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/ssh/config/env_loader.py` with `logger.warning(...)` using `%`-style
  deferred formatting to satisfy G004. The module already exposes a
  module-scoped `logger = logging.getLogger(__name__)`, so all operator
  notices (invalid path, cannot access, too large, dotenv exception, encoding
  error, generic read error, OS read error, too many lines, invalid username)
  route through the existing logger. Each migrated call carries the standard
  `# WHY: preserve operator notice verbatim; route through logger for
  capture/redirection.` annotation and preserves the legacy `[WARNING]` prefix
  verbatim in the message string.
- **Test migration (Changed)**: migrated 8 tests in
  `tests/unit/ssh/config/test_env_loader_wave9.py` from `capsys` to `caplog`
  using `caplog.set_level(logging.WARNING, logger="src.ssh.config.env_loader")`
  and `any(SUBSTR in r.getMessage() for r in caplog.records)` assertions.
  30/30 tests pass; ruff T20 clean; ruff full clean; black clean.

### #886 Phase 2 slice 71/N: retire `print()` in `src/gateway/gateway_stats_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/gateway/gateway_stats_exporter.py` with `logging.info(...)` using
  `%`-style deferred formatting to satisfy G004. Covers the load-error branch
  in `_load_gateway_stats_for_conflicts`, the healthy-config short-circuit and
  export-summary lines in `_export_conflict_results`, and the per-conflict
  sample lines plus truncation trailer in `_display_conflict_samples`. Each
  migrated call carries the standard `# WHY:` annotation preserving legacy
  operator-visible text via the logger for capture/redirection.
- **Test migration (Changed)**: migrated 5 tests in
  `tests/unit/gateway/test_gateway_stats_exporter.py` from `capsys` to
  `caplog` with `caplog.at_level(logging.INFO)` wrappers and
  `record.getMessage()` substring assertions. 32/32 tests pass; ruff T20
  clean; ruff full clean; black clean.

### #886 Phase 2 slice 70/N: retire `print()` in `src/export/sites_by_ap_model_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/export/sites_by_ap_model_exporter.py` with `logging.info(...)` using
  `%`-style deferred formatting to satisfy G004. Covers the "Available AP
  models" header and numbered per-model listing in `_print_model_options`, the
  invalid-selection notice in `_resolve_model_choice`, the export-success
  summary line in `_finalize_ap_model_export`, and the menu banner plus the
  inventory-fetch / no-APs / site-detail-fetch / no-matching-sites operator
  notices in `export_sites_by_ap_model`. Each migrated call carries the
  standard `# WHY:` annotation preserving legacy operator-visible text via the
  logger.
- **Tests (Migrated)**: `tests/unit/export/test_sites_by_ap_model_exporter.py`
  swapped `capsys` for `caplog` across the six impacted tests
  (`test_prints_numbered_list_with_counts`, `test_out_of_bounds_returns_none`,
  `test_zero_selection_returns_none`, `test_non_numeric_returns_none`,
  `test_slugifies_model_and_writes_csv`, `test_no_models_returns_early`,
  `test_no_matching_rows_returns_early`) wrapping each call under
  `with caplog.at_level(logging.INFO):` and asserting substrings against
  `record.getMessage()`. All 21 tests pass locally.

### #886 Phase 2 slice 69/N: retire `print()` in `src/export/site_insights/device_metric_operation.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/export/site_insights/device_metric_operation.py` with `logging.info(...)`
  using `%`-style deferred formatting to satisfy G004. Covers the menu-banner
  and metrics-refresh notices in `execute` / `_refresh_const_metrics`, the
  empty-metric-list branch in `_emit_empty_metric_list`, the missing-MAC and
  invalid-MAC user-facing errors in `_validate_mac`, the per-metric progress
  line in `_collect_metrics`, and the success / zero-data / error summary lines
  in `_export_with_data` / `_export_empty` / `_export_error`. Each migrated
  call carries the standard `# WHY:` annotation preserving legacy
  operator-visible text via the logger.
- **Tests (Unchanged)**: `tests/unit/export/site_insights/test_device_metric_operation_wave3.py`
  already uses `caplog` exclusively (no `capsys` / `readouterr` usage), so no
  test migration was required. All 41 tests continue to pass locally.

### #886 Phase 2 slice 68/N: retire `print()` in `src/export/org_site_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 9 `print()` calls in
  `src/export/org_site_exporter.py` with `logging.info(...)` using `%`-style
  deferred formatting to satisfy G004. Covers the cache-reuse and fetch-start
  notices plus the empty-result branch in `sites_list_api`, the export-success
  notice in `sites_list_api`, the header banner and export-count summary in
  `sites_with_location`, the guest-header banner and count summary in
  `current_guests`, and the count summary in `historical_guests`. Each migrated
  call carries the standard `# WHY:` annotation preserving legacy
  operator-visible text via the logger.
- **Tests (Unchanged)**: `tests/unit/export/test_org_site_exporter.py` uses
  mock-based assertions with no `capsys` / `readouterr` usage, so no test
  migration was required. All 9 tests continue to pass locally.

### #886 Phase 2 slice 67/N: retire `print()` in `src/refactors/tui_launcher.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 8 remaining `print()`
  calls in `src/refactors/tui_launcher.py` with `logging.info(...)` (module
  already uses root `logging.<level>(...)` for structured tracing) using
  `%`-style deferred formatting. Migrations cover the two-line activation
  banner in `_print_welcome` (Terminal-User-Interface-activated notice +
  navigation-key hint), the three session-boot lines in `_ensure_api_session`
  (initializing banner, failure banner on `initialize_mist_session -> False`,
  and success banner on the truthy path), the Ctrl+C banner in
  `_handle_keyboard_interrupt`, the crash banner in `_handle_fatal_error`
  (f-string converted to `%`-style to satisfy G004), and the return-to-menu
  banner in `_print_exit_message`. Each migrated call carries the standard
  `# WHY:` annotation preserving legacy operator-visible text via the logger.
- **Tests (Migrated)**: `tests/unit/refactors/test_tui_launcher.py` had eight
  `capsys.readouterr().out` assertions across `TestPrintWelcome`,
  `TestEnsureApiSession` (three sub-cases), `TestHandlerHelpers` (two
  sub-cases), and `TestPrintExitMessage` (two sub-cases). All eight were
  converted to `caplog.at_level(logging.INFO, logger="root")` + record-based
  assertions (`stdout = "\n".join(rec.getMessage() for rec in caplog.records)`).
  The unused `capsys` parameter in `test_launch_aborts_when_session_init_fails`
  was dropped since that test only tracks mock invocation counts. Full local
  run: 22/22 pass on `tests/unit/refactors/test_tui_launcher.py`.

### #886 Phase 2 slice 66/N: retire `print()` in `src/gateway/overrides/override_report_writer.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 8 remaining `print()`
  calls in `src/gateway/overrides/override_report_writer.py` with
  `logging.info(...)` (module already uses root `logging.<level>(...)` for its
  debug/info traces) using `%`-style deferred formatting. Migrations cover the
  header-only fast-path in `OverrideReportWriter.write_empty` (report-written
  banner + repeated compliant-fleet notice), and all six operator-facing lines
  in `OverrideReportWriter._print_summary_lines` (report-written banner,
  overridden-ports summary, API-optimization saved-calls line, target-ports
  echo, outliers-hint line, and the conditional zero-entry compliant-fleet
  repeat). Each migrated call carries the standard `# WHY:` annotation
  preserving legacy operator-visible text via the logger.
- **Tests (Migrated)**: `tests/unit/gateway/overrides/test_override_report_writer.py`
  had four `capsys.readouterr().out` assertions covering write_empty,
  write_full (both entry-count branches), and the direct `_print_summary`
  parity test. All four were converted to `caplog.at_level(logging.INFO,
  logger="root")` + record-based assertions (`stdout = "\n".join(rec.getMessage()
  for rec in caplog.records)`). Full local run: 5/5 pass on
  `tests/unit/gateway/overrides/test_override_report_writer.py`.

### #886 Phase 2 slice 65/N: retire `print()` in `src/export/wifi_clients_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 8 remaining `print()`
  calls in `src/export/wifi_clients_exporter.py` with `logging.info(...)` (module
  already uses root `logging.<level>(...)` for its debug/info/warning/exception
  traces) using `%`-style deferred formatting. Migrations cover the workflow
  header in `_announce_start`, the pre-fetch operator line in `_announce_fetch`,
  the failure surface line in `_log_export_failure`, the defensive empty-merge
  banner in `_log_empty_merge`, the no-site cancel-path notice in
  `_ensure_site_selected`, the no-data placeholder header in
  `_write_no_data_placeholder`, and both operator lines in the success summary
  emitter (`_print_success_summary`). Each migrated call carries the standard
  `# WHY:` annotation preserving legacy operator-visible text via the logger.
- **Tests (Migrated)**: `tests/unit/export/test_wifi_clients_exporter.py` had
  two `capsys.readouterr().out` assertions covering the pipeline-failure and
  empty-merge banners. Both were converted to `caplog.at_level(logging.INFO,
  logger="root")` + record-based assertions (`out = "\n".join(rec.getMessage()
  for rec in caplog.records)`); `import logging` was added to the test module.
  Full local run: 30/30 pass across `tests/unit/export/test_wifi_clients_exporter.py`
  and `tests/unit/test_wifi_clients_exporter.py`.

### #886 Phase 2 slice 64/N: retire `print()` in `src/export/site_webhook_deliveries_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 8 remaining `print()`
  calls in `src/export/site_webhook_deliveries_exporter.py` with
  `logging.info(...)` (module already uses root `logging.<level>(...)` for its
  info/warning/error traces) using `%`-style deferred formatting. Migrations
  cover: the no-webhooks-configured operator notice and the per-webhook
  enumeration line in `_select_webhook_id`; the invalid-selection and
  out-of-range validation notices in `_resolve_webhook_choice`; the no-data
  and post-export count notices in `_persist_site_webhook_deliveries`; and
  the workflow banner plus the SDK-error surface line in `deliveries`. Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation.
- **Tests (Verified)**: no dedicated `test_site_webhook_deliveries_exporter.py`
  suite exists, and no `capsys` assertion covered this module. The full
  `tests/unit/test_arango_writer.py` suite (which references the
  `searchSiteWebhooksDeliveries` operationId for entity-type mapping) passes
  (249/249) locally, confirming no regression to shared persistence wiring.

### #886 Phase 2 slice 63/N: retire `print()` in `src/refactors/serial_cc/sle_metrics.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 7 remaining `print()`
  calls in `src/refactors/serial_cc/sle_metrics.py` with `logging.info(...)`
  (module already uses root `logging.<level>(...)` for its info/warning/error
  traces) using `%`-style deferred formatting. Migrations cover the exported/
  empty summary lines in `_export_results`, the retrieval-complete summary
  and top-level error notice in `_run_retrieval`, the workflow banner in
  `execute`, and the two "retrieving/attempting" info lines in `execute`
  covering the service-category and specialized-metric counts. Each migrated
  call carries the standard `# WHY: preserve operator notice verbatim; route
  through logger for capture/redirection.` annotation.
- **Test migration (Changed)**: converted the 1 `capsys` assertion in
  `tests/unit/serial_cc/test_sle_metrics.py::test_sle_metrics_fast_mode_reduces_scope`
  to `caplog` capture (`with caplog.at_level(logging.INFO, logger="root"):`,
  aggregating `record.getMessage()` values before substring assertion on
  "SLE data retrieval completed"). All 4 tests across the unit + integration
  sle_metrics suites pass locally.

### #886 Phase 2 slice 62/N: retire `print()` in `src/refactors/serial_cc/security_events.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 7 remaining `print()`
  calls in `src/refactors/serial_cc/security_events.py` with `logging.info(...)`
  (module already uses root `logging.<level>(...)` for its info/warning/error
  traces) using `%`-style deferred formatting. Migrations cover the fast-mode
  cache-hit notice in `execute`, the two banner lines in `_run_export_workflow`
  (header + completion summary), the empty-dataset summary and populated-
  dataset summary in `_export_flattened_dataset`, and the two rogue-export
  summary lines in `_export_rogue_combined` (empty + populated). Each migrated
  call carries the standard `# WHY: preserve operator notice verbatim; route
  through logger for capture/redirection.` annotation.
- **Test migration (Changed)**: converted 1 `capsys` assertion in
  `tests/unit/serial_cc/test_security_events.py` and 4 `capsys` assertions in
  `tests/unit/serial_cc/test_security_events_wave8.py` to `caplog` capture
  (`with caplog.at_level(logging.INFO, logger="root"):`, aggregating
  `record.getMessage()` values before substring assertions). Dropped the unused
  `capsys` parameter from `test_export_rogue_data_iterate_exception_aborts`.
  All 23 tests in the two suites pass locally.

### #886 Phase 2 slice 61/N: retire `print()` in `src/export/wan_client_events_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 7 remaining `print()`
  calls in `src/export/wan_client_events_exporter.py` with `logging.info(...)`
  / `logging.error(...)` (module already imports `logging` and emits via root
  `logging.<level>(...)` for info/warning/error/exception traces) using
  `%`-style deferred formatting. Migrations cover the `_announce_start`
  banner, the `_announce_fetch` pre-fetch operator line, the
  `_log_export_failure` operator-facing error line (routed via
  `logging.error`), the `_ensure_site_selected` cancel-path notice, the
  `_write_no_data_placeholder` empty-result notice, and the two success-
  summary lines in `_print_success_summary` (header + record count). Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation.
- **Test migration (Changed)**: none required — no `capsys`-based tests
  currently target `WanClientEventsExporter`.

### #886 Phase 2 slice 60/N: retire `print()` in `src/export/site_insights/site_metric_operation.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 7 remaining `print()`
  calls in `src/export/site_insights/site_metric_operation.py` with
  `logging.info(...)` (module already uses root `logging.<level>(...)` for its
  info/warning/error/debug traces) using `%`-style deferred formatting.
  Migrations cover the operation banner, refresh-in-progress notice, empty-
  metrics operator prompt, retrieval progress line, per-metric success summary,
  zero-data summary, and the exception-path summary in `_export_error`. Each
  migrated call carries the standard `# WHY: preserve operator notice
  verbatim; route through logger for capture/redirection.` annotation.
- **Test migration (Changed)**: converted the 5 `capsys` assertions in
  `tests/unit/export/site_insights/test_site_metric_operation_wave9.py` to
  `caplog` capture (`with caplog.at_level(logging.INFO, logger="root"):`,
  followed by joining `r.getMessage() for r in caplog.records`) so the tests
  read from the logger channel the code now emits on.

### #886 Phase 2 slice 59/N: retire `print()` in `src/ssh/config/csv_loader.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/ssh/config/csv_loader.py` with `logger.info(...)` using the
  module's pre-existing `logger = logging.getLogger(__name__)` and `%`-style
  deferred formatting. Migrations cover the legacy-fallback notice in
  `_resolve_csv_path()`, the broad-except read-failure warning in
  `_read_validated_commands()`, the 3-line invalid-row warning summary in
  `_warn_invalid_rows()` (header + first 3 rows + `and N more` truncation
  notice), and the too-many-commands warning in `_enforce_command_cap()`.
  Each migration is annotated with `# WHY: preserve operator notice verbatim;
  route through logger for capture/redirection.`
- **Test migration (Changed)**: updated
  `tests/unit/ssh/config/test_csv_loader.py` to switch five `capsys.readouterr().out`
  assertions to `caplog.at_level(logging.INFO, logger="src.ssh.config.csv_loader")`
  + joined `caplog.records`, aligning coverage with the logger channel the code
  now emits on. Added `import logging` and a module-scoped `_LOGGER_NAME`
  constant.

### #886 Phase 2 slice 58/N: retire `print()` in `src/inventory/org_device_inventory_summary.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/inventory/org_device_inventory_summary.py` with
  `logging.info(...)` using `%`-style deferred formatting. Migrations cover
  the four-line distribution-summary banner helper (separator, capitalized
  label, separator, tabulated table), the `run_for_org` elapsed-time summary,
  and the `execute()` guard-clause "No organization selected" operator error.
  Each migration is annotated with `# WHY: preserve operator notice verbatim;
  route through logger for capture/redirection.`
- **Test migration (Changed)**: updated
  `tests/unit/inventory/test_org_device_inventory_summary_wave8.py` to switch
  four assertions from `capsys.readouterr().out` to
  `caplog.at_level(logging.INFO, logger="root")` + joined `caplog.records`,
  aligning coverage with the logger channel the code now emits on.

### #886 Phase 2 slice 57/N: retire `print()` in `src/gateway/gateway_ha_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/gateway/gateway_ha_exporter.py` with `logging.info(...)` using
  `%`-style deferred formatting. Migrations cover the "no HA gateways found"
  operator notice in `_collect_ha_gateways()` plus the terminal summary
  table rendered by `_print_ha_summary()` (section header, column header
  row, separator line, per-row data lines, trailing blank line). Row
  formatting now uses `%-30s %-8s %-12s %-20s %-20s %-18s` positional
  parameters so the operator-visible layout is preserved verbatim while the
  emission runs through the logger for capture/redirection. A `# WHY:`
  comment tags each migrated line.
- **Tests**: migrated 3 `capsys.readouterr().out` assertions in
  `tests/unit/gateway/test_gateway_ha_exporter.py` (in `TestCollectHaGateways`
  and `TestPrintHaSummary`) to `caplog.at_level(logging.INFO, logger="root")`
  + `"\n".join(r.getMessage() for r in caplog.records)`. `import logging`
  added. 18/18 tests pass.
- **Lint**: `ruff --select T20 src/gateway/gateway_ha_exporter.py` now clean.

### #886 Phase 2 slice 56/N: retire `print()` in `src/export/org_template_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/export/org_template_exporter.py` with `logging.info(...)`
  using `%`-style deferred formatting. Migrations cover the AP template
  export header, empty-branch operator notice, and success count summary in
  `_persist_ap_template_profiles()` / `ap_templates()`, plus the switch
  template export header, empty-branch operator notice, and success count
  summary in `_persist_switch_template_csv()` / `switch_templates()`.
  Operator-visible text preserved verbatim; a `# WHY:` comment tags each
  migrated line to make the redirection intent explicit for reviewers.
- **Tests**: existing suite `tests/unit/export/test_org_template_exporter.py`
  contained no `capsys` assertions on the migrated lines; 18/18 tests pass
  unchanged.
- **Lint**: `ruff --select T20 src/export/org_template_exporter.py` now clean.

### #886 Phase 2 slice 55/N: retire `print()` in `src/export/org_device_stats_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/export/org_device_stats_exporter.py` with `logging.info(...)`
  and `logging.warning(...)` using `%`-style deferred formatting. Migrations
  cover the fast-mode cache-hit operator notices in
  `_device_stats_cache_hit`, `_port_stats_cache_hit`, and
  `_vpn_peer_stats_cache_hit`; the empty-rows "no port statistics" warning
  and post-export record-count confirmation in `_save_device_port_stats_output`;
  and the fast-mode collected-records summary line in
  `_log_fast_port_stats_summary`. Operator-facing text preserved verbatim; no
  behavior change beyond routing through the configured logger. Companion
  `capsys` → `caplog` migration in
  `tests/unit/export/test_org_device_stats_exporter.py` covers the 6 affected
  cache-hit/summary/export assertions.

### #886 Phase 2 slice 54/N: retire `print()` in `src/device/utility_commands.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/device/utility_commands.py` with `logging.info(...)` /
  `logging.error(...)` using `%`-style deferred formatting. Migrations cover
  `_print_api_error` (formatted HTTP-error line including status and any
  server-side detail), `_print_api_result` (success arrow line), and
  `_handle_clear_session_error` (the 400-status two-line operator guidance
  about `service_name`/`session_ids` request-body keys plus the generic
  fallback and the nested-exception guard). Error and success text preserved
  verbatim; no behavior change beyond routing through the configured logger.
  Companion `capsys` → `caplog` migration in
  `tests/unit/test_device_utility_commands.py` covers the 11 affected
  success/error-path assertions.

### #886 Phase 2 slice 53/N: retire `print()` in `src/capture/site_capture_loop.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/capture/site_capture_loop.py` with `logging.info(...)` using
  `%`-style deferred formatting. Three migrations in `_run_one_iteration`
  cover the iteration header banner, iteration-complete banner, and
  "Waiting … seconds before next check" nap notice. Three migrations in
  `_handle_user_interrupt` cover the wide interrupt banner, the
  "Completed N loop iteration(s)" summary, and the reassurance line about
  downloaded PCAPs and graceful exit. Banner text and separator widths are
  preserved verbatim; no behavior change beyond routing through the
  configured logger.

### #886 Phase 2 slice 52/N: retire `print()` in `src/site/address_audit/comparison_display.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 5 remaining `print()`
  calls in `src/site/address_audit/comparison_display.py` with
  `logging.info(...)` / `logging.warning(...)` using `%`-style deferred
  formatting. Migrated callsites in `render` (PrettyTable render),
  `prompt_post_table` (per-state summary line plus the `[1] Save` / `[q] Quit`
  menu), and the invalid-choice re-prompt branch. User-facing message text
  preserved verbatim; no behavior change beyond routing through the configured
  logger.

### #886 Phase 2 slice 51/N: retire `print()` in `src/gateway/_wan2_variable_template.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 5 remaining `print()`
  calls in `src/gateway/_wan2_variable_template.py` with `logging.info(...)` /
  `logging.warning(...)` / `logging.error(...)` using `%`-style deferred
  formatting. Migrated callsites in `_fetch_template_config` (analyzer failure
  notice), `_classify_port_key` (two complex-port-pattern operator warnings),
  `_analyze_templates_parallel` (analysis banner), and
  `_apply_template_changes` (apply banner). No behavior change beyond routing
  through the configured logger; user-facing message text preserved verbatim
  (including the legacy "!?" prefix operators rely on).

### #886 Phase 2 slice 50/N: retire `print()` in `src/export/site_export_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 5 remaining `print()`
  calls in `src/export/site_export_utils.py` with `logging.info(...)` /
  `logging.warning(...)` / `logging.error(...)` using `%`-style deferred
  formatting. Migrated callsites in `_emit_debug_table` (PrettyTable render),
  `_write_insight_rows` (the "! N records" success and "! 0 records ... (no
  metrics available)" empty branches), `_export_data` (record-count summary),
  and `insights` (operator-facing error branch). Companion tests in
  `tests/unit/export/test_site_export_utils_extended.py` migrated from
  `capsys` to `caplog` (`caplog.at_level(..., logger="root")` + record-list
  join). No behavioral change; operator messages preserved verbatim.

### #886 Phase 2 slice 49/N: retire `print()` in `src/export/site_config_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 5 remaining `print()`
  calls in `src/export/site_config_exporter.py` with `logging.info(...)` /
  `logging.warning(...)` using `%`-style deferred formatting. Migrated
  callsites in `_persist_site_wlans_csv` (the "! 0 records exported..." and
  "! N records exported..." user-facing notices) and in `settings()` (the
  "Site Configuration Settings:" banner, "! N site configurations exported
  to AllSiteConfigs.csv" record-count notice, and "! No site configurations
  found." empty-result notice). All user-facing strings — including the
  leading `!` sentinel and the literal `data\` path fragment — are preserved
  verbatim.
- **Tests (Changed)**: swapped `capsys.readouterr().out` assertions in the
  two `TestSettings` cases (`test_no_data_warns_and_returns` and
  `test_with_data_flattens_and_writes`) for `caplog.records` scans under
  `caplog.at_level("WARNING"/"INFO", logger="root")` so the assertions read
  from the logger channel the code now emits on.
- **Rationale**: incremental progress toward ruff `T20` (T201/T203) selector
  enablement (issue #886). Behavior-preserving; the module already imported
  `logging` and used `logging.info/warning` at module level, so no new
  imports were introduced. `logging.warning` is used for the empty-result
  notice because the original string carried an implicit warning semantic
  ("No site configurations found."); the other four callsites remain
  informational.

### #886 Phase 2 slice 48/N: retire `print()` in `src/analytics/insight_metrics_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 5 remaining `print()`
  calls in `src/analytics/insight_metrics_utils.py` with `logging.info(...)` /
  `logging.warning(...)`. All 5 calls live in
  `InsightMetricsUtils.export_const_insight_metrics`: the "Export Available
  Insight Metrics:" banner and two `! Note:` / `! For best results` guidance
  lines, the "! ConstInsightMetrics.csv is available" success message, and
  the "! Warning: ConstInsightMetrics.csv was not created..." missing-file
  notice. The first four map to `logging.info` (banner/informational tone);
  the last maps to `logging.warning` since the original string carried a
  "Warning:" prefix. All user-facing strings preserved verbatim.
- **Companion tests (Changed)**:
  `tests/unit/analytics/test_insight_metrics_utils.py` updated so
  `test_export_const_insight_metrics_delegates_and_reports_present` and
  `test_export_const_insight_metrics_warns_when_csv_missing` capture
  `caplog` records instead of `capsys` stdout. Root-logger `at_level("INFO")`
  / `at_level("WARNING")` scoping added inside each test's context manager.
- **Rationale**: incremental progress toward ruff `T20` (T201/T203) selector
  enablement (issue #886). Behavior-preserving; the module already imported
  `logging` and used `logging.info/warning/debug/error` directly (no module
  `logger` object), so the migrated calls follow that existing convention.

### #886 Phase 2 slice 47/N: retire `print()` in `src/ssh/config/host_parser.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/ssh/config/host_parser.py` with `logger.warning(...)` using
  `%`-style deferred formatting. Migrated callsites: the oversize-input
  truncation notice in `_truncate_oversize`, the two invalid-host warnings
  in `_warn_invalid_hosts` (summary line plus "... and N more" tail), and
  the too-many-hosts cap notice in `_enforce_host_cap`. All user-facing
  strings (including the `[WARNING]` prefixes and "... and N more" tail
  line) are preserved verbatim.
- **Docstring (Changed)**: updated `_warn_invalid_hosts` summary line from
  "Print the same user-facing warning..." to "Emit the same user-facing
  warning..." to match the logger-based emission.
- **Rationale**: incremental progress toward ruff `T20` (T201/T203) selector
  enablement (issue #886). Behavior-preserving; the module already imported
  `logging` and defined `logger = logging.getLogger(__name__)`, so no new
  imports were introduced. `logger.warning` is used because the original
  strings carried a `[WARNING]` prefix — the semantic level is warning.

### #886 Phase 2 slice 46/N: retire `print()` in `src/ssh/config/command_parser.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/ssh/config/command_parser.py` with `logger.warning(...)`
  using `%`-style deferred formatting. Migrated callsites: the oversize-input
  truncation notice in `_truncate_oversize`, the two invalid-command warnings
  in `_warn_invalid_commands` (summary line plus "... and N more" tail), and
  the too-many-commands cap notice in `_enforce_command_cap`. All user-facing
  strings (including the `[WARNING]` prefixes and "... and N more" tail line)
  are preserved verbatim.
- **Docstring (Changed)**: updated `_warn_invalid_commands` summary line from
  "Print the same user-facing warning..." to "Emit the same user-facing
  warning..." to match the logger-based emission.
- **Rationale**: incremental progress toward ruff `T20` (T201/T203) selector
  enablement (issue #886). Behavior-preserving; the module already imported
  `logging` and defined `logger = logging.getLogger(__name__)`, so no new
  imports were introduced. `logger.warning` is used (rather than
  `logging.info` as in the pivot_renderer slice) because the original
  strings carried a `[WARNING]` prefix — the semantic level is warning.

### #886 Phase 2 slice 45/N: retire `print()` in `src/inventory/inventory_summary/pivot_renderer.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/inventory/inventory_summary/pivot_renderer.py` with
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  all live in `_print_table`: the leading legacy banner rule, the
  "Version Distribution per Model" header, the trailing rule, and the
  PrettyTable body render itself. Companion test
  `tests/unit/inventory/inventory_summary/test_pivot_renderer.py` was
  updated: two stdout assertions (`_print_table` unit test and the
  `render` end-to-end test) now read `caplog.text` instead of
  `capsys.readouterr().out`, since the banner is emitted through the
  logger. Full baseline holds: 8949 passed, 0 failed, 77 skipped,
  5 xfailed, 1 xpassed.

### #886 Phase 2 slice 44/N: retire `print()` in `src/export/site_wan_usage_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/export/site_wan_usage_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  cover the empty-rows notice in `_persist_site_wan_usages`, the per-site
  record-count notice, the `wan_usages` menu header, and the user-facing
  error notice on the API-failure branch. Hoisted the inline `# WHY:`
  comments above the migrated calls to keep line length under 120 chars.
  Full baseline holds: 8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed.

### #886 Phase 2 slice 43/N: retire `print()` in `src/export/site_nac_client_events_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/export/site_nac_client_events_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  cover the empty-rows notice in `_persist_site_nac_client_events`, the
  per-site record-count notice, the `nac_client_events` menu header, and the
  user-facing error notice on the API-failure branch. Hoisted the inline
  `# WHY:` comments above the migrated calls to keep line length under 120
  chars. Full baseline holds: 8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed.

### #886 Phase 2 slice 42/N: retire `print()` in `src/export/site_mist_edge_events_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/export/site_mist_edge_events_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  cover the empty-rows notice in `_persist_site_mist_edge_events`, the
  per-site record-count notice, the `mist_edge_events` menu header, and the
  user-facing error notice on the API-failure branch. Hoisted the inline
  `# WHY:` comments above the migrated calls to keep line length under 120
  chars. Full baseline holds: 8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed.

### #886 Phase 2 slice 41/N: retire `print()` in `src/export/site_guest_authorization_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/export/site_guest_authorization_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  cover the empty-rows notice in `_persist_site_guest_authorizations`, the
  per-site record-count notice, the `guest_authorizations` menu header, and
  the user-facing error notice on the API-failure branch. Hoisted the inline
  `# WHY:` comments above the migrated calls to keep line length under 120
  chars. Full baseline holds: 8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed.

### #886 Phase 2 slice 40/N: retire `print()` in `src/export/site_client_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 4 remaining `print()`
  calls in `src/export/site_client_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Migrated callsites
  cover the empty-rows notice in `_persist_site_clients`, the per-site
  record-count notice, the `clients` header + start-of-export trace, and
  the user-facing error notice on the API-failure branch. Hoisted the
  inline `# WHY:` comments above the migrated calls to keep line length
  under 120 chars.
- **Tests (Changed)**: migrated three assertions in
  `tests/unit/export/test_site_client_exporter.py` from `capsys.readouterr()`
  stdout checks to `caplog` INFO-level record checks
  (`test_empty_rows_logs_notice_and_returns`,
  `test_non_empty_rows_flattens_escapes_writes_and_logs`,
  `test_api_error_is_logged_and_user_notice_emitted`). Full baseline holds:
  8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed.

### #886 Phase 2 slice 39/N: retire `print()` in `src/ssh/batch/interactive_batch_executor.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/ssh/batch/interactive_batch_executor.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. The migrated
  callsites are (1) `InteractiveBatchExecutor._setup_log_context` per-host
  "Logging to: …" destination banner, (2) `InteractiveBatchExecutor._handle_step_interrupt`
  "[INTERRUPT] … Ctrl+C detected!" notice, and (3) `InteractiveBatchExecutor._write_step_header`
  per-step "Executing step N: …" redacted console line. Each `# WHY: …`
  comment was moved one line above the migrated call so the source stays
  under the 120-char E501 gate. `import logging` was already present at
  module scope.
- **Test posture**: no `capsys.readouterr()` assertions in the interactive
  batch executor test module targeted the removed prints (existing `capsys`
  hits under `tests/unit/test_ssh_runner.py` cover unrelated host-validation
  flows), so no test migration was required for this slice.
- **Verification**:
  - `ruff check --select T201,T203 src/ssh/batch/interactive_batch_executor.py` — no issues.
  - `ruff check src/ssh/batch/interactive_batch_executor.py` — no issues.
  - `black --check src/ssh/batch/interactive_batch_executor.py` — clean.
  - Targeted pytest (`tests/unit/ssh/batch/` + `tests/unit/test_ssh_runner.py`): 173 passed, 0 failed.
  - Full-suite pytest baseline held: 8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed.
- **Scope guardrail**: T20 stays scoped to migrated files; the global selector
  flip in `pyproject.toml` is deferred to the final wrap-up PR after every
  remaining offender has been migrated file-by-file.

### #886 Phase 2 slice 38/N: retire `print()` in `src/ssh/batch/batch_executor.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/ssh/batch/batch_executor.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. The migrated
  callsites are (1) `BatchExecutor._setup_host_log` "Logging to: …" per-host
  destination banner, (2) `BatchExecutor._write_command_header` per-command
  "Executing command: …" console line, and (3) `BatchExecutor._handle_interrupt`
  "Ctrl+C detected!" interrupt notice. Each inline `# WHY: …` comment was
  moved one line above the migrated call so the source stays under the
  120-char E501 gate. `import logging` was already present at module scope.
- **Test posture**: no `capsys.readouterr()` assertions targeted the removed
  prints (the `capsys` hits in `tests/unit/test_ssh_runner.py` cover unrelated
  host-validation flows), so no test migration was required for this slice.
- **Verification**:
  - `ruff check --select T201,T203 src/ssh/batch/batch_executor.py` — no issues.
  - `ruff check src/ssh/batch/batch_executor.py` — no issues.
  - `black --check src/ssh/batch/batch_executor.py` — clean.
  - Targeted pytest (`tests/unit/test_ssh_runner.py` + `tests/unit/ssh/batch/test_interactive_batch_executor_scrubbing.py`): 173 passed, 0 failed.
  - Full-suite pytest baseline held: 8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed.
- **Scope guardrail**: T20 stays scoped to migrated files; the global selector
  flip in `pyproject.toml` is deferred to the final wrap-up PR after every
  remaining offender has been migrated file-by-file.

### #886 Phase 2 slice 37/N: retire `print()` in `src/refactors/serial_cc/test_results_by_site.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/refactors/serial_cc/test_results_by_site.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. One call lives in
  `GatewayTestResultsService._export_results` for the empty-result branch
  ("No gateway test results found. CSV not created.") and one for the export
  count summary ("`<N>` gateway test results exported to `<file>`"); the third is
  the "Gateway Synthetic Test Results:" operation banner in
  `GatewayTestResultsService.execute`. Each print's inline `# User-facing ...`
  comment was moved one line above the migrated `logging.info(...)` call to
  keep the source under the 120-char E501 gate. `import logging` was already
  present at module scope.
- **Test posture**: no `capsys.readouterr()` assertions in
  `tests/unit/serial_cc/test_test_results_by_site.py` or
  `tests/integration/serial_cc/test_test_results_by_site_integration.py`
  targeted the removed prints, so no test migration was required for this
  slice.
- **Verification**:
  - `ruff check --select T201,T203 src/refactors/serial_cc/test_results_by_site.py` — no issues.
  - `ruff check src/refactors/serial_cc/test_results_by_site.py` — no issues.
  - `black --check src/refactors/serial_cc/test_results_by_site.py` — clean.
  - Targeted pytest for the file's unit + integration modules: 6 passed, 0 failed, 2 skipped.
  - Full-suite pytest baseline held: 8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed.
- **Scope guardrail**: T20 stays scoped to migrated files; the global selector
  flip in `pyproject.toml` is deferred to the final wrap-up PR after every
  remaining offender has been migrated file-by-file.

### #886 Phase 2 slice 36/N: retire `print()` in `src/refactors/maps_manager_launcher.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/refactors/maps_manager_launcher.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Two of the calls
  live in `MapsManagerLauncher._handle_import_error` (the "Could not load
  Maps Manager module." failure banner and the "Ensure src/maps/maps_manager.py
  exists" remediation hint) and one in `MapsManagerLauncher._handle_fatal_error`
  (the user-visible `ERROR: <error>` banner). Each print's inline
  `# User-facing ... banner.` comment was moved one line above the migrated
  `logging.info(...)` call to keep the source under the 120-char E501 gate.
  `import logging` was already present at module scope.
- **Test posture (Changed)**: six tests in
  `tests/unit/refactors/test_maps_manager_launcher.py`
  (`TestLaunchImportFailure.test_import_failure_prints_and_aborts`,
  `TestLaunchImportFailure.test_import_failure_direct_call`,
  `TestLaunchOrgIdFailure.test_get_org_id_raises`,
  `TestRunInteractiveMenuFailures.test_external_class_unset_raises_and_handled`,
  `TestRunInteractiveMenuFailures.test_run_interactive_menu_raises`,
  `TestHandleFatalError.test_prints_and_logs`) previously asserted on
  `capsys.readouterr().out` for the removed `print()` output; they now use
  `caplog.at_level(logging.INFO)` and assert on `caplog.text`, with the
  fixture signature switched from `capsys: pytest.CaptureFixture` to
  `caplog: pytest.LogCaptureFixture`. No behavior asserted by the tests
  changed - only the capture mechanism moved from stdout to the logging
  system. The module-import `import pytest` comment updated from
  `capsys/caplog` to `caplog` fixtures.
- **Verification**: `ruff check --select T201,T203 src/refactors/maps_manager_launcher.py`
  → No issues (0 T20 violations remaining in this file). `ruff check` + `black --check`
  clean on both changed files. Targeted `pytest tests/unit/refactors/test_maps_manager_launcher.py`
  → **13 passed, 0 failed, 0 skipped**. Full-suite `pytest` → **8949 passed,
  0 failed, 77 skipped, 5 xfailed, 1 xpassed** — matches the pre-slice baseline exactly.

### #886 Phase 2 slice 35/N: retire `print()` in `src/export/org_client_security_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/export/org_client_security_exporter.py` with module-level
  `logging.info(...)` using `%`-style deferred formatting. Two of the calls
  live in `OrgClientSecurityExporter._export_rogues` (the export-count banner
  and the empty-result banner) and one in
  `OrgClientSecurityExporter._check_csv_cache_fresh` (the fast-mode cache-hit
  banner). Each print's inline `# User-facing ... banner.` comment was moved
  one line above the migrated `logging.info(...)` call to keep the source
  under the 120-char E501 gate. `import logging` was already present at module
  scope.
- **Test posture (Changed)**: three tests in
  `tests/unit/export/test_org_client_security_exporter.py`
  (`TestCheckCsvCacheFresh.test_returns_true_when_fresh`,
  `TestExportRogues.test_writes_when_rogues_present`,
  `TestExportRogues.test_empty_rogues_logs_only`) previously asserted on
  `capsys.readouterr().out` for the removed `print()` output; they now use
  `caplog.at_level("INFO")` and assert on `caplog.text`, with the fixture
  signature switched from `capsys: pytest.CaptureFixture` to
  `caplog: pytest.LogCaptureFixture`. No behavior asserted by the tests
  changed — same substrings (`"Fast mode"`, `"2 rogue APs exported"`,
  `"No rogue APs detected"`) are verified against the new log stream.
- **Verification**: `ruff check --select T201,T203 src/export/org_client_security_exporter.py`
  reports zero remaining print/pprint violations against the migrated file.
  `ruff check` and `black --check` are clean on both changed files.
  Targeted `pytest tests/unit/export/test_org_client_security_exporter.py
  tests/integration/serial_cc/test_security_events_integration.py -q` →
  26 passed, 0 failed, 1 skipped. Full-suite baseline holds:
  **8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed**.
- **Follow-up**: 111-ish files still contain `print()` calls (per the
  `.tmp_census.py` T20 aggregation of `ruff check --select T201,T203 src`).
  Each subsequent slice continues to attack the smallest-remaining files
  first. Once the last `src/**/*.py` `print()` is gone the final #886 PR
  flips the T20 selector on in `pyproject.toml` (add `"T20"` to the `select`
  list, drop the "Phase 2 goal" comment) and closes the issue.

### #886 Phase 2 slice 34/N: retire `print()` in `src/refactors/serial_cc/switch_vc_stats.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `src/refactors/serial_cc/switch_vc_stats.py` (both inside
  `SwitchVcStatsService.execute`) with module-level `logging.info(...)` using
  `%`-style deferred formatting, matching the file's pre-existing
  `logging.info(...)` / `logging.warning(...)` / `logging.debug(...)`
  convention (no module `logger` binding is used elsewhere in this module).
  The operator banner `print("Switch Virtual Chassis Statistics:")` becomes
  `logging.info("Switch Virtual Chassis Statistics:")`, sitting next to the
  existing `logging.info("Exporting all switch virtual chassis stats...")`.
  The f-string
  `print(f"! {len(all_vc_stats)} switch VC stats exported to OrgSwitchVCStats.csv")`
  becomes
  `logging.info("! %d switch VC stats exported to OrgSwitchVCStats.csv", len(all_vc_stats))`,
  which produces a near-duplicate of the immediately following
  `logging.info("! Switch VC stats exported to OrgSwitchVCStats.csv (%d records).", ...)`
  line; the duplication is intentional to preserve the original operator UX
  under the migration (same conservative pattern used in slices 32/33).
  `import logging` was already present at module scope.
- **Test posture**: no existing test asserts on the two migrated banners
  (verified via ripgrep against `tests/`), so the test suite is unchanged.
- **Verification**: `ruff check --select T201,T203 src/refactors/serial_cc/switch_vc_stats.py`
  reports 0 issues; `ruff check` and `black --check` clean on the source
  file; targeted `pytest tests/unit/refactors/` = 294 passed; full `pytest`
  suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 33/N: retire `print()` in `src/gateway/wan2_variable.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `src/gateway/wan2_variable.py` (both inside
  `GatewayWan2VariableMigrator._log_no_changes_needed`) with module-level
  `logging.info(...)` using `%`-style deferred formatting, matching the file's
  pre-existing `logging.info(...)` / `logging.warning(...)` convention (no
  module `logger` binding is used elsewhere in this module). The f-string
  `print(f"\n  No templates found with {self._search_pattern} port configurations.")`
  becomes `logging.info("\n  No templates found with %s port configurations.", self._search_pattern)`,
  and the closing `print("  No changes needed.")` becomes
  `logging.info("  No changes needed.")`. The helper's docstring was updated
  from "Print + log the 'no templates require modification' outcome." to
  "Log the 'no templates require modification' outcome." to match the new
  behavior. `import logging` was already present at module scope.
- **Test posture**: no existing test asserts on the two migrated banners
  (verified via ripgrep against `tests/`), so the test suite is unchanged.
- **Verification**: `ruff check --select T201,T203 src/gateway/wan2_variable.py`
  reports 0 issues; `ruff check` and `black --check` clean on the source
  file; targeted `pytest tests/unit/gateway/` = 309 passed; full `pytest`
  suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 32/N: retire `print()` in `src/gateway/overrides/wan_override_walker.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `src/gateway/overrides/wan_override_walker.py` with module-level
  `logging.info(...)` / `logging.warning(...)`, matching the file's
  pre-existing convention (no module `logger` binding is used elsewhere in
  this module). `WanOverrideWalker.walk` now emits the legacy compliance
  header via `logging.info("Gateway Ports Overridden from Template (Compliance Outliers):")`
  and the `MIST_WAN_TARGET_PORTS`-missing operator banner via
  `logging.warning(" MIST_WAN_TARGET_PORTS not configured in .env - skipping port override analysis")`,
  sitting next to the existing
  `logging.warning("MIST_WAN_TARGET_PORTS environment variable not set")`
  operator-hint pair. `import logging` was already present at module scope.
- **Test posture**: `test_walk_early_exits_when_no_target_ports_configured`
  in `tests/unit/gateway/test_wan_override_walker_extended.py` was migrated
  off the `capsys` fixture; the assertion now reads `caplog.text` under
  `caplog.at_level("WARNING")` (which the test already declared) to verify
  the migrated operator banner. The unused `capsys` parameter was removed.
- **Verification**: `ruff check --select T201,T203 src/gateway/overrides/wan_override_walker.py`
  reports 0 issues; `ruff check` and `black --check` clean on both source
  and test files; targeted pytest for
  `tests/unit/gateway/test_wan_override_walker.py` +
  `tests/unit/gateway/test_wan_override_walker_extended.py` = 16 passed;
  full `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 31/N: retire `print()` in `src/export/gateway_test_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `src/export/gateway_test_exporter.py` with module-level
  `logging.warning(...)` / `logging.info(...)` using `%`-style deferred
  formatting. `_export_synthetic_results` now emits the empty-results banner
  via `logging.warning("! No synthetic test results found. CSV not created.")`
  and the export-success line via
  `logging.info("! %s gateway synthetic test results exported to %s", len(all_stats), filename)`,
  matching the file's pre-existing `logging.info(...)` / `logging.warning(...)`
  convention (no module `logger` binding is used elsewhere in this module).
  `import logging` was already present at module scope.
- **Test posture**: two tests in
  `tests/unit/export/test_gateway_test_exporter.py`
  (`TestExportSyntheticResults.test_no_stats_warns_and_returns` and
  `test_writes_csv_via_dataexporter`) were migrated from the `capsys`
  fixture to `caplog`; both assert on `caplog.text` under
  `caplog.at_level(logging.WARNING)` / `caplog.at_level(logging.INFO)`
  respectively. `import logging` was added to the test module.
- **Verification**: `ruff check` reports 0 issues on both source and test
  files; `black --check` clean; 0 remaining T201 matches in
  `src/export/gateway_test_exporter.py`; targeted pytest for the module
  (`tests/unit/export/test_gateway_test_exporter.py` +
  `tests/unit/export/test_gateway_test_exporter_runtime_wiring.py`) = 32
  passed; full `pytest` suite green (8949 passed, 0 failed, 77 skipped,
  5 xfailed, 1 xpassed).

### #886 Phase 2 slice 30/N: retire `print()` in `tools/plan_wave_builder.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `tools/plan_wave_builder.py` with `logger.info(...)` using
  `%`-style deferred formatting. `main()` now emits the wave-summary line via
  `logger.info("Wrote %s prompt files + wave_manifest.json", len(manifest))`
  and each per-entry manifest line via
  `logger.info("  %s %s -> %s", entry["spec_num"], entry["operation_id"], entry["agent_id"])`,
  so the CLI utility's per-wave progress trace flows through the standard
  logging handler chain rather than raw stdout. `import logging` was added
  at module scope and a module-level `logger = logging.getLogger(__name__)`
  was introduced (the file previously had no logger wiring).
- **Test posture**: no existing test references `tools/plan_wave_builder.py`
  (verified by ripgrep across `tests/`); no test edits required.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `tools/plan_wave_builder.py`; full `pytest`
  suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 29/N: retire `print()` in `tools/_rebuild_backlog_tsv.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `tools/_rebuild_backlog_tsv.py` with `logger.info(...)` using
  `%`-style deferred formatting. The `main()` completion status line now
  emits via `logger.info("wrote %s sub-A rows -> %s", len(rows), OUT)` so the
  CLI utility's end-of-run summary flows through the standard logging
  handler chain rather than raw stdout. `import logging` was added at
  module scope and a module-level `logger = logging.getLogger(__name__)`
  was introduced (the file previously had no logger wiring).
- **Test posture**: no existing test references
  `tools/_rebuild_backlog_tsv.py` (verified by ripgrep across `tests/`);
  no test edits required.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `tools/_rebuild_backlog_tsv.py`; full
  `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 28/N: retire `print()` in `src/ssh/command/command_runner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/ssh/command/command_runner.py` with `logger.info(...)` using
  `%`-style deferred formatting. `SingleCommandRunner._setup_host_log` now
  emits the per-host log-file status line via
  `logger.info("- [%s] Logging to: %s", request.hostname, host_log_file)`
  through the injected `ssh_runner_v2` logger, so the user-facing message
  flows through the same handler chain as the surrounding runner lifecycle
  logs. `import logging` was already present at module scope.
- **Test posture**: no existing test asserted on the `"- [<host>] Logging
  to: <path>"` stdout substring (verified by ripgrep across
  `tests/unit/ssh/`); no test edits required. Existing
  `tests/unit/ssh/test_command_runner.py` suite remains green as-is (5
  passed).
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/ssh/command/command_runner.py`;
  targeted `pytest tests/unit/ssh/test_command_runner.py` runs 5 passed;
  full `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 27/N: retire `print()` in `src/refactors/wan2_migration_launcher.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/refactors/wan2_migration_launcher.py` with `logging.warning(...)`
  using `%`-style deferred formatting. `WAN2MigrationLauncher._handle_fatal_error`
  now surfaces the user-visible error banner via
  `logging.warning("ERROR: %s", error)` so the operator-facing message flows
  through the same handler chain as the paired
  `logging.error("Error running WAN2 Migration: %s", error, exc_info=True)`
  record. `import logging` was already present at module scope.
- **Test posture**: `tests/unit/refactors/test_wan2_migration_launcher.py` had
  three tests (`TestLaunchFatalError::test_launch_wire_failure_logs_and_prints`,
  `TestLaunchFatalError::test_launch_execute_failure_logs_and_prints`, and
  `TestHandleFatalError::test_prints_and_logs`) rewritten from
  `capsys.readouterr().out` to `caplog.text`. Each `caplog.at_level(logging.ERROR)`
  context was widened to `logging.WARNING` so the new banner emission is
  captured alongside the pre-existing ERROR log entry. Assertion substrings
  (`"ERROR: wire boom"`, `"ERROR: flow boom"`, `"ERROR: boom-direct"`) are
  preserved verbatim. The `capsys` parameter and the header comment
  mentioning `capsys` were removed.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/refactors/wan2_migration_launcher.py`;
  targeted `pytest tests/unit/refactors/test_wan2_migration_launcher.py` runs
  8 passed; full `pytest` suite green (8949 passed, 0 failed, 77 skipped,
  5 xfailed, 1 xpassed).

### #886 Phase 2 slice 26/N: retire `print()` in `src/refactors/service_ping_launcher.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/refactors/service_ping_launcher.py` with `logging.warning(...)`
  using `%`-style deferred formatting. `ServicePingLauncher._handle_fatal_error`
  now surfaces the user-visible error banner via
  `logging.warning("ERROR: %s", error)` so the operator-facing message flows
  through the same handler chain as the paired
  `logging.error("Error running Service Ping: %s", error, exc_info=True)`
  record. `import logging` was already present at module scope.
- **Test posture**: `tests/unit/refactors/test_service_ping_launcher.py` had
  three tests (`TestLaunchFatalError::test_launch_wire_failure_logs_and_prints`,
  `TestLaunchFatalError::test_launch_execute_failure_logs_and_prints`, and
  `TestHandleFatalError::test_prints_and_logs`) rewritten from
  `capsys.readouterr().out` to `caplog.text`. Each `caplog.at_level(logging.ERROR)`
  context was widened to `logging.WARNING` so the new banner emission is
  captured alongside the pre-existing ERROR log entry. Assertion substrings
  (`"ERROR: wire boom"`, `"ERROR: execute boom"`, `"ERROR: boom-direct"`) are
  preserved verbatim. The `capsys` parameter and the docstring header comment
  mentioning `capsys` were removed.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/refactors/service_ping_launcher.py`;
  targeted `pytest tests/unit/refactors/test_service_ping_launcher.py` runs
  8 passed; full `pytest` suite green (8949 passed, 0 failed, 77 skipped,
  5 xfailed, 1 xpassed).

### #886 Phase 2 slice 25/N: retire `print()` in `src/export/org_alarm_event_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/export/org_alarm_event_exporter.py` with `logging.warning(...)`
  using `%`-style deferred formatting. The `OrgAlarmEventExporter.device_events()`
  operator-visible export banner now emits
  `logging.warning("! %s device events exported to OrgDeviceEvents.csv", len(events))`
  so the confirmation reaches the same handler chain as the surrounding
  `logging.info(...)` records. `import logging` was already present at module
  scope.
- **Test posture**: `tests/unit/export/test_org_alarm_event_exporter.py::
  TestDeviceEvents::test_with_events_logs_sample` was rewritten from
  `capsys.readouterr().out` to `caplog.text`. Pytest's default WARNING-level
  caplog capture is sufficient here (no autouse DEBUG fixture required); the
  assertion substring `"3 device events exported"` is preserved verbatim.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/export/org_alarm_event_exporter.py`;
  targeted `pytest tests/unit/export/test_org_alarm_event_exporter.py` runs
  10 passed; full `pytest` suite green (8949 passed, 0 failed, 77 skipped,
  5 xfailed, 1 xpassed).

### #886 Phase 2 slice 24/N: retire `print()` in `src/export/org_admin_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/export/org_admin_exporter.py` with `logging.warning(...)`. The
  completion banner at the tail of `OrgAdminExporter.usage()` now emits
  `logging.warning(" License usage data exported to OrgUsage")` so the
  operator-visible confirmation flows through the same handler chain as the
  pre-existing `logging.info(...)` companion record. `import logging` was
  already present at module scope.
- **Test posture**: `tests/unit/export/test_org_admin_exporter.py::
  test_usage_delegates_to_apidata_fetcher_execute` was rewritten from
  `capsys.readouterr().out` to `caplog.text`. Pytest's default WARNING-level
  caplog capture is sufficient here (no autouse DEBUG fixture required); the
  assertion substring `"License usage data exported to OrgUsage"` is preserved
  verbatim.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/export/org_admin_exporter.py`; targeted
  `pytest tests/unit/export/test_org_admin_exporter.py` runs 14 passed; full
  `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 23/N: retire `print()` in `src/export/data_exporter.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 1 remaining `print()`
  call in `src/export/data_exporter.py` with `logging.warning(...)` using
  `%`-style deferred formatting. The `PermissionError` branch of
  `_write_csv_with_exception_handling` now emits
  `logging.warning("! Cannot write to %s. Is it open in another program?",
  csv_file_path)` so the operator-visible hint arrives through the same
  handler chain as the accompanying `logging.error(...)` record.
  `import logging` was already present at module scope.
- **Test posture**: `tests/unit/export/test_data_exporter.py::
  TestWriteCsvWithExceptionHandling::test_permission_error_reraises` was
  rewritten from `capsys.readouterr().out` to `caplog.text`. Pytest's
  default WARNING-level caplog capture is sufficient here (no autouse
  DEBUG fixture required); the assertion substring `"another program"`
  is preserved verbatim.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining T201 matches in `src/export/data_exporter.py`; targeted
  `pytest tests/unit/export/test_data_exporter.py` runs 68 passed; full
  `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 22/N: retire `print()` in `src/ssh/ssh_runner_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 40 remaining `print()`
  calls in `src/ssh/ssh_runner_manager.py` with `logging.warning(...)` for
  user-visible banners covering the full SSH-runner setup flow: prompt
  headers, missing-data notices, gateway-template listing and selection
  errors, online-gateway target listing, cancellation notices, credential
  and command validation errors, and post-execution success/failure counts.
  All migrated call sites use `%`-style deferred formatting so record args
  stay unrendered when the level is filtered out. `import logging` was
  already present at module scope.
- **Test posture**: `tests/unit/ssh/test_ssh_runner_manager_extended.py`
  gains an autouse `_capture_all_log_levels` fixture that pins
  `caplog.set_level(logging.DEBUG)` for parity with earlier SSH slices, and
  all 26 `capsys.readouterr().out` assertions against migrated banners were
  rewritten to read `caplog.text`. Assertion substrings and their case
  sensitivity were preserved verbatim so behavioral coverage is unchanged.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining `print(` matches in `src/ssh/ssh_runner_manager.py`; targeted
  `pytest tests/unit/ssh/test_ssh_runner_manager.py
  tests/unit/ssh/test_ssh_runner_manager_extended.py` runs 70 passed; full
  `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 21/N: retire `print()` in `src/ssh/cli_shell_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 11 remaining `print()`
  calls in `src/ssh/cli_shell_manager.py` with `logging.warning(...)` for
  user-visible banners (session-create failure, connection lost, exit banner,
  send-error, pyte-missing install hint, WebSocket connect/connected) and
  `logging.debug(...)` for `if debug:`-gated traces (resize payload, raw recv,
  outgoing keystroke, wakeup handshake). All migrated call sites use
  `%`-style deferred formatting so record args stay unrendered when the level
  is filtered out. `import logging` added in the alphabetical stdlib block.
- **Test posture**: `tests/unit/ssh/test_cli_shell_manager.py` gains an
  autouse `_capture_all_log_levels` fixture that pins `caplog.set_level(
  logging.DEBUG)` because this module has both `logging.debug` and
  `logging.warning` sites and pytest's caplog defaults to WARNING. All 7
  `capsys.readouterr()` assertions against migrated banners were rewritten to
  read `caplog.text`, matching the pattern established in earlier slices.
- **Verification**: `ruff check` reports 0 issues; `black --check` clean;
  0 remaining `print(` matches in `src/ssh/cli_shell_manager.py`; targeted
  `pytest tests/unit/ssh/test_cli_shell_manager.py` runs 33 passed; full
  `pytest` suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed,
  1 xpassed).

### #886 Phase 2 slice 20/N: retire `print()` in `src/ssh/ssh_runner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 2 remaining `print()`
  calls in `src/ssh/ssh_runner.py` with `logging.warning(...)`. The
  per-host command-completion banner (`_read_and_log_outputs`) now emits
  `logging.warning("- [%s] Command completed with exit status: %s", hostname,
  exit_status)` so operator-visible status arrives through the same handler
  chain as the rest of the SSH runner's structured logs. The disconnect
  banner (`_disconnect`) now emits `logging.warning(">> SSH connection
  closed")` for the same reason. Both records are WARNING level (not INFO)
  to preserve their default visibility on CLI runs where the root logger is
  typically configured to filter INFO.
- **Test posture**: no test changes required — the existing tests in
  `tests/unit/test_ssh_runner.py` and `tests/unit/ssh/test_ssh_runner_manager*.py`
  do not assert on either migrated banner, and neither uses
  `capsys.readouterr()` against those emission sites.
- **Verification**: `ruff check src/ssh/ssh_runner.py` reports 0 issues;
  `black --check` clean; targeted `pytest tests/unit/test_ssh_runner.py
  tests/unit/ssh/` runs 359 passed; full `pytest` suite green
  (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 19/N: retire `print()` in `src/troubleshooting/marvis_troubleshoot_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all `print()` calls in
  `src/troubleshooting/marvis_troubleshoot_utils.py` (the extracted Marvis
  client/device/network troubleshooting + insights workflows) with
  `logging.warning(...)` for operator-visible banners, `logging.info(...)` for
  structured pre/post API call records, `logging.debug(...)` for trace-level
  entry/exit, and `logging.error(...)` / `logging.exception(...)` for
  failure paths. Multi-line banners were consolidated into single
  `logging.warning` records so headers arrive atomically at every configured
  log handler: workflow entry banners (`client_connectivity`,
  `device_performance`, `network_connectivity`, `view_insights`) each collapse
  their menu header + divider into one record via
  `logging.warning("%s\n%s", _MENU_HEADER_X, _HEADER_SEP)`; the shared error
  guidance emitter (`_print_error_guidance`) assembles the failure message
  plus canned bullets into a `list[str]` and emits one
  `logging.warning("%s", "\n".join(lines))`; the raw-response preview helper
  (`_print_raw_response_preview`) emits a single record with the truncation
  suffix baked in; the raw-key preview helper (`_print_raw_keys_preview`)
  builds its diagnostic lines and emits atomically. Cancel-path messages and
  the static Marvis usage guide were folded into single WARNING records
  rather than one-print-per-line. Cosmetic blank `print()` spacers were
  dropped rather than emitted as empty log records.
- **Test migration (Changed)**:
  `tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py`
  swapped all `capsys.readouterr().out` assertions for `caplog.text` across
  every affected test and added a module-level autouse fixture
  (`_capture_warnings`) that calls `caplog.set_level(logging.WARNING)` so
  migrated warnings are captured deterministically across CI runners. The
  two ERROR-routed paths (`test_view_insights_exception_hits_error_handler`,
  `test_handle_insights_error_prints_guidance`) are wrapped with
  `with caplog.at_level(logging.ERROR):` because `_handle_insights_error`
  emits at ERROR level. The small companion `test_marvis_troubleshoot_utils.py`
  received the same autouse fixture (even though it had no capsys usage) so
  both test modules share a consistent capture posture.
- **Verification**: `ruff check
  src/troubleshooting/marvis_troubleshoot_utils.py
  tests/unit/troubleshooting/test_marvis_troubleshoot_utils.py
  tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py`
  reports 0 issues; `black --check` clean; full `pytest` suite green
  (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 18/N: retire `print()` in `src/troubleshooting/interactive_test_runner.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 35 `print()` calls in
  `src/troubleshooting/interactive_test_runner.py` (interactive-safe
  systematic test suite runner) with `logging.warning(...)` for
  operator-visible banners and `logging.error(...)` for site-resolution
  failures. Multi-line UI blocks were consolidated into single
  `logging.warning` records so banners arrive atomically at every configured
  log handler and cannot interleave with concurrent producers:
  `_print_suite_header` (4 → 1 record for the header/note/timestamp/divider),
  `_print_summary_stats` (10 → 1 record covering the entire summary block),
  and `_print_option_listings` (2 static header lines → 1 record). Dynamic
  lists (`_print_tested_options`, `_print_skipped_options`) use the
  `logging.warning("%s", "\n".join(lines))` pattern to guard against
  format-string surprises from option descriptions or skip reasons. Dropped
  cosmetic blank-line `print()` spacers rather than emitting empty log
  records that would clutter handler output. `_log_selector_miss` combined
  its 2 diagnostic records into a single warning so the selector-miss
  notification stays atomic.
- **Test migration (Changed)**:
  `tests/unit/troubleshooting/test_interactive_test_runner.py` swapped
  `capsys.readouterr().out` assertions for `caplog.text` across the 5
  affected tests (`_log_selector_miss`, `_lookup_selector_site`,
  `_resolve_site_or_close` no-site, `_resolve_site_or_close` exception,
  `_print_skipped_options`, `_print_summary_verdict`) and added a
  module-level `autouse` fixture (`_capture_warnings`) that calls
  `caplog.set_level(logging.WARNING)` so migrated warnings are captured
  deterministically across CI runners. `_resolve_site_or_close` assertions
  were tightened with `caplog.at_level("ERROR")` because that path now
  routes via `logging.error`.
- **Verification**: `ruff check src/troubleshooting/interactive_test_runner.py
  tests/unit/troubleshooting/test_interactive_test_runner.py` reports 0
  issues; `black --check` clean; full `pytest` suite green (8949 passed, 0
  failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 17/N: retire `print()` in `src/troubleshooting/troubleshoot_utils.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 12 `print()` calls in
  `src/troubleshooting/troubleshoot_utils.py` (Marvis interactive
  troubleshooting menu dispatcher) with `logging.warning(...)` for
  operator-visible menu output. Consolidated the header/divider block (3 → 1
  record) and the numbered-options block (6 → 1 record) so each banner arrives
  atomically at every configured log handler and cannot interleave with
  concurrent producers. Invalid-choice and exit handlers now route their
  user-facing notice through `logging.warning` while retaining their existing
  audit-trail (`logging.warning`) and trace (`logging.debug`) records.
- **Test migration (Changed)**: `tests/unit/troubleshooting/test_troubleshoot_utils.py`
  swapped 12 `capsys.readouterr().out` assertions for `caplog.text` and added
  a module-level `autouse` fixture (`_capture_warnings`) that calls
  `caplog.set_level(logging.WARNING)` so the migrated warnings are captured
  deterministically across CI runners regardless of default logger
  propagation.
- **Verification**: `ruff check src/troubleshooting/troubleshoot_utils.py
  --select T20` reports 0 issues; full `ruff check .` clean; full `pytest`
  suite green (8949 passed, 0 failed, 77 skipped, 5 xfailed, 1 xpassed).

### #886 Phase 2 slice 16/N: retire `print()` in `src/org/org_ticket_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 45 `print()` calls in
  `src/org/org_ticket_manager.py` (Menus 188-193: list/create/comment/update/
  view/export org support tickets) with `logging.warning(...)` for the
  operator-visible ticket list table, ticket detail block, per-comment
  rendering, cancellation/help banners, and `logging.error(...)` for API
  failures (fetch errors, invalid selections, retrieval failures). Multi-line
  UI blocks were consolidated into single `logging.warning` records with
  embedded `\n` to preserve atomic log-record boundaries: 3-line list header +
  separator (3 → 1), 6-row ticket metadata block with top/bottom bars (8 → 1),
  and per-comment header + body (2 → 1). WHY-comments preserved on migrated
  lines.
- **Tests (Changed)**: migrated `tests/unit/test_org_ticket_manager.py` (63
  `capsys` refs) and `tests/test_ticket_manager.py` (20 `capsys` refs) to
  `caplog`, gated by a per-file autouse `caplog.set_level(logging.WARNING)`
  fixture so the tests deterministically observe the new WARNING/ERROR
  records across CI runners regardless of default logger propagation. No
  production behavior change; the visible surface (subject text, cancellation
  banner text, "no tickets" message text, ticket metadata) is identical to
  the pre-migration output.
- **Verification**: `ruff check --select T20 src/org/org_ticket_manager.py`
  → 0 issues; `grep -c "print(" src/org/org_ticket_manager.py` → 0; full
  worktree `ruff check .` clean; full pytest 8949 passed / 0 failed.

### #886 Phase 2 slice 15/N: retire `print()` in `src/org/org_config_migration_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 44 `print()` calls in
  `src/org/org_config_migration_manager.py` (the org WAN/Gateway config
  export/import bundle manager) with `logging.warning(...)` for operator-
  visible output (export banners, per-type object counts, export summary
  table with dashed rule totals, bundle-file selection prompts, bundle
  preview metadata, IMPORT safety warning, per-object OK/SKIP status,
  import report header, and per-status totals block) and
  `logging.error(...)` for failure paths (per-type fetch errors,
  invalid-selection guidance, bundle load errors, source/dest validation
  errors, and per-object create failures). Multi-line print blocks were
  consolidated into single `logging.warning` records with embedded `\n`
  to keep atomic groups intact under logging's one-record-per-call model:
  export summary header (5 → 3), no-bundles guidance (2 → 1), source-org
  WARNING (2 → 1), bundle preview trio (4 → 2), IMPORT safety WARNING
  (2 → 1), and IMPORT REPORT header (3 → 1). All f-string formatting was
  converted to %-style deferred args per the print-avoidance rule (T20
  selector target of #886). No companion test file exists for this
  manager. Full unit suite still passes (8529/8529). No behavior change;
  only the emission channel moves from `stdout` to the root logger's
  WARNING/ERROR streams.

### #886 Phase 2 slice 14/N: retire `print()` in `src/wan_vpn_builder.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 40 `print()` calls in
  `src/wan_vpn_builder.py` (the WAN Hub-Spoke VPN Builder backing Menu 164)
  with `logging.warning(...)` for operator-visible output (headers, existing-
  VPN table, profile list, VPN preview, path-keys preview, role legend,
  cancellation / no-op acks, per-profile update summary) and
  `logging.error(...)` for API-failure paths (missing org, VPN create
  failures, profile update failures). Multi-line table headers
  (`_display_existing_vpns` and `_display_profile_list` three-line preambles;
  the four-line `_display_vpn_preview` header + threshold warning) were
  consolidated into single `logging.warning` records with embedded `\n` to
  keep header output atomic under logging's one-record-per-call model. Blank
  separator `print()`s became `logging.warning("")` for the same reason. All
  f-string formatting was converted to %-style deferred args per the
  print-avoidance rule (T20 selector target of #886). Companion unit tests
  in `tests/unit/test_wan_vpn_builder.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with
  `caplog.set_level(logging.WARNING)` on all five affected tests. Full unit
  suite still passes (8529/8529). No behavior change; only the emission
  channel moves from `stdout` to the root logger's WARNING/ERROR streams.

### #886 Phase 2 slice 13/N: retire `print()` in `src/wan_hub_group_manager.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 30 `print()` calls in
  `src/wan_hub_group_manager.py` (the WAN Hub Group Number Manager backing
  Menu 163) with `logging.warning(...)` for operator-visible output
  (banners, profile list rows, action menu, selection echoes, pod-value
  validation errors, cancel acks, no-op reasons, mixed-pod warnings, final
  update summary) and `logging.error(...)` for API-failure paths
  (`_MSG_ERR_PROFILES`, `_MSG_ERR_VPNS`, per-VPN `updateOrgVpn` failure).
  WARNING/ERROR are the two levels visible under the default root-logger
  configuration, preserving the pre-migration UX. The six-line action-menu
  banner (`_display_action_menu`) was consolidated into a single multi-line
  `logging.warning` with embedded `\n` because logging emits one record per
  call and per-line emission would fragment the output visually. The blank
  separator `print()` between the profile list header and the numbered
  entries became `logging.warning("")` for the same reason. All f-string
  formatting was converted to %-style deferred args per the print-avoidance
  rule (T20 selector target of #886). Companion unit tests in
  `tests/unit/test_wan_hub_group_manager.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with a
  `caplog.set_level(logging.WARNING)` (or `logging.ERROR` for the two
  API-failure assertions) prefix so the suite continues to assert the
  operator-visible output through the logging path. No behavioural change
  beyond the emit channel; all 8529 unit tests remain green.

### #886 Phase 2 slice 12/N: retire `print()` in `src/org_data_collector.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 16 `print()` calls in
  `src/org_data_collector.py` (the bulk org-level read sweep) with
  `logging.warning(...)` so the print-avoidance rule (T20 selector target of
  #886) can eventually be enabled repo-wide. WARNING level chosen for
  operator-visible cancel confirmation, category banners, per-operation
  progress lines (`... OK` / `FAILED (ExceptionClass)`), and the closing
  summary banner (Total / Succeeded / Failed / Skipped / Duration) so they
  surface on the default root-logger configuration (INFO is suppressed by
  default). The original streaming `print(..., end=" ", flush=True)` progress
  pattern was restructured into two complete lines per operation because the
  logging module has no partial-line output capability; the visible outcome
  is preserved. Companion unit tests in
  `tests/unit/test_org_data_collector.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with a
  `caplog.set_level(logging.WARNING)` prefix so the suite continues to assert
  the operator-visible output through the logging path. `_report_failure`
  keeps its `(api_name, error)` signature so the direct-call test needs no
  update beyond the fixture swap. No behavioural change beyond the emit
  channel; all 8529 unit tests remain green.

### #886 Phase 2 slice 11/N: retire `print()` in root `MistHelper.py` (issue #886)

- **Print-to-logger migration (Changed)**: replaced all 98 `print()` calls in
  the root `MistHelper.py` entry point with `logging.warning(...)` /
  `logging.info(...)` / `logging.error(...)` so the print-avoidance rule (T20
  selector target of #886) can eventually be enabled repo-wide. WARNING level
  chosen for operator-visible container-mode banners, credential preflight
  diagnostics, TUI activation/shutdown notices, non-interactive menu
  dispatch confirmations, and post-menu success/interrupt echoes so they
  surface on the default root-logger configuration (INFO is suppressed by
  default). ERROR level used for preflight rejections, TUI crashes, session
  initialisation failures, and post-menu exceptions. Three pre-logging
  stderr prints at the top of the file (before `import logging`) remain
  intentionally as `print(..., file=sys.stderr)` guarded by `# noqa: T201`
  because they must execute before the logging module is imported.
  Companion unit tests in
  `tests/unit/test_credential_preflight.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with a
  `caplog.set_level(logging.ERROR)` prefix so the suite continues to assert
  the operator-visible failure output through the logging path. No
  behavioural change beyond the emit channel; all 8529 unit tests remain
  green.

### #886 Phase 2 slice 10/N: retire `print()` in `src/reports/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the remaining `print()`
  calls in `src/reports/e911_bssid.py`,
  `src/reports/global_wired_client_report_generator.py`,
  `src/reports/offline_device_reporter.py`,
  `src/reports/sfp_transceiver_data_processor.py`, and
  `src/reports/wired_client_manufacturer_report_generator.py` with
  `logging.warning(...)` / `logging.info(...)` / `logging.error(...)` so
  the print-avoidance rule (T20 selector target of #886) can eventually be
  enabled repo-wide. WARNING level chosen for operator-visible report
  headers, threshold prompts, per-type/per-site breakdowns, CSV-write
  confirmations, and all-clear/no-devices notices so they surface on the
  default root-logger configuration (INFO is suppressed by default).
  Companion unit tests in
  `tests/unit/reports/test_global_wired_client_report_generator.py`,
  `tests/unit/reports/test_offline_device_reporter.py`,
  `tests/unit/reports/test_sfp_transceiver_data_processor.py`,
  `tests/unit/reports/test_wired_client_manufacturer_report_generator.py`,
  and `tests/unit/test_e911_bssid.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with a
  `caplog.set_level(logging.WARNING)` prefix so the suite continues to
  assert operator-visible output through the logging path. No behavioural
  change beyond the emit channel; all 203 tests under
  `tests/unit/reports/` + `tests/unit/test_e911_bssid.py` remain green.

### #886 Phase 2 slice 9/N: retire `print()` in `src/auth/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the remaining `print()`
  calls in `src/auth/interactive/clouds.py`,
  `src/auth/interactive/credential_prompter.py`,
  `src/auth/interactive/login_orchestrator.py`, and
  `src/auth/interactive/msp_org_selector.py` with `logging.warning(...)` /
  `logging.error(...)` / `logging.info(...)` / `logging.debug(...)` so the
  print-avoidance rule (T20 selector target of #886) can eventually be
  enabled repo-wide. WARNING level chosen for operator-visible cloud/MSP/org
  menu banners, credential-validation banners, auth-failure messages, 2FA
  prompts, and paginated-picker status output so they surface on the default
  root-logger configuration (INFO is suppressed by default). Companion unit
  tests in `tests/unit/auth/interactive/test_credential_prompter.py`,
  `tests/unit/auth/interactive/test_login_orchestrator.py`, and
  `tests/unit/auth/interactive/test_msp_org_selector.py` were migrated from
  `capsys`/`captured.out` to `caplog`/`caplog.text` with a
  `caplog.at_level(logging.WARNING)` wrapper around each call site so the
  suite continues to assert operator-visible output through the logging path.
  No behavioural change beyond the emit channel; all 96 tests under
  `tests/unit/auth/` remain green.

### #886 Phase 2 slice 8/N: retire `print()` in `src/ssid_consolidation/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the remaining `print()`
  calls in `src/ssid_consolidation/ssid_template_consolidation.py`,
  `src/ssid_consolidation/_ssid_template_cache.py`,
  `src/ssid_consolidation/_ssid_template_cluster.py`,
  `src/ssid_consolidation/_ssid_template_phase1.py`,
  `src/ssid_consolidation/_ssid_template_phase2.py`,
  `src/ssid_consolidation/_ssid_template_phase3.py`, and
  `src/ssid_consolidation/_ssid_template_phase45.py` with `logging.warning(...)`
  so the print-avoidance rule (T20 selector target of #886) can eventually be
  enabled repo-wide. WARNING level chosen for operator-visible phase banners,
  plan-summary tables, conflict listings, phase-menu output, "Phase 1 cache
  not found" bail messages, and per-phase status footers so they surface on
  the default root-logger configuration (INFO is suppressed by default).
  Companion unit tests in `tests/unit/test_ssid_template_consolidation.py`
  were migrated from `capsys`/`captured.out` to `caplog`/`caplog.text` with
  a `caplog.at_level(logging.WARNING)` wrapper around each call site so the
  suite continues to assert operator-visible output through the logging path.
  No behavioural change beyond the emit channel; all 241 tests in the module
  remain green.

### #886 Phase 2 slice 7/N: retire `print()` in `src/ui/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the remaining `print()`
  calls in `src/ui/prompt_utils.py`, `src/ui/tui.py`,
  `src/ui/runtime/tui_runner.py`, and `src/ui/interactive_display_utils.py`
  with `logging.warning(...)` / `logging.error(...)` / `logging.exception(...)`
  so the print-avoidance rule (T20 selector target of #886) can eventually be
  enabled repo-wide. Existing paired `print(...)` + `logging.info/error/warning(...)`
  emit sites were collapsed into single log calls to avoid double-emission
  (notably the Rich-missing fatal in `MistHelperTUI._init_rich` and the
  TUI exit banner in `TuiRunner.run`). WARNING level chosen for operator-visible
  interactive UI surfaces (site/device selection headers, "Loading site
  information", "Found N clients", legend/summary lines, per-selection
  "Site: ..." confirmations, "Invalid site index", "No devices ..." notices,
  "site" vs "organization" fetch scope hints, "No site selected", and the TUI
  "\[EXIT] ... closed" banner) so they surface on the default root-logger
  configuration (INFO is suppressed by default); ERROR level retained for the
  Rich-import fatal in `MistHelperTUI._init_rich`. Companion unit tests in
  `tests/unit/ui/test_prompt_utils.py` (~13 tests across the site-selection,
  device-inventory, client-fetch, sites-cache, client-summary, client-table,
  and extract-selected-client suites) and
  `tests/unit/ui/test_tui.py::TestInitRich::test_import_error_triggers_sys_exit`
  were updated to assert against `caplog.text` under
  `caplog.at_level(logging.WARNING/ERROR)` instead of `capsys.readouterr().out`;
  the Rich-missing assertion string was updated from `"Rich library required"`
  to `"Rich library not available"` to match the collapsed
  `logging.error(...)` message. Seventh of ~20+ per-subdirectory slices of #886;
  T20 selector flip and E402 audit will land after all `src/` subdirs are
  print-free.

### #886 Phase 2 slice 6/N: retire `print()` in `src/input/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 24 remaining `print()`
  calls in `src/input/prompt_client_utils.py` with `logging.warning(...)` /
  `logging.error(...)` / `logging.exception(...)` so the print-avoidance rule
  (T20 selector target of #886) can eventually be enabled repo-wide. Touched
  `select_client_mac` (empty-state notice, fetch-failure exception), the ten
  header/table/options lines in `_render_client_selection_prompt` (moved from
  `print()` to `logging.warning` so the interactive prompt UI still surfaces
  on the default root-logger config where INFO is suppressed),
  `_handle_client_selection_input` (non-digit and out-of-range validation
  hints), `_finalize_client_choice` ("Selected: ..." confirmation),
  `_parse_client_choice` (Exiting/valid-number/Invalid-index hints),
  `select_client` (heading + fetch-error), `_run_client_selection_flow`
  (no-clients notice), and `select_site_and_device_ids` (no-site / no-device
  notices). WARNING level chosen for operator-visible summaries so they
  surface on the default root-logger configuration (INFO is suppressed by
  default); ERROR level for the `select_client` failure path;
  `logging.exception` for `select_client_mac` so the fetch stack trace is
  preserved. Existing `print(...)` + `logging.info/error/warning(...)` pairs
  were collapsed into single log calls to avoid double-emission. Companion
  unit tests in `tests/unit/input/test_prompt_client_utils.py` (12 tests
  across 7 classes) were updated to assert against `caplog.text` under
  `caplog.at_level(logging.WARNING/ERROR)` instead of
  `capsys.readouterr().out`. Sixth of ~20+ per-subdirectory slices of #886;
  T20 selector flip and E402 audit will land after all `src/` subdirs are
  print-free.

### #886 Phase 2 slice 5/N: retire `print()` in `src/api/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 14 remaining `print()`
  calls in `src/api/api_data_fetcher.py` with `logging.warning(...)` /
  `logging.error(...)` so the print-avoidance rule (T20 selector target of
  #886) can eventually be enabled repo-wide. Touched `_log_entry` (fetch-start
  banner), `_log_retry_attempt` (retry backoff notice), `_save_recovered_data`
  (unexpected-structure + recovered-rows notices), `_handle_no_recovery`
  (unrecoverable-data notice), `_handle_rate_limit` (partial-save notice),
  `_emergency_save_and_raise` (emergency-save notice), `_handle_outer_exception`
  (no-data-collected notice), `_save_partial_data_on_error` (five-line summary
  block + save-failure error), and `_export_and_display_data` (records-exported
  notice). WARNING level chosen for operator-visible summaries so they surface
  on the default root-logger configuration (INFO is suppressed by default);
  ERROR level for the two failure paths (`_handle_no_recovery`,
  `_save_partial_data_on_error` write failure). Existing `print(...)` +
  `logging.info(...)` pairs were collapsed into single WARNING lines and the
  redundant error-path `print(...)` in `_handle_api_exception` was retired.
  Companion unit tests in `tests/unit/api/test_api_data_fetcher.py` (12 tests)
  were updated to assert against `caplog.text` under
  `caplog.at_level(logging.WARNING/ERROR)` instead of
  `capsys.readouterr().out`. Fifth of ~20+ per-subdirectory slices of #886;
  T20 selector flip and E402 audit will land after all `src/` subdirs are
  print-free.

### #886 Phase 2 slice 4/N: retire `print()` in `src/cache/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 9 remaining `print()`
  calls in `src/cache/cache_utils.py` with `logging.warning(...)` /
  `logging.error(...)` so the print-avoidance rule (T20 selector target of
  #886) can eventually be enabled repo-wide. Touched `clear_cache` (empty
  state, discovered-files banner, per-file list, cleared-summary), `_scan_cache_candidates`
  (I/O error path), `_delete_cache_files` (per-file OSError path),
  `create_address_parse_failures_csv` (success and failure notices), and
  `fast_cache_hit` (cache-hit notice). WARNING level chosen for operator-visible
  summaries so they surface on the default root-logger configuration (INFO is
  suppressed by default); ERROR level for the two failure paths. Existing
  `print(...)` + `logging.info(...)` pairs were collapsed into single WARNING
  lines to avoid double-emission. Companion unit tests in
  `tests/unit/cache/test_cache_utils.py` were updated to assert against
  `caplog.text` instead of `capsys.readouterr().out`. Fourth of ~20+
  per-subdirectory slices of #886; T20 selector flip and E402 audit will
  land after all `src/` subdirs are print-free.

### #886 Phase 2 slice 3/N: retire `print()` in `src/config/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 7 remaining `print()`
  calls in `src/config/config_utils.py` with `logging.error(...)` /
  `logging.warning(...)` so the print-avoidance rule (T20 selector target of
  #886) can eventually be enabled repo-wide. Touched
  `_resolve_org_id_via_prompt` (three `--test`/`--testinteractive`
  fail-closed messages, no-session guard, no-orgs-returned guard) and
  `check_stop_signal` (stop-signal detection notice). ERROR level chosen for
  the fatal-abort paths and WARNING for the operator-visible stop notice so
  both surface on the default root-logger configuration (INFO is suppressed by
  default). The `check_stop_signal` `print(...)` + `logging.info(...)` pair
  was collapsed into a single WARNING line. Companion unit test
  `tests/unit/test_config_utils_org_id_preflight.py::test_test_mode_fails_closed_without_calling_select_org`
  was updated to assert against `caplog.text` instead of
  `capsys.readouterr().out`. Third of ~20+ per-subdirectory slices of #886;
  T20 selector flip and E402 audit will land after all `src/` subdirs are
  print-free.

### #886 Phase 2 slice 2/N: retire `print()` in `src/audit/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 6 remaining `print()`
  calls in `src/audit/audit_analysis_ops.py` with `logging.warning(...)` so the
  print-avoidance rule (T20 selector target of #886) can eventually be enabled
  repo-wide. Touched `_prompt_audit_time_range_input` (time-range examples
  banner), `_render_audit_analysis_reports` (Mermaid + HTML report paths), and
  `audit_log_analysis` (fetch banner, raw-entry count, filter summary). WARNING
  level chosen so operators still see the summary on the default root-logger
  configuration (INFO is suppressed by default; WARNING is not). Companion
  unit tests in `tests/unit/audit/test_audit_analysis_ops.py` were updated to
  assert against `caplog.text` instead of `capsys.readouterr().out`. Second of
  ~20+ per-subdirectory slices of #886; T20 selector flip and E402 audit will
  land after all `src/` subdirs are print-free.

### #886 Phase 2 slice 1/N: retire `print()` in `src/utils/` (issue #886)

- **Print-to-logger migration (Changed)**: replaced the 3 remaining `print()`
  calls in `src/utils/` with `logging.warning(...)` so the print-avoidance rule
  (T20 selector target of #886) can eventually be enabled repo-wide. Touched
  `src/utils/input_utils.py` (`_handle_eof` / `_handle_interrupt`) and
  `src/utils/filter_operator_engine.py` (`validate_operator_value`). Collapsed
  the previous `print(...)` + `logging.info(...)` pairs into a single WARNING
  line each so operators still see the notice on the default root-logger
  configuration (INFO is suppressed by default; WARNING is not). Companion
  unit tests in `tests/unit/utils/test_input_utils_wave9.py` and
  `tests/unit/utils/test_filter_operator_engine.py` were updated to assert
  against `caplog.text` instead of `capsys.readouterr().out`. First of ~20+
  per-subdirectory slices of #886; T20 selector flip and E402 audit will land
  after all `src/` subdirs are print-free.

### Menu 205: Search Org Mist Edge Events (spec 866 / issue #1374)

- **New menu 205 (Added)**: `OrgExportUtils.mist_edge_events()` wraps the
  previously unreachable Mist API `searchOrgMistEdgeEvents` operation
  (`GET /api/v1/orgs/{org_id}/mxedges/events/search`). Provides the org-scope
  peer of the site-scoped `SiteMistEdgeEventsExporter` (menu 201) so operators
  can pull Mist Edge event history across every mxedge in the org in one shot
  rather than iterating sites. Delegates to the shared
  `OrgExportUtils.export_data` scaffold used by sibling `jsi_*` entrypoints:
  prompts for org (via `ConfigUtils.get_cached_or_prompted_org_id`), pages all
  rows through `APIDataFetcher` / `mistapi.get_all`, and persists via
  `DataExporter.write_with_format_selection` so CSV / SQLite / ArangoDB
  backends all work uniformly. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already
  registers the endpoint as `composite_pk` on `(id, mxedge_id, timestamp)` with
  indexes on `org_id` and `type` -- no schema changes required. Sort order
  stabilised on `timestamp` to align with the composite PK and yield newest-
  first output. Fulfills spec 866.

### Menu 204: Search Org JSI Assets and Contracts (spec 865 / issue #1373)

- **New menu 204 (Added)**: `OrgExportUtils.jsi_assets()` wraps the previously
  unreachable Mist API `searchOrgJsiAssetsAndContracts` operation
  (`GET /api/v1/orgs/{org_id}/jsi/inventory/search`). Delegates to the shared
  `OrgExportUtils.export_data` scaffold used by sibling `jsi_pbn` / `jsi_sirt`
  entrypoints: prompts for org (via `ConfigUtils.get_cached_or_prompted_org_id`),
  pages all rows through `APIDataFetcher` / `mistapi.get_all`, and persists via
  `DataExporter.write_with_format_selection` so CSV / SQLite / ArangoDB backends
  all work uniformly. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already registered the
  endpoint as `auto_increment_with_unique` with indexes on `org_id` and `serial`
  -- no schema changes required. Sort order stabilised on `serial` to match the
  PK index. Fulfills spec 865.

### Menu 203: Search Site WAN Client Events (spec 899 / issue #1407)

- **New menu 203 (Added)**: `WanClientEventsExporter` (delegated from
  `SiteClientExporter.wan_client_events`) prompts the operator to select a site from
  `SiteList.csv`, then calls
  `mistapi.api.v1.sites.wan_clients.events.search.searchSiteWanClientEvents` (paginated
  via `mistapi.get_all`, page size 1000). Site identifiers (`site_id` and `site_name`)
  are stamped onto every event row before the flattened, CSV-safe payload is persisted
  through `DataExporter.write_with_format_selection` — so CSV, SQLite, and
  ArangoDB+Redis backends all work uniformly. An empty response emits a fixed-schema
  sentinel CSV so downstream tooling still receives an artifact. Registered in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` as a `composite_pk` on `(id, timestamp)` with
  indexes on `site_id`, `ev_type`, and `wcid` so repeated runs upsert instead of
  duplicating. Fulfills spec 899.

### Menu 202: Search Site NAC Client Events (spec 891 / issue #1399)

- **New menu 202 (Added)**: `SiteNacClientEventsExporter.nac_client_events()` wraps
  the previously unreachable Mist API `searchSiteNacClientEvents` operation
  (`GET /api/v1/sites/{site_id}/nac_clients/events/search`). Operator picks a site
  (shared `SiteDeviceExporter._resolve_site_for_stats` helper), the exporter pages all
  NAC client event rows via `mistapi.get_all`, flattens + escapes them with
  `DataProcessingUtils`, then persists through `DataExporter.write_with_format_selection`
  so CSV / SQLite / ArangoDB backends all work. Empty responses surface a friendly
  "no NAC client event data" notice instead of failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  already defined a composite PK (`id`, `mac`, `timestamp`) for this operationId -- no
  schema changes required. Registered as `interactive_safe` in `OperationRegistry`
  (requires site selection).

### Menu 201: Search Site Mist Edge Events (spec 890 / issue #1398)

- **New menu 201 (Added)**: `SiteMistEdgeEventsExporter.mist_edge_events()` wraps
  the previously unreachable Mist API `searchSiteMistEdgeEvents` operation
  (`GET /api/v1/sites/{site_id}/mxedges/events/search`). Operator picks a site (shared
  `SiteDeviceExporter._resolve_site_for_stats` helper), the exporter pages all Mist Edge
  event rows via `mistapi.get_all`, flattens + escapes them with `DataProcessingUtils`,
  then persists through `DataExporter.write_with_format_selection` so CSV / SQLite /
  ArangoDB backends all work. Empty responses surface a friendly "no Mist Edge event
  data" notice instead of failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defined a PK
  for this operationId -- no schema changes required. Registered as `interactive_safe` in
  `OperationRegistry` (requires site selection).

### Menu 200: Search Site Guest Authorization (spec 889 / issue #1397)

- **New menu 200 (Added)**: `SiteGuestAuthorizationExporter.guest_authorizations()` wraps
  the previously unreachable Mist API `searchSiteGuestAuthorization` operation
  (`GET /api/v1/sites/{site_id}/guests/search`). Operator picks a site (shared
  `SiteDeviceExporter._resolve_site_for_stats` helper), the exporter pages all authorized
  guest rows via `mistapi.get_all`, flattens + escapes them with `DataProcessingUtils`,
  then persists through `DataExporter.write_with_format_selection` so CSV / SQLite /
  ArangoDB backends all work. Empty responses surface a friendly "no guest authorization
  data" notice instead of failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defined a PK
  for this operationId -- no schema changes required. Registered as `interactive_safe` in
  `OperationRegistry` (requires site selection).

### Menu 199: Search Site Webhook Deliveries (spec 902 / issue #1410)

- **New menu 199 (Added)**: `SiteWebhookDeliveriesExporter.deliveries()` wraps the
  previously unreachable Mist API `searchSiteWebhooksDeliveries` operation
  (`GET /api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search`). Operator picks a
  site (shared `SiteDeviceExporter._resolve_site_for_stats` helper), then picks a webhook
  by 1-based index from `listSiteWebhooks`, and the exporter pages all delivery attempts
  via `mistapi.get_all`, flattens + escapes them with `DataProcessingUtils`, then persists
  through `DataExporter.write_with_format_selection` so CSV / SQLite / ArangoDB backends
  all work. Empty responses surface a friendly "no webhook delivery data" notice instead
  of failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defined a composite PK on
  `(id, timestamp)` for this operationId -- no schema changes required. Registered as
  `interactive_safe` in `OperationRegistry` (requires site + webhook selection).

### Menu 198: Search Site WAN Usages (spec 901 / issue #1409)

- **New menu 198 (Added)**: `SiteWanUsageExporter.wan_usages()` wraps the previously
  unreachable Mist API `searchSiteWanUsage` operation
  (`GET /api/v1/sites/{site_id}/wan_usages/search`). Operator picks a site (shared
  `SiteDeviceExporter._resolve_site_for_stats` helper), the exporter pages all rows via
  `mistapi.get_all`, flattens + escapes them with `DataProcessingUtils`, then persists
  through `DataExporter.write_with_format_selection` so CSV / SQLite / ArangoDB backends
  all work. Empty responses surface a friendly "no WAN usage data" notice instead of
  failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defined a composite PK on
  `(mac, port_id, peer_mac)` for this operationId, and `arango_writer` already routed it
  to the `wan_usage` collection -- no schema changes required.

### Menu 197: Client Packet Capture Downloader (issue #421)

- **New menu 197 (Added)**: `ClientPacketCaptureDownloader` guides the operator through
  a four-step interactive flow — pick a site, pick a wireless client (by index or MAC
  in any punctuation), pick a VLAN grouping, then stream every completed PCAP for that
  VLAN into `data/packet_captures/<mac>/vlan_<id>/`. Uses
  `mistapi.api.v1.sites.clients.searchSiteWirelessClients` (7-day window, paginated via
  `mistapi.get_all`) and `mistapi.api.v1.sites.pcaps.listSitePacketCaptures`
  (client-MAC-filtered). Captures still in progress (no `pcap_url`) are skipped.
  Downloads stream in 8 KiB chunks with a 300 s timeout. Menu slots 195 and 196 were
  already occupied, so this feature registers as slot 197.

### Safe, Repeatable `--test` Clean Run (feature 1020)

- **Fail-closed `OperationRegistry` default (Fixed, Security)**: `OperationRegistry.get()`
  no longer defaults unregistered menu options to `safe` (a fail-**open** default that
  would let a credentialed `--test`/`--testinteractive` run silently invoke any
  unclassified option, including destructive menu 194). Unknown options now resolve to a
  new fail-**closed** `unregistered` category (a `SKIP_CATEGORIES` member), so they are
  ineligible for both test modes and surface a loud, actionable skip reason. All 60
  previously-unregistered `menu_actions` keys received explicit classifications
  (read-only exports -> `safe`; heavy sweeps 14/18 -> `resource_intensive`; ticket
  writes 189/190/191 and clone 194 -> `destructive`; ticket view 192 -> `interactive`),
  and three pre-existing destructive entries (175/176/186) gained the required
  `DESTRUCTIVE` marker.
- **Exhaustive menu/registry coverage guardrail (Added)**: replaced the brittle 11-key
  `WAVE1_ENTRY_ROUTING_BASELINE` sample as the sole coverage mechanism with
  `tests/guardrails/test_operation_registry_menu_coverage.py`, which asserts exact
  key-parity between `menu_actions` and the new
  `OperationRegistry.registered_options()` and fails CI the instant they diverge.
- **Isolated-venv install guard (Added, Security)**: `DependencyCheckOrchestrator` now
  refuses to auto-install/upgrade dependencies into a non-isolated (system) Python
  interpreter by default, distinguishing "no `.venv`" from "broken `.venv` launcher" in
  the diagnostic text. Override with `MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true`; the
  existing `DISABLE_AUTO_INSTALL` gate is unchanged.
- **Secret-safe credential/config preflight (Added)**: `_establish_mist_session()` now
  runs a host/token preflight (all modes) and `ConfigUtils` a non-interactive org-id
  guard (`--test`/`--testinteractive`) that fail closed with redacted, actionable
  messages referencing `deploy/.env.example` **before** any `mistapi`/`requests` call —
  preventing malformed-URL requests on a blank host and never leaking token contents.
- **`deploy/.env.example` clarification (Docs)**: documented that the non-interactive
  org-id path reads `org_id`/`ORG_ID` (not `MIST_ORG_ID`).
- **Gateway test runtime wiring (Fixed)**: menus 33 and 34 now configure the
  gateway runtime dependencies before either gateway inventory lookup or
  site-result service delegation. This fixes the credentialed menu-33
  systematic-test failure caused by an uninitialized `APICoreFetchUtils`.
- **Windows type-check compatibility (Fixed)**: the Unix-only container user
  detector now explicitly skips non-POSIX platforms and dynamically resolves
  Unix account APIs after that guard, preserving container behavior while
  allowing the configured `mypy src` check to pass on Windows.
- **Formatting baseline (Fixed)**: applied the repository's Black formatting to
  `MistHelper.py` and `tests/unit/test_lint_diagram_refs.py`.
- **Root security scan baseline (Fixed)**: replaced two runtime `assert`
  statements in dependency installation and upgrade paths with explicit
  package-specification guards, preventing optimization from removing the
  checks and leaving the root `MistHelper.py` Bandit scan clean.

### Mist API Coverage Audit

- **OpenAPI GET endpoint catalog + diff**: Added `tools/openapi_endpoint_catalog.py`
  which parses `documentation/mist-api-openapi31json.json`, emits
  `documentation/MIST_API_GET_ENDPOINTS.md` (508 GET ops across 190 tags) and
  `documentation/MIST_API_MISSING_ENDPOINTS.md` (408 GETs not yet wired into
  MistHelper.py). The tool is idempotent and runs `ruff` / `black` clean.
- **SpecKit feature scaffolds (408 specs)**: Generated `specs/500-mist-*` through
  `specs/907-mist-*` -- one feature dir per missing GET endpoint, each containing a
  `spec.md` parameterized from the OpenAPI metadata (operationId, path, tag,
  required/optional params, mistapi SDK module) and pre-checked against the
  Constitution (Inline Comments VI, Action Logging VII, 5-Item Rule, `safe_input`,
  `DataExporter`, `ENDPOINT_PRIMARY_KEY_STRATEGIES`, ASCII-only logging, README +
  CHANGELOG updates). Each spec is its own SpecKit workflow ready for
  `speckit.plan` / `speckit.tasks` / `speckit.implement`.

### Added

- Added menu `196` for `GetOrgLicenseAsyncClaimStatus` so operators can export org-level async claim-job summary data and optional per-device detail rows through `DataExporter` with composite upsert keys for SQLite/Redis/Arango backends.
- **Address audit now logs a per-phase timing breakdown (menu 195)**: a Tier-3 run
  spends 12-20 seconds per site and it was not obvious where that time went. A tiny
  always-on ``PhaseTimer`` now accumulates wall-clock time per stage (SQLite cache
  read, Tier-1 internal, Tier-2 Nominatim incl. its rate-limit sleep, Tier-3 browser
  total, and the Tier-3 sub-steps: locating the input, the human-like typing, the
  fresh-result poll incl. the suite grace, and the politeness delay). At the end of
  the run the audit logs the breakdown sorted slowest-first to ``data/script.log``,
  turning "it feels slow" into a measurement. Live data shows the human-like typing
  (``ui.type_query``) dominates -- tune it with ``UI_GEOCODE_MIN_KEY_DELAY_MS`` /
  ``UI_GEOCODE_MAX_KEY_DELAY_MS`` (faster typing trades against Google's bot
  heuristics), or lower the ``UI_GEOCODE`` politeness/timeout knobs.

- **Address audit now flags rows it cannot safely auto-correct, as review-only
  (menu 195)**: two new classification states protect against pushing a wrong or
  non-unique address to Mist, and both are **excluded from write-back** (they are
  never offered for push, and they show a blank Suggested Address so the operator
  decides by hand from the Mist/CSV/SNMP columns):
  - **`CONFLICTING_HINTS`** -- the Mist address, the customer CSV, and the SNMP
    location disagree on the **house number with no majority** (every hint names a
    different number, or only two hints have numbers and they differ). A 2-vs-1
    split still has a clear majority and is left alone (the lone dissenter is the
    outlier); a suite on a dissenting hint does not rescue it, because a suite is
    only meaningful on the agreed-upon street number. This stops the tool from
    silently picking one of several *different valid stores* for a single site --
    e.g. a real T-Mobile site whose SNMP location was stale ``1520 Route 38 ...
    Hainesport NJ`` while Mist and the CSV pointed at a Hawaii address.
  - **`DUPLICATE_ADDRESS`** -- two or more *different* sites resolve to the
    **identical** full address (same suite, or both lacking one), which would make
    them indistinguishable for shipping. Sites that share only a base street but
    carry *different* suites are the normal strip-mall case and are left untouched
    because their full addresses differ.

- **Address audit can now push corrected addresses back to Mist (menu 195)**: the
  audit was read-only; you reviewed the comparison and fixed addresses by hand.
  After saving the comparison report you are now offered an **optional write-back**.
  It is gated twice for safety: a single batch opt-in (`[y/N]`, default No), then a
  **per-site `[y/N]` confirmation** that shows the site's address BEFORE (current
  Mist value) and AFTER (the suggested correction) side by side. Only the sites you
  say yes to are written. The write is minimal and safe -- it fetches the full Mist
  site record, replaces **only** the `address` field, and PUTs the record back, so
  `latlng`, `timezone`, `country_code`, sitegroup and template IDs are all
  preserved. Each write is fail-soft: a read-only token (HTTP 403) or any API error
  is recorded as a failed outcome and never aborts the batch. Afterwards you are
  prompted to save a **before/after correction report**
  (`data/address_corrections_<timestamp>.csv`) listing every reviewed site and
  whether it was pushed, skipped, or failed. Only correctable rows are offered
  (MISSING_SUITE, MISSING_NUMBER, WRONG_STREET, CSV_BETTER, AMBIGUOUS); matches and
  Mist-better rows are never touched.

### Changed

- **Address audit suite/unit detection is consolidated and typo-tolerant (menu
  195)**: three modules (``address_resolver``, ``audit_engine``, ``ui_geocoder``)
  each defined their own suite/unit keyword regex, which drifted out of sync -- a
  real customer file spelled it ``Sute A-103`` and only some detectors recognized
  it, so that unit was dropped from the suggested address (cosmetic, but sloppy).
  All three now derive from a single ``SUITE_KEYWORDS`` constant in a shared
  ``suite_patterns`` module, so a spelling is added in exactly one place. The common
  misspelling ``sute`` is now recognized everywhere (``ste``/``Ste.`` were already
  covered); ``suit`` is deliberately excluded to avoid matching ``lawsuit`` /
  ``pursuit``. Detection/classification behavior is otherwise unchanged.

- **Address audit Source column now names Google explicitly (menu 195)**: the
  Tier-3 web authority is Google Places autocomplete, accessed by driving the Mist
  portal's address box, but the Source column labelled it only `Mist UI` -- which
  does not make it obvious that Google deduced the suggested address. It now reads
  `Google (Mist UI)` so it is unmistakable when Google found, filled in, or
  confirmed an address (the Issue Type column still says *what* changed:
  `MISSING_SUITE`/`MISSING_NUMBER`/`WRONG_STREET` mean Google corrected a blank,
  `ADDRESS_MATCH` means Google confirmed the existing value).

- **Address audit diagnostic logging no longer prints to the terminal (menu
  195)**: the audit's `logging.*` calls (e.g. the Nominatim "no result" warnings)
  were written to both `data/script.log` AND the console, where they interleaved
  with and corrupted the tqdm progress bar. The feature speaks to the operator
  exclusively through `print` (the comparison table, the prompts, the write-back
  confirmations), so its logging is purely a diagnostic trail. For the duration of
  a run a filter is attached to the root logger's CONSOLE handlers that drops only
  this package's records; the file handler is untouched, so `script.log` still
  captures everything while the terminal shows just the table, prompts, and a
  clean progress bar.

- **Address audit types into Google's box with a human-like, randomized cadence
  (menu 195)**: the Tier-3 geocoder previously typed each query at a fixed 40 ms
  cadence, which is robotic and risks Google's autocomplete throttling / bot
  heuristics. It now types one character at a time with a randomized
  inter-keystroke delay (default 60-190 ms, from an unpredictable `SystemRandom`
  source) plus an occasional longer "thinking" pause, so the input rhythm
  resembles a person. The bounds are tunable via `UI_GEOCODE_MIN_KEY_DELAY_MS` /
  `UI_GEOCODE_MAX_KEY_DELAY_MS`.

- **Address audit now flags incomplete Mist addresses (missing house number)
  (menu 195)**: a Mist site whose street had no house number (`S Federal Hwy`)
  was reported ADDRESS_MATCH against the web-resolved `2315 S Federal Hwy` --
  i.e. "no change needed" -- even though the street *number* was missing, which
  makes the address unshippable. A new ninth classification state,
  `MISSING_NUMBER`, now surfaces these so the operator can add the number the web
  found. Rows where Mist already has a house number are unaffected.

- **Address audit now adjudicates suite *conflicts*, not just missing suites (menu
  195)**: Tier-3 was skipped whenever the Mist address already carried any suite,
  so when the customer CSV claimed a *different* unit (Mist `#204` vs CSV
  `Suite H200` at the Mall at Millenia) the audit reported MIST_BETTER without ever
  checking which unit is real. Tier-3 now also runs when the CSV unit disagrees
  with Mist's, so the web adjudicates the correct shippable unit. Identical units
  expressed differently (`Suite 100` vs `Ste 100`) still skip the lookup.

- **Address audit query is now built by house-number consensus (menu 195)**: the
  geocoding query was built SNMP-location-first, so when a site's SNMP location
  pointed at a different address -- even a different state -- the audit geocoded
  the wrong place. One real T-Mobile site in Palm Beach Gardens, FL had an SNMP
  location of `1520 Route 38 ... Hainesport NJ`, and the audit "corrected" the FL
  store to a **New Jersey** address (a shipping-safety bug). The Mist address, the
  SNMP location, and the customer CSV are now treated as equal *hints*: the audit
  votes on the house number across all three and uses the agreed-upon, cleanest,
  suite-bearing source, so one bad hint can no longer hijack the query. SNMP
  directional glue (`SFederal` -> `S Federal`, `NMilitary` -> `N Military`) is
  repaired before voting. Tier 3 also retries once **without** the business-name
  prefix when the `"<business> <address>"` query returns nothing (a store may not
  sit at that exact number), which recovers rows that previously hit NO_RESULT.

- **Address audit Tier-3 now self-spawns a browser and deduces the suite (menu 195)**:
  Two gaps stopped the Mist-portal path from ever working. (1) Tier-3 only ever
  *took over* a browser at `localhost:9222` -- which nothing was running, and
  `localhost` resolved to IPv6 `::1` (`ECONNREFUSED`). The default mode is now
  `auto`: it takes over a running debuggable browser if present, otherwise it
  **spawns Edge for you**, waits while you log into Mist and open a site's
  settings page, then takes it over (CDP endpoint fixed to `127.0.0.1`). A
  one-time readiness probe confirms the "Location Search" box is visible and
  guides you to it if not. (2) Tier-3 never ran for the rows that needed it --
  `_combine` returned the Tier-1/Tier-2 result first, so Google-via-Mist (the
  only source that knows the real suite) was skipped on every MISSING_SUITE row.
  Tier-3 now runs whenever a suite is actually missing and, when it returns a
  confident result, **acts as the authority** (overriding the internal guess);
  if it returns nothing, results are exactly as before (graceful). The single
  `ADDRESS_AUDIT_GEOCODE` knob now accepts `off | auto | attach | launch`
  (default `auto`).

- **Address audit Tier-3 web geocoding is flag-free (menu 195)**: The Tier-3
  browser geocoder no longer requires the `--ui-geocode` CLI flag (removed). The
  Mist site address, the SNMP location variable, and the customer CSV are all
  treated as *hints*, fused into one best-guess query and verified against the
  web to deduce the true, shippable address.

### Fixed

- **Menu 196 prompted for `Org ID (UUID)` instead of using the configured org**:
  the async license-claim exporter
  (`LicenseExportUtils.export_org_license_async_claim_status`) was written to read a
  non-existent env var `MIST_ORG_ID` and then call `InputUtils.safe_input(...,
  default_value=...)`. `safe_input` always prompts -- `default_value` only supplies
  the fallback on empty ENTER -- so with no `MIST_ORG_ID` key set anywhere it always
  fell through to an interactive `Org ID (UUID):` prompt, ignoring the operator's
  configured org. It now uses the standard resolver
  `ConfigUtils.get_cached_or_prompted_org_id()` like every other menu operation
  (precedence: cached global -> `org_id`/`ORG_ID` env -> `.env` file -> interactive
  org picker only as a last resort). The same helpers also stopped using the
  deprecated naive `datetime.utcnow()` for their `polled_at_utc` column and now use
  timezone-aware `datetime.now(UTC)` to match the rest of the codebase. Unit tests
  updated to stub the resolver. (#576)

  (menu 195)**: Tier-3 types ``{business} {address}`` (including the suite) into the
  Mist dashboard's Google Places box, but Google's autocomplete often resolves to
  the street/establishment and drops a unit typed at the end -- and the freshness
  guard only waited for the *house number*, so it accepted the bare street without
  the unit. The unit then vanished from the suggestion, and because Mist also
  lacked it the row even read ``ADDRESS_MATCH`` ("no change needed"). A real run
  lost the unit on four sites whose CSV **and** SNMP location both confirmed it
  (FLSS2SJB ``Unit 200``, FLS01302 ``Suite 100``, FLS01501 ``Suite 98``, FLSE8677
  ``Unit 8``). Two changes fix this: (1) when a unit was typed, the freshness guard
  now waits a short bounded grace (``_SUITE_GRACE_S``) for the unit to also appear
  in the top suggestion before accepting it (Google usually catches up); and (2) if
  the unit still never appears, the unit we typed is re-appended to Google's street
  -- but only when it is safe (the suggestion carries no *other* unit, and the house
  numbers agree, so a different unit or a different building is never overwritten).
  Restored rows now correctly read ``MISSING_SUITE`` instead of a false
  ``ADDRESS_MATCH``, so the operator can add the unit.

- **Address audit suggestion glued the business name to Hawaii hyphenated house
  numbers (menu 195)**: the Tier-3 (Google-via-Mist) suggestion cleaner strips the
  establishment name that Google glues to the address (``T-Mobile931 US Highway
  ...`` -> ``931 US Highway ...``) by anchoring on the ``<house-number> <street>``
  start. Its anchor required the house number to be followed by a space, but
  Hawaii's grid addresses use a hyphenated house number (``74-5450``), so the
  anchor never matched and the business name survived in the output (real run:
  ``T-Mobile74-5450 Makala Blvd #107`` for site HIS00364). The anchor now accepts
  an optional ``-<digits>`` run in the house number, so the prefix is stripped
  (``74-5450 Makala Blvd #107``) while every non-hyphenated address and suite dash
  (``Sute A-103``) is unaffected.

- **Logging and on-screen output crashed on non-Western characters (all menus)**:
  running any operation against data containing characters outside the Windows
  console's default `cp1252` codec raised `UnicodeEncodeError` and dumped a
  `--- Logging error ---` traceback. This surfaced in the address audit (menu 195)
  with a real Hawaii dataset -- an address such as `315 East Makaʻala Street,
  Hawaiʻi County` contains the Hawaiian ʻokina (`U+02BB`), which crashed the
  `data/script.log` file handler and corrupted the progress bar. Both log file
  handlers are now opened with `encoding="utf-8"`, and `stdout`/`stderr` are
  reconfigured to UTF-8 with a `backslashreplace` fallback at startup, so the
  comparison table and any other `print` of international addresses are safe too.
  The fix is global (the logging setup lives in the root module) and fail-soft:
  if a stream cannot be reconfigured the worst case is the prior behavior, with no
  new failure introduced.

- **Address audit Nominatim suggestion leaked raw OpenStreetMap formatting (menu
  195)**: when a row was validated by Tier-2 (OpenStreetMap) rather than Tier-3,
  the "Suggested Address" showed OSM's verbose `display_name` -- e.g.
  `T-Mobile, 1200, Northwest 87th Avenue, Doral, Miami-Dade County, Florida,
  33172, United States` -- complete with the business name, county, and country.
  OSM only validates the *street*, so the suggestion is now Mist's own
  already-formatted address with the trailing country dropped
  (`1200 NW 87th Ave #1st, Doral, FL 33172`), consistent with the Tier-1/Tier-3
  outputs and never losing an existing suite. (Side effect: a row where Mist's
  address already matches now reads ADDRESS_MATCH instead of the misleading
  MIST_BETTER.)

- **Address audit MISSING_NUMBER never fired on real data (menu 195)**: the
  missing-house-number check (added in the prior release) tested the whole Mist
  address string for any digit, but Mist stores the address as one formatted
  string ending in the ZIP (`S Federal Hwy, Fort Pierce, FL 34982, USA`) -- so the
  ZIP's digits made every address look like it already had a house number, and a
  number-less street was still reported ADDRESS_MATCH. The check now inspects only
  the leading street segment (before the first comma) for a leading house number,
  so `S Federal Hwy, ...` is correctly flagged MISSING_NUMBER against the
  web-resolved `2315 S Federal Hwy`. (The unit test was strengthened to use full
  Mist-style strings so it would have caught this.)

- **Address audit suggested address glued the street/suite to the city (menu
  195)**: Google's autocomplete sometimes returned the street fused to the city
  with no separator (`2315 S Federal HwyFort Pierce`, `...suite 330Brandon`),
  leaving an un-shippable suggested address. The cleaner now splits a street-type
  suffix (`Hwy`, `Blvd`, `Dr`, ...) or a number glued directly to a following
  capitalized city word, while deliberately preserving legitimately camel-cased
  cities (`DeFuniak`) and alphanumeric street names (`A1A`) -- only street
  suffixes and digits trigger a split, never a generic lowercase->uppercase
  boundary.

- **Address audit hid wrong-side-of-street addresses as a MATCH (menu 195)**: the
  street comparison ignored directionals, so a Mist address of `1606 E Jefferson`
  was reported as ADDRESS_MATCH against the web-confirmed `1606 West Jefferson` --
  East vs West are different streets, and shipping to the wrong one is a real risk.
  The comparison now flags a conflicting *leading* directional (the one right after
  the house number, so a directional inside a city name like `West Palm Beach` is
  ignored) as WRONG_STREET, while treating abbreviations as equal (`S` = `South`,
  `NW` = `Northwest`). The street-name comparison also now includes ordinal names
  (`107th`, `A1A`), so `1455 NW 107th Ave` reliably matches `1455 Northwest 107th
  Avenue` regardless of whether Google abbreviates or spells out the directional
  and street type.

- **Address audit suggested-address still showed the business name on number-first
  streets (menu 195)**: the suggestion cleaner stripped Google's glued business
  name only when the street name began with a letter, so rows whose street starts
  with a digit kept the prefix (`T-Mobile4103 14th St W`). It now strips the
  prefix in that case too (`4103 14th St W, Bradenton, FL 34205`) and splits a
  directional fused to the city (`...Ave NLive Oak` -> `...Ave N Live Oak`).

- **Address audit Tier-3 captured the WRONG suggestion (one-row lag) (menu 195)**:
  Google Places leaves the previous query's suggestions in the dropdown until the
  new request returns, so the geocoder read each address's result one lookup late
  -- every row was shifted by one and therefore wrong (e.g. the query for
  `1701 Ohio Ave` captured `7535 North Kendall Drive`). The geocoder now anchors
  on the query's house number and polls until the TOP suggestion actually
  contains it, dismissing the stale dropdown first; on timeout it returns
  NO_RESULT rather than risk a stale, wrong address. It also cleans Google's row
  text -- stripping the glued business-name prefix (`T-Mobile931 US Highway...`)
  and trailing `, USA` -- so the suggested value is the clean, shippable street
  line with its suite preserved (`931 US Highway 331 Ste A2, DeFuniak Springs, FL
  32435`). NOTE: anyone who ran the audit before this fix should re-run it and
  discard the prior output; the cached results were shifted.

- **Address audit misleading Nominatim log (menu 195)**: The "Nominatim returned
  no result" warning printed the business-name + suite query string even though
  the actual geocode used the suite-stripped street, making it look like the
  wrong thing was searched. It now logs the street actually geocoded.

- **Address audit suggested-address cleanup (menu 195)**: Suggested addresses
  were polluted with the customer's SAP internal store-code prefix
  (e.g. `S2SJB - `, `08806 - `) and sometimes carried the SNMP field's stale ZIP.
  The SNMP enricher now strips the leading SAP store code (it is not part of the
  postal address), and Tier-1 rebuilds a clean suggestion from Mist's own
  street/city/state/ZIP plus the discovered suite -- preferring the customer CSV
  suite over the SNMP one. The suite detector was broadened to catch `#3`,
  `Space P239`, `Spc`, `Rm`, `Lot`, and `Apartment` in addition to
  Suite/Ste/Unit/Apt/Bldg. Result: `S2SJB - 5550 N Military Trl Unit 200 ... FL
  33496` now renders as the clean, shippable `5550 N Military Trl Unit 200,
  Boca Raton, FL 33431`.

- **Address audit external validation via OpenStreetMap (menu 195)**: Nominatim
  (Tier 2) silently failed for every site because the resolver verified TLS
  certificates, which Zscaler SSL inspection breaks -- so the audit only ever
  used internal CSV/SNMP comparison and the "Source" column never showed external
  validation. The resolver now skips TLS verification for the public Nominatim
  call by default (override with `MIST_SKIP_SSL_VERIFY=false`), strips the
  suite/unit before geocoding (OpenStreetMap has no US retail suites) so the base
  street can match, validates the street on **every** row, and records a
  `street_validated` flag surfaced as `Internal+OSM` / `Nominatim` in the Source
  column. The Nominatim step now logs visibly (INFO on hit, WARNING on miss).
  Verified live: real streets validate (confidence ~0.88), nonsense streets do
  not. NOTE: OpenStreetMap validates the street only; business-name + suite
  confirmation still requires the optional Tier-3 Google-Places browser tier
  (auto-engaged when a debuggable browser is available).

- **Address audit CSV delimiter (menu 195)**: The CSV ingester assumed tab
  delimiters and silently skipped every row of a comma-delimited file (the Excel
  default `.csv`), reporting "No valid rows parsed". The delimiter is now
  **auto-detected** per file (tab / comma / semicolon / pipe), an Excel BOM is
  stripped, blank lines no longer count as parse failures, and addresses that
  contain the delimiter (e.g. "6670 US Highway 129, Suite 1") are reconstructed
  by parsing on the fixed serial/model + city/state/zip anchors. Verified against
  a real 44-row customer export (44 parsed, 0 skipped).

### Added -- site address audit from CSV

- **Site Address Audit from CSV (menu 195, read-only)**: New `src/site/address_audit/`
  subpackage that reconciles a customer-provided tab-delimited CSV (serial, model,
  address, city, state, zip) against Mist site records and surfaces address
  discrepancies (the common strip-mall "missing suite/unit" case for retail
  fleets). Pipeline: ingest + sanitize CSV -> match each row to a Mist site by
  device **serial number** (golden key) with a rapidfuzz >=85% address fallback
  -> enrich with SNMP location (`vars.snmp_location` + `snmp_config.location`)
  -> resolve/validate the address through three **free** tiers and classify into
  one of eight states -> render an old-vs-suggested comparison table -> optionally
  save a timestamped CSV to `data/`. **Zero Mist writes**; write-back is an inert
  `AddressCorrector` stub. Address resolution tiers (no paid APIs; there is no Mist
  geocoding endpoint): (1) internal CSV/SNMP/Mist comparison, no network;
  (2) Nominatim street validation reusing `NominatimValidator`; (3) optional
  Playwright "hijack" of the live Mist dashboard Location Search field
  (`--ui-geocode`, OFF by default) that launches or takes over (CDP) the system
  browser -- the only free path to Google-quality retail suite numbers. Results
  cached in an additive `geocoding_cache` table in `data/mist_data.db`
  (`INSERT OR REPLACE`). Classification anchors on the street house number plus a
  street-name word so SNMP store-number prefixes and partial addresses do not
  cause false `WRONG_STREET` results. Adds the `--ui-geocode` CLI flag and a
  `BUSINESS_NAME` `.env` lookup (prompted at runtime when blank, skippable for
  private addresses). 11 new modules + 8 unit-test files (58 tests). Spec:
  `specs/1003-site-address-audit/`.

### Lint / Compliance

- **Issue #429 -- CONV-LOG-FSTRING sweep**: Converted all 695 eager-formatting
  logging calls in `MistHelper.py` to lazy `%s`-style arguments
  (681 G004 + 6 G003 + 8 G201 -> 0). Delivered in four ~170-site tranches with
  a frozen parity-test baseline (`tests/fixtures/issue_429_log_baseline.json`)
  and four new test modules (parity, hypothesis property, codemod idempotency,
  lazy-sentinel) gating every tranche. Enabled the `G` ruff rule family in
  `[tool.ruff.lint] select` and scoped it to `MistHelper.py` only via
  `per-file-ignores`; `src/`, `tools/`, `web_portal/`, top-level helper
  scripts, and the codemod synthetic-input fixture retain eager formatting
  pending follow-up issues. Codemod (`tools/codemod_logging_lazy.py`) +
  capture script (`tools/capture_log_baseline.py`) preserved for re-runs.

### Dependency Updates

- Raised Mist API dependency floors to `mistapi>=0.63.1` in `requirements.txt`, `pyproject.toml`, and the runtime import manager so documented, packaged, and auto-install paths stay aligned.

### Compatibility Validation

- Live compatibility validation against `mistapi 0.63.1` succeeded for MistHelper session initialization plus representative org/site read paths: self lookup, sites, inventory, wireless clients, alarms, events, SLE exports, audit logs, and support tickets.

### Changed -- serial CC refactor extractions

- **Serial CC refactor (offender #8)**: Extracted `OrgClientSecurityExporter.security_events` workflow into `src/refactors/serial_cc/security_events.py` (`SecurityEventsService`) and reduced `MistHelper.py` method to thin delegator. Post-refactor Radon complexity in `MistHelper.py` is now `A (1)` for this symbol.
- **Serial CC refactor (offender #9)**: Extracted `OrgExportUtils.sle_metrics` workflow into `src/refactors/serial_cc/sle_metrics.py` (`SLEMetricsService`) and reduced `MistHelper.py` method to thin delegator. Post-refactor Radon complexity in `MistHelper.py` is now `A (1)` for this symbol.
- **Serial CC refactor**: Delegated `_LegacyPacketCaptureManager._start_site_client_capture_wireless` to `src/refactors/serial_cc/start_site_client_capture_wireless.py` (`SiteWirelessClientCaptureService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Delegated `_LegacyPacketCaptureManager._start_site_scan_capture` to `src/refactors/serial_cc/start_site_scan_capture.py` (`SiteScanCaptureService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `GlobalImportManager._get_global_assignments` into `src/refactors/serial_cc/global_assignments_builder.py` (`GlobalAssignmentsBuilderService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `SiteClientExporter.client_insights` into `src/refactors/serial_cc/site_client_insights.py` (`SiteClientInsightsService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `GlobalImportManager.initialize_all_imports` into `src/refactors/serial_cc/import_initialization_service.py` (`ImportInitializationService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Decomposed `OrgInventoryExporter.combined_inventory_with_site_info` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Decomposed `OrgDeviceStatsExporter.device_port_stats` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (3)`.
- **Serial CC refactor**: Decomposed `_LegacyPacketCaptureManager._execute_site_capture_loop_legacy` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (4)`.
- **Serial CC refactor**: Decomposed `OrgAlarmEventExporter.device_events_52w_legacy` in place into 7 class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity from `E (38)` to `B (8)`.
- **Serial CC refactor**: Decomposed `execute_with_connection_pool_management` in place into 3 module-level helpers (`_pool_configure`, `_pool_process_batch_wait_loop`, `_pool_log_batch_exception`) and reduced complexity from `D (21)` to `B (6)`.
- **Serial CC refactor**: Decomposed `run_systematic_test` in place into 4 module-level helpers (`_systematic_test_build_safe_list`, `_systematic_test_emit_skips`, `_systematic_test_run_option`, `_systematic_test_resolve_fast_mode`) and reduced complexity from `D (21)` to `B (8)`. No D or E grade offenders remain in `MistHelper.py`.

### Removed

- **Dead legacy classes**: Removed 5 orphaned `_Legacy*` classes (`_LegacyPacketCaptureManager`, `_LegacyGatewayStatsExporter`, `_LegacyGatewayExportUtils`, `_LegacyWAN2MigrationManager`, `_LegacyWANProbeDeviceOverrideManager`) from `MistHelper.py`. These were inline implementations retained for rollback safety after their logic was migrated to canonical classes (`PacketCaptureManager` -> `src/capture/`, `GatewayStatsExporter`, `GatewayExportUtils`, `WAN2MigrationManager`, `WANProbeDeviceOverrideManager`). Verified unreferenced (no instantiations, aliases, subclasses, or dynamic forwarders reach them). Deletion removed 3,939 lines (27,666 -> 23,722) and cleared the two worst CRITICAL complexity hotspots (`start_org_packet_capture_legacy` CC 53, `with_wan_overrides_legacy` CC 46). Compliance violations dropped 1440 -> 1214; classes 101 -> 96.

### Fixed -- menu 13 access point undercount

- **Menu 13 still undercounted APs (claimed-but-never-connected APs dropped)** (#417): Even after #415, AP counts were short because the AP path used `countOrgDevices(distinct="version")`, which only returns version-keyed buckets. APs that are **claimed and assigned to a site but have never connected** report no firmware version and were silently dropped (e.g. T-Mobile_USA_Retail AP41 showed 9428 vs the portal's 9676). These APs have a `site_id`, so the #415 unassigned supplement did not catch them either. APs are now counted directly from `getOrgInventory(type="ap")` — the same source as the portal "Claim APs" screen — so every claimed AP is counted exactly once with a three-way version bucket: `unassigned` (no `site_id`), the real firmware version (assigned + connected), or `unknown` (assigned but never connected). Switches and gateways are unchanged, and the unassigned supplement is now switch-only to avoid double counting APs. Conservation is verified against real inventory data and four new unit tests cover every AP state.
- **Menu 13 undercounted devices (unassigned AP/switch inventory excluded)** (#415): The Org Device Inventory Summary counted APs via `countOrgDevices` and switches via `searchOrgDevices`, both of which return only devices **assigned to a site**. Unassigned APs and switches sitting in org inventory were therefore omitted from the model-count, firmware-summary, and version-per-model reports, understating totals and leaving the reports internally inconsistent (gateways already used `getOrgInventory`, which includes unassigned stock). A supplemental `getOrgInventory(type="ap,switch")` fetch now pulls claimed-but-unassigned APs and switches (filtered client-side on a missing `site_id`), merges them into the model counts, and surfaces them under a dedicated `unassigned` firmware column in the firmware summary and version-per-model pivot (single-org and MSP combined). The `unassigned` bucket is kept distinct from `unknown` (an assigned device that never reported firmware). Assigned-but-offline/disconnected devices were already counted (the assigned-device APIs do not filter on connection state), so no change was needed there. Gateways are intentionally excluded from the supplemental fetch to avoid double counting.

## [26.06.09.22.10] - Fix E911BSSIDReportGenerator module-level access

### Fixed

- **Tests**: `tests/integration/test_mistapi_sdk_compatibility.py::test_maps_and_wlan_helpers_are_covered` and `test_e911_report_runs_with_stubbed_maps_and_wlans` no longer fail with `AttributeError: module 'MistHelper' has no attribute 'E911BSSIDReportGenerator'`. Moved `E911BSSIDReportGenerator` import from function-local (aliased as `_E911`) to module-level so tests can access it via `MistHelper.E911BSSIDReportGenerator`. Closes #364.

## [26.06.08] - Menu 194 Clone Device Config to Gateway Template

### Added

- **Menu 194**: Clone Device Config to Gateway Template — promote a gateway device's local configuration into a reusable org-level gateway template. Selects site → selects gateway device → fetches live device config via `getSiteDevice` → strips device metadata → prompts for template name/type/model → requires typed `CREATE` confirmation → calls `createOrgGatewayTemplate` → exports result to CSV. Implemented in `src/gateway/device_template_cloner.py` with delegation stub in `MistHelper.py`.

## [26.05.27.05.29] - Decomposition Wave 2 Complete (Phases 1-9)

### Added

- **9 feature-domain packages** extracted from `MistHelper.py` into `src/`:
  - `src/analytics/` — `SiteInventoryHealthAnalyzer`, `SiteAnalyticsConfigurator`, `ZoneConfigurationAnalyzer`
  - `src/capture/` — `PacketCaptureManager`, `PacketCaptureDownloadManager`
  - `src/export/` — `SiteExportUtils`, `SiteInsightsExporter`
  - `src/gateway/` — `GatewayExportUtils`, `GatewayStatsExporter`, `GatewayOverrideAnalyzer`, `WAN2MigrationManager`, `WanProbeDeviceOverrideManager`
  - `src/inventory/` — `OrgDeviceInventorySummaryCore`, `OrgDeviceInventoryMSPOrchestrator`, `InventoryCSVComparator`
  - `src/site/` — `SiteConfigManager`
  - `src/ssh/` — `EnhancedSSHRunner`, `SSHRunnerManager`
  - `src/troubleshooting/` — `MarvisTroubleshootUtils`
  - `src/websocket/` — `ServicePingManager`, `ServicePingDiscoveryMixin`
- Hard-gate evidence checklists for all 9 phases in `specs/193-main-decomposition-wave-2/checklists/`
- Wave 2 Module Ownership table in README.md documenting phase-to-package-to-menu mapping
- Updated `src/` directory layout in README.md reflecting actual feature-domain structure

### Changed

- `MistHelper.py` entrypoint now delegates to `src/` modules while preserving compatibility surface
- README Architecture Evolution section updated with current `src/` layout and decomposition status
- Packet capture ownership moved to `src/capture/` with `MistHelper.py` orchestration compatibility

### Fixed

- Restored packet capture legacy test compatibility by keeping wrapper hook behavior for `_poll_and_download_pcap`, `_poll_for_pcap_url`, and `_save_pcap_file`
- Prevented CI `exit code 2` by replacing `MagicMock(side_effect=KeyboardInterrupt)` with plain function in `TestPollAndDownloadPcap::test_keyboard_interrupt`

## [25.05.25.05.29] - Ticket Viewer & Detail Export

### Added

- **Menu 192**: Interactive ticket detail viewer with comments (`OrgTicketManager.view_ticket`)
- **Menu 193**: Export all tickets with full details and comments to CSV/SQLite (`OrgTicketManager.export_ticket_details`)
- Primary key strategy for `getOrgTicket` endpoint (natural PK on `id`)
- Private helpers: `_select_ticket`, `_fetch_ticket_detail`, `_display_ticket_detail`
- 7 new tests for menus 192-193 and `_select_ticket` helper

### Changed

- **Menu 190** (Add Comment): Refactored to use interactive ticket selector instead of raw ID prompt
- **Menu 191** (Update Ticket): Refactored to use interactive ticket selector instead of raw ID prompt
- `OrgTicketManager` class expanded from 4 to 6 public operations (list, create, add comment, update, view, export)
- Operation count updated: 191 → 193

## [25.06.13.00.00] - Support Ticket Management

### Added

- **Menu 188**: List/export all organization support tickets to CSV/SQLite (`OrgTicketManager.list_tickets`)
- **Menu 189**: Create a new support ticket with subject, type, and optional comment (`OrgTicketManager.create_ticket`)
- **Menu 190**: Add a comment to an existing ticket with optional file attachment (`OrgTicketManager.add_comment`)
- **Menu 191**: Update ticket fields (subject, status, type) on an existing ticket (`OrgTicketManager.update_ticket`)
- New `OrgTicketManager` class with full ticket lifecycle management
- Primary key strategies for `getOrgTicket`, `createOrgTicket`, `updateOrgTicket`, `addOrgTicketComment`
- Attachment support via `addOrgTicketCommentFile` multipart API (integrated into Menu 190)
- Comprehensive test suite: `tests/test_ticket_manager.py` (14 tests covering all 4 operations + edge cases)
- Operation count updated: 187 → 191

## [26.05.21.00.00] - Menu Regrouping

### Changed (BREAKING)

All 188 menu operations (0-187) renumbered into 30 logical contiguous groups. Any scripts or aliases that hard-code a `--menu N` number must be updated. The migration script `scripts/menu_regroup.py` was used to apply all 425 touch points (menu_actions keys, _REGISTRY keys, optimized_test_order values, WAVE1 baseline keys/values, and Menu #XX logging references).

**New group structure:**

| Range | Group | Safety |
| - | - | - |
| 0 | Exit | — |
| 1–7 | Org Sites & Analysis | safe |
| 8–14 | Org Device Inventory | safe |
| 15–19 | Org Device Stats | safe / resource_intensive |
| 20–26 | Org Events & Logs | safe |
| 27–30 | Org Client Stats | safe |
| 31–36 | Org Gateway Operations | safe |
| 37–41 | Org Templates | safe |
| 42–50 | Org Config & Admin | safe |
| 51–55 | Org SLE & Insights | safe |
| 56–59 | Org Misc Exports | safe / resource_intensive |
| 60–72 | Site Device Exports | interactive_safe |
| 73–79 | Site Insights & Anomalies | interactive_safe |
| 80–91 | Site Stats & Metrics | interactive_safe |
| 92–96 | Interactive Viewers | interactive_safe |
| 97–101 | Long-Running Exports | resource_intensive |
| 102–115 | WebSocket Show Commands | websocket |
| 116–123 | WebSocket Diagnostics | websocket |
| 124–127 | Device Diagnostics | interactive |
| 128–133 | Device Management | interactive |
| 134–135 | Packet Capture | interactive |
| 136–147 | Interactive Tools | interactive |
| 148–150 | Config Management | interactive |
| 151–152 | Continuous Loops | continuous_loop |
| 153 | Bulk | resource_intensive |
| 154–157 | Destructive: Firmware | destructive |
| 158–160 | Destructive: Reboot/Reprovision | destructive |
| 161–162 | Destructive: Virtual Chassis | destructive |
| 163–167 | Destructive: Template Changes | destructive |
| 168–170 | Destructive: Site Config | destructive |
| 171–174 | Destructive: Test Data | destructive |
| 175–176 | Destructive: SSH Runners | destructive |
| 177–187 | Destructive: Clear/Reset/Import | destructive |

**Complete old→new mapping (for migration reference):**

```text
0→0   1→20  2→21  3→22  4→31  5→102 6→103 7→104 8→105 9→134 10→135
11→1  12→8  13→15 14→19 15→16 16→33 17→9  18→59 19→34 20→2
21→11 22→10 23→4  24→17 25→12 26→32 27→3  28→35 29→62 30→65
31→60 32→61 33→63 34→64 35→37 36→38 37→39 38→40 39→41 40→27
41→28 42→24 43→29 44→30 45→42 46→44 47→45 48→46 49→69 50→66
51→67 52→68 53→73 54→47 55→48 56→136 57→49 58→43 59→50
60→137 61→138 62→139 63→97 64→98 65→99 66→51 67→52 68→74
69→75 70→92 71→93 72→94 73→95 74→96 75→151 76→152 77→100
78→101 79→140 80→121 81→76 82→54 83→53 84→77 85→78 86→79
87→118 88→119 89→120 90→154 91→158 92→161 93→162 94→14 95→18
96→36 97→175 98→176 99→155 100→156 101→141 102→148 103→149
104→163 105→150 106→164 107→171 108→172 109→173 110→174 111→165
112→142 113→166 114→167 115→143 116→157 117→144 118→168 119→6
120→169 121→7 122→170 123→123 124→106 125→107 126→108 127→109
128→110 129→111 130→112 131→113 132→114 133→115 134→116 135→117
136→124 137→125 138→128 139→129 140→159 141→122 142→160 143→130
144→131 145→132 146→133 147→177 148→178 149→179 150→180 151→181
152→182 153→183 154→184 155→185 156→126 157→127 158→26 159→145
160→89 161→90 162→91 163→146 164→147 165→153 166→5 167→56
168→57 169→55 170→70 171→71 172→72 173→88 174→25 175→186
176→58 177→187 178→80 179→81 180→82 181→83 182→84 183→85
184→86 185→23 186→87 187→13
```

Closes #368

## [26.05.20.17.31]

### Refactored

- `main()` decomposed into 9 focused private helper functions: `_initialize_deferred_imports`, `_build_argument_parser`, `_setup_runtime_flags`, `_initialize_dependencies`, `_establish_mist_session`, `_configure_runtime_options`, `_run_tui_mode`, `_run_cli_mode`, `_run_interactive_mode`. Function reduced from 561 lines / CC 89 (Grade F) to 25 lines / CC 13 (Grade C). Behavior and CLI interface unchanged. Closes #353

## [26.05.20.16.57]

### Refactored

- `initialize_mist_session` decomposed into 14 focused private helper functions: `_load_mistapi_module`, `_parse_api_tokens`, `_check_token_rate_limit`, `_introspect_apisession_class`, `_build_session_attempts`, `_log_session_attempt_traceback`, `_execute_session_attempts`, `_filter_available_tokens`, `_create_session_with_available_tokens`, `_retry_with_filtered_tokens`, `_try_session_fallback`, `_ensure_mist_get_method`, `_log_session_auth_status`, `_validate_initialized_session`. Function reduced from 248 lines / CC 67 (Grade F) to 37 lines / CC 8 (Grade B). Behavior and global state management unchanged. Closes #351

## [26.05.20.16.29]

### Changed

- README: Update operation count from 184 to 185 entries and range from (1-185) to (1-186), reflecting Menu 186 added in PR #339

### Added

- Menu 178: Export site aggregate health & capacity statistics (`getSiteStats`)
- Menu 179: Export site gateway performance metrics summary (`getSiteGatewayMetrics`)
- Menu 180: Export site switch performance metrics summary (`getSiteSwitchesMetrics`)
- Menu 181: Export site BLE beacon statistics (`listSiteBeaconsStats`)
- Menu 182: Export site WxLAN rule usage statistics (`getSiteWxRulesUsage`)
- Menu 183: Export site asset statistics (`listSiteAssetsStats`)
- Menu 184: Export current RRM channel & power plan per AP radio (`getSiteCurrentChannelPlanning`)
- Menu 185: Export self (admin account) audit log (`listSelfAuditLogs`)
- Menu 186: Export HA gateway cluster info, stats & node pair for a site (`GatewayHaExporter`) -- shows is_ha, node_name, cluster MAC (vc_mac), cluster_config/cluster_stat, and per-device node0/node1 MAC pair from `GetSiteDeviceHaClusterNode`
- New `GatewayHaExporter` class for HA gateway cluster info (stats + cluster node membership)
- New `SelfExportUtils` class for account-scoped data exports (admin audit logs)
- 2 new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries: `GetSiteDeviceHaClusterNode` (composite_pk) and `listSiteGatewayHaStats` (composite_pk)
- 18 net-new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for previously uncovered endpoints
  (15 natural_pk, 3 composite_pk, 3 auto_increment_with_unique from probe run 3)

### Changed -- menu reference documentation

- `documentation/menu_reference.md` extended to include all menus 164-185 (was truncated at 163)
- README operation count updated from 176 to 184

- Menu 176: Export Org WAN/Gateway Config — exports 6 org-level config types (networks, services, VPNs, gateway templates, device profiles, service policies) to a single timestamped JSON bundle for cross-org migration (#191)
- Menu 177: Import Org WAN/Gateway Config — imports config bundle into destination org with conflict detection (name match, IP/subnet overlap), dependency-ordered creation, cross-reference ID remapping, and dry-run mode (#191)
- New `OrgConfigMigrationManager` class encapsulating all export/import/conflict/remapping logic

### Security

- Fixed CodeQL `py/stack-trace-exposure` violations in `src/maps/maps_manager.py` (#302)
  - Updated exception logging to use `type(e).__name__: {str(e)}` instead of exception objects (lines 9506, 9528, 9556)
- Fixed CodeQL `py/clear-text-logging-sensitive-data` violation in `src/device/utility_commands.py` (#302)
  - Removed `exc_info=True` from error logging in ZTP password handler (line 1302)

### Refactored

- Reduced `intelligent_map_replacement_wizard` CC from 126 to ≤10 in `src/maps/maps_manager.py` (#294)
  - Extracted `_wizard_run` (orchestration body), `_wizard_fetch_devices`, `_wizard_fetch_zones`, `_wizard_fetch_beacons`, `_wizard_scale_path_nodes`, and updated `_wizard_fetch_assets`, `_wizard_scale_geometry`, `intelligent_map_replacement_wizard` to delegate to helpers
  - All new methods CC ≤10; `src/maps/*` remains in CI radon exclusion pending #293
- Reduced `interactive_map_viewer` CC from 43 to 8 in `src/maps/maps_manager.py` (#295)
  - Extracted `_install_visualization_packages` (CC=5), `_check_visualization_packages` (CC=4), `_fetch_map_details` (CC=3), `_fetch_devices_on_map` (CC=3), `_fetch_zones_on_map` (CC=3), `_filter_clients_for_map` (CC=5), `_fetch_clients_on_map` (CC=8), `_handle_coverage_exception` (CC=3), `_fetch_map_coverage` (CC=6)
- Reduced `launch_viewer_standalone` CC from 30 to 3 in `src/maps/maps_manager.py` (#296)
- Extracted `PlotlyMapDataSerializer` into `src/maps/plotly_map_serializer.py` and integrated `_launch_plotly_viewer` store/dropdown payload construction through serializer helpers (#293, Phase 2)
  - Replaced inline `dcc.Store` payload dict/list construction for map config, available maps/sites, selected zone, refresh times, and cache bust
  - Replaced repeated dropdown/store map list serialization in site-switch and map-refresh callbacks
  - Added serializer unit tests in `tests/maps/test_plotly_map_serializer.py` (5 tests)
- Extracted `PlotlyCoverageHeatmapRenderer` into `src/maps/plotly_heatmap_renderer.py` and delegated RF heatmap trace construction from `_launch_plotly_viewer` (#293, Phase 3)
  - Replaced large inline coverage parsing/rendering block with `build_heatmap_trace(...)`
  - Added heatmap renderer unit tests in `tests/maps/test_plotly_heatmap_renderer.py` (5 tests)
- Extracted `PlotlyMapFigureBuilder` into `src/maps/plotly_map_figure_builder.py` and delegated walls/wayfinding/zones rendering from `_launch_plotly_viewer` (#293, Phase 4)
  - Replaced large inline layer rendering blocks with `add_walls(...)`, `add_wayfinding(...)`, and `add_zones(...)`
  - Added figure builder unit tests in `tests/maps/test_plotly_map_figure_builder.py` (5 tests)
- Extracted initial callback logic into `src/maps/plotly_map_callback_manager.py` and delegated `_launch_plotly_viewer` callbacks for layer toggles and click-details rendering (#293, Phase 5a)
  - Replaced inline callback bodies with `apply_layer_toggles(...)` and `build_click_details(...)`
  - Added callback manager unit tests in `tests/maps/test_plotly_map_callback_manager.py` (5 tests)

### Refactored -- maps manager complexity

- Reduced cyclomatic complexity of most methods in `src/maps/maps_manager.py` (#251); remaining high-CC methods deferred to dedicated follow-on issues (#293–#296)
  - Extracted `_check_dependencies`, `_configure_logging`, `_setup_api_session`, `_filter_org_privileges`, `_prompt_org_selection`, `_detect_org_from_session`, and `_resolve_org_id` from `main()` (CC 29→7)
  - Extracted `_download_all_site_map_images`, `_select_map_from_site`, `_backup_print_summary`, and other helpers to reduce method-level CC throughout the module
  - `src/maps/*` remains in CI radon exclusion until #293–#296 are resolved (`_launch_plotly_viewer` CC=138, `intelligent_map_replacement_wizard` CC=126, `interactive_map_viewer` CC=43, `launch_viewer_standalone` CC=30)
- Extracted `WebSocketManager`, `WebSocketNetworkDiagCommands`, and `WebSocketCommands` from `MistHelper.py` into `src/websocket/` modules, reducing `MistHelper.py` by ~1,789 lines (#209)
- Added `src/websocket/context.py` with `WebSocketCmdDeps` dataclass for clean dependency injection into extracted WebSocket command classes
- Updated CI radon exclusion to include `src/websocket/manager.py` (contains complex `wait_for_command_result` method)

## [26.05.12.07.25] - 2026-05-12

### Refactored

- Eliminated 3 thin wrapper classes (`SSIDTemplateConsolidationManager`, `E911BSSIDReportGenerator`, `ZoneConfigurationAnalyzer`) and 1 standalone wrapper function (`update_gateway_templates_wan2_variable`) by moving their logic directly into appropriate existing classes: `OrgExportUtils.ssid_template_consolidation`, `OrgExportUtils.e911_bssid_compliance_report`, `SiteExportUtils.zone_config_analysis`, `GatewayExportUtils.wan2_variable_migration`. Updated dispatch entries 104, 119, 159, and 160 accordingly (#287)

## [26.05.12.06.57] - 2026-05-12

### Added

- New menu item 173: `SitesByAPModelExporter.export_sites_by_ap_model` — prompts user to select an AP model from the models present in the organisation, then exports a CSV listing every site that contains APs of that model, including site name, site address, city, state, country, AP count, and individual AP MAC addresses. Uses mistapi's paginated fetch engine for parallel multi-page retrieval (#286)

## [26.05.11.00.00] - 2026-05-11

### Refactored

- Extract `FirmwareManager` class (2327 lines) to `src/firmware/firmware_manager.py` using dependency injection pattern consistent with `BulkAPFirmwareUpgrader`, `OrgLevelAPFirmwareUpgrader`, and other extracted firmware modules. MistHelper.py retains a 50-line thin wrapper (#203)

## [26.05.07.16.34] - 2026-05-07

### Fixed

- FR-001: Renamed `searchOrgBgpPeers` → `searchOrgBgpStats` (mistapi 0.62.0 function rename; line ~16191)
- FR-002: Renamed `searchOrgTunnels` → `searchOrgTunnelsStats` (mistapi 0.62.0 function rename; line ~16198)
- FR-003: Renamed `listOrgSitesStats` → `listOrgSiteStats` (mistapi 0.62.0 function rename; line ~16205)
- All three were confirmed `AttributeError` runtime crashes. No such function names exist in mistapi 0.62.0.

### Security

- FR-004: Attached `LogSanitizer` (mistapi `__logger`) to root logger at startup. Automatically redacts API tokens, passwords, and sensitive field values from all log output. Wrapped in `try/except ImportError` for backward compatibility with pre-0.59.3 mistapi.

### Added

- FR-005: Updated `requirements.txt` to `mistapi>=0.62.0` (was `>=0.61.4`)
- FR-006: New menu 166 — Export E911 Report (`getOrgE911Report`): exports organization E911 data to CSV
- FR-007: New menu 167 — Export JSI PBN Data (`searchOrgJsiPbn`): exports JSI Product Bulletin Notifications
- FR-008: New menu 168 — Export JSI SIRT Advisories (`searchOrgJsiSirt`): exports JSI Security Incident Response Team advisories
- FR-009: New menu 169 — Export Org OSPF Stats (`searchOrgOspfStats`): org-level OSPF adjacency statistics
- New menu 170 — Export Site OSPF Stats (`searchSiteOspfStats`): site-level OSPF adjacency statistics
- FR-010: New menu 171 — Export MxEdge Upgrade Status (`listSiteMxEdgeUpgrades`): site-level MxEdge firmware upgrade records
- FR-011: New menu 172 — Export Auto-Map Assignment Status (`getSiteAutoMapAssignmentStatus`): site auto-map assignment state
- Added `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for all 5 new API endpoints: `getOrgE911Report`, `listSiteMxEdgeUpgrades`, `getSiteAutoMapAssignmentStatus` (new); `searchOrgOspfStats`, `searchSiteOspfStats` (already present, verified)

## [26.04.26.01.53] - 2026-04-26

### Added

- Bulk Org Data Collection (Menu 165): New external module `src/org_data_collector.py` with `OrgDataCollector` class. Executes 137 org-level read API calls (64 list, 36 search, 6 get, 31 count) in a single pass to populate ArangoDB, Redis, and SQLite backends. Covers admins, API tokens, licenses, SSO/SSO roles, device profiles, network templates, RF templates, site templates, AP templates, security policies/profiles (AAMW, AV, IDP, SecIntel), PSKs, webhooks, VPNs, EVPN topologies, WxLAN rules/tags/tunnels, MxEdge/MxEdge clusters/tunnels, NAC portals/rules/tags, assets/asset filters, alarm templates, site groups, services, service policies, certificates, guest authorizations, PSK portals, tickets, dashboards, SDK invites/templates, Marvis client invites, packet captures, JSI data, firmware versions/upgrades, and 31 count endpoints. Includes per-call error handling (skip on failure, continue with remaining), categorized progress display, pagination support for non-paginated APIs, and collection summary.
- 68 additional ENDPOINT_PRIMARY_KEY_STRATEGIES entries for all new org-level API endpoints (31 count endpoints as auto_increment, entity endpoints as natural_pk, event/search data as composite_pk).

### Fixed

- Fixed `OrgExportUtils.export_data()` to accept optional `limit` parameter (default 1000). When `limit=None`, the limit parameter is omitted from API calls, fixing failures on non-paginated endpoints that reject the `limit` argument.
- Removed 4 broken/parent-dependent operations from org data collector: `listOrgSsoLatestFailures` (requires sso_id), `listOrgNacPortalSsoLatestFailures` (requires nacportal_id), `searchOrgWebhooksDeliveries` (requires webhook_id), `listOrgJsiPastPurchases` (HTTP 400).

## [26.04.23.16.39] - 2026-04-23

### Added

- WAN Hub-Spoke VPN Builder (Menu 164): New external module `src/wan_vpn_builder.py` with `WanVpnBuilder` class. Fetches gateway device profiles, lets the user assign hub/spoke roles and pod values, auto-generates full-mesh hub paths and hub-spoke paths with cross-connects, previews the VPN payload, creates the VPN via API, and optionally writes port_vpn_paths back to each profile. Supports typed CREATE confirmation (FR-007). Includes 61 unit tests covering all pure logic, API helpers, prompts, and the full workflow.

## [26.04.22.20.38] - 2026-04-22

### Added

- WAN Hub Group Number Manager (Menu 163): New external module `src/wan_hub_group_manager.py` with `WanHubGroupNumberManager` class. Lists all gateway device profiles with current pod (group number) values from hub-spoke VPN paths, lets the user select a profile, then set pod (1-128) or clear to default (1). Batch updates all matching VPN paths across multiple VPN objects. Uses trailing-hyphen prefix matching to avoid false collisions (for example, DC1- against DC1-BACKUP-). Warns on inconsistent pod values. Follows the external module pattern with an `execute(apisession, get_org_id_func, safe_input_func)` static method. This was the first menu operation extracted into an external module under `src/`, following the dependency-injection pattern.
- 33 unit tests for WanHubGroupNumberManager covering profile fetching, path matching, pod set and clear, input validation, and module architecture. They cover all four user stories.

## [26.04.20.20.23] - 2026-04-20

### Added

- Wired Client Manufacturer Report (Menu 162): New WiredClientManufacturerReportGenerator class fetches all org wired clients, displays indexed manufacturer summary with counts sorted by frequency, and lets the user select a manufacturer to export filtered records. Supports "export all" option. Uses existing searchOrgWiredClients API with limit=1000 and standard DataExporter CSV/SQLite output.

## [26.04.09.21.30] - 2026-04-09

### Compatibility Audit

- MistAPI compatibility audit alignment: raised the documented dependency floor to `mistapi>=0.61.4` and `websocket-client>=1.8.0`, updated the site client insights workflow to call `getSiteInsightMetricsForClient(..., metrics=metric)`, and added regression coverage for alarms, device-event pagination, site client stats, site SLE summaries, client insight metrics, and the E911 BSSID report.

## [26.04.08.18.41] - 2026-04-08

### Added

- SSID Template Consolidation (Menu 159): Complete rewrite as SSIDTemplateConsolidationManager with 5-phase guided workflow. Phase 1: read-only audit builds site-template-SSID matrix with cross-cluster deviation analysis. Phase 2: auto-detect site-specific deviations and write MISTHELPER_* site variables. Phase 3: create site groups by Mist Edge cluster affinity. Phase 4: build consolidated WLAN templates with Jinja variable references for deviations. Phase 5: disable old per-site SSIDs. Includes JSON cache/resume, CONFIRM gates on all write phases, and DataExporter dual CSV/SQLite output.

## [26.04.07.22.27] - 2026-04-07

### Fixed

- E911 BSSID Report (Menu 160): Fixed radio band and SSID resolution. Radio stats now fetched from site-level listSiteDevicesStats (not org-level which omits radio_stat). SSID resolution now uses full 3-source chain: site-level WLANs (listSiteWlans), site template WLANs (getOrgSiteTemplate wlans field), and org WLANs via WLAN template assignment (listOrgTemplates applies.site_ids/sitegroup_ids/org_id -> listOrgWlans filtered by template_id). Refactored _fetch_lookups into focused helpers: _fetch_org_wlan_templates, _fetch_org_wlans, _fetch_site_maps, _fetch_site_radio_stats, _resolve_site_ssids, _resolve_site_template_wlans, _get_assigned_template_ids, _add_wlans_to_band_lookup. Site lookup now stores sitegroup_ids and sitetemplate_id for template resolution.

## [26.04.07.22.13] - 2026-04-07

### Changed

- E911 BSSID Report (Menu 160): Enhanced with radio band details and SSID names. Now parses radio_stat from listOrgDevicesStats to resolve each radio MAC to its band (2.4/5/6 GHz), channel, and power. Fetches listSiteWlans per site to build band-to-SSID lookup, mapping WLAN band config (24/5/6/both) to radio bands. New CSV columns: AP MAC, Band, Radio MAC, Channel, Power, SSIDs on Band. Sort order updated to include Band. _fetch_lookups returns dict with radio_bands and wlan_bands lookups; _build_bssid_rows accepts consolidated lookups dict (2 params vs prior 4).

## [26.04.07.21.00] - 2026-04-07

### Added

- E911 BSSID Compliance Report (Menu 160): New E911BSSIDReportGenerator class queries all AP radio MACs via listOrgApsMacs, resolves site name/address via listOrgSites, AP name/site/map via listOrgDevicesStats(type=ap), floor names via listSiteMaps per site, derives 16 BSSIDs per radio MAC (last nibble 0x0-0xF), outputs sorted CSV (Site Name, Site Address, Map Name, AP Name, BSSID) with compliance gap detection for APs missing map assignments. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.28.19.09] - 2026-03-28

### Added

- Offline Device Report (Menu 158): New OfflineDeviceReporter class scans entire org via listOrgDevicesStats (type=all, status=all), filters devices offline beyond user-configurable threshold (default 48h), resolves site names via lookup dict, displays summary stats (total devices, per-type breakdown, top 5 sites) + PrettyTable (max 50 rows), saves human-readable CSV with timestamped filename to data/. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.20.22.31] - 2026-03-20

### Added

- Device Utility Commands: 35 new operations (menus 123-157) covering traceroute, OSPF diagnostics, session/service-path inspection, BGP/ARP/DHCP/802.1X/EVPN show commands, DNS resolution, live traffic monitoring, device locate, port bounce, cable test, reprovision/re-adopt, ZTP password retrieval, config command export, support file upload, 7 clear/reset operations, DHCP lease release, stats polling, and device snapshots
- DeviceUtilityCommands class: Uses mistapi SDK methods (not raw requests) with WebSocket result streaming, device-type validation, port selection from live stats, and three-tier destructive confirmation (none/y-N/typed keyword)
- 14 new ENDPOINT_PRIMARY_KEY_STRATEGIES entries for dual-output (CSV/SQLite) support on all device utility results

## [26.03.05.02.49] - 2026-03-05

### Added

- Web Portal: Flask-based browser interface on port 8055 (--web-portal CLI flag)
- Data Browser: Browse, search, preview, and download CSV/SQLite output files
- Operations: Run data extraction operations (menus 1-89) with real-time SSE progress
- Map Viewer: Interactive Plotly.js floor plan viewer with device markers
- Theme System: Dark, Light, and High Contrast themes with instant switching and localStorage persistence
- Portal Branding: Customizable title, logo, and accent color via ENV variables
- Container Integration: Dual-process startup (Gunicorn + sshd) on ports 8055 and 2200
- Security: CSP headers, CSRF protection, IP allowlist, path traversal guard

### Changed

- Replaced Dash dependency with Flask + Gunicorn for lighter footprint
- Updated Containerfile: EXPOSE 8055, COPY web_portal/, bundled vendor assets
- Updated compose.yml: Port 8055:8055 replaces 8050:8050, WEB_PORT env var
- Container start.sh: Dual-process with SIGTERM trap for clean shutdown

## [26.03.04.22.30] - 2026-03-04

### Changed

- God-class decomposition: All 95 classes now comply with 5-Item Rule (max 5 public methods per class)
- 13 non-compliant classes decomposed via rename-to-private and sub-class extraction
- GlobalImportManager: 13->5 pub (8 renamed private)
- RateLimitingUtils: 6->1 pub (5 renamed private)
- APIFetchUtils: 9->3 pub (extracted APICoreFetchUtils, APITenantFetchUtils)
- AddressUtils: 9->5 pub (4 renamed private)
- WebSocketCommands: 7->4 pub (extracted WebSocketNetworkDiagCommands)
- OrgExportUtils: 51->5 pub (12 renamed private, extracted 7 sub-classes: OrgSiteExporter, OrgInventoryExporter, OrgDeviceStatsExporter, OrgTemplateExporter, OrgClientSecurityExporter, OrgAdminExporter, OrgConfigExporter)
- MapsManager: 28->0 pub (all 28 renamed private - dead/internal-only code)
- EnhancedSSHRunner: 24->5 pub (19 renamed private)
- SiteExportUtils: 22->3 pub (3 renamed private, extracted 4 sub-classes: SiteDeviceExporter, SiteClientExporter, SiteConfigExporter, SiteAnomalyExporter)
- RoutingUtils: 16->3 pub (13 renamed private)
- PromptUtils: 12->5 pub (extracted PromptNetworkDeviceUtils, PromptClientUtils)
- GatewayExportUtils: 12->4 pub (3 renamed private, extracted GatewayTestExporter, GatewayStatsExporter)
- FirmwareManager: 10->4 pub (6 renamed private)
- 16 new sub-classes created following {Scope}{Domain}{Action} naming convention
- Zero functionality changes - all tests pass (49/49) after every decomposition

## [26.03.04.00.55] - 2026-03-04

### Changed

- Extract OrgAlarmEventExporter from OrgExportUtils (5-Item Rule compliance)
- New class contains 5 alarm/event methods: alarms(), alarm_templates(), events(), device_events(), device_events_52w()
- OrgExportUtils reduced from 56 to 51 methods; documented extraction pattern for future decomposition
- Consolidated redundant logging in alarms() (two start messages merged into one)

## [26.03.03.23.35] - 2026-03-03

### Changed

- Menu 122: Show ALL RADIUS WLANs including compliant ones marked '(COMPLIANT)' for full org visibility
- Menu 122: Accept 'q', 'quit', 'cancel', 'back' at selection prompt for safe exit without changes
- Menu 122: Respect --dry-run flag (preview without API calls, DRYRUN_ CSV prefix)
- Menu 122: Respect --debug flag (verbose API response and compliance evaluation logging)
- Menu 122: DRY-RUN and DEBUG mode banners displayed at startup when flags are active

## [26.03.03.22.27] - 2026-03-03

## [26.02.18.19.30] - 2026-02-18

### Added

- Menu 121: Site Inventory Health Analysis - Find sites with APs missing switches/gateways or with offline infrastructure
- Generates two reports: SitesMissingInfrastructure and SitesWithOfflineInfrastructure
- Uses org-level APIs for efficient bulk analysis across all sites

## [26.02.09.00.33] - 2026-02-09

### Changed

- Menu 120: Added engagement hours to standard configuration (all days set to empty string)
- Detects and clears custom operating hours (sun/mon/tue/wed/thu/fri/sat) to defaults

## [26.02.08.23.58] - 2026-02-08

### Changed

- Menu 120: Added WiFi settings to standard configuration (enabled=true, locate_connected=true, locate_unconnected=false)
- SiteAnalyticsConfigurator now checks and applies STANDARD_WIFI settings across all sites

## [26.02.08.23.46] - 2026-02-08

## [26.02.08.23.37] - 2026-02-08

## [26.02.08.23.28] - 2026-02-08

### Changed

- Menu 119: Extended to analyze engagement dwell tags (passerby/bounce/engaged/stationed time ranges)
- Menu 119: Extended to analyze engagement dwell tag custom names
- Menu 119: Extended to analyze occupancy settings (min_duration, clients_enabled, etc.)
- Menu 119: Extended to analyze analytics enabled/disabled status across sites
- Menu 119: Exports 5 CSV files: Summary, AllZones, ZoneFrequency, DwellConfigs, OccupancyConfigs

## [26.02.08.23.20] - 2026-02-08

## [26.02.05.00.25] - 2026-02-05

### Fixed

- Menu 116: Add full pagination support using mistapi.get_all()
- Menu 116: Inventory fetch now retrieves ALL APs (not just first 1000)
- Menu 116: Stats fetch now retrieves ALL device stats with pagination

## [26.02.05.00.20] - 2026-02-05

### Fixed

- Menu 116: Use listOrgAvailableDeviceVersions API (not getOrgDeviceUpgrade)
- Menu 116: Fix 'Unknown' firmware version display - match by MAC address
- Menu 116: Add limit=1000 to listOrgDevicesStats call for proper pagination

## [26.02.05.00.15] - 2026-02-05

### Fixed

- Menu 116: Use getOrgInventory API instead of listOrgDevices (listOrgDevices doesn't support type filter)
- Fixed 'listOrgDevices() got an unexpected keyword argument type' error

## [26.02.04.16.35] - 2026-02-04

### Changed

- Direct interactive login without org selection flow
- Proper inventory fetch with limit=1000 pagination

### Fixed

- Menu 117: Skip MSP/Org selection after login (exports ALL, not selected)
- Menu 117: Use getOrgInventory API instead of listOrgDevices for full inventory
- Fixed device count showing '1 (unknown:1)' for every org

## [26.02.04.16.20] - 2026-02-04

### Changed

- Menu 117: Auto-prompt for interactive login when MSP privileges missing
- No longer requires user to manually run --login or Menu 115 first
- Improved UX: offers to switch authentication in-place if needed

## [26.02.05.06.15] - 2026-02-05

### Changed

- Output includes MSP/Org/Site context columns for each device
- Device type breakdown summary (ap, switch, gateway counts)
- Site name lookup for user-friendly output
- Progress display showing org-by-org processing

## [26.02.05.05.45] - 2026-02-05

### Changed

- Site scope selection: 'All sites' or specific site selection
- Version selection per model with automatic grouping by target version
- Full upgrade strategy support (big_bang, serial, canary, rrm)
- Dry-run mode with --dry-run flag
- API efficiency display showing call savings vs site-level approach

## [26.02.05.04.35] - 2026-02-05

### Changed

- API call estimate now correctly counts unique versions per site
- Upgrade output shows version with list of models being upgraded

## [26.02.05.04.20] - 2026-02-05

### Changed

- Confirmation screen now shows total upgrade API calls
- Per-site breakdown shows device count and call reason
- Note about additional auto-upgrade API calls if step 9 is used

## [26.02.05.04.02] - 2026-02-05

### Changed

- MSP selection now supports selecting multiple MSPs in one workflow
- Organization selection per MSP with consistent selection patterns
- Site selection per org with configurable ranges and pagination
- Upgrade plan summary shows MSPs, orgs, and sites before confirmation
- Dry-run mode skips confirmation and shows simulation banner

## [26.02.05.03.18] - 2026-02-05

### Changed

- FirmwareManager now detects MSP privileges and shows mode [3] when available
- Sequential processing with per-org confirmation and interrupt handling
- Upgrade summary report showing completed/failed/interrupted organizations

## [26.02.02.23.15] - 2026-02-02

### Changed

- Session-based authentication with cookie management for MSP API endpoints
- Two-factor authentication (2FA) support in interactive login flow
- Cloud selection during interactive login (Global, EU, GovCloud, Custom)
- MSP organization export includes msp_id and msp_name context fields

## [26.02.02.21.06] - 2026-02-02

### Changed

- Family-based version selection: Select one version per ap_type family, applies to all models
- AP models grouped by ap_type from /api/v1/const/device_models (ruby, jewel, aphx, etc.)
- Universal version detection aggregates firmware compatibility across all API entries
- Semantic version sorting (0.14.x now correctly sorts above 0.8.x)
- Auto-upgrade scheduling: Added day_of_week and time_of_day options

## [26.01.28.19.03] - 2026-01-28

## [26.01.28.18.55] - 2026-01-28

## [26.01.28.18.51] - 2026-01-28

### Changed

- Menu 90 'All sites' mode: Now displays full site list before confirmation prompt
- AP Discovery Summary: Enhanced to show per-site model breakdown (e.g., 'Site-A: 12 APs (AP45:8, AP34:4)')
- Clarified that sites with no APs or all APs at target will be skipped

## [26.01.28.18.46] - 2026-01-28

## [26.01.28.18.40] - 2026-01-28

## [26.01.28.18.30] - 2026-01-28

## [26.01.18.02.10] - 2026-01-18

## [26.01.17.23.15] - 2026-01-17

## [26.01.17.23.00] - 2026-01-17

## [26.01.17.22.45] - 2026-01-17

## [26.01.17.22.30] - 2026-01-17

## [26.01.17.22.15] - 2026-01-17

## [26.01.17.22.00] - 2026-01-17

## [26.01.17.21.45] - 2026-01-17

## [26.01.17.21.30] - 2026-01-17

## [26.01.17.20.45] - 2026-01-17

## [26.01.17.19.30] - 2026-01-17

## [26.01.17.19.15] - 2026-01-17

## [26.01.17.18.30] - 2026-01-17

## [26.01.17.17.53] - 2026-01-17

## [26.01.17.17.24] - 2026-01-17

## [25.07.10.08.00] - 2025-07-10

## [25.07.10.07.25] - 2025-07-10

## [25.07.10.05.30] - 2025-07-10

## [25.07.10.05.15] - 2025-07-10

## [25.07.10.05.00] - 2025-07-10

## [25.07.09.23.25] - 2025-07-09

## [25.07.09.23.15] - 2025-07-09

## [25.07.09.23.00] - 2025-07-09

## [25.07.09.22.45] - 2025-07-09

## [25.07.09.22.15] - 2025-07-09

## [25.07.09.22.08] - 2025-07-09

## [25.07.09.22.00] - 2025-07-09

## [26.01.16.21.30] - 2026-01-16

## [26.01.16.21.00] - 2026-01-16

## [26.01.16.20.30] - 2026-01-16

## [26.01.16.20.00] - 2026-01-16

## [26.01.16.19.30] - 2026-01-16

## [26.01.16.19.15] - 2026-01-16

## [26.01.16.18.45] - 2026-01-16

## [26.01.16.05.30] - 2026-01-16

## [26.01.15.22.45] - 2026-01-15

### Documentation

- Updated interactive_fetch_device_data_to_csv docstring to support config object pattern

## [26.01.15.21.30] - 2026-01-15

## [26.01.16.00.15] - 2026-01-16

### Documentation

- Added dataclasses import and config classes section near top of MistHelper.py
- Updated function docstrings to mark individual parameters as deprecated in favor of config objects

## [26.01.15.23.56] - 2026-01-15

### Documentation

- Compliance audit: Applied copilot-instructions.md naming and ASCII guidelines

## [26.01.15.16.30] - 2026-01-15

## [26.01.12.16.41] - 2026-01-12

## [26.01.09.18.45] - 2026-01-09

## [26.01.09.17.30] - 2026-01-09

## [25.01.09.19.00] - 2025-01-09

## [26.01.08.15.32] - 2026-01-08

## [25.12.22.20.30] - 2025-12-22

## [25.12.22.19.54] - 2025-12-22

## [25.12.22.19.30] - 2025-12-22

## [25.12.22.18.00] - 2025-12-22

## [25.12.22.17.30] - 2025-12-22

## [25.12.22.13.45] - 2025-12-22

### Documentation

- Added Python 3.13 and mistapi 0.59+ requirements to copilot-instructions.md
- Added Runtime Requirements section to agents.md specifying Python 3.13+ and mistapi 0.59+

## [25.01.21.15.30] - 2025-01-21

### Documentation

- Added Data Directory Permissions section to README troubleshooting
- Updated agents.md with CRITICAL permission requirements in deployment pipeline
- Updated copilot-instructions.md with permission fix between image pull and container restart

## [25.12.15.14.45] - 2025-12-15

### Documentation

- README Section 1 - Updated operation count from 97 to 112 menu entries
- README Section 1 - Updated line count from 22k to 44k lines
- README Section 1 - Updated date to 2025-12-15
- README Section 3 - Removed non-existent run-misthelper.py from directory table
- README Section 6 - Added missing CLI flags: --dry-run, --tui, --testinteractive
- README Section 8 - Fixed menu 40-44 description to mention rogue client/AP detections
- README Section 8 - Added missing menu items 101 (TUI), 111 (Clone Templates), 112 (Maps Manager)
- README Section 14 - Updated container commands to use direct podman commands instead of run-misthelper.py

## [25.12.12.17.10] - 2025-12-12

## [25.12.12.17.03] - 2025-12-12

## [25.12.12.21.55] - 2025-12-12

### Changed

- Zone name input field appears when Zone mode is selected
- Clear All Drawings button with guidance to use eraser tool
- Success/error feedback messages for all save operations

## [25.12.12.21.50] - 2025-12-12

### Changed

- Added coordinate sample logging to verify refresh data
- Added warning log if Clients trace not found during refresh
- Removed visibility toggle override during refresh to preserve user settings

## [25.12.12.21.35] - 2025-12-12

### Changed

- Changed browser tab title from 'Dash' to 'MistHelper Map Viewer'

## [25.12.12.21.30] - 2025-12-12

### Changed

- Set update_title=None on Dash app to prevent tab title flicker from 1-second countdown interval

## [25.12.12.21.20] - 2025-12-12

### Changed

- Upgraded refresh trace logging from debug to info level for visibility

## [25.12.12.17.15] - 2025-12-12

### Changed

- Moved live refresh controls from sidebar to header bar for better visibility
- Added countdown timers showing seconds until next client refresh and minutes:seconds until RF heatmap refresh
- Countdown updates every second when auto-refresh is enabled
- Compact refresh control panel with dark background in header

## [25.12.12.16.45] - 2025-12-12

### Changed

- dcc.Store component: stores site_id, map_id, PPM, and map dimensions for refresh callbacks
- dcc.Interval components: two separate intervals for clients (30s) and coverage (5min) with disabled-by-default state
- Callback architecture: separate callbacks for toggle, client refresh, and coverage refresh with proper state management
- API session reference: refresh callbacks use stored API session for authenticated requests

## [25.12.12.15.35] - 2025-12-12

### Changed

- Explicit warning in console when map_ppm is 0 or missing

## [25.12.12.15.30] - 2025-12-12

### Changed

- Uses first 10 clients with both pixel and meter coordinates to calculate average PPM
- Logs PPM validation results (pass/mismatch) with exact values for debugging

## [25.12.12.14.30] - 2025-12-12

### Changed

- Added heatmap coordinate debug logging to script.log
- Logs coverage X/Y ranges in both pixels and meters for PPM validation

## [25.12.09.14.44] - 2025-12-09

### Documentation

- README and READY_FOR_MIGRATION license references now call out AGPL-3.0-only so downstream consumers see the correct terms immediately.

## [25.12.04.14.15] - 2025-12-04

### Changed

- Heatmap interpolation: zsmooth='best' provides smooth color transitions between grid points
- Gap interpolation: connectgaps=True fills in missing grid cells for complete coverage visualization
- Debug logging: added per-device orientation logging to script.log for troubleshooting
- Coordinate system fix: corrected AP orientation angle conversion (Mist 0°=north to math coordinates with Y-axis flip)

## [25.12.04.13.15] - 2025-12-04

### Changed

- RSSI tooltip: hover over grid cells shows Max RSSI and Avg RSSI in dBm
- Grid size calculation: coverage gridsize (meters) converted to pixels for proper visualization scale
- Error handling: graceful degradation when coverage API unavailable (backend database issues, no data)
- Backend error detection: psycopg2/database errors logged as warnings, not errors (expected transient issues)

## [25.12.04.13.07] - 2025-12-04

### Changed

- Device marker colors: dynamic color array based on individual device status instead of static type-based colors
- Crosshair orientation indicators: now use status-based colors matching device state
- Device labels: border colors match device status for consistent visual feedback
- Type-specific status colors: APs (green/red/orange), Switches (cyan/red/orange), Gateways (magenta/red/orange)

## [25.12.03.17.30] - 2025-12-03

### Changed

- Larger crosshair indicators: increased from 25px to 40px for better visibility of device orientation markers
- Larger orientation dots: increased from 10px to 16px with thicker lines (3px width) for improved visual clarity
- Increased dot distance: orientation direction indicator moved from 35px to 50px from device center
- Annotation toggle control: all text labels (zones, devices, clients, beacons) now hide/show with their parent layers
- Unified visibility management: annotations and traces both controlled by layer toggle callbacks

## [25.12.03.17.15] - 2025-12-03

### Changed

- Multi-checklist architecture: 5 separate checklists for granular layer management
- Client type detection: automatic WiFi/Wired classification based on SSID field presence
- Coverage radius calculation: dynamic radius based on vBeacon power level (-12 to +4 dBm range)
- Client-AP linking: automatic AP lookup by MAC address for association line drawing
- Mesh topology detection: automatic mesh uplink discovery from device mesh_uplink field
- Layer toggle callback: enhanced to handle multiple checklist inputs with combined layer array
- Map statistics: added vBeacon and BLE beacon counts to Map Info panel
- Add vBeacon/Beacon buttons: header toolbar buttons with green/cyan color coding

### Documentation

- Layer controls now match Mist portal Location Settings panel organization
- Client separation provides visual distinction between WiFi and Wired network access

## [25.12.03.16.47] - 2025-12-03

### Changed

- Auto-Zone UI: prominent purple button with robot emoji in header utilities bar
- Zone checklist: all zones checked by default, styled with dark theme
- Zone selection feedback: green highlighted text shows selected zone details
- Edit zone placeholder: guides to Mist API updateSiteMap for vertex modification
- Remove zone warning: red destructive warning for zone deletion operations
- Click handling: detects zone clicks from hovertext and displays zone information

### Documentation

- Added Location Zones panel matching Juniper Mist portal zone management interface
- Auto-Zone feature provides AI-powered automatic zone creation from wall analysis

## [25.12.03.16.44] - 2025-12-03

### Changed

- Drawing Tools UI: color-coded buttons matching element types (magenta/cyan/orange/red)
- Tool guidance: status messages direct users to appropriate toolbar drawing tools
- Destructive warnings: delete buttons highlighted in red with bold warnings
- Sidebar reorganization: Drawing Tools section above Measurement Tools for better workflow
- Compact layout: measurement tools condensed with smaller font for space efficiency

### Documentation

- Added Drawing Tools panel matching Juniper Mist portal map editor interface
- Quick-action buttons provide shortcuts and guidance for common map editing tasks

## [25.12.03.16.41] - 2025-12-03

### Changed

- Validation path styling: magenta color (#ff00ff) with dotted line style for clear differentiation
- Hover information: shows path name and point count on mouseover
- Path naming: displays custom path names or defaults to 'Path 1', 'Path 2', etc.
- Coordinate processing: extracts x,y from path coordinate arrays with validation
- Logging integration: debug messages for path rendering with point counts

### Documentation

- Added validation paths feature matching Juniper Mist portal site survey path capability
- Validation paths used for Wi-Fi coverage testing and performance analysis along routes

## [25.12.03.16.39] - 2025-12-03

### Changed

- Utilities UI redesign: replaced dropdown with horizontal button bar for cleaner interface
- Direct action buttons: Change Image, Remove Image, Rename, Delete as individual buttons in header
- Visual hierarchy: Delete button highlighted in red (#ff4444) for critical action awareness
- Improved spacing: buttons in header bar with inline status messages
- Darker header: #2a2a2a background for better contrast with map area

## [25.12.03.16.38] - 2025-12-03

### Changed

- Utilities UI: dropdown positioned in header top-right matching Mist portal layout
- Action feedback: status messages display warnings for destructive operations
- Color coding: orange for caution (change/rename), red for destructive (remove/delete)
- Logging integration: all utility actions logged with map_id for audit trail
- Header redesign: title and utilities dropdown in flex layout with purple border separator

### Documentation

- Added Utilities dropdown matching Juniper Mist portal map management interface
- Placeholder implementations note required API integrations for full functionality

## [25.12.03.16.35] - 2025-12-03

### Changed

- Set Origin UI: toggle button with mode indicator in sidebar Tools section
- Visual feedback: button highlights in purple when origin-setting mode is active
- Status display: shows current origin coordinates and confirmation when set
- Origin initialization: loads existing origin_x/origin_y from map data if present
- Interactive workflow: click button to activate, click map to set, click button again to exit mode

### Documentation

- Added Set Origin feature matching Juniper Mist portal coordinate system alignment capability

## [25.12.03.16.32] - 2025-12-03

### Changed

- Set Scale UI: input field for length in meters + button in sidebar Tools section
- Workflow guidance: numbered steps (1. Draw line, 2. Enter length) for clear user instructions
- Dynamic PPM: measurement callback reads current PPM from figure metadata instead of static value
- Scale validation: prevents setting scale with invalid/missing length or without drawn line
- Professional styling: scale input and button match dark theme with purple accent (#667eea)

### Documentation

- Added Set Scale feature matching Juniper Mist portal UI/UX for floor plan calibration

## [25.12.03.16.30] - 2025-12-03

### Changed

- Map viewer rotation indicators: replaced triangular wedges with Mist-style crosshair + directional dot
- Crosshair: 25px horizontal and vertical lines at device center (always visible)
- Directional dot: 10px marker positioned 35px from center at orientation angle (only if angle != 0)
- Crosshair color matches device type (green for APs, orange for switches, magenta for gateways)
- Dot shows orientation angle on hover for quick reference

### Documentation

- Updated rotation indicator design to match Juniper Mist portal UI/UX patterns

## [25.12.03.16.22] - 2025-12-03

### Changed

- Map viewer text rendering: switched from mode='markers+text' to mode='markers' + separate annotations
- Annotation-based labels: support bgcolor, bordercolor, borderwidth, and borderpad for professional appearance
- Device labels: positioned 15px above markers with device-type-specific colored borders (green/orange/magenta)
- Client labels: positioned 10px above markers with smaller font and green styling
- Zone labels: automatically positioned at min(x), min(y) coordinates (upper-left bounding box corner)
- Improved label positioning: all labels use xanchor/yanchor for precise placement without overlap

### Documentation

- Added technical note in CSS explaining why text-shadow doesn't work on Plotly SVG elements
- Removed obsolete text-shadow CSS rules that had no effect on map labels

## [25.12.02.20.30] - 2025-12-02

### Changed

- Clone operation uses temporary files for image download/upload to avoid filesystem pollution
- Automatic cleanup of temporary files in all code paths (success, failure, exception)
- Enhanced error handling with separate warnings for download vs upload failures
- User-friendly progress messages at each stage: select, download, create, upload, complete
- Clone confirmation shows full plan before execution including image copy status
- Educational note: zones are site-level objects (not map objects) requiring separate cloning

### Documentation

- Added comprehensive docstring explaining full clone capability including image/walls/paths/zones
- Clone summary clearly shows which elements were successfully copied

## [25.12.02.18.00] - 2025-12-02

### Changed

- Database schema - Added natural primary key strategies for listSiteMaps and getSiteMap with proper indexes
- Interactive sub-menu - Single entry point (Menu 112) with 0 to return to main menu, organized by operation category
- Safety features - Input validation, EOF/interrupt handling, confirmation prompts for destructive operations (placeholders)
- Image handling - JWT token URL support, automatic format detection (png/jpg), organized directory structure by site
- Progress indicators - tqdm progress bars for bulk site/map operations with descriptive labels
- Error handling - Graceful per-site error logging without halting bulk operations, comprehensive exception tracking

### Documentation

- Updated operation count from 111 to 112 total menu entries
- Added Maps Manager category section to menu_actions documentation
- Documented map database strategies in ENDPOINT_PRIMARY_KEY_STRATEGIES configuration

## [25.12.02.17.15] - 2025-12-02

### Documentation

- Updated agents.md Git workflow - clarified that staging alone does not create checkpoints
- Added minimal Git workflow instructions for local commits and rollback procedures
- Removed verbose workflow examples, keeping only essential commands for AI agents

## [25.12.02.16.43] - 2025-12-02

### Documentation

- Added detailed docstrings for clone_gateway_templates_by_state_and_country() explaining address parsing logic
- Documented support for US, CA, MX, CR, PA, HN, GT, and other Central American address formats
- Updated menu option tables with entry 111 for gateway template cloning by geography
- Documented --testinteractive and --dry-run CLI flag usage in help text
- Noted limitations: Multi-word state names (e.g., 'Quintana Roo') may capture last word only

## [25.12.02.11.10] - 2025-12-02

### Documentation

- Added code comments explaining mistapi's expectation of comma-separated token string
- Documented that mistapi handles token rotation internally when configured correctly

## [25.12.02.11.05] - 2025-12-02

## [25.12.02.11.15] - 2025-12-02

### Documentation

- Identified that error occurs when mistapi library validates tokens against Mist API
- Token validation failure suggests tokens need to be refreshed or regenerated
- mistapi library bug: does not handle missing 'privileges' key in API response gracefully

## [25.12.02.11.00] - 2025-12-02

## [25.12.01.17.40] - 2025-12-01

### Changed

- Menu 14 (fast mode): Added extensive debug logging to track data type issues in parallel processing
- Added type validation logging for start_time, end_time, and duration calculations
- Added logging for successful_results and failed_sites return types from execute_with_connection_pool_management
- Added per-result type checking in flattening loop with warnings for unexpected types
- Added site tuple structure validation logging to diagnose dict vs tuple issues

## [25.12.01.17.35] - 2025-12-01

## [25.12.01.17.30] - 2025-12-01

## [25.12.01.17.20] - 2025-12-01

### Changed

- Enhanced error handling in fetch_and_display_api_data with three-layer defense against data loss
- Added response structure validation and logging for debugging unexpected API formats
- Automatic recovery attempts from alternate response structures (response.data['data'], direct lists)
- User-friendly messages explain partial data saves and recovery attempts
- Detailed debug logs capture response types and available keys for troubleshooting

### Documentation

- Updated export_device_port_stats_to_csv docstring with performance optimization notes
- Added fetch_and_display_api_data docstring explaining enhanced error handling layers
- Documented safety features: emergency saves, structure validation, graceful degradation

## [25.11.25.13.49] - 2025-11-25

## [25.11.25.13.40] - 2025-11-25

### Changed

- Pre-flight analysis shows assignment plan before execution
- Exports successful assignments to SuccessfulAPProfileAssignments.csv with AP/profile details
- Exports failed assignments to FailedAPProfileAssignments.csv for troubleshooting
- Exports skipped APs to SkippedAPsNoMatchingProfile.csv for profile creation planning
- Comprehensive summary report showing successful, failed, and skipped counts
- Detailed logging for each AP assignment with full error context
- Gracefully skips APs without model information instead of failing

### Documentation

- Menu 110 marked as DESTRUCTIVE operation requiring 'ASSIGN' confirmation
- Pre-assignment analysis shows counts of APs with/without matching profiles
- Operation count updated from 110 to 111 total menu operations
- Lists APs that will be skipped due to missing matching Device Profiles

### Security

- Requires explicit uppercase 'ASSIGN' confirmation before device assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.3s delay between AP assignments

## [25.11.25.13.23] - 2025-11-25

### Changed

- Progress display shows unique AP models discovered across organization
- Exports successful creations to CreatedAPModelDeviceProfiles.csv with model/profile/ID details
- Exports failures to FailedAPModelDeviceProfiles.csv for troubleshooting
- Comprehensive summary report showing profiles created, failed, and skipped (existing)
- Detailed logging for each profile creation with full error context
- Warns about devices with missing model information for inventory visibility

### Documentation

- Menu 109 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- Device Profiles created with minimal payload to ensure all settings inherit/auto by default
- Operation count updated from 109 to 110 total menu operations
- Devices without model information are logged and reported but do not block execution

### Security

- Requires explicit uppercase 'CREATE' confirmation before profile creation
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between Device Profile creations

## [25.11.25.12.28] - 2025-11-25

### Changed

- Progress display shows country distribution and site counts per country
- Exports successful assignments to SuccessfulRFTemplateAssignments.csv with site/template details
- Exports failures to FailedRFTemplateAssignments.csv for troubleshooting
- Comprehensive summary report showing templates created, sites assigned, failures, and skipped sites
- Detailed logging for each template creation and site assignment with full error context
- Template reuse logic - skips creation if RF-{country} template already exists

### Documentation

- Menu 108 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- RF template configuration uses default/auto settings: band_24 (20MHz auto), band_5 (40MHz auto), band_6 (80MHz auto)
- Operation count updated from 108 to 109 total menu operations
- Sites without country codes are skipped with warning message and logged

### Security

- Requires explicit uppercase 'CREATE' confirmation before template creation and site assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between template creations and 0.3s between site assignments

## [25.11.25.14.30] - 2025-11-25

### Changed

- Progress display shows site creation status with index counter
- Exports successful creations to CreatedTestSites.csv with site IDs
- Exports failures to FailedTestSites.csv for troubleshooting
- Comprehensive summary report showing total/success/failure counts
- Detailed logging for each site creation attempt with full error context

### Documentation

- Menu 107 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- CSV structure documented: name (required), address, country_code, lat, lng, timezone, notes
- Operation count updated from 107 to 108 total menu operations

### Security

- Requires explicit uppercase 'CREATE' confirmation before execution
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between site creations to avoid API throttling

## [25.11.25.09.30] - 2025-11-25

### Documentation

- Menu 25: Updated function docstring to document all three output files (weekly, summary, master)

## [25.11.21.17.00] - 2025-11-21

## [25.11.13.16.15] - 2025-11-13

### Documentation

- Menu 104: Updated docstring explains device override preservation critical safety feature
- Menu 104: Console output clearly shows two-phase migration: templates then device overrides
- Menu 104: Explains risk of static IP loss without device override migration

## [25.11.13.15.45] - 2025-11-13

## [25.11.13.14.30] - 2025-11-13

### Documentation

- Menu 103: CRITICAL overrides (DHCP->Static) clearly flagged for manual review priority
- Menu 103: User guidance explains static IPs will be lost if template DHCP applied without device overrides
- Menu 103: Console output shows breakdown of override severity levels with actionable next steps

## [25.10.30.17.50] - 2025-10-30

## [25.10.30.19.50] - 2025-10-30

## [25.10.29.13.55] - 2025-10-29

## [25.10.29.00.15] - 2025-10-29

### Changed

- Converted remaining progress messages to logging (only user-facing data remains as print)
- Debug logs now show template assignment determination before WLAN fetching
- Added logging for org WLAN filtering process with template_id matching

### Documentation

- Clarified architecture: WLAN templates are configuration containers, not WLAN collections
- Org WLANs exist independently and optionally reference templates for config inheritance
- Templates define what configuration to apply; WLANs reference them via template_id

## [25.10.28.23.15] - 2025-10-28

### Changed

- Debug output written to log file instead of console for cleaner user experience
- Detailed logging shows applies.site_ids, applies.sitegroup_ids, applies.wxtag_ids, applies.org_id
- Shows WLAN structure type (list vs dict) and WLAN count per template in debug logs

## [25.10.28.22.30] - 2025-10-28

### Documentation

- Site Templates (/sitetemplates): Full site configs with embedded WLANs
- WLAN Templates (/templates): WLAN-specific templates assignable to sites
- Org WLANs (/wlans): Standalone org-level WLANs (not template-based)

## [25.10.28.22.09] - 2025-10-28

## [25.10.28.21.00] - 2025-10-28

### Changed

- Enhanced WLAN inheritance detection across three levels: site, site_template, org_template
- Org WLAN template modifications now show clear impact scope (which sites affected)
- Improved warning messages distinguish between site template and org template changes
- API routing automatically selects correct update endpoint based on WLAN source level

## [25.10.21.15.00] - 2025-10-21

### Changed

- Results grid uses Rich Table with DOUBLE box style for prominence
- Columns auto-detected from first result item keys
- Scroll position tracked with results_scroll_offset state variable
- Help text dynamically shows grid controls when viewing results
- Grid appears automatically after successful API call with tabular data
- Execution state now includes 'viewing_results' for grid display mode

## [25.10.21.14.55] - 2025-10-21

### Changed

- Parameter submission logic clarified with explicit handling for required vs optional
- Debug logging differentiates between 'stored' and 'skipped' parameters
- API calls now only include parameters explicitly provided by user or auto-filled from .env

## [25.10.21.14.50] - 2025-10-21

### Changed

- Debug JSON files now include both raw_response (complete) and parsed_data (extracted)
- Object introspection via dir() and getattr() captures all non-private attributes
- Handles nested objects recursively to preserve full response hierarchy
- Graceful fallback to string representation for non-serializable types

## [25.10.21.14.45] - 2025-10-21

### Changed

- Results show structure depth with indentation (dict keys, list items, nested objects)
- Dictionary items display with type and count header (e.g., 'results: dict (5 keys)')
- List items show count and preview first N items with key-value pairs
- Nested structures recursively formatted up to 3 levels deep
- Sample item display shows first 3 key-value pairs per dict in list
- Value strings truncated to 60 chars in nested views, 200 chars at top level

## [25.10.21.14.30] - 2025-10-21

## [25.10.21.12.18] - 2025-10-21

### Changed

- Improved result display - shows sample keys and values for dict items in lists
- Better preview formatting - displays first 3 items with key-value pairs for API results
- Result metadata - shows function name, parameters (redacted), timestamp, and parsed data structure
- Debug file notifications - output panel shows where debug results were saved
- Tip messages - suggests viewing debug logs for large datasets

## [25.10.21.12.12] - 2025-10-21

### Changed

- Parameter prompts now display in prominent input boxes with clear headers
- Box-style input prompts show parameter name, requirement status, and default value
- Current input highlighted with white-on-gray background for visibility
- Previously entered parameters shown below with checkmarks
- Progress indicator shows N/M parameters completed
- Visual hierarchy: Current prompt (bold yellow box) → Previous inputs (dim with checkmarks)

## [25.10.21.12.09] - 2025-10-21

### Changed

- TUI stays active during function execution - no screen clearing or context switches
- Output panel shows execution progress (prompting → executing → completed)
- Previously entered parameters visible while prompting for next parameter
- Backspace support for editing input inline
- Escape cancels execution and returns to navigation mode
- Help text changes based on mode (navigation vs input)
- Smart result formatting in output panel (type, count, preview)
- Input mode clearly indicated with magenta Output panel border

## [25.10.21.12.04] - 2025-10-21

### Changed

- TUI now automatically uses values from .env file for function parameters
- Parameters like org_id, site_id, device_id automatically filled from environment variables
- No need to manually enter org_id when executing functions if configured in .env
- Environment values displayed with [from .env] indicator for transparency

## [25.10.21.11.58] - 2025-10-21

### Changed

- Function execution no longer interferes with TUI display refresh cycle
- Ctrl+C during execution properly returns to TUI without freezing
- Terminal mode properly managed across Live() context transitions

## [25.10.21.11.52] - 2025-10-21

### Changed

- Smart result preview system - shows type, count, and sample items without converting entire result to string
- Lists/tuples: Shows item count and first 3 items with truncation indicators
- Dicts: Shows key count and first 5 keys for large dictionaries
- Strings: Truncates at 200 characters with length indicator
- Memory-safe handling: Never converts full result to string, uses repr() with limits
- Helpful tip displayed for large results (>10 items) suggesting use of main menu CSV/SQLite export options

### Security

- Result preview limits prevent memory exhaustion attacks from malformed API responses
- Safe repr() usage with character limits prevents infinite recursion or excessive memory use

## [25.10.21.11.49] - 2025-10-21

### Changed

- Added intelligent viewport scrolling - visible window follows cursor through item list
- Viewport height automatically calculated based on available panel height (minus borders)
- Selection stays centered in viewport when possible, adjusts near top/bottom boundaries
- Debug logging for viewport calculations when --debug flag is set (selection position, scroll range, visible items)

## [25.10.21.11.43] - 2025-10-21

## [25.10.21.17.30] - 2025-10-21

### Changed

- MistHelperTUI class redesigned with hierarchical navigation state (current_path, breadcrumb)
- Dynamic discovery using Python inspect and importlib for package introspection
- Parameter prompting system with required/optional detection and default value support
- Result display with formatted preview and error handling
- Automatic apisession initialization and injection for API call execution
- Drill-down navigation (Enter on modules) and back navigation (Escape key)
- Real-time function signature and documentation display
- Educational design - learn API structure by exploring

## [25.10.14.17.00] - 2025-10-14

### Fixed

- Downloads now complete reliably without threading complexity

### Removed

- Queue-based background downloader (replaced with simpler synchronous approach)

## [25.10.07.16.15] - 2025-10-07

### Fixed

- Wired client API module - Corrected import path to mistapi.api.v1.sites.wired_clients (separate module from wireless clients)
- AttributeError on wired client fetch - Resolved 'module has no attribute searchSiteWiredClients' error
- Verified: Wireless clients use mistapi.api.v1.sites.clients.searchSiteWirelessClients
- Verified: Wired clients use mistapi.api.v1.sites.wired_clients.searchSiteWiredClients

## [25.10.06.18.30] - 2025-10-06

### Fixed

- Corrected session attribute in PCAP polling functions
- Site PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Org PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap() (line 4072)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap_org() (line 4212)
- PCAP downloads now work correctly - polling no longer throws AttributeError
- Root cause: `PacketCaptureManager.__init__` stores session as `self.mist_session`, not `self.apisession`

## [25.10.06.18.25] - 2025-10-06

### Changed

- Added comprehensive debug logging to PCAP download polling functions
- Site-level PCAP polling now logs every poll attempt with detailed capture state
- Org-level PCAP polling now logs every poll attempt with detailed capture state
- Logs response status code, number of captures returned, and capture found/not found status
- When capture found, logs all relevant fields: enabled, format, type, duration, expiry, timestamp, pcap_url
- Logs when pcap_url is NOT SET YET vs when it becomes available
- Logs available capture IDs when our capture is not found in the list
- Exception handling now uses exc_info=True for full traceback in logs
- Debug logs will reveal why PCAP downloads timeout (capture not found, pcap_url never set, API errors)
- Run with --debug flag to see detailed polling behavior in script.log

## [25.10.06.18.20] - 2025-10-06

### Fixed

- Corrected mistapi function names for listing packet captures
- Changed listSitePcapCaptures to correct listSitePacketCaptures (3 occurrences)
- Changed listOrgPcapCaptures to correct listOrgPacketCaptures (1 occurrence)
- Previous function names caused AttributeError when checking for existing captures
- Pre-check for existing captures now works correctly before launching new ones
- Locations: Single AP pre-check, multi-AP pre-check, site PCAP polling, org PCAP polling
- Function names now match mistapi SDK and Mist API operationId values
- operationId: listSitePacketCaptures and listOrgPacketCaptures per OpenAPI spec
