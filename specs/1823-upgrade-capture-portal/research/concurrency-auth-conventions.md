# Feature 1823 research: concurrency, authentication, and repository conventions

Read-only research. This document changes no source code.

Every claim below carries a `path:line` citation. Where the document infers rather than
reads, the text says so in an **Inference** note.

Configuration appears by variable name only. This document reproduces no value from
`.env`.

---

## Part A. Concurrency

### A1. ConnectionPoolExecutor

File: `src/refactors/connection_pool_executor.py` (339 lines).

The module docstring records the extraction. The class came from `MistHelper.py:7545`.
The private `_pool_*` helper chain came from `MistHelper.py:7374-7542`. See
`src/refactors/connection_pool_executor.py:1-15`.

**Class**

`class ConnectionPoolExecutor:` at `src/refactors/connection_pool_executor.py:59`.
Every member is a `@staticmethod`. The class holds no instance state.

**Public entry point**

`src/refactors/connection_pool_executor.py:314-326`:

```python
@staticmethod
def execute(
    work_items: list[Any],
    worker_function: Any,
    batch_description: str = "items",
    retry_function: Any | None = None,
) -> tuple[list[Any], list[Any]]:
```

The signature takes four parameters. The Five-Item Rule allows five.

**Return shape**

`execute` returns `(successful_results, failed_items)`. Both members are lists. The
empty-input path returns `[], []` at `src/refactors/connection_pool_executor.py:326`. The
normal path returns through `_pool_finalize_execution` at
`src/refactors/connection_pool_executor.py:295`.

**Worker contract**

The executor calls `executor.submit(config.worker_function, item, config.connection_semaphore)`
at `src/refactors/connection_pool_executor.py:178`. A worker function must accept two
positional arguments. The first is one work item. The second is a
`threading.Semaphore`.

**Concurrency bound**

The bound has two layers.

1. Thread count. `_pool_resolve_thread_sizing` at
   `src/refactors/connection_pool_executor.py:63` picks the thread count. In
   connection-aware mode the thread count equals the maximum connection count
   (`src/refactors/connection_pool_executor.py:67`). Otherwise the thread count comes from
   `os.cpu_count()` with a fallback constant
   (`src/refactors/connection_pool_executor.py:73`).
2. Connection count. `_pool_configure` builds
   `connection_semaphore = threading.Semaphore(max_conn)` at
   `src/refactors/connection_pool_executor.py:90`. The executor passes this semaphore to
   every worker. The worker must acquire it around each API call.

The pool creates `ThreadPoolExecutor(max_workers=config.max_threads)` at
`src/refactors/connection_pool_executor.py:176`.

Work runs in batches. The batch size is `max_threads * FastModeDevicesPerThread.VALUE`
(`src/refactors/connection_pool_executor.py:92`).

The drain loop uses `wait(pending, return_when=FIRST_COMPLETED)` at
`src/refactors/connection_pool_executor.py:152`, inside a `tqdm` progress context at
`src/refactors/connection_pool_executor.py:148`.

**Retry hook**

`_pool_apply_retry` at `src/refactors/connection_pool_executor.py:245` calls
`retry_function(failed_items, connection_semaphore)` at
`src/refactors/connection_pool_executor.py:254`. The retry function must return
`(retry_results, still_failed)`. `_pool_maybe_retry` at
`src/refactors/connection_pool_executor.py:279` skips the retry when nothing failed.

**Circular-import guard**

`_resolve_fast_mode_env` at `src/refactors/connection_pool_executor.py:31` late-binds
`import MistHelper` inside the function body at
`src/refactors/connection_pool_executor.py:46`. New modules that need MistHelper globals
must use the same late-binding pattern.

**Every caller**

| Caller | Lines |
| --- | --- |
| `MistHelper.py` public export list | `MistHelper.py:141` |
| `MistHelper.py` import | `MistHelper.py:536` |
| `MistHelper.py` dependency injection | `MistHelper.py:3232` (`execute_fn=ConnectionPoolExecutor.execute`) |
| `src/api/api_fetch_utils.py` | `src/api/api_fetch_utils.py:213-214` |
| `src/export/gateway_test_exporter.py` | `src/export/gateway_test_exporter.py:187,196` |
| `src/export/org_device_stats_exporter.py` | `src/export/org_device_stats_exporter.py:372,381` |
| `src/gateway/gateway_export_utils.py` | `src/gateway/gateway_export_utils.py:16,569` |
| `src/refactors/serial_cc/test_results_by_site.py` | `src/refactors/serial_cc/test_results_by_site.py:10,29,107` |
| `src/gateway/gateway_stats_exporter.py` | `src/gateway/gateway_stats_exporter.py:12` (injected, no direct import) |
| `src/gateway/overrides/_deps.py` | `src/gateway/overrides/_deps.py:18,37` (the `execute_fn` injection slot) |

`src/refactors/serial_cc/test_results_by_site.py:57` shows a correct worker shape:
`_invoke_search_api(deps, site_id, connection_semaphore)`.

---

### A2. Threading tuning settings (names only)

