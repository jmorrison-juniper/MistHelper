---
description: "Task list for feature 1823-upgrade-capture-portal"
---

# Tasks: Upgrade Pre-Check and Post-Check Portal

**Input**: Design documents from `/specs/1823-upgrade-capture-portal/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `research/` (six reference
documents), `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: The specification asks for unit tests, contract tests, and browser
tests. Every test task below is required, not optional.

**Organization**: Tasks are grouped by user story. Each story is independently
implementable and independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with its siblings. It touches a different
  file and depends on no incomplete task.
- **[Story]**: The user story the task serves. Setup, Foundational, and Polish
  tasks carry no story label.
- Every task names an exact file path.

## Path Conventions

This repository is a single Python project. Source lives under `src/`. Tests live
under `tests/`. The new package is `src/upgrade_portal/`. The new upgrade seam is
`src/firmware/upgrade_service.py`.

---

## Rules that apply to every task in this file

Read these once. They bind every implementation task. Do not repeat them in a
task description.

| Rule | Detail |
| --- | --- |
| Five-Item Rule | At most 5 parameters, 5 blocks, 5 operations for each block, and 25 lines for each function. A request context object carries wider input. |
| Docstrings | Every module, class, function, and method carries a Google-style docstring with a "Why" section after the summary. `interrogate` enforces 90 percent. `pydoclint` enforces content. |
| Inline comments | Constitution Principle VI asks for a comment on each generated line that states why the line exists. |
| Logging | Use stdlib `logging` with `%s` placeholders. Never use an f-string. Use ASCII characters only. Log at info before an action and at debug after it. Carry a run identifier and a site identifier on every record. `structlog` stays inside `src/db`. |
| Credentials | Never show, log, or store a password value or a token value (FR-009). Name the variable, never the value. |
| Writing style | Every docstring, comment, message, and page string follows Simplified Technical English. See `documentation/ASD-STE100_writing-guide.md`. |
| Coverage | The floor for the new package is 90 percent. `pyproject.toml:419-420` sets 90. |
| Forbidden import | The portal never imports `src/firmware/firmware_manager.py`. That module holds four globals at `:34-37`. The save-and-restore blocks at `:1736` and `:1797` are not thread safe. |
| Forbidden call | Never call `getOrgSsrUpgrade`. The installed SDK builds the cancel path inside that function at `mistapi/api/v1/orgs/ssr.py:167`. |
| Concurrency | Use threads. Never use asyncio. Use `ConnectionPoolExecutor` with about 4 workers at the call-group level. Never fan out per device. |
| Reserved word | The word `snapshot` is reserved. The cloud upgrade body already uses that field name for a Junos file action. The internal term is `capture`. |

## Work that is out of scope

Do not do either of these inside this feature.

1. **Do not repair issue #1824.** `_is_standalone_mode()` at
   `src/export/data_exporter.py:141` gates every polyglot write on a container
   check. `_csv_fallback` at `src/db/router.py:372-382` returns `success=True`
   after it writes zero rows. `plan.md:322-330` forbids the repair here. FR-031
   makes the portal verify its own write by a read-back, so the portal does not
   depend on the repair.
2. **Do not repair `src/db/retention.py:100`.** The line reads an attribute named
   `_database` while the writer names the handle `self._db`. The purge therefore
   never runs. A repair would start to delete captures. FR-032 asks for unlimited
   retention.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton, register the feature with the
repository guardrails, and put every vendored asset in place.

- [ ] T001 Create the package skeleton at `src/upgrade_portal/` with `__init__.py`, and create the five subpackage directories `app/`, `capture/`, `upgrade/`, `compare/`, and `runtime/`, each with its own `__init__.py`
- [ ] T002 [P] Create `src/upgrade_portal/app/routes/__init__.py` and the asset directories `src/upgrade_portal/app/assets/templates/` and `src/upgrade_portal/app/assets/static/`
- [ ] T003 [P] Create the test package directories `tests/unit/upgrade_portal/`, `tests/contract/upgrade_portal/`, and `tests/e2e/upgrade_portal/`, each with an `__init__.py`
- [ ] T004 [P] Add the menu 238 entry to `src/utils/operation_registry.py` with the correct category, because the fail-closed guardrail breaks the build without it
- [ ] T005 [P] Add the `upgradeCaptureWrite` entry with strategy `natural_pk` and key field `capture_id` to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `src/refactors/endpoint_primary_key_strategies.py`
- [ ] T006 [P] Add the `upgradeRunWrite` entry with strategy `natural_pk` and key field `run_id` to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `src/refactors/endpoint_primary_key_strategies.py`
- [ ] T007 Add the menu 238 registration for the capture portal to `MistHelper.py`
- [ ] T008 Add the `--capture-portal` command-line flag and the launcher function for menu 238 to `MistHelper.py`
- [ ] T009 [P] Create `wsgi_capture.py` at the repository root as the WSGI entry point that imports `create_app` from `src/upgrade_portal/app/factory.py`
- [ ] T010 [P] Add `ENV CAPTURE_PORT=8056` and extend the `EXPOSE` line to include 8056 in `Containerfile`
- [ ] T011 [P] Publish port 8056 next to the existing port 8055 in `compose.yml`
- [ ] T012 Start the second Gunicorn process for `wsgi_capture:app` on port 8056 with the `gthread` worker class in `container/scripts/start.sh`
- [ ] T013 [P] Add the new test paths and the coverage source for `src/upgrade_portal` to `pyproject.toml`
- [ ] T014 [P] Vendor the Bootstrap 5 stylesheet into `src/upgrade_portal/app/assets/static/vendor/bootstrap/bootstrap.min.css`, because the content security policy is `'self'` only and no asset may load from a network
- [ ] T015 [P] Vendor the Bootstrap 5 bundle script into `src/upgrade_portal/app/assets/static/vendor/bootstrap/bootstrap.bundle.min.js`
- [ ] T016 [P] Create the base stylesheet `src/upgrade_portal/app/assets/static/css/portal.css` with the shared layout rules
- [ ] T017 [P] Create the default theme `src/upgrade_portal/app/assets/static/css/themes/default.css`
- [ ] T018 [P] Create the brand theme `src/upgrade_portal/app/assets/static/css/themes/magenta.css` with the primary color `#E20074`. Put the brand name inside the file content only. `.gitignore:31-35` and `.dockerignore:93-96` exclude any path that matches `*tmo*`, `*TMO*`, `*t-mobile*`, or `*T-Mobile*`.
- [ ] T019 [P] Create `src/upgrade_portal/app/assets/static/js/portal.js` with the shared helpers for the cross-site request forgery header, the JSON fetch wrapper, and the flash message region
- [ ] T020 [P] Create the Playwright configuration for the new browser tests in `tests/e2e/upgrade_portal/playwright.config.py` with `screenshot: only-on-failure`, `trace: retain-on-failure`, `testIdAttribute: data-testid`, and `baseURL: http://127.0.0.1:8056`
- [ ] T021 [P] Create the shared unit and contract fixtures in `tests/unit/upgrade_portal/conftest.py`
- [ ] T022 [P] Create the contract fixtures with a Flask test client in `tests/contract/upgrade_portal/conftest.py`
- [ ] T023 [P] Create the browser fixtures in `tests/e2e/upgrade_portal/conftest.py`. Reuse the shape of the `gunicorn_server` fixture at `tests/e2e/conftest.py:56-99`, which has no consumer today, and bind it to port 8056.
- [ ] T024 Run `ruff check src/upgrade_portal`, `black --check src/upgrade_portal`, and `mypy src/upgrade_portal` once against the empty skeleton to prove that every gate already covers the new package

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the application shell, the shared runtime services, and the
storage bootstrap. Every user story depends on this phase.

**CRITICAL**: No user story work can begin until this phase is complete.

### Application shell

