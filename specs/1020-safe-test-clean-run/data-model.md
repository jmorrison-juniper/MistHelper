# Data Model: Safe `--test` Clean Run

**Feature**: `1020-safe-test-clean-run` | **Input**: `spec.md` Key Entities section, grounded against actual code in `research.md`.

This feature has no persisted database schema changes (no new tables, no
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entries — it modifies control-flow/safety
logic, not data export). "Entities" here are the in-memory/config objects the
functional requirements act on, expressed as concrete Python shapes already
present or to be added in the named files.

## 1. Menu Option

Represents one numbered entry in `menu_actions` (`MistHelper.py:3641`).

| Field | Type | Source | Notes |
|---|---|---|---|
| `option_id` | `str` (numeric key, e.g. `"194"`) | `menu_actions` dict key | 197 keys today (0-196), all numeric strings, no lettered-suffix keys currently reachable. |
| `handler` | `Callable` | `menu_actions[option_id][0]` | The function/lambda invoked when the option runs. |
| `description` | `str` | `menu_actions[option_id][1]` | Human-readable label shown in the interactive menu; used by preliminary classification (destructive labels are prefixed `" DESTRUCTIVE: ..."` per Constitution III). |

**Invariant this feature adds**: every `option_id` present in `menu_actions`
MUST have a corresponding entry in `OperationRegistry._REGISTRY` (enforced by
the new coverage guardrail, R2). No lifecycle/state transitions — menu
options are static for the duration of a process.

## 2. Operation Classification

Represents one entry in `OperationRegistry._REGISTRY`
(`src/utils/operation_registry.py:51-274`).

| Field | Type | Notes |
|---|---|---|
| `option_id` | `str` | Matches a `Menu Option.option_id`. |
| `category` | `str` (enum) | One of 8 documented values: `safe`, `interactive_safe`, `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop`, `interactive` — **plus a 9th value added by this feature**: `unregistered` (fail-closed fallback only; never written into `_REGISTRY` directly, only returned by `get()` for keys absent from the dict). |
| `skip_reason` | `str` (optional) | Human-readable reason shown in `--test`/`--testinteractive` skip listings; destructive entries MUST contain the substring `"DESTRUCTIVE"` (enforced by guardrail). |

**State/transition rule (the defect this feature fixes)**:

```text
Before (defect):  option_id not in _REGISTRY -> category = "safe"  (fail-OPEN)
After (fixed):    option_id not in _REGISTRY -> category = "unregistered" (fail-CLOSED, in SKIP_CATEGORIES)
```

`category` membership determines mode eligibility:

| Category | `--test` (`is_safe`) | `--testinteractive` (`is_interactive_safe`) |
|---|---|---|
| `safe` | ✅ | ❌ (unless also mapped via `interactive_safe`) |
| `interactive_safe` | ❌ | ✅ |
| `unregistered` (new) | ❌ | ❌ |
| all other `SKIP_CATEGORIES` members | ❌ | ❌ |

**New public accessor** (added by this feature, not a schema change but a
capability the coverage guardrail depends on):
`OperationRegistry.registered_options() -> set[str]` returns
`set(cls._REGISTRY.keys())`, mirroring the existing `safe_options()` /
`unsafe_options()` classmethod pattern (`operation_registry.py:339-352`).

## 3. Systematic Test Run

Represents one execution of `RunSystematicTestManager.run()`
(`src/refactors/run_systematic_test.py:75-99`) or the analogous
`--testinteractive` runner (`src/refactors/run_interactive_test.py`).

| Field | Type | Source |
|---|---|---|
| `safe_options` | `list[str]` | `_build_systematic_test_options()` (`MistHelper.py:4766-4778`), via `OperationRegistry.safe_options`/`interactive_safe_options`. |
| `unsafe_list` | `list[str]` | Same call; every non-safe option, each carrying its `skip_reason`. |
| `all_options` | `list[str]` | `sorted(menu_actions.keys(), ...)` — used by the coverage guardrail to diff against `registered_options()`. |
| `org_id` | `str` | Resolved once via `_resolve_systematic_test_context()` (`MistHelper.py:4801-4806`) → `ConfigUtils.get_cached_or_prompted_org_id()`. |
| `success_count` / `error_count` | `int` | Accumulated by `_execute_systematic_test_loop`. |
| `telemetry_path` | `Path` | `TelemetryEmitter.timestamped_path("data")` — JSONL evidence file for the loop-protocol's live-run stage (R5). |
| `outcome` | `bool` | Return value of `RunSystematicTestManager.run()` / `_report_systematic_outcome`. |