| Variable name | Definition site | Role |
| --- | --- | --- |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | `src/refactors/fast_mode_constants.py:21-22` | Bounds simultaneous API connections. Also sets the thread count in connection-aware mode. |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | `src/refactors/fast_mode_constants.py:30-31` | Selects connection-aware sizing or CPU-aware sizing. |
| `FAST_MODE_FALLBACK_THREADS` | `MistHelper.py:2392` | Thread count when `os.cpu_count()` returns nothing. |
| `FAST_MODE_DEVICES_PER_THREAD` | `src/refactors/fast_mode_devices_per_thread.py:26-27` | Devices per worker thread. Multiplies into the batch size. |

`MistHelper.py:113` exports `FAST_MODE_FALLBACK_THREADS` in the public surface list.
`specs/1016-misthelper-suppression-cleanup/contracts/public_api_snapshot.txt:50` records
the same name in the public API snapshot.

Web-portal thread settings carry no environment variable.
`web_portal/services/operation.py:315-316` derives the worker count from `os.cpu_count()`
in code.

Gunicorn thread settings live in a shell script, not in an environment variable. The
flags are `--workers`, `--worker-class`, `--threads`, and `--timeout` at
`container/scripts/start.sh:58-61`. `WEB_PORT` at `container/scripts/start.sh:52` selects
the listen port.

---

### A3. asyncio use

**The core MistHelper application uses no asyncio.**

A repository-wide grep for `asyncio` across `**/*.py`, with `mist-ops-platform/**`
excluded, returned no matches.

All `async def` matches came from `mist-ops-platform/`. That directory is a separate
FastAPI project. It is tracked in this repository as ordinary files. `git ls-files`
reports 110 files there. The repository has no `.gitmodules` file, so the directory is
not a submodule.

One further match is prose inside a docstring at `src/websocket/commands.py:33`. It is
not code.

**Conclusion.** Feature 1823 must use threads. No asyncio event loop exists to join.
The mistapi SDK calls are blocking calls.

---

### A4. API rate limit and the polling risk

**The constant**

`src/utils/rate_limiting.py:56` defines `_DEFAULT_REQUEST_LIMIT = 5000`. The inline
comment describes it as the fallback API request quota per hour when the API omits the
value.

`MistHelper.py:2275` sets the same default per-window quota with `"limit": 5000`.

`src/reports/e911_bssid.py:937` names the same figure in prose as the 5000 API calls per
clock-hour rate limit.

**Where enforcement happens**

Enforcement is per call, not per pool.

- `src/api/api_data_fetcher.py:167` defines `_apply_rate_limiting`.
- `src/api/api_data_fetcher.py:170` calls `mh.RateLimitingUtils.get_rate_limited_delay`.
- `src/utils/rate_limiting.py:571` defines that helper.
- `src/api/api_data_fetcher.py:263` defines `_is_rate_limit_error`, which detects HTTP 429.
- `src/api/api_data_fetcher.py:268` defines `_handle_rate_limit`, which performs recovery.

The delay is adaptive. Each call sleeps before it runs.

**The polling risk for feature 1823**

The quota is per clock hour, and it is shared across the whole process.

A 20-second settle-gate poll issues 180 requests per device per hour. That figure comes
from arithmetic, not from a source file. **Inference.**

With one request per device per poll, a 5000-request hourly quota supports about 27
devices under continuous 20-second polling. That leaves no headroom for the capture
work, the upgrade calls, the site listing, or any other menu operation in the same
process.

Design consequences follow.

1. Poll the fleet with one bulk request where a bulk endpoint exists. Do not poll each
   device separately.
2. Share one rate-limit accounting path. Every thread must pass through
   `src/api/api_data_fetcher.py:167`. A new module that calls the SDK directly bypasses
   the accounting and breaks the quota model.
3. Back off the poll interval as the device count grows. A fixed 20-second interval does
   not scale to a large fleet.

**Inference.** The repository holds no per-fleet poll budget calculator today. The
feature must add one.

---

### A5. Recommended threading model

**What one Gunicorn worker can keep alive**

The container runs Gunicorn with a single worker process, the threaded worker class, a
fixed small thread count, and a request timeout. See `container/scripts/start.sh:56-63`.
The `wsgi.py:4` docstring records the same shape.

A worker process **can** keep the following alive after an HTTP request ends.

- Module-level globals. They live for the process lifetime.
- Any `threading.Thread` the request handler started. The thread outlives its request.
- Any object a process-level service holds, such as a `ThreadPoolExecutor`.

A worker process **cannot** keep anything alive across the following events.

- A worker restart or a container restart.
- An arbiter kill after the Gunicorn timeout expires. That kills the process and every
  thread inside it.
- A deploy or a code reload.
- A second worker process. With one worker there is no second process today. A future
  scale-out to more workers would split the in-memory state, and each worker would hold a
  different view.

The thread count also caps concurrent HTTP requests. A request handler that blocks holds
one of those slots for its whole duration. A long upgrade must never block a handler.

**The existing precedent to copy**

`web_portal/services/operation.py` already solves this problem.

- `web_portal/services/operation.py:318` builds
  `ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="op")` once, in the
  service constructor.
- `web_portal/services/operation.py:329` submits the work with
  `self._pool.submit(self._execute_operation, run, parameters)` and returns at once.
- `web_portal/services/operation.py:313-314` holds run state in `self._runs`, guarded by
  `self._lock`.
- `web_portal/services/operation.py:332` exposes `get_run_status(run_id)` for polling.
- `web_portal/services/operation.py:345` exposes `stop_operation(run_id)`, which writes
  the `stop_loop.txt` sentinel.