- [ ] T025 Implement the configuration reader in `src/upgrade_portal/app/config.py`. Read `CAPTURE_PORT` with the default 8056, the secret key, the theme list, the poll interval of 30 seconds, and the ArangoDB and Redis settings by variable name.
- [ ] T026 Implement the security layer in `src/upgrade_portal/app/security.py`. Set the content security policy to `'self'` only, register `flask-wtf` cross-site request forgery protection, add the standard response headers, and add the internet protocol allow list.
- [ ] T027 Implement the application factory `create_app` in `src/upgrade_portal/app/factory.py`. Register the five blueprints, register the teardown handler, and configure stdlib logging with the run identifier and the site identifier fields.
- [ ] T028 Add the JSON error envelope and the error handlers for the codes 400, 401, 403, 404, 409, 429, and 500 to `src/upgrade_portal/app/factory.py`. Follow the one shape in `contracts/README.md:31-39`. A test asserts on `code`, never on `message`.
- [ ] T029 Add the `csrf_missing` error path to `src/upgrade_portal/app/security.py`. A request that changes state without a valid token receives 400.
- [ ] T030 Add the `GET /healthz` route to `src/upgrade_portal/app/factory.py`. Return `{"status": "ok", ...}` with no database call.

### Shared templates

- [ ] T031 Create the base layout `src/upgrade_portal/app/assets/templates/layout.html` with the `csrf-meta` meta tag, the vendored Bootstrap link, the theme link, and the `portal.js` script tag
- [ ] T032 [P] Create the shared navigation partial `src/upgrade_portal/app/assets/templates/partials/nav.html` with the `nav-sites`, `nav-history`, `theme-select`, and `signout-button` test identifiers
- [ ] T033 [P] Create the shared flash partial `src/upgrade_portal/app/assets/templates/partials/flash.html` with the `flash-message` test identifier
- [ ] T034 [P] Create the shared error page `src/upgrade_portal/app/assets/templates/error.html`

### Runtime services

- [ ] T035 Implement the per-user session registry and the sign-in guard in `src/upgrade_portal/runtime/identity.py`. Hold the operator email, the browser identifier, and the cloud session by reference. Never hold a password value or a token value.
- [ ] T036 Add the environment-token credential mode and the `not_authenticated` guard decorator to `src/upgrade_portal/runtime/identity.py` (FR-006, FR-007). The full MSP flow arrives in User Story 5.
- [ ] T037 Add the `browser_id` first-party cookie writer to `src/upgrade_portal/runtime/identity.py`. Two windows on one computer share the value. Two computers do not.
- [ ] T038 Implement the thread pool sizing and the shutdown handler in `src/upgrade_portal/runtime/pools.py`. Wrap `ConnectionPoolExecutor.execute` from `src/refactors/connection_pool_executor.py:314-326` with about 4 workers. A worker function accepts one work item and one `threading.Semaphore`.
- [ ] T039 Add the late-binding import guard to `src/upgrade_portal/runtime/pools.py`. Import `MistHelper` inside a function body, as `src/refactors/connection_pool_executor.py:46` does, to avoid a circular import.
- [ ] T040 Implement the stop request store in `src/upgrade_portal/runtime/signals.py`. Hold the request in the run record. Use no file sentinel and no process working directory path. Every output belongs under `data/`.
- [ ] T041 Implement the `UpgradeRun` record writer in `src/upgrade_portal/runtime/runs.py`. Build the key `run-{uuid4hex}`, set `schema_version` to the integer 1, and write every field in `data-model.md:217-236`.
- [ ] T042 Add the run state machine transitions to `src/upgrade_portal/runtime/runs.py`. Follow the states at `data-model.md:240-251`. Write `updated_at` on every state change.
- [ ] T043 Add the run status view builder to `src/upgrade_portal/runtime/runs.py`. Return `phase_order`, `phases`, `targets`, `stop_request`, `pre_capture_id`, `post_capture_id`, and `message`, as `contracts/http-api.md` requires.

### Storage bootstrap

- [ ] T044 Implement the collection bootstrap in `src/upgrade_portal/capture/store.py`. Create `upgrade_captures`, `upgrade_runs`, and the edge collection `capture_for_run` at startup. `_ensure_collection` at `src/db/arango_writer.py:3957-3963` creates a collection but creates no index.
- [ ] T045 Add the idempotent index creation for the eight indexes at `data-model.md:374-383` to `src/upgrade_portal/capture/store.py`. Add no time-to-live index. A time-to-live index would delete the exact document the operator must read months later.
- [ ] T046 Add the write path to `src/upgrade_portal/capture/store.py`. Call `DataExporter.write_with_format_selection()` at `src/export/data_exporter.py:104-111` with the operation name `upgradeCaptureWrite` or `upgradeRunWrite`.
- [ ] T047 Add the read-back verification to `src/upgrade_portal/capture/store.py` (FR-031, decision D9). Read the key back, compare the stored `schema_version` and the stored digest, and report the true outcome. `WriteResult.success` alone is not proof.

### Foundational tests

- [ ] T048 [P] Unit test the configuration defaults and the `CAPTURE_PORT` override in `tests/unit/upgrade_portal/test_config.py`
- [ ] T049 [P] Unit test the session registry, the guard decorator, and the browser cookie in `tests/unit/upgrade_portal/test_identity.py`
- [ ] T050 [P] Unit test the thread pool sizing and the shutdown handler in `tests/unit/upgrade_portal/test_pools.py`
- [ ] T051 [P] Unit test the run record builder, the key shape, and every state transition in `tests/unit/upgrade_portal/test_runs.py`
- [ ] T052 [P] Unit test the stop request store in `tests/unit/upgrade_portal/test_signals.py`
- [ ] T053 [P] Unit test the read-back verification, including the case where the write reports success after it wrote zero rows, in `tests/unit/upgrade_portal/test_store.py`
- [ ] T054 [P] Contract test the error envelope shape and every status code in `tests/contract/upgrade_portal/test_errors.py`
- [ ] T055 [P] Contract test the content security policy header, the cross-site request forgery rejection, and the `not_authenticated` guard in `tests/contract/upgrade_portal/test_security.py`
- [ ] T056 [P] Contract test `GET /healthz` in `tests/contract/upgrade_portal/test_health.py`

**Checkpoint**: The application starts, answers `/healthz`, refuses an
unauthenticated request, and writes a verified document. User story work can now
begin.

---

## Phase 3: User Story 1 - Record the state of a site before an upgrade (Priority: P1) 🎯 MVP

**Goal**: An operator signs in, picks an organization and a site, starts a
capture, watches the progress, and sees a verified badge with a stored size above
zero.

**Independent Test**: Run Scenario A in `quickstart.md:57-87`. A 250-device site
finishes in 90 seconds or less. The verified badge appears. The device count in
the capture equals the count in the inventory view. Every chassis member appears
as its own row.

### Tests for User Story 1

> Write these tests first. Prove that they fail before the implementation starts.

- [ ] T057 [P] [US1] Contract test `GET /api/orgs/<org_id>/sites` and `GET /api/sites/<site_id>/inventory` in `tests/contract/upgrade_portal/test_select.py`
- [ ] T058 [P] [US1] Contract test `POST /api/sites/<site_id>/captures` with the `bad_tier` and `site_not_found` error codes in `tests/contract/upgrade_portal/test_capture_start.py`
- [ ] T059 [P] [US1] Contract test `GET /api/captures/<id>/status` for the `state`, `percent`, `sections`, `counts`, `partial_reasons`, `verified`, and `message` fields in `tests/contract/upgrade_portal/test_capture_status.py`
- [ ] T060 [P] [US1] Contract test `GET /api/captures/<id>` with the `capture_not_found` error code in `tests/contract/upgrade_portal/test_capture_read.py`
- [ ] T061 [P] [US1] Browser test the site picker and the inventory view in `tests/e2e/upgrade_portal/test_site_selection.py`. Drive `site-search`, `site-row-{site_id}`, `site-open-{site_id}`, `inventory-table`, `inventory-row-{mac}`, and `inventory-count-total`.
- [ ] T062 [P] [US1] Browser test the capture journey in `tests/e2e/upgrade_portal/test_capture.py`. Drive `capture-tier-select`, `capture-start-button`, `capture-progress`, `capture-progress-percent`, `capture-section-{name}`, `capture-verified-badge`, and `capture-size-bytes`.

### Implementation for User Story 1

