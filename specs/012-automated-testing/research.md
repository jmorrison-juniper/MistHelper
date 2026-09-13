# Research: Automated Testing Infrastructure

**Feature**: 012-automated-testing | **Date**: 2026-03-11

## R1: Unit Test Import Isolation Strategy

**Question**: How to import MistHelper utility functions for unit testing without triggering module-level side effects?

**Findings**: MistHelper.py has significant side effects on import:
- Lines 67-79: Creates `data/` directory, configures `logging.basicConfig`
- Line 153: `DataDirectoryChecker` runs immediately — writes test file to `data/`, calls `sys.exit(1)` if `data/` is not writable
- Lines 868-882: `load_dotenv()` modifies `os.environ`
- Lines 1968-1999: `initialize_all_imports()` installs packages via UV/pip — but **skipped** when `--test` or `--skip-deps` in `sys.argv`
- `mistapi` import is deferred (set to `None` at line 778, loaded later by `GlobalImportManager`)
- `argparse` is inside `main()`, not at module level
- `if __name__ == "__main__"` guard exists at line 54548

**Decision**: Duplicate the specific utility functions/classes into unit test files (same pattern as `scripts/test_stop_signal.py`) rather than importing from MistHelper.py directly. This avoids all side effects and keeps tests truly isolated.

**Rationale**: The existing `test_stop_signal.py` already uses this pattern successfully. The functions under test (`flatten_dict`, `escape_multiline`, `get_unique_keys`, `check_stop_signal`) are pure/static with no API dependencies. Duplicating ~50 lines of pure logic is simpler and more reliable than engineering an import shim to suppress side effects.

**Alternatives Considered**:
- *Extract utilities to separate module files*: Would require major refactoring of MistHelper.py monolith, out of scope for this feature
- *Use `importlib` with mocked sys.argv*: Fragile — any new side effect added to MistHelper.py would break tests
- *Import with `unittest.mock.patch`*: Still triggers some side effects before patches apply

**Future**: When MistHelper is eventually modularized (separate feature), utility functions can be imported directly and the duplicated test copies retired.

## R2: Operation Classification Architecture

**Question**: How are operations classified as safe vs destructive, and how should this be centralized?

**Findings**: Classification is currently **duplicated** across two inline dictionaries:
- `run_systematic_test()` at line ~51122: `unsafe_options` dict with 58 entries, each mapping option string to skip reason string. Categories include: destructive, WebSocket/interactive, site-selection-required, WIP, resource-intensive, continuous-loop
- `run_interactive_test()` at line ~51420: `interactive_read_only_options` dict with 21 entries — operations that need interactive input but are read-only safe
- No centralized `OPERATION_REGISTRY` or `SAFE_OPERATIONS` constant exists

**Decision**: Create an `OperationRegistry` class that centralizes operation classification. This replaces the two inline dicts with a single authoritative source. Each operation gets a category (`safe`, `interactive_safe`, `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop`) and metadata (skip reason, required params like `site_id`).

**Rationale**: Centralization eliminates the current duplication between `run_systematic_test()` and `run_interactive_test()`. It also makes it trivial to add new operations (one place to update) and enables the test harness to auto-determine which operations to run vs skip vs skip-with-event.

**Alternatives Considered**:
- *Keep inline dicts*: Existing duplication would grow worse with new telemetry requirements
- *Use a config file (JSON/YAML)*: Adds external file dependency with no real benefit — the classification is code-level knowledge

## R3: Non-Interactive Parameter Selection

**Question**: How should the test harness auto-select parameters (site, device) without user input?

**Findings**: MistHelper already has non-interactive parameter passing via the `--menu` CLI mode (line ~54150):
- Resolves `--site` name to `site_id` via API lookup
- Resolves `--device` name to `device_id`
- Uses `inspect.signature(func)` to pass only accepted params dynamically
- `run_interactive_test()` already fetches the first site: `mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1)` and injects `site_id` via `inspect.signature(func)` introspection

**Decision**: Extend the existing `inspect.signature(func)` introspection pattern from `run_interactive_test()` to the unified `TestHarness`. For site-dependent operations, fetch the first available site (already proven pattern). For device-dependent operations, fetch the first device from that site. All parameter resolution happens before invocation with no user prompts.

**Rationale**: This reuses proven patterns already in the codebase rather than inventing new parameter resolution. The `inspect.signature()` approach is flexible — it automatically adapts when function signatures change.

**Alternatives Considered**:
- *Hardcode test parameters in config*: Brittle — breaks when sites/devices change
- *Use mocked parameters*: Defeats the purpose of live e2e testing