`src/config/config_utils.py:159` defines `check_stop_signal`, which reads and removes
that sentinel. Long loops call it once per iteration.

`web_portal/services/event_bus.py:37-39` runs a heartbeat on a daemon thread with a lock
at `web_portal/services/event_bus.py:30`.

**Recommended model for feature 1823**

Use three distinct layers. Do not merge them.

1. **Capture collection (fan-out, bounded, short).** Use
   `ConnectionPoolExecutor.execute` at
   `src/refactors/connection_pool_executor.py:314`. Write a worker with the
   `(item, connection_semaphore)` signature. Supply a retry function that returns
   `(retry_results, still_failed)`. This layer already respects the connection semaphore
   and already reports progress.

2. **Settle-gate polling (fan-out, bounded, repeating).** Use a separate
   `ConnectionPoolExecutor.execute` pass per poll round. Do not create one long-lived
   thread per device. One thread per device does not bound the connection count and does
   not share the rate-limit accounting. Sleep between rounds in the driver, not in the
   workers.

3. **Upgrade driver (single, long-lived, survives the request).** Own one process-level
   service object. Build its `ThreadPoolExecutor` once in the constructor, exactly as
   `web_portal/services/operation.py:318` does. Submit the driver and return the run
   identifier at once. Expose a status endpoint that reads guarded state. Expose a stop
   path that honours `check_stop_signal` at `src/config/config_utils.py:159`.

**Durability warning.** In-memory run state dies with the worker process. If an upgrade
must survive a restart, the driver must persist its state to disk and must reload that
state at startup. **Inference.** No such persistence exists in
`web_portal/services/operation.py` today. The service keeps `self._runs` in memory only
(`web_portal/services/operation.py:313`).

**Thread-local caution.** `web_portal/services/input_hook.py:24` stores the input queue
in `threading.local()`. `web_portal/services/input_hook.py:19-20` states the intent
plainly. A background thread does not inherit the request thread's thread-local values.
Any value the driver needs must pass as an explicit argument.

---

## Part B. Authentication and multiple organizations

### B1. LoginOrchestrator

File: `src/auth/interactive/login_orchestrator.py` (311 lines).

**Signature**

`src/auth/interactive/login_orchestrator.py:16-21`:

```python
def __init__(
    self,
    state: dict[str, Any],
    safe_input: Callable[..., str],
    detect_msp_privileges: Callable[[], list[dict[str, Any]]],
) -> None:
```

`execute(self) -> bool` at `src/auth/interactive/login_orchestrator.py:27` returns `True`
on success.

The orchestrator writes results into the shared `state` dictionary. It writes no module
global itself.

**Flow**

1. Resolve the SDK (`src/auth/interactive/login_orchestrator.py:30`).
2. Prompt for the cloud through `CloudSelector`
   (`src/auth/interactive/login_orchestrator.py:34`).
3. Collect the email and the password
   (`src/auth/interactive/login_orchestrator.py:38`).
4. Authenticate (`src/auth/interactive/login_orchestrator.py:44`).

**How it forces credential login over token login**

`_create_api_session` builds the session at
`src/auth/interactive/login_orchestrator.py:136-142` with `email`, `password`, `host`,
`console_log_level`, and `show_cli_notif`.

It then calls `_clear_pre_existing_token` at
`src/auth/interactive/login_orchestrator.py:147`. That helper wipes the SDK token slots
at `src/auth/interactive/login_orchestrator.py:161-162`:

```python
apisession._apitoken = []  # Force the SDK to use the email/password credentials
apisession._apitoken_index = -1  # Reset the cursor that picks the next token
```

This is the mechanism. Without it the SDK would prefer a cached API token over the
supplied credentials.

**Two-factor handling**

- `_needs_two_factor` at `src/auth/interactive/login_orchestrator.py:174` checks
  `error_data.get("two_factor_required")` at
  `src/auth/interactive/login_orchestrator.py:179`. It then falls back to the flat key at
  `src/auth/interactive/login_orchestrator.py:181`. Two response shapes exist.
- `_handle_two_factor` at `src/auth/interactive/login_orchestrator.py:183` prompts through
  `CredentialPrompter(self.safe_input).prompt_two_factor()` at
  `src/auth/interactive/login_orchestrator.py:187`.
- It replays the login with `apisession.login_with_return(two_factor=code)` at
  `src/auth/interactive/login_orchestrator.py:193`.
- An aborted prompt clears the session at
  `src/auth/interactive/login_orchestrator.py:189` and returns `None`.

**Session finalisation**

`_finalize_session` at `src/auth/interactive/login_orchestrator.py:216` writes
`self.state["apisession"]` at `src/auth/interactive/login_orchestrator.py:218`. It then
applies a timeout at `src/auth/interactive/login_orchestrator.py:222` and announces MSP
grants at `src/auth/interactive/login_orchestrator.py:223`.

**Portal consequence.** The prompts read from stdin through the injected `safe_input`.
A web portal must inject a different callable that reads the submitted form field. The
constructor already supports that, because `safe_input` is a parameter.

---

### B2. MSP privilege detection

File: `src/refactors/msp_privilege_detection.py` (176 lines).

**Signature**

`detect_msp_privileges(session: Any) -> list[dict[str, Any]]` at
`src/refactors/msp_privilege_detection.py:141`.