- [ ] T063 [P] [US1] Implement the device inventory read in `src/upgrade_portal/capture/devices.py`. Call the site inventory with `vc=True`, so every chassis member appears as its own entry (decision D11).
- [ ] T064 [US1] Add the device statistics read to `src/upgrade_portal/capture/devices.py`. Pass `type="all"` to `listSiteDevicesStats`. The default returns access points only. A capture with only access points means the code missed this parameter.
- [ ] T065 [US1] Add the `device_index` builder to `src/upgrade_portal/capture/devices.py`. Build the flat map at `data-model.md:100-115` with `name`, `type`, `model`, `serial`, `version`, `status`, `uptime`, `site_id`, `vc_role`, `vc_mac`, `num_members`, and `ip`. Set `vc_role` to `standalone` when the device is not a chassis member. Store no timestamp.
- [ ] T066 [US1] Add the page-count guard to `src/upgrade_portal/capture/devices.py`. `mistapi.get_all` returns an empty list without an error on an unexpected shape, so compare the returned length against the reported `total` and record a partial reason on a mismatch.
- [ ] T067 [P] [US1] Implement the wired client read in `src/upgrade_portal/capture/clients.py`. Build a `ClientRecord` with `mac`, `hostname`, `ip`, `device_mac`, `device_name`, `port_id`, `vlan`, and `username`.
- [ ] T068 [US1] Add the wireless client read to `src/upgrade_portal/capture/clients.py`. Call `listSiteWirelessClientsStats` for the signal strength and `searchSiteWirelessClients` for the random media access control flag, then join the two results on `mac`. A client in one source only still enters the list, with the missing fields absent.
- [ ] T069 [US1] Add the guest client read to `src/upgrade_portal/capture/clients.py`
- [ ] T070 [US1] Normalize every media access control address to lower case with no separator in `src/upgrade_portal/capture/clients.py` and `src/upgrade_portal/capture/devices.py`. The comparison matches on `mac` alone.
- [ ] T071 [P] [US1] Implement the tier 3 extra reads in `src/upgrade_portal/capture/extras.py` for `switch_ports`, `poe`, `radios`, `tunnels`, `bgp_peers`, and `alarms`. The port data and the radio data need no extra cloud call.
- [ ] T072 [US1] Implement the capture document assembly in `src/upgrade_portal/capture/assembly.py`. Build every top-level field at `data-model.md:43-68`. Set `schema_version` to the integer 1 and `capture_id` to `cap-{run_hex}-{ordinal:02d}`.
- [ ] T073 [US1] Add the digest builder to `src/upgrade_portal/capture/assembly.py`. Build `devices`, `clients_wired`, `clients_wireless`, `clients_guest`, `extras`, and `whole`. Hash the canonical JSON form with every volatile field removed. The volatile list is `timestamp`, `last_seen`, `uptime`, `_ts`, and any counter of bytes or packets.
- [ ] T074 [US1] Add the `counts` builder to `src/upgrade_portal/capture/assembly.py` for the nine integer keys at `data-model.md:179-183`
- [ ] T075 [US1] Add the eight validation rules at `data-model.md:188-196` to `src/upgrade_portal/capture/assembly.py`
- [ ] T076 [US1] Add the partial-capture path to `src/upgrade_portal/capture/assembly.py`. Set `capture_status` to `partial` and write one `partial_reasons` entry with `section`, `reason`, and `http_status` for each failed section.
- [ ] T077 [US1] Add the `stored_size_bytes` measurement to `src/upgrade_portal/capture/store.py` (FR-032b). Measure the stored document. The value is greater than zero after a successful write.
- [ ] T078 [US1] Add the capture list and load functions to `src/upgrade_portal/capture/store.py`. Only a `verified` capture may take part in a comparison.
- [ ] T079 [US1] Add the `CaptureForRun` edge write with the key `edge-{capture_key}` to `src/upgrade_portal/capture/store.py`
- [ ] T080 [US1] Wire the six capture call groups through `src/upgrade_portal/runtime/pools.py` inside `src/upgrade_portal/capture/assembly.py`. The groups are devices, wireless statistics, wireless search, wired clients, ports, and the small tier 3 calls. Keep the pages inside one group sequential, because the cloud paginates with a cursor.
- [ ] T081 [US1] Implement the capture state machine `pending -> collecting -> assembling -> writing -> verified` with the `write_failed`, `partial`, and `failed` branches in `src/upgrade_portal/capture/store.py`
- [ ] T082 [P] [US1] Implement the organization list route and the site list route in `src/upgrade_portal/app/routes/select.py` (FR-012 to FR-015). Return a device count for each site.
- [ ] T083 [US1] Implement the inventory route in `src/upgrade_portal/app/routes/select.py`. Do not pass `type="all"` to `searchOrgDevices`. The value is not legal on that endpoint.
- [ ] T084 [US1] Implement `POST /api/sites/<site_id>/captures` in `src/upgrade_portal/app/routes/capture.py` (FR-021 to FR-028). Return 202 and start the collection on a background thread. Reject an unknown tier with `bad_tier`.
- [ ] T085 [US1] Implement `GET /api/captures/<id>/status` in `src/upgrade_portal/app/routes/capture.py`. Return `state`, `percent`, the `sections` map, `counts`, `partial_reasons`, `verified`, and `message`.
- [ ] T086 [US1] Implement `GET /api/captures/<id>` and the capture page route in `src/upgrade_portal/app/routes/capture.py` (FR-029 to FR-032b). Return `capture_not_found` for an unknown identifier.
- [ ] T087 [P] [US1] Create the site list template `src/upgrade_portal/app/assets/templates/select/sites.html` with the `site-search`, `site-row-{site_id}`, `site-lock-state-{site_id}`, and `site-open-{site_id}` test identifiers
- [ ] T088 [P] [US1] Create the inventory template `src/upgrade_portal/app/assets/templates/select/inventory.html` with the `inventory-table`, `inventory-row-{mac}`, and `inventory-count-total` test identifiers
- [ ] T089 [P] [US1] Create the capture template `src/upgrade_portal/app/assets/templates/capture/capture.html` with the `capture-tier-select`, `capture-start-button`, `capture-progress`, `capture-progress-percent`, `capture-section-{name}`, `capture-verified-badge`, `capture-partial-warning`, `capture-size-bytes`, and `capture-error` test identifiers
- [ ] T090 [US1] Add the 30-second capture status poll to `src/upgrade_portal/app/assets/static/js/portal.js` (decision D3). Use no server-sent event. The existing event bus caps at 10 subscribers.
- [ ] T091 [P] [US1] Unit test the device reads, the `device_index` builder, the chassis member expansion, and the page-count guard in `tests/unit/upgrade_portal/test_capture_devices.py`
- [ ] T092 [P] [US1] Unit test the client reads, the wireless join on `mac`, and the address normalization in `tests/unit/upgrade_portal/test_capture_clients.py`
- [ ] T093 [P] [US1] Unit test the document assembly, the digest builder, the volatile field stripping, the counts, the validation rules, and the partial path in `tests/unit/upgrade_portal/test_capture_assembly.py`
- [ ] T094 [P] [US1] Unit test the tier 3 extra reads in `tests/unit/upgrade_portal/test_capture_extras.py`

**Checkpoint**: User Story 1 is complete. An operator can record the state of a
site and prove that the portal stored it. This is the minimum viable product.

---

## Phase 4: User Story 2 - Compare the state before and after (Priority: P1)

**Goal**: An operator picks two verified captures of one site and reads every
difference, with a statistics region and a download.

**Independent Test**: Run Scenario B in `quickstart.md:90-117`. The comparison
renders in 3 seconds or less. A client that changed access point counts as
`moved`, never as `missing`. Two captures of a quiet site show zero device
changes. The skipped section list names any section whose digest matched.

### Tests for User Story 2