## R4: NDJSON Telemetry Best Practices

**Question**: What is the best approach for NDJSON event emission in Python?

**Findings**: No existing structured telemetry in MistHelper. Current test output is `print()` + `logging.info()` with human-readable prefixes (`SYSTEMATIC_TEST:`, `INTERACTIVE_TEST:`). `json.dumps` appears only 3 times in debug logging for API response diagnostics.

**Decision**: Create a `TelemetryEmitter` class with:
- `__init__(file_path)`: Opens file in append mode. Creates `data/` dir if needed.
- `emit(event_dict)`: Writes `json.dumps(event) + "\n"` with best-effort error handling (catch `OSError`, log warning, continue)
- `close()`: Flushes and closes file handle
- Context manager support (`__enter__`/`__exit__`)
- Timestamped filename support: `test_events_YYYYMMDD_HHMMSS.jsonl` for `--test` mode, `test_events.jsonl` for live progress events
- Retention: Delete oldest files when count exceeds configurable limit (default 10)

**Rationale**: Simple append-only write pattern. NDJSON requires no buffering, no complex serialization — just `json.dumps()` + newline. Best-effort wrapping ensures FR-008 compliance (telemetry never breaks operations). The class stays under 25 lines per method (Five-Item Rule).

**Alternatives Considered**:
- *`structlog`*: Adds external dependency for a simple append-write pattern. Overkill.
- *Python `logging.FileHandler` with JSON formatter*: Mixes telemetry with application logs — harder for AI consumers to parse
- *Write to SQLite*: Adds complexity, NDJSON is simpler for streaming reads

## R5: CI Pipeline Enhancement

**Question**: How should the GitHub Actions workflow be modified to add test gating?

**Findings**: Current CI (`.github/workflows/container-build.yml`):
- Two jobs: `validate` → `build-and-push`
- `validate` runs: `python -m py_compile MistHelper.py` + `ast.parse()`
- `build-and-push` depends on `validate` via `needs: validate`
- Triggers: push to `main` (specific file changes) or manual dispatch
- No test execution, no pytest

**Decision**: Add a `test` job between `validate` and `build-and-push`:
1. `validate` (existing — syntax check)
2. `test` (NEW — `needs: validate`, runs `pip install pytest && python -m pytest tests/unit/ -v`)
3. `build-and-push` (existing — change `needs: validate` to `needs: test`)

The `test` job:
- Uses `actions/setup-python` with Python 3.13
- Installs only `pytest` (unit tests have no other dependencies)
- Does NOT install `mistapi` or other heavy deps (unit tests are isolated)
- Does NOT need `.env` or API credentials
- Reports results via GitHub Actions annotations (pytest's default behavior)

**Rationale**: Minimal change to existing CI. The new job slots between existing jobs. If tests fail, the build-and-push job is skipped (GitHub Actions `needs` dependency). No credentials needed in CI.

**Alternatives Considered**:
- *Add tests to existing `validate` job*: Less granular reporting, mixes syntax validation with functional testing
- *Separate workflow file*: Unnecessary complexity — one workflow with sequential jobs is clearer

## R6: Progress Hook Injection Points

**Question**: Where in MistHelper.py should progress events be emitted?

**Findings**: Site/device iteration loops follow a consistent pattern across the codebase. Operations that iterate over sites typically:
1. Call `mistapi.api.v1.orgs.sites.listOrgSites()` to get site list
2. Loop over sites with `for site in sites`
3. Call per-site API endpoint inside the loop
4. Collect results and write output

Key loop locations (representative — there are ~40 such loops):
- Device inventory (Menu 11): iterates sites, fetches devices per site
- Device stats (Menu 12): iterates sites, fetches device stats per site
- Client data (Menu 66-67): iterates sites, fetches client data per site

**Decision**: Add progress hook calls at three points in each loop:
1. Before loop: `telemetry.emit(progress_start(operation, total_sites))`
2. Inside loop: `telemetry.emit(progress_tick(operation, site_name, completed, remaining))`
3. After loop: `telemetry.emit(progress_complete(operation, processed, total, was_stopped, duration))`

Implement as helper methods on `TelemetryEmitter` to keep call sites minimal (single method call, not dict construction). Start with the 10 most-used operations and expand.

**Rationale**: Three-point pattern (start/tick/complete) gives AI agents everything needed for progress monitoring without excessive detail. Helper methods keep call sites clean and under the 25-line function limit.

**Alternatives Considered**:
- *Decorator-based approach*: Hard to inject into existing loops without restructuring
- *tqdm integration*: tqdm is display-oriented, not structured data — would need separate telemetry anyway