`session` is a required positional parameter. The function writes no global. The module
docstring states this at `src/refactors/msp_privilege_detection.py:11-16`. The caller
publishes the result if it wants to.

**Normalized return shape**

`src/refactors/msp_privilege_detection.py:93-98`:

```python
msp_info: dict[str, Any] = {
    "msp_id": msp_id,
    "msp_name": msp_name,
    "role": priv.get("role", "unknown"),
    "scope": priv.get("scope", "unknown"),
}
```

The function returns a list of these dictionaries.

**Source of the data**

`_msp_fetch_user_data` at `src/refactors/msp_privilege_detection.py:124` calls
`self_api.getSelf(session)` at `src/refactors/msp_privilege_detection.py:129`.
`_msp_extract_from_user_data` reads `user_data["privileges"]` at
`src/refactors/msp_privilege_detection.py:113`. Only dictionary grants that carry
`msp_id` qualify (`src/refactors/msp_privilege_detection.py:82`).

`_msp_resolve_name` at `src/refactors/msp_privilege_detection.py:67` resolves a display
name. It falls back to a second API call through `_fetch_msp_name` at
`src/refactors/msp_privilege_detection.py:49`. That call is per MSP grant, so it costs
requests.

**Failure behaviour**

The function returns an empty list on every failure path. It returns `[]` with no session
(`src/refactors/msp_privilege_detection.py:155`), on a malformed payload
(`src/refactors/msp_privilege_detection.py:163`), and on any exception
(`src/refactors/msp_privilege_detection.py:175`). It never raises. A portal cannot
distinguish "no MSP access" from "detection failed" by return value alone.

---

### B3. MSP organization selector — the searchable-list problem

File: `src/auth/interactive/msp_org_selector.py` (236 lines).

**Signature**

`class MspOrgSelector:` at `src/auth/interactive/msp_org_selector.py:10`. The constructor
at `src/auth/interactive/msp_org_selector.py:13-18` takes `state`, `safe_input`, and
`select_org_fallback`. `select()` at `src/auth/interactive/msp_org_selector.py:24` runs
the workflow.

`MistHelper.py:2556` constructs the selector.

**How it fetches organizations**

`_fetch_msp_orgs` at `src/auth/interactive/msp_org_selector.py:120` calls
`mistapi_module.api.v1.msps.orgs.listMspOrgs(apisession, msp_id)` at
`src/auth/interactive/msp_org_selector.py:124`. It sorts by lowercase name at
`src/auth/interactive/msp_org_selector.py:136`.

**Pagination does not work. It is dead code.**

`_paginated_pick` at `src/auth/interactive/msp_org_selector.py:153` hard-codes both page
variables.

- `current_page = 0` at `src/auth/interactive/msp_org_selector.py:155`.
- `total_pages = 1` at `src/auth/interactive/msp_org_selector.py:156`.

The inline comments state the intent openly. Line 156 reads "Force single-page rendering
so the full org list shows as one index."

`_render_page` at `src/auth/interactive/msp_org_selector.py:172` also hard-codes the
slice.

- `start_index = 0` at `src/auth/interactive/msp_org_selector.py:179`.
- `end_index = len(orgs)` at `src/auth/interactive/msp_org_selector.py:180`.

The whole list always renders at once.

The navigation branches in `_interpret_choice` can never run. Line 208 requires
`current_page < total_pages - 1`, which is `0 < 0`. Line 210 requires `current_page > 0`,
which is `0 > 0`. Both are always false.

The multi-page hint at `src/auth/interactive/msp_org_selector.py:189` also never prints,
because it requires `total_pages > 1`.

**No text filter exists.**

`_interpret_choice` at `src/auth/interactive/msp_org_selector.py:198` accepts exactly
three input classes.

1. Blank or `"q"` means skip (`src/auth/interactive/msp_org_selector.py:205`).
2. `"n"` or `"p"` means navigate. Both branches are unreachable, as shown above.
3. A one-based integer index means select
   (`src/auth/interactive/msp_org_selector.py:212-218`).

Any other text falls to `logging.warning("  X Invalid input - try again")` at
`src/auth/interactive/msp_org_selector.py:215`.

**Conclusion for feature 1823.** The new portal cannot reuse this picker for a searchable
organization list. It must build a new picker. The reusable part is `_fetch_msp_orgs` at
`src/auth/interactive/msp_org_selector.py:120`, which returns a sorted list of
dictionaries. Each dictionary carries `name` and `id`
(`src/auth/interactive/msp_org_selector.py:183-184`).

`_record_org_selection` at `src/auth/interactive/msp_org_selector.py:222` writes
`self.state["org_id"]` at `src/auth/interactive/msp_org_selector.py:226`.

---

### B4. Organization identifier resolution — exact precedence and exact spelling

File: `src/config/config_utils.py`.

`get_cached_or_prompted_org_id` at `src/config/config_utils.py:133` resolves the value.
Its docstring at `src/config/config_utils.py:134` states the precedence.

**The exact order**

| Step | Source | Line |
| --- | --- | --- |
| 1 | Class cache `ConfigUtils._org_id_cache` | `src/config/config_utils.py:142-144` |
| 2 | Environment variable `org_id`, then `ORG_ID` | `src/config/config_utils.py:145` |
| 3 | The `.env` file, matched on a line that starts with `org_id=` | `src/config/config_utils.py:150`, matcher at `src/config/config_utils.py:86` |
| 4 | Interactive prompt through `mistapi.cli.select_org` | `src/config/config_utils.py:155`, call at `src/config/config_utils.py:123` |