- [ ] T095 [P] [US2] Contract test `GET /api/comparisons` for the statistics keys, `device_deltas`, `client_deltas`, and `skipped_sections` in `tests/contract/upgrade_portal/test_comparison.py`
- [ ] T096 [P] [US2] Contract test the `capture_site_mismatch` and `capture_not_verified` refusals in `tests/contract/upgrade_portal/test_comparison_errors.py`
- [ ] T097 [P] [US2] Contract test the comma-separated value download and the JSON download, including the `bad_format` error code, in `tests/contract/upgrade_portal/test_comparison_export.py`
- [ ] T098 [P] [US2] Browser test the comparison journey in `tests/e2e/upgrade_portal/test_comparison.py`. Drive `compare-before-select`, `compare-after-select`, `compare-run-button`, `compare-statistics`, `compare-stat-{name}`, `compare-device-table`, `compare-device-row-{mac}`, `compare-client-table`, `compare-client-row-{mac}`, `compare-filter-{outcome}`, `compare-export-csv`, and `compare-export-json`.

### Implementation for User Story 2

- [ ] T099 [P] [US2] Implement the device comparison in `src/upgrade_portal/compare/diff.py`. Compare `status`, `version`, `model`, `name`, `ip`, `vc_role`, and `num_members`. Exclude `uptime`, because uptime always differs.
- [ ] T100 [US2] Add the four device outcomes `unchanged`, `changed`, `added`, and `removed` to `src/upgrade_portal/compare/diff.py`. A `changed` entry lists each field with the value before and the value after.
- [ ] T101 [US2] Add the digest short-circuit to `src/upgrade_portal/compare/diff.py`. Read `digests` first and skip a section whose digest matched. Record the skipped section in `skipped_sections`.
- [ ] T102 [P] [US2] Implement the client comparison in `src/upgrade_portal/compare/clients.py`. Match on `mac` alone. Strip `timestamp` from any composite registry key before the match, because a key that holds a timestamp makes every row look new.
- [ ] T103 [US2] Add the four client outcomes `present`, `moved`, `added`, and `missing` to `src/upgrade_portal/compare/clients.py`. A change of serving device counts as `moved`. `moved` is its own statistic and never a loss.
- [ ] T104 [P] [US2] Implement the statistics roll-up in `src/upgrade_portal/compare/statistics.py` for `devices_unchanged`, `devices_changed`, `devices_added`, `devices_removed`, `clients_present`, `clients_moved`, `clients_added`, `clients_missing`, and `client_return_rate`
- [ ] T105 [US2] Add the device version change count and the elapsed run time to `src/upgrade_portal/compare/statistics.py`
- [ ] T106 [P] [US2] Implement the view models in `src/upgrade_portal/compare/render.py`. Build the header, the device section, the client section, and the statistics section.
- [ ] T107 [US2] Add the outcome filter to `src/upgrade_portal/compare/render.py`, so the interface can show one outcome at a time
- [ ] T108 [P] [US2] Implement the comma-separated value export and the JSON export in `src/upgrade_portal/compare/download.py`. Write one row for each difference. Write no credential value.
- [ ] T109 [US2] Add the `bad_format` refusal to `src/upgrade_portal/compare/download.py`
- [ ] T110 [US2] Implement `GET /api/comparisons` and the comparison page route in `src/upgrade_portal/app/routes/review.py` (FR-064 to FR-071). Refuse two captures of different sites with `capture_site_mismatch`. Refuse an unverified capture with `capture_not_verified`.
- [ ] T111 [US2] Implement the comparison download routes in `src/upgrade_portal/app/routes/review.py`
- [ ] T112 [P] [US2] Create the comparison picker template `src/upgrade_portal/app/assets/templates/review/compare_select.html` with the `compare-before-select`, `compare-after-select`, and `compare-run-button` test identifiers
- [ ] T113 [P] [US2] Create the comparison view template `src/upgrade_portal/app/assets/templates/review/compare.html` with the `compare-statistics`, `compare-stat-{name}`, `compare-device-table`, `compare-device-row-{mac}`, `compare-client-table`, `compare-client-row-{mac}`, `compare-filter-{outcome}`, `compare-export-csv`, and `compare-export-json` test identifiers
- [ ] T114 [P] [US2] Unit test the device comparison, the compared field list, the uptime exclusion, and the digest short-circuit in `tests/unit/upgrade_portal/test_compare_diff.py`
- [ ] T115 [P] [US2] Unit test the client comparison, the `mac` match key, the timestamp stripping, and the `moved` outcome in `tests/unit/upgrade_portal/test_compare_clients.py`
- [ ] T116 [P] [US2] Unit test the statistics roll-up and the client return rate in `tests/unit/upgrade_portal/test_compare_statistics.py`
- [ ] T117 [P] [US2] Unit test the view models and the outcome filter in `tests/unit/upgrade_portal/test_compare_render.py`
- [ ] T118 [P] [US2] Unit test both export formats in `tests/unit/upgrade_portal/test_compare_download.py`

**Checkpoint**: User Stories 1 and 2 both work on their own. An operator can
record a site twice and read every difference.

---

## Phase 5: User Story 3 - Start an upgrade and watch every device return (Priority: P2)

**Goal**: An operator picks target versions, types `UPGRADE`, and watches the
cascade settle in order. The post-check capture starts on its own. A stop control
cancels every device that has not started to write firmware.

**Independent Test**: Run Scenario C in `quickstart.md:120-157` and Scenario D in
`quickstart.md:160-181` on a laboratory site. The portal refuses to start without
a verified pre-check. The phases settle in the fixed cascade order. A device
counts as settled only after three signals. The run status endpoint answers in
under 1 second.

### The upgrade seam

- [ ] T119 [P] [US3] Create `src/firmware/upgrade_service.py` with the frozen dataclasses `DeviceTarget`, `UpgradeOptions`, `UpgradePlan`, `UpgradeSubmission`, and `CancelOutcome`, plus the `GatewayFamily` enumeration with the members `JUNOS` and `SSR`. Follow `contracts/upgrade-service.md:37-92` exactly. The contract wins over the earlier proposal at `research/upgrade-reuse.md:624-707`, which shares only the module path and four names.
- [ ] T120 [US3] Implement `classify_gateway(device) -> GatewayFamily` in `src/firmware/upgrade_service.py`. Return `SSR` when the device type equals `ssr`, or when the model string holds `SSR` or `128T`. Return `JUNOS` for every other gateway. The one existing discriminator is `_is_ssr_inventory_row` at `src/firmware/firmware_manager.py:2291`. Repeat the test without the module state.
- [ ] T121 [US3] Implement `build_body(targets, options, family)` in `src/firmware/upgrade_service.py`. Keep it pure with no input and no output. Send `reboot` for a switch or a gateway only. Send the Junos file action field for a Junos device only. Send a canary phase list whenever the strategy is canary. Never send an unread field.
- [ ] T122 [US3] Implement `plan_upgrade(targets, options, org_id, site_id)` in `src/firmware/upgrade_service.py`. Keep it pure with no cloud call. Group access points, switches, and Junos gateways at site scope through `upgradeSiteDevices`. Group session smart routers at organization scope through `upgradeOrgSsrs`. Add a warning when a target list mixes families.
- [ ] T123 [US3] Implement `invoke_upgrade(session, plan)` in `src/firmware/upgrade_service.py`. Perform one cloud call. Never retry. Never raise for a cloud error status. Record the status in `raw_status`. Raise `ValueError` for a malformed plan.
- [ ] T124 [US3] Implement `cancel_upgrade(session, plan, upgrade_id)` in `src/firmware/upgrade_service.py`. Call `cancelSiteDeviceUpgrade` at `mistapi/api/v1/sites/devices.py:1289`, `cancelOrgDeviceUpgrade` at `mistapi/api/v1/orgs/devices.py:894`, or `cancelOrgSsrUpgrade` at `mistapi/api/v1/orgs/ssr.py:173`. Sort each address into `cancelled` or `already_writing`. Write one plain sentence into `message`.
- [ ] T125 [US3] Implement `read_upgrade_status(session, scope, identifier, upgrade_id)` in `src/firmware/upgrade_service.py`. Read `current_phase`, not `phase`. Treat `reboot_in_progress` as a list of addresses inside `targets`, not as a boolean. Never call `getOrgSsrUpgrade`. Use `getSiteSsrUpgrade` for a site-scope read, or read the device statistics for an organization-scope read.
- [ ] T126 [US3] Implement `list_available_versions(session, site_id, models)` in `src/firmware/upgrade_service.py`. Read the cloud once and group the answer by model.
- [ ] T127 [US3] Add the module prohibition guard test to `tests/unit/upgrade_portal/test_upgrade_service_prohibitions.py`. Prove that `src/firmware/upgrade_service.py` holds no `firmware_manager` import, no `print`, no `input`, no `safe_input`, and no module global, as `contracts/upgrade-service.md:200-207` requires.