**Lifecycle**: `_prepare_sweep` (banner + classify + telemetry-open +
org/fast-mode resolve) → `_execute_sweep` (iterate `safe_options`) →
`_build_summary` → `_finalize_sweep` (emit + print + return outcome). This
feature does not change the lifecycle shape; it changes what `safe_options`
contains (fewer false positives once fail-closed) and inserts the credential
preflight before `_resolve_systematic_test_context()` reaches the org-id
prompt fallback (R4).

## 4. Credential Preflight Result

New conceptual entity (no existing class yet) — the outcome of the new
`_preflight_verify_credentials()` check (R4) inserted at the top of
`_establish_mist_session()` (`MistHelper.py:5201`).

| Field | Type | Notes |
|---|---|---|
| `host_present` | `bool` | Derived from `_parse_api_tokens()` host value being non-empty and not an obvious placeholder. |
| `token_present` | `bool` | Derived from `_parse_api_tokens()` tokens list being non-empty. |
| `redacted_token_preview` | `str` | Built via existing `_redact_tokens()` (`MistHelper.py:2562-2564`) — never the raw token. |
| `remediation_message` | `str` | Points at `deploy/.env.example` and the exact env var names the code reads (`MIST_APITOKEN`/`MIST_API_TOKEN`, `MIST_HOST`, `org_id`/`ORG_ID`). |
| `verdict` | `Literal["pass", "fail_closed"]` | On `fail_closed`, the process MUST exit before any `mistapi`/`requests` call is made — no partial session object is constructed. |

No persistence — this is a synchronous pre-condition check, evaluated once
per process invocation, never written to disk or logged with secret values.

## 5. Virtual Environment Precondition

New conceptual entity — the outcome of the new
`_is_running_in_isolated_venv()` predicate (R3) on
`DependencyCheckOrchestrator` (`src/bootstrap/dependency_check.py`).

| Field | Type | Notes |
|---|---|---|
| `sys_prefix` | `str` | `self.sys_module.prefix` |
| `sys_base_prefix` | `str` | `self.sys_module.base_prefix` |
| `legacy_real_prefix` | `str \| None` | `getattr(self.sys_module, "real_prefix", None)` — older `virtualenv` fallback signal per spec Assumptions. |
| `is_isolated` | `bool` | `sys_prefix != sys_base_prefix or legacy_real_prefix is not None`. |
| `override_env_present` | `bool` | New env var (naming TBD at implementation time following the `_ENV_*` convention, e.g. `MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL`) explicitly set by the operator to opt back into system-Python installs. |
| `verdict` | `Literal["allow_install", "block_install"]` | `allow_install` iff `is_isolated or override_env_present` (and the pre-existing `DISABLE_AUTO_INSTALL` gate is not already blocking, which is evaluated independently and unchanged). |

## 6. Validation Loop Verdict

New conceptual entity — the aggregate state the iterative loop protocol (R5)
tracks across repeated invocations of the test layers.

| Field | Type | Notes |
|---|---|---|
| `stage` | `Literal["static", "unit_suite", "diagnosis", "live_credentialed"]` | Which of the 4 loop stages (R5) is active. |
| `auto_repeatable` | `bool` | `True` for `static`/`unit_suite`; `False` for `live_credentialed` (external gate — requires operator-supplied `.env`). |
| `last_failure_evidence` | `str \| None` | The failing assertion/traceback line(s) that must drive the next fix — never a guessed cause. |
| `credentials_available` | `bool` | Detected via the Credential Preflight Result (§4) `verdict`; when `False`, the loop records `live_credentialed` as **blocked**, not failed, and does not retry it automatically. |