**The exact spelling and letter case**

`src/config/config_utils.py:145` reads:

```python
org_id_env = os.environ.get("org_id") or os.environ.get("ORG_ID")
```

The primary name is **lowercase `org_id`**. The secondary name is **uppercase `ORG_ID`**.

**`MIST_ORG_ID` is not read by this resolver.** This is the trap.

`src/config/config_utils.py:111-115` prints operator guidance that names `org_id`, not
`MIST_ORG_ID`. `MistHelper.py:2724` prints a matching error that reads "also set org_id
(or ORG_ID) - not MIST_ORG_ID".

`MIST_ORG_ID` does exist elsewhere, and that is why the trap persists.

- `wsgi.py:47` reads `MIST_ORG_ID` during the portal bootstrap.
- `wsgi.py:88` then writes the resolved value back into `os.environ["ORG_ID"]`. That write
  is what makes `ConfigUtils` see the value at all.
- `src/maps/maps_manager.py:2720` reads all three names in order, `org_id`, then `ORG_ID`,
  then `MIST_ORG_ID`.
- `tests/integration/conftest.py:34,85` read `MIST_ORG_ID` first, then `org_id`.
- `deploy/.env.example:17-19` documents that the main path reads the lowercase `org_id`
  line, and that `MIST_ORG_ID` serves later fallbacks such as maps.
- `CHANGELOG.md:3059` and `CHANGELOG.md:3243-3245` record the same trap.

**Recommendation.** Feature 1823 must read `org_id` first and `ORG_ID` second, exactly as
`src/config/config_utils.py:145` does. If the feature also honours `MIST_ORG_ID`, it must
follow the `wsgi.py:88` pattern and normalize into `ORG_ID`. It must not invent a fourth
name.

**Fail-closed behaviour under test flags.** `_resolve_org_id_via_prompt` at
`src/config/config_utils.py:93` refuses to prompt under `--test` and `--testinteractive`
(`src/config/config_utils.py:106`).

---

### B5. Site selection and the missing searchable picker

File: `src/ui/prompt_utils.py`.

`select_site_id_from_csv(csv_file: str = "SiteList.csv")` at `src/ui/prompt_utils.py:127`
is the site picker.

Behaviour:

1. Regenerate the CSV through `CacheUtils.check_and_generate_csv`
   (`src/ui/prompt_utils.py:130`).
2. Load the index map and the name map (`src/ui/prompt_utils.py:131`).
3. Print **every** site in an unbounded loop (`src/ui/prompt_utils.py:135-136`).
4. Prompt once (`src/ui/prompt_utils.py:137`).
5. Accept a numeric index (`src/ui/prompt_utils.py:139`) or an exact name match
   (`src/ui/prompt_utils.py:144`).

Helpers: `_load_site_csv_maps` at `src/ui/prompt_utils.py:154`, `_pick_site_by_index` at
`src/ui/prompt_utils.py:164`, `_pick_site_by_name` at `src/ui/prompt_utils.py:179`,
`select_site` at `src/ui/prompt_utils.py:189`, `select_site_with_logging` at
`src/ui/prompt_utils.py:200`.

The function writes the module global `mh.LAST_SELECTED_SITE_ID` at
`src/ui/prompt_utils.py:142` and `src/ui/prompt_utils.py:146`.

**No searchable site picker exists anywhere in the repository.**

A repository-wide search for a site search or site filter helper returned only unrelated
matches. The hits are device filters, WLAN filters, exclusion filters, and asset filters.
The only text-search feature in the web portal is a data-file browser filter at
`web_portal/services/data_browser.py:181` (`_filter_rows`), used for CSV, JSON, log, and
SQLite previews. It does not select a site.

`web_portal/routes/maps.py:29-30` takes `site_id` straight from the URL path. It never
prompts.

**Conclusion.** Feature 1823 must build its own searchable site picker. It can reuse the
CSV cache path at `src/ui/prompt_utils.py:130` and the map loader at
`src/ui/prompt_utils.py:154`. It must not reuse the prompt loop.

---

### B6. What blocks two concurrent Mist sessions in one process

Two distinct layers of shared global state block it today.

**Layer 1. `ConfigUtils` class variables**

`src/config/config_utils.py:43` declares `class ConfigUtils:`. Two class variables act as
process-wide singletons.

```python
_org_id_cache: ClassVar[str | None] = None   # src/config/config_utils.py:50
_apisession: ClassVar[Any] = None            # src/config/config_utils.py:51
```

Writers: `set_apisession` at `src/config/config_utils.py:54` and `set_cached_org_id` at
`src/config/config_utils.py:65`. Reader: `get_cached_org_id` at
`src/config/config_utils.py:76`.

The cache short-circuits every later lookup at `src/config/config_utils.py:142-144`. A
second user who sets a different organization overwrites the first user's value for the
whole process.

**Layer 2. `MistHelper` module globals**

| Global | Line |
| --- | --- |
| `apisession: Any \| None = None` | `MistHelper.py:2412` |
| `org_id: str \| None = None` | `MistHelper.py:2387` |
| `msp_privileges: list[dict[str, Any]] = []` | `MistHelper.py:2415` |
| `selected_msp: dict[str, Any] \| None = None` | `MistHelper.py:2416` |