### Tests for User Story 3

- [ ] T128 [P] [US3] Contract test `POST /api/runs`, `POST /api/runs/<id>/options`, and the `bad_option` and `pre_capture_missing` error codes in `tests/contract/upgrade_portal/test_upgrade_options.py`
- [ ] T129 [P] [US3] Contract test `POST /api/runs/<id>/start` with `{"confirm": "UPGRADE"}`, and the `confirmation_required` refusal for any other word, in `tests/contract/upgrade_portal/test_upgrade_start.py`
- [ ] T130 [P] [US3] Contract test `GET /api/runs/<id>/status` for `phase_order`, `phases`, `targets`, `stop_request`, `pre_capture_id`, `post_capture_id`, and `message` in `tests/contract/upgrade_portal/test_run_status.py`
- [ ] T131 [P] [US3] Contract test `POST /api/runs/<id>/stop` with `{"confirm": "STOP"}`, and the `run_not_stoppable` and `confirmation_required` refusals, in `tests/contract/upgrade_portal/test_upgrade_stop.py`
- [ ] T132 [P] [US3] Browser test the upgrade journey in `tests/e2e/upgrade_portal/test_upgrade.py`. Drive `upgrade-version-select-{mac}`, `upgrade-version-select-all`, `upgrade-reboot-toggle`, `upgrade-strategy-select`, `upgrade-target-table`, `upgrade-target-row-{mac}`, `upgrade-warning-list`, `upgrade-confirm-input`, `upgrade-start-button`, `upgrade-state`, `upgrade-phase-{name}`, `upgrade-phase-progress-{name}`, and `upgrade-device-state-{mac}`.
- [ ] T133 [P] [US3] Browser test the stop control in `tests/e2e/upgrade_portal/test_stop.py`. Drive `stop-button`, `stop-confirm-input`, `stop-confirm-submit`, `stop-outcome`, `stop-outcome-cancelled`, `stop-outcome-writing`, and `stop-outcome-message`.

### Implementation for User Story 3

- [ ] T134 [P] [US3] Implement the version list and the target choice in `src/upgrade_portal/upgrade/options.py` (FR-016 to FR-020). Fetch the inventory with the virtual chassis parameter omitted, because an upgrade targets the logical device (decision D11).
- [ ] T135 [US3] Add the option mapping to `src/upgrade_portal/upgrade/options.py`. Map the interface controls onto the `UpgradeOptions` fields `reboot`, `junos_file_action`, `strategy`, and `start_time`. Refuse an unknown value with `bad_option`.
- [ ] T136 [US3] Add the gateway family split to `src/upgrade_portal/upgrade/options.py`. Call `classify_gateway` and set `gateway_family` and `scope` on each target entry. A session smart router always uses `org`.
- [ ] T137 [P] [US3] Implement the event key discovery in `src/upgrade_portal/upgrade/events.py`. Load the catalogue from `listDeviceEventsDefinitions` at start, filter for keys that end in `_CONNECTED` and `_RESTARTED`, and cache the result. Hard-code no key list. Only the access point restart event is vendor confirmed.
- [ ] T138 [US3] Add the event poll to `src/upgrade_portal/upgrade/events.py`. Call `searchOrgDeviceEvents` once every 20 seconds at organization scope. Pass `device_type` explicitly for each family. The default is `ap`, so a switch gate or a gateway gate would wait forever.
- [ ] T139 [US3] Add the cursor handling to `src/upgrade_portal/upgrade/events.py`. Use `search_after`, never `page`. Both vendored documents advise `page`, and no `page` parameter exists. Narrow the window with `start` and `end` and raise `limit`, so each poll fits one page.
- [ ] T140 [P] [US3] Implement the settle gate rules in `src/upgrade_portal/upgrade/gate.py`. A device settles only after three signals: a reconnect event, an uptime that decreased together with a version that changed, and then an extra wait of 60 seconds. An access point waits a further 60 seconds.
- [ ] T141 [US3] Add the uptime comparison to `src/upgrade_portal/upgrade/gate.py`. The test is "current is less than previous", never "current is near zero". A device that reboots quickly reports a small positive uptime. Treat a null reading as "no reading" and retry. A null reading is not zero.
- [ ] T142 [US3] Add the statistics poll to `src/upgrade_portal/upgrade/gate.py`. Call `listOrgDevicesStats` once every 20 seconds for the whole fleet with a narrow `fields` list. Use no per-device poll. Keep the total under 360 calls each hour, under 8 percent of the 5000 call quota at `src/utils/rate_limiting.py:56`.
- [ ] T143 [US3] Add the reboot hint reader to `src/upgrade_portal/upgrade/gate.py`. Read `targets.reboot_in_progress` from the upgrade job to learn which devices are mid-reboot with one call. Build no logic on the device statistics `status` field, which carries no description and no enumeration.
- [ ] T144 [P] [US3] Implement the run driver thread in `src/upgrade_portal/upgrade/driver.py`. Run one long-lived thread for each run. No other thread writes the run record.
- [ ] T145 [US3] Add the fixed cascade order to `src/upgrade_portal/upgrade/driver.py` (FR-052 to FR-058). Run the gateway gate, then the switch gate, then the access point gate, then the wireless client gate. A phase starts only after the phase before it reports settled.
- [ ] T146 [US3] Add the wireless client gate to `src/upgrade_portal/upgrade/driver.py` (FR-054). Open the client gate only after the access point gate settles.
- [ ] T147 [US3] Add the automatic post-check capture to `src/upgrade_portal/upgrade/driver.py` (FR-059 to FR-063). Start the post-check on its own after the client phase settles. Write the capture with `ordinal` 2 and `role` `post`.
- [ ] T148 [US3] Add the tracker path rule to `src/upgrade_portal/upgrade/driver.py`. Resolve every tracker path into `data/`. `src/firmware/firmware_manager.py:3713` writes `ActiveUpgrades.json` to the process working directory. Do not copy that defect.
- [ ] T149 [P] [US3] Implement the stop control in `src/upgrade_portal/upgrade/stop.py` (FR-038a to FR-038i). Require the typed word `STOP`. Call `cancel_upgrade` for each plan. Write the outcome lists `cancelled`, `already_writing`, and `no_cancel_available`, plus one plain sentence.
- [ ] T150 [US3] Add the mid-flash rule to `src/upgrade_portal/upgrade/stop.py` (FR-038c, FR-038d). Never interrupt a device that is writing firmware. Say plainly in the message that such a device will finish.
- [ ] T151 [US3] Implement `POST /api/runs` and `POST /api/runs/<id>/options` in `src/upgrade_portal/app/routes/upgrade.py` (FR-033 to FR-037). Accept the body `{targets:[{mac, version_target}], reboot, junos_file_action, strategy}`.
- [ ] T152 [US3] Implement `POST /api/runs/<id>/start` in `src/upgrade_portal/app/routes/upgrade.py` (FR-038). Require `{"confirm": "UPGRADE"}`. Refuse any other word with `confirmation_required`. Refuse a run with no verified pre-check with `pre_capture_missing`.
- [ ] T153 [US3] Implement `GET /api/runs/<id>/status` and the run page route in `src/upgrade_portal/app/routes/upgrade.py` (FR-039 to FR-051). Answer in under 1 second while an upgrade runs.
- [ ] T154 [US3] Implement `POST /api/runs/<id>/stop` in `src/upgrade_portal/app/routes/upgrade.py`. Require `{"confirm": "STOP"}`. Refuse a run in a state that cannot stop with `run_not_stoppable`.
- [ ] T155 [P] [US3] Create the upgrade options template `src/upgrade_portal/app/assets/templates/upgrade/options.html` with the `upgrade-version-select-{mac}`, `upgrade-version-select-all`, `upgrade-reboot-toggle`, `upgrade-strategy-select`, `upgrade-target-table`, `upgrade-target-row-{mac}`, and `upgrade-warning-list` test identifiers
- [ ] T156 [P] [US3] Create the confirmation template `src/upgrade_portal/app/assets/templates/upgrade/confirm.html` with the `upgrade-confirm-input` and `upgrade-start-button` test identifiers
- [ ] T157 [P] [US3] Create the run progress template `src/upgrade_portal/app/assets/templates/upgrade/progress.html` with the `upgrade-state`, `upgrade-phase-{name}`, `upgrade-phase-progress-{name}`, and `upgrade-device-state-{mac}` test identifiers
- [ ] T158 [P] [US3] Create the stop template `src/upgrade_portal/app/assets/templates/upgrade/stop.html` with the `stop-button`, `stop-confirm-input`, `stop-confirm-submit`, `stop-outcome`, `stop-outcome-cancelled`, `stop-outcome-writing`, and `stop-outcome-message` test identifiers
- [ ] T159 [US3] Add the 30-second run status poll to `src/upgrade_portal/app/assets/static/js/portal.js`
- [ ] T160 [P] [US3] Unit test `classify_gateway` for the `ssr` type, the `SSR` model, the `128T` model, and every other gateway in `tests/unit/upgrade_portal/test_upgrade_service_classify.py`
- [ ] T161 [P] [US3] Unit test `build_body` for each of the four body rules in `tests/unit/upgrade_portal/test_upgrade_service_body.py`
- [ ] T162 [P] [US3] Unit test `plan_upgrade` for the four grouping rules, the organization scope of a session smart router, and the mixed-family warning in `tests/unit/upgrade_portal/test_upgrade_service_plan.py`
- [ ] T163 [P] [US3] Unit test `invoke_upgrade` and `cancel_upgrade`, including the no-retry rule and the `ValueError` on a malformed plan, in `tests/unit/upgrade_portal/test_upgrade_service_invoke.py`
- [ ] T164 [P] [US3] Unit test `read_upgrade_status` for the `current_phase` field name and the list shape of `reboot_in_progress` in `tests/unit/upgrade_portal/test_upgrade_service_status.py`
- [ ] T165 [P] [US3] Unit test the option mapping and the family split in `tests/unit/upgrade_portal/test_upgrade_options.py`
- [ ] T166 [P] [US3] Unit test the event key discovery, the `device_type` parameter, and the `search_after` cursor in `tests/unit/upgrade_portal/test_upgrade_events.py`
- [ ] T167 [P] [US3] Unit test the three settle signals, the uptime decrease rule, the null uptime rule, and the two extra waits in `tests/unit/upgrade_portal/test_upgrade_gate.py`
- [ ] T168 [P] [US3] Unit test the cascade order, the automatic post-check, and the data path rule in `tests/unit/upgrade_portal/test_upgrade_driver.py`
- [ ] T169 [P] [US3] Unit test the stop outcome lists and the mid-flash message in `tests/unit/upgrade_portal/test_upgrade_stop.py`

**Checkpoint**: User Story 3 is complete. An operator can drive a full upgrade and
watch every device return.

---

## Phase 6: User Story 4 - Several sites at once without collision (Priority: P2)

**Goal**: A Redis lock stops two operators from upgrading one site at the same
time. The lock survives a restart and works across every worker process. Reading
data never needs the lock.

**Independent Test**: Run Scenario E in `quickstart.md:184-205`. Operator B sees
the site and its data, but a start attempt returns `409 site_locked`. The refusal
names the holder. The lock survives a portal restart. Two workers give the same
answer.

### Tests for User Story 4

- [ ] T170 [P] [US4] Contract test the lock acquire, refresh, release, and takeover endpoints, plus the `site_locked`, `lock_lost`, and `confirmation_required` error codes, in `tests/contract/upgrade_portal/test_lock.py`
- [ ] T171 [P] [US4] Contract test that a comparison page and a history page work with no lock in `tests/contract/upgrade_portal/test_lock_free_reads.py`
- [ ] T172 [P] [US4] Browser test the two-operator journey in `tests/e2e/upgrade_portal/test_two_operators.py`. Drive `lock-banner`, `lock-take-button`, `lock-confirm-input`, `lock-confirm-submit`, `lock-release-button`, `lock-error`, and `site-lock-state-{site_id}`.

### Implementation for User Story 4

- [ ] T173 [US4] Implement the Redis client and the lock key `misthelper:lock:site:{org_id}:{site_id}` in `src/upgrade_portal/runtime/lock.py`. Open a direct `redis.Redis` client with the same constructor arguments the writers use at `src/db/redis_writer.py:542-547`. Do not use `RedisJSONWriter`. That writer applies a 7-day expiry at `src/db/redis_writer.py:598`, and FR-032a forbids an expiring path.
- [ ] T174 [US4] Add the atomic acquire to `src/upgrade_portal/runtime/lock.py`. Run one `SET key value NX EX 300`. Never read and then write. A read followed by a write is not atomic, and two operators would both win.
- [ ] T175 [US4] Add the four acquire outcomes to `src/upgrade_portal/runtime/lock.py`: a free lock returns 200 with the token, the same operator and the same browser return 200 with state `resume`, a different holder under 300 seconds returns `409 site_locked`, and a different holder at or over 300 seconds returns `400 confirmation_required`
- [ ] T176 [US4] Add the compare-and-extend refresh Lua script from `contracts/site-lock.md:69-77` to `src/upgrade_portal/runtime/lock.py`. Return 200 with `expires_in` on 1 and `409 lock_lost` on 0.
- [ ] T177 [US4] Add the compare-and-delete release Lua script to `src/upgrade_portal/runtime/lock.py`. Release on `complete`, `stopped`, or `failed`. Do not release when a browser closes, because the run continues.
- [ ] T178 [US4] Add the takeover path to `src/upgrade_portal/runtime/lock.py`. Require the full 300-second cooldown and the typed word `CONFIRM`. Write an audit record with the old email, the new email, and the time. A takeover never cancels a running upgrade.
- [ ] T179 [US4] Add the three failure behaviors from `contracts/site-lock.md:112-122` to `src/upgrade_portal/runtime/lock.py`. Refuse an upgrade start with 503 when Redis is unreachable. Retry a heartbeat for 60 seconds, then move the run to `failed`. Show a read-only page with the lock state unknown. An in-memory fallback is forbidden.
- [ ] T180 [US4] Keep the `lock_token` out of every log line in `src/upgrade_portal/runtime/lock.py`. The token is not a credential, and it still never reaches a log record.
- [ ] T181 [US4] Add the lock endpoints to `src/upgrade_portal/app/routes/select.py` (FR-072 to FR-083)
- [ ] T182 [US4] Add the lock check to the upgrade start handler in `src/upgrade_portal/app/routes/upgrade.py`. Refuse with `409 site_locked` and name the holder, so the second operator knows whom to ask.
- [ ] T183 [US4] Add the driver heartbeat every 60 seconds to `src/upgrade_portal/upgrade/driver.py`, so a closed browser does not drop a live upgrade
- [ ] T184 [P] [US4] Create the lock banner partial `src/upgrade_portal/app/assets/templates/partials/lock_banner.html` with the `lock-banner`, `lock-take-button`, `lock-confirm-input`, `lock-confirm-submit`, `lock-release-button`, and `lock-error` test identifiers
- [ ] T185 [US4] Add the 60-second browser heartbeat to `src/upgrade_portal/app/assets/static/js/portal.js`
- [ ] T186 [P] [US4] Unit test the acquire outcomes, the refresh script, the release script, the takeover, and every failure behavior in `tests/unit/upgrade_portal/test_lock.py`

**Checkpoint**: User Story 4 is complete. Two operators can work on two sites at
the same time, and neither can collide on one site.

---

## Phase 7: User Story 5 - Sign in with a managed service provider account (Priority: P3)