`_snapshot_session_globals_to_state` at `MistHelper.py:2419` copies all five names,
including `mistapi`, into a state dictionary (`MistHelper.py:2422-2428`).

`_restore_session_globals_from_state` at `MistHelper.py:2431` rebinds them with
`global apisession, mistapi, msp_privileges, selected_msp, org_id` at `MistHelper.py:2433`.
It then mirrors both values into the `ConfigUtils` cache at `MistHelper.py:2440-2441`.

Further `global` statements appear at `MistHelper.py:2476`
(`global apisession, msp_privileges, org_id`) and at `MistHelper.py:2546`
(`_select_msp_and_org`).

**Layer 3. The WSGI bootstrap writes those same globals at import time**

`wsgi.py:98` runs `_bootstrap_api_session()` at module import. `wsgi.py:83` then assigns
`MistHelper.apisession = wsgi_session`. `wsgi.py:87` assigns
`MistHelper.org_id = wsgi_org_id`. `wsgi.py:88` writes `os.environ["ORG_ID"]`.

The write to `os.environ` is process-wide. It affects every thread.

**The plain statement.** One process holds exactly one Mist session and exactly one
organization identifier today. Every request thread reads the same
`MistHelper.apisession`, the same `MistHelper.org_id`, the same
`ConfigUtils._apisession`, and the same `ConfigUtils._org_id_cache`. A second concurrent
login overwrites the first. Two users cannot hold two different sessions.

**Inference.** A per-user session in feature 1823 needs a session registry keyed by user,
plus explicit session passing through every call path. `detect_msp_privileges` at
`src/refactors/msp_privilege_detection.py:141` already takes an explicit session and is
therefore safe. Any code path that reads `mh.apisession` is not safe, and there are many
such paths.

---

## Part C. Repository conventions and gates

### C1. Binding-rule checklist

Sources: `AGENTS.md`, `.github/copilot-instructions.md`,
`.specify/memory/constitution.md` (version 1.4.0, `.specify/memory/constitution.md:474`).

| Rule | Requirement | Citation |
| --- | --- | --- |
| Five-Item Rule, parameters | A function takes at most 5 parameters | `.specify/memory/constitution.md:58`, `AGENTS.md:56` |
| Five-Item Rule, blocks | A function holds at most 5 logical blocks | `.specify/memory/constitution.md:60` |
| Five-Item Rule, operations | A function performs at most 5 operations | `.specify/memory/constitution.md:63` |
| Five-Item Rule, length | A function runs at most 25 lines | `.specify/memory/constitution.md:65` |
| Inline comments | Every line carries an explanatory comment | `.specify/memory/constitution.md:168-197`, `AGENTS.md:63-65` |
| Action logging | Log before and after every operation | `.specify/memory/constitution.md:199-236`, `AGENTS.md:66-69` |
| Log format | Use `%s` placeholders, never f-strings, for performance and security | `.specify/memory/constitution.md:210-211` |
| ASCII only | Logs and printed output use ASCII characters only | `AGENTS.md:59`, `.github/copilot-instructions.md:198` |
| Safe input | Read input through `safe_input()`, never bare `input()` | `AGENTS.md:57`, `.github/copilot-instructions.md:163-177` |
| Structured logging | Any new service or module requires structured, machine-parseable log entries through `structlog` or an equivalent | `.specify/memory/constitution.md:158-160` |
| Docstring coverage | 90 percent floor, enforced by `interrogate` | `pyproject.toml:493`, `.github/workflows/ci.yml:73` |
| Mandated exporter | Write output through `DataExporter.write_with_format_selection(data, filename, api_function_name=...)` | `.github/copilot-instructions.md:100` |
| Primary keys | Register a strategy in `ENDPOINT_PRIMARY_KEY_STRATEGIES` | `AGENTS.md:58` |
| Class-based design | Use classes, avoid wrapper functions, use full-word iterator names | `.specify/memory/constitution.md:71-91`, `.specify/memory/constitution.md:83` |
| Safety first | Follow the safety-first principle | `.specify/memory/constitution.md:93-119` |
| Fix, do not suppress | Fix the finding, do not add a suppression | `.specify/memory/constitution.md:299-322` |
| Path handling | Follow the documented path handling rule | `AGENTS.md:60` |
| Writing standard | Follow Simplified Technical English | `CLAUDE.md`, `AGENTS.md:74-87`, `documentation/ASD-STE100_writing-guide.md` |

The f-string ban has a stated reason at `.specify/memory/constitution.md:210-211`. Lazy
`%s` formatting defers the string build until the record actually emits. That saves work
when the level filters the record out, and it stops attacker-supplied text from entering
the format string.

Working examples of the log style appear throughout
`src/refactors/msp_privilege_detection.py`, for example at
`src/refactors/msp_privilege_detection.py:100-105`.

---

### C2. Operation registry

**File:** `src/utils/operation_registry.py`.

**Shape**

`_OptionEntry = dict[str, str]` at `src/utils/operation_registry.py:29`.

`_REGISTRY: dict[str, _OptionEntry]` at `src/utils/operation_registry.py:55`. The key is
the menu number **as a string**. The value is a dictionary with a required `category` key
and an optional `skip_reason` key
(`src/utils/operation_registry.py:49-50`).

Two entry forms appear in practice.