**Goal**: An operator signs in with an email address and a password, answers a
two-factor challenge, and picks one organization from the list the account may
reach.

**Independent Test**: Sign in with a managed service provider account. The
organization list shows every permitted organization. A request for a forbidden
organization returns `org_not_permitted`. No credential value appears in any log
line or on any page.

### Tests for User Story 5

- [ ] T187 [P] [US5] Contract test the sign-in endpoint, the two-factor endpoint, and the `bad_credentials`, `rate_limited`, and `bad_two_factor_code` error codes in `tests/contract/upgrade_portal/test_auth.py`
- [ ] T188 [P] [US5] Contract test the organization list, the organization choice, and the `org_not_permitted` refusal in `tests/contract/upgrade_portal/test_org_scope.py`
- [ ] T189 [P] [US5] Contract test that no response body and no log record holds a password value or a token value in `tests/contract/upgrade_portal/test_no_credential_leak.py`
- [ ] T190 [P] [US5] Browser test the sign-in journey in `tests/e2e/upgrade_portal/test_signin.py`. Drive `signin-email`, `signin-password`, `signin-submit`, `signin-error`, `twofactor-code`, `twofactor-submit`, `org-search`, `org-row-{org_id}`, `org-select-{org_id}`, and `signout-button`.

### Implementation for User Story 5

- [ ] T191 [US5] Implement the email and password sign-in in `src/upgrade_portal/app/routes/auth.py` (FR-006 to FR-008). Refuse a bad pair with `bad_credentials`. Refuse a throttled attempt with `rate_limited`.
- [ ] T192 [US5] Add the two-factor challenge to `src/upgrade_portal/app/routes/auth.py` (FR-009, FR-010). Refuse a bad code with `bad_two_factor_code`. Never log the code.
- [ ] T193 [US5] Implement the organization picker in `src/upgrade_portal/app/routes/auth.py` (FR-011). Build the portal's own picker. Do not reuse `src/auth/interactive/msp_org_selector.py`, which hard-codes `current_page = 0` and `total_pages = 1` at `:155-156`, so the navigation branches at `:208` and `:210` can never run.
- [ ] T194 [US5] Add the sign-out route to `src/upgrade_portal/app/routes/auth.py`. Drop the cloud session and clear the server-side session.
- [ ] T195 [US5] Add the organization scope enforcement to `src/upgrade_portal/runtime/identity.py`. Refuse a request for an organization the session may not reach with `403 org_not_permitted`.
- [ ] T196 [US5] Add the credential redaction guard to `src/upgrade_portal/runtime/identity.py` (FR-009). Refer to a stored credential by its variable name only.
- [ ] T197 [P] [US5] Create the sign-in template `src/upgrade_portal/app/assets/templates/auth/signin.html` with the `signin-email`, `signin-password`, `signin-submit`, and `signin-error` test identifiers
- [ ] T198 [P] [US5] Create the two-factor template `src/upgrade_portal/app/assets/templates/auth/twofactor.html` with the `twofactor-code` and `twofactor-submit` test identifiers
- [ ] T199 [P] [US5] Create the organization picker template `src/upgrade_portal/app/assets/templates/auth/orgs.html` with the `org-search`, `org-row-{org_id}`, and `org-select-{org_id}` test identifiers
- [ ] T200 [P] [US5] Unit test the sign-in flow, the two-factor flow, the organization scope check, and the credential redaction in `tests/unit/upgrade_portal/test_auth.py`

**Checkpoint**: User Story 5 is complete. A managed service provider operator can
reach every permitted organization and no other.

---

## Phase 8: User Story 6 - Read a comparison from a past upgrade (Priority: P3)

**Goal**: An operator opens the history page for a site, reads the stored size of
each record, opens an old capture, and compares any two captures of that site.

**Independent Test**: Run Scenario F in `quickstart.md:208-223`. No capture
disappears with age. Every row shows the stored size. A capture written by an
older schema version still opens, or the page says plainly that the version is
too new to render.

### Tests for User Story 6

- [ ] T201 [P] [US6] Contract test the capture history endpoint and the run history endpoint, including the page parameters, in `tests/contract/upgrade_portal/test_history.py`
- [ ] T202 [P] [US6] Contract test the schema version refusal for a capture written by a newer version in `tests/contract/upgrade_portal/test_schema_version.py`
- [ ] T203 [P] [US6] Browser test the history journey in `tests/e2e/upgrade_portal/test_history.py`. Drive `history-table`, `history-row-{capture_id}`, `history-open-{capture_id}`, `history-page-next`, and `history-page-previous`.

### Implementation for User Story 6

- [ ] T204 [US6] Implement the capture history route in `src/upgrade_portal/app/routes/review.py` (FR-084). List captures for one site in time order through the `site_id` and `started_at` index.
- [ ] T205 [US6] Implement the run history route in `src/upgrade_portal/app/routes/review.py` (FR-085) through the `site_id` and `created_at` index
- [ ] T206 [US6] Add the page window to `src/upgrade_portal/app/routes/review.py` for the next page and the previous page
- [ ] T207 [US6] Add the schema version reader to `src/upgrade_portal/capture/store.py`. A reader that finds a higher integer than it understands refuses to render and says so plainly.
- [ ] T208 [US6] Show the `stored_size_bytes` column in the history view through `src/upgrade_portal/compare/render.py`, so an operator can watch the growth
- [ ] T209 [P] [US6] Create the history template `src/upgrade_portal/app/assets/templates/review/history.html` with the `history-table`, `history-row-{capture_id}`, `history-open-{capture_id}`, `history-page-next`, and `history-page-previous` test identifiers
- [ ] T210 [P] [US6] Unit test the history query, the page window, and the schema version refusal in `tests/unit/upgrade_portal/test_history.py`

**Checkpoint**: Every user story is independently functional.

---

## Phase 9: Polish and Cross-Cutting Concerns

**Purpose**: Close the observability, performance, security, and documentation
work that touches more than one story.

- [ ] T211 Implement `GET /readyz` in `src/upgrade_portal/app/factory.py`. Perform a real write and a real read-back against a scratch key, and a real Redis check. A check that only opens a connection would report ready while every write failed silently.
- [ ] T212 [P] Add the observability audit to `tests/unit/upgrade_portal/test_logging_contract.py` (FR-086 to FR-088). Prove that every log call in `src/upgrade_portal/` uses `%s` placeholders, uses ASCII characters only, carries a run identifier and a site identifier, and holds no credential value.
- [ ] T213 [P] Add the guardrail test for the menu 238 registry entry to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T214 [P] Add the guardrail test for the two `natural_pk` strategy entries to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T215 [P] Add the guardrail test that proves the theme file `src/upgrade_portal/app/assets/static/css/themes/magenta.css` is tracked by git and not excluded by `.gitignore` or `.dockerignore` to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T216 [P] Add the guardrail test that proves the portal imports no name from `src/firmware/firmware_manager.py` to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T217 [P] Add the guardrail test that proves the portal calls no `getOrgSsrUpgrade` to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T218 [P] Add the guardrail test that proves the word `snapshot` appears in no identifier and in no page string under `src/upgrade_portal/` to `tests/unit/upgrade_portal/test_guardrails.py`
- [ ] T219 [P] Add the performance test for the 90-second Tier 2 capture target (SC-002) and the 3-second comparison render target (SC-005) to `tests/unit/upgrade_portal/test_performance.py`
- [ ] T220 [P] Add the rate-limit budget test to `tests/unit/upgrade_portal/test_rate_budget.py`. Prove that one upgrade run consumes at most 7.2 percent of the hourly quota.
- [ ] T221 [P] Add the browser test that proves every asset loads from the portal itself and no request reaches an outside host to `tests/e2e/upgrade_portal/test_assets.py`
- [ ] T222 Run `bandit -r src/upgrade_portal src/firmware/upgrade_service.py` and clear every finding
- [ ] T223 Run `interrogate -v src/upgrade_portal src/firmware/upgrade_service.py` and reach 90 percent or above
- [ ] T224 Run `pydoclint --style=google src/upgrade_portal` and clear every finding
- [ ] T225 Run `ruff check`, `black --check`, and `mypy` over `src/upgrade_portal` and `src/firmware/upgrade_service.py` and clear every finding
- [ ] T226 Run `pytest tests/unit/upgrade_portal tests/contract/upgrade_portal --cov=src/upgrade_portal` and reach 90 percent coverage or above
- [ ] T227 Audit every function in `src/upgrade_portal/` and `src/firmware/upgrade_service.py` against the Five-Item Rule and split any function that breaks it
- [ ] T228 Audit every docstring, comment, message, and page string against `documentation/ASD-STE100_writing-guide.md` and correct any breach
- [ ] T229 [P] Add the portal section to `README.md` with the launch command, the menu number 238, and the port 8056
- [ ] T230 [P] Add the operator guide to `documentation/upgrade_capture_portal.md` with the five views, the three confirmation words, and the two out-of-scope defects
- [ ] T231 Update `CLAUDE.md` with the new package, the new menu number, and the new port
- [ ] T232 Run every scenario in `quickstart.md` and record the result
- [ ] T233 Run the container build and prove that the theme file is inside the image and that both ports answer

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependency. Start at once.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Story 1 (Phase 3)**: Depends on Foundational only.
- **User Story 2 (Phase 4)**: Depends on Foundational. Needs a stored capture to
  compare, so it needs User Story 1 for a live test. The pure comparison functions
  test on their own with two fixture documents.