```python
"1": {"category": "safe"},                                     # src/utils/operation_registry.py:330
"0": {"category": "interactive", "skip_reason": "Exit option"} # src/utils/operation_registry.py:57
```

**Category names**

The docstring lists them at `src/utils/operation_registry.py:8-20`.

| Category | Meaning | Line |
| --- | --- | --- |
| `safe` | Automated GET. Runs in `--test` | `src/utils/operation_registry.py:10` |
| `interactive_safe` | Read-only but needs a site or a device. Runs in `--testinteractive` | `src/utils/operation_registry.py:11` |
| `destructive` | Modifies state. Always skipped | `src/utils/operation_registry.py:12` |
| `wip` | Work in progress. Unstable | `src/utils/operation_registry.py:13` |
| `resource_intensive` | Takes over one hour or hits rate limits | `src/utils/operation_registry.py:14` |
| `websocket` | Needs a WebSocket and interactive selection | `src/utils/operation_registry.py:15` |
| `continuous_loop` | Never terminates without a user stop | `src/utils/operation_registry.py:16` |
| `interactive` | Needs user input that no runner can automate | `src/utils/operation_registry.py:17` |
| `unregistered` | Fail-closed fallback. Never written by hand | `src/utils/operation_registry.py:18-20` |

Membership sets:

- `SAFE_CATEGORIES = frozenset({"safe"})` at `src/utils/operation_registry.py:455`.
- `INTERACTIVE_SAFE_CATEGORIES = frozenset({"interactive_safe"})` at
  `src/utils/operation_registry.py:457`.
- `SKIP_CATEGORIES` at `src/utils/operation_registry.py:459-472`, which holds
  `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop`,
  `interactive`, and `unregistered`.

**What a new menu number must add**

Add one key to `_REGISTRY` at `src/utils/operation_registry.py:55`. The key is the menu
number as a string. The value must carry a `category`. Add a `skip_reason` whenever the
category sits in `SKIP_CATEGORIES`.

For feature 1823 the likely correct categories are `interactive` for the portal launch
entry and `destructive` for any entry that starts an upgrade. **Inference**, based on the
category definitions and on the existing entries such as
`src/utils/operation_registry.py:101-104`.

**Failure mode when a number is missing**

`get` at `src/utils/operation_registry.py:475` fails closed.

- It looks the option up at `src/utils/operation_registry.py:482`.
- On a miss it logs a warning at `src/utils/operation_registry.py:486-488`.
- It returns `{"category": "unregistered", "skip_reason": "Unregistered menu option - fail-closed pending classification"}`
  at `src/utils/operation_registry.py:489-492`.

Because `unregistered` sits in `SKIP_CATEGORIES`, `is_safe`
(`src/utils/operation_registry.py:495`) and `is_interactive_safe`
(`src/utils/operation_registry.py:500`) both return `False`. The option never runs in
`--test` or in `--testinteractive`.

**Practical effect.** A missing entry does not crash. It silently disables automated test
coverage for the new menu number and emits a warning. A guardrail test then fails.

---

### C3. Quality gates — exact commands and thresholds

Workflow: `.github/workflows/ci.yml`, job group named "Quality Gates"
(`.github/workflows/ci.yml:8`).

| Gate | Exact command | Threshold | Scope | Citation |
| --- | --- | --- | --- | --- |
| Ruff | `ruff check .` | zero findings | whole repository | `.github/workflows/ci.yml:112` |
| Black | `black --check --diff .` | zero diffs | whole repository | `.github/workflows/ci.yml:143` |
| mypy | `mypy ${MYPY_PATHS} --config-file pyproject.toml` | zero errors, strict | `src/ MistHelper.py wsgi.py` | `.github/workflows/ci.yml:182`, paths at `.github/workflows/ci.yml:59` |
| pytest | `pytest --cov=${SRC_PATH} --cov-fail-under=${COVERAGE_THRESHOLD}` | 80 | `src/` | `.github/workflows/ci.yml:220`, threshold at `.github/workflows/ci.yml:71` |
| Bandit | `bandit -c pyproject.toml -r .` | zero findings | whole repository | `.github/workflows/ci.yml:251` |
| pip-audit | `pip-audit -r requirements.txt` | zero unresolved CVEs | `requirements.txt` | `.github/workflows/ci.yml:297` |
| Pylint | `pylint ${SRC_PATH} --fail-under=${PYLINT_THRESHOLD}` | 9.5 | `src/` | `.github/workflows/ci.yml:328`, threshold at `.github/workflows/ci.yml:72` |
| Radon | `radon cc ${RADON_PATHS} -a -nb` plus a JSON check | no block above complexity 10 | `src/ MistHelper.py wsgi.py starlink_dashboard.py` | `.github/workflows/ci.yml:344-346`, paths at `.github/workflows/ci.yml:62`, rule at `.github/workflows/ci.yml:60` |
| Vulture | `vulture ${VULTURE_PATHS} --min-confidence ${VULTURE_CONFIDENCE}` | confidence 70, zero findings | `src/ MistHelper.py wsgi.py starlink_dashboard.py web_portal` | `.github/workflows/ci.yml:376`, paths at `.github/workflows/ci.yml:64`, confidence at `.github/workflows/ci.yml:77` |
| pydocstyle | `pydocstyle ${PYDOCSTYLE_PATHS}` | zero violations | `src/ wsgi.py web_portal` | `.github/workflows/ci.yml:395`, paths at `.github/workflows/ci.yml:67` |
| Interrogate | `interrogate ${INTERROGATE_PATHS} --fail-under ${INTERROGATE_THRESHOLD} -v` | 90 | `src/ MistHelper.py wsgi.py starlink_dashboard.py web_portal tools` | `.github/workflows/ci.yml:411`, paths at `.github/workflows/ci.yml:70`, threshold at `.github/workflows/ci.yml:73` |
| Diagram reference lint | `python scripts/lint_diagram_refs.py` | zero findings | documentation diagrams | `.github/workflows/ci.yml:427` |
| Menu reference drift | `python scripts/generate_menu_wiki.py` then a staleness check | committed output must match | menu documentation | `.github/workflows/ci.yml:443-445` |
| E2E smoke | `pytest tests/e2e/ -v --timeout=60` | all pass | `tests/e2e/` | `.github/workflows/ci.yml:476` |