- **User Story 3 (Phase 5)**: Depends on Foundational. Needs User Story 1 for the
  pre-check and the post-check. The upgrade seam and the settle gate test on their
  own.
- **User Story 4 (Phase 6)**: Depends on Foundational. Adds a lock check to the
  User Story 3 start handler, so complete User Story 3 first for the full journey.
  The lock module tests on its own.
- **User Story 5 (Phase 7)**: Depends on Foundational. Replaces the environment
  credential mode from T036. Independent of every other story.
- **User Story 6 (Phase 8)**: Depends on Foundational and on the store from User
  Story 1. Independent of User Stories 3, 4, and 5.
- **Polish (Phase 9)**: Depends on every story the team plans to ship.

### User Story Dependencies

| Story | Priority | Hard dependency | Soft dependency |
| --- | --- | --- | --- |
| US1 Record the state | P1 | Foundational | None |
| US2 Compare two records | P1 | Foundational | US1 for a live capture |
| US3 Upgrade and settle | P2 | Foundational | US1 for the two captures |
| US4 Lock a site | P2 | Foundational | US3 for the start refusal |
| US5 Managed service provider sign-in | P3 | Foundational | None |
| US6 History | P3 | Foundational, `capture/store.py` | US1 |

### Within Each User Story

- Write the tests first. Prove that they fail.
- Build the data readers before the assembly.
- Build the assembly before the store.
- Build the store before the route.
- Build the route before the template.
- Finish one story before the next priority starts.

### Parallel Opportunities

- Setup: T002 through T006 and T009 through T023 run in parallel. T001 comes
  first. T007 and T008 both edit `MistHelper.py`, so they run in order.
- Foundational: T031 through T034 run in parallel. T048 through T056 run in
  parallel.
- User Story 1: T057 through T062 run in parallel. T063, T067, and T071 start
  three different modules in parallel. T087 through T089 run in parallel. T091
  through T094 run in parallel.
- User Story 2: T095 through T098 run in parallel. T099, T102, T104, T106, and
  T108 start five different modules in parallel. T114 through T118 run in
  parallel.
- User Story 3: T128 through T133 run in parallel. T134, T137, T140, T144, and
  T149 start five different modules in parallel. T155 through T158 run in
  parallel. T160 through T169 run in parallel.
- User Story 4: T170 through T172 run in parallel. T173 through T180 all edit
  `runtime/lock.py`, so they run in order.
- User Story 5: T187 through T190 run in parallel. T197 through T199 run in
  parallel.
- User Story 6: T201 through T203 run in parallel.
- Polish: T212 through T221 run in parallel. T229 and T230 run in parallel.
- Across teams: once Foundational ends, one developer takes User Story 1, a
  second takes User Story 5, and a third starts the upgrade seam of User Story 3.

---

## Parallel Example: User Story 1

```bash
# Launch every test for User Story 1 together:
Task: "Contract test the site list and the inventory in tests/contract/upgrade_portal/test_select.py"
Task: "Contract test the capture start in tests/contract/upgrade_portal/test_capture_start.py"
Task: "Contract test the capture status in tests/contract/upgrade_portal/test_capture_status.py"
Task: "Contract test the capture read in tests/contract/upgrade_portal/test_capture_read.py"
Task: "Browser test the site picker in tests/e2e/upgrade_portal/test_site_selection.py"
Task: "Browser test the capture journey in tests/e2e/upgrade_portal/test_capture.py"

# Launch the three capture readers together:
Task: "Implement the device inventory read in src/upgrade_portal/capture/devices.py"
Task: "Implement the wired client read in src/upgrade_portal/capture/clients.py"
Task: "Implement the tier 3 extra reads in src/upgrade_portal/capture/extras.py"

# Launch the three templates together:
Task: "Create src/upgrade_portal/app/assets/templates/select/sites.html"
Task: "Create src/upgrade_portal/app/assets/templates/select/inventory.html"
Task: "Create src/upgrade_portal/app/assets/templates/capture/capture.html"
```

---

## Implementation Strategy

### Minimum viable product first (User Story 1 only)

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational. This phase blocks every story.
3. Complete Phase 3 User Story 1.
4. **Stop and validate.** Run Scenario A in `quickstart.md`.
5. Deploy or demonstrate.

At this point an operator can record the state of a site and prove that the portal
stored it. That is a useful product on its own, with no upgrade risk.

### Incremental delivery

1. Setup and Foundational give a running application shell.
2. Add User Story 1. Test on its own. Deploy. This is the minimum viable product.
3. Add User Story 2. Test on its own. Deploy. The operator can now compare two
   records with no upgrade.
4. Add User Story 3. Test on a laboratory site only. Deploy.
5. Add User Story 4. Test with two browsers. Deploy.
6. Add User Story 5. Test with a managed service provider account. Deploy.
7. Add User Story 6. Test with an old capture. Deploy.
8. Complete Phase 9 Polish.

Each story adds value and breaks no earlier story.

### Parallel team strategy

With three developers, after Foundational ends:

- Developer A: User Story 1, then User Story 2, then User Story 6.
- Developer B: the upgrade seam T119 to T127, then the rest of User Story 3.
- Developer C: User Story 5, then User Story 4.

Developer B and Developer C meet at T182, which adds the lock check to the upgrade
start handler.

---

## Notes

- A `[P]` task touches a different file and depends on no incomplete task.
- The `[Story]` label maps a task to one user story for traceability.
- Verify that a test fails before the implementation starts.
- Commit after each task or after each logical group.
- Stop at any checkpoint to validate a story on its own.
- Two contradictions in the source documents are already resolved. First,
  `contracts/upgrade-service.md:35-195` wins over `research/upgrade-reuse.md:624-707`
  for the seam signatures. Second, `pyproject.toml:419-420` wins over
  `.github/workflows/ci.yml:71` for the coverage floor, so the target is 90.
- Five items need a decision during User Story 3. Record each decision in a code
  comment when the task lands.
  1. The four-field `UpgradeOptions` cannot express `download_strategy`,
     `reboot_strategy`, `force`, `snapshot`, `channel`, or
     `max_failure_percentage`. Decide which fields the interface needs before
     T135.
  2. `list_available_versions` takes `site_id`, while
     `listOrgAvailableDeviceVersions` and `listOrgAvailableSsrVersions` are both
     organization-scoped. Decide the scope before T126.
  3. The contract lists no dry-run parameter. Decide before T123 whether the seam
     needs one.
  4. `UpgradePlan.endpoint` is typed `str`. Decide before T119 whether the value
     is a literal string or an enumeration member.
  5. No vendor guidance sets a settle time for a switch or a gateway. The
     60-second wait and the 120-second wait are this feature's own choice.
     Measure both during the pilot and record the result at T232.