Python version: `3.13` (`.github/workflows/ci.yml:46`).

Matching settings in `pyproject.toml`:

- `line-length = 120` for Ruff (`pyproject.toml:137`) and for Black (`pyproject.toml:436`).
- `target-version = "py313"` for Ruff (`pyproject.toml:138`) and
  `["py313"]` for Black (`pyproject.toml:437`).
- `[tool.coverage.report] fail_under = 90` (`pyproject.toml:419-420`). **Note the
  mismatch.** The local coverage report floor is 90. The CI gate floor is 80
  (`.github/workflows/ci.yml:71`). The stricter local number wins when a developer runs
  `pytest` with the project configuration.
- `[tool.pylint.main] fail-under = 9.5` (`pyproject.toml:440-441`).
- `[tool.pylint.format] max-line-length = 120` (`pyproject.toml:464`).
- `[tool.interrogate] fail-under = 90` (`pyproject.toml:492-493`).
- `[tool.pytest.ini_options] addopts = "-v --tb=short"` (`pyproject.toml:403`).
- `[tool.ste_linter]` (`pyproject.toml:107`) backs the separate STE workflow at
  `.github/workflows/ste-lint.yml`.

Two further workflows apply. `.github/workflows/codeql.yml` runs CodeQL.
`.github/workflows/ste-lint.yml` runs the Simplified Technical English linter.

Local pre-push commands from `AGENTS.md:23-26`:

```text
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
```

`AGENTS.md:30` gives the test invocation. `.github/copilot-instructions.md:548` names the
pre-commit hook.

**Warning.** CodeQL inline suppression comments do not work. The `# lgtm[...]` and
`# codeql[...]` forms are ignored. Dismiss an alert through the API instead. This comes
from the operator memory file, not from a repository file. **Inference from operator
notes.**

---

### C4. Pull-request rules

| Rule | Requirement | Citation |
| --- | --- | --- |
| Branch naming | `<type>/<issue>-<slug>` | `.specify/memory/constitution.md:396-405`, `.github/copilot-instructions.md:622` |
| Worktree creation | `git worktree add ../MistHelper-<slug> -b <type>/<issue>-<slug> main` | `AGENTS.md:33-34` |
| Worktree teardown | Follow the documented teardown steps | `AGENTS.md:37-39` |
| Required labels | Every pull request carries the required label set | `.specify/memory/constitution.md:407-415`, `.github/copilot-instructions.md:359-364` |
| Merge method | Squash merge only | `.specify/memory/constitution.md:433` |
| Auto-merge | Follow the documented auto-merge policy | `.github/copilot-instructions.md:566-576` |
| Forbidden actions | Follow the NEVER list | `.github/copilot-instructions.md:468-476` |
| Web UI validation | Open the portal, interact, then generate Playwright tests into `tests/e2e/` | `.github/copilot-instructions.md:628`, `.github/copilot-instructions.md:586` |

The portal listens on port 8055 (`.github/copilot-instructions.md:582`). The
`gunicorn_server` fixture at `tests/e2e/conftest.py:57` manages the server lifecycle for
browser tests.

**Warning.** Do not merge with an administrator bypass. Check `mergeStateStatus` instead.
A `SKIPPED` conditional check does not block a merge. This comes from the operator memory
file, not from a repository file. **Inference from operator notes.**

---

## Part D. Consolidated risk list for feature 1823

1. **Rate limit.** A 20-second poll across a large fleet exhausts the hourly quota. Use
   bulk endpoints and back off. See section A4.
2. **Single session.** The process holds one session and one organization identifier. An
   MSP login for a second user overwrites the first. See section B6.
3. **No searchable pickers.** Neither the organization picker nor the site picker supports
   text search. Both need new code. See sections B3 and B5.
4. **Organization variable case.** Read `org_id` first and `ORG_ID` second. Do not read
   `MIST_ORG_ID` as the primary name. See section B4.
5. **Worker death.** In-memory run state dies with the Gunicorn worker. Persist the state
   if the upgrade must survive a restart. See section A5.
6. **Thread-local loss.** A background thread does not inherit request thread-local
   values. Pass every value explicitly. See section A5.
7. **Registry omission.** A missing operation-registry entry fails closed and breaks the
   guardrail test. See section C2.
8. **Coverage mismatch.** The local coverage floor is 90 and the CI floor is 80. Target 90.
   See section C3.
