# Research: Safe `--test` Clean Run

**Feature**: `1020-safe-test-clean-run` | **Date**: 2026-11 | **Input**: `spec.md`

All items below were resolved by direct source inspection in this worktree
(branch `1020-safe-test-clean-run`), not by external research, since this is a
defect-remediation feature against the existing MistHelper codebase. Every
"Decision" is grounded in an exact file/line citation so `/speckit.tasks` can
generate tasks without re-discovering the code.

---

## R1. Registry fail-open default (User Story 1 / FR-001–FR-007)

- **Decision**: Change `OperationRegistry.get()` (`src/utils/operation_registry.py:310-317`)
  to default unregistered options to a new `"unregistered"` category instead of
  `{"category": "safe"}`. Add `"unregistered"` to `SKIP_CATEGORIES`
  (`operation_registry.py:306-308`) so it is excluded from *both*
  `SAFE_CATEGORIES` and `INTERACTIVE_SAFE_CATEGORIES`. Because `is_safe()` and
  `is_interactive_safe()` both call `get()` (lines 320-327), a single change to
  the fallback fixes `--test` and `--testinteractive` uniformly (FR-007) with
  no per-mode branching.
- **Rationale**: `SKIP_CATEGORIES` membership is exactly what `skip_reason()`/
  `skip_category()` already expect (lines 330-337) — using an existing
  mechanism instead of inventing a parallel code path minimizes blast radius
  and keeps `WAVE1_ENTRY_ROUTING_BASELINE`/telemetry callers working unchanged.
- **Alternatives considered**:
  - *Raise an exception from `get()` for unregistered options*: rejected —
    dozens of call sites (`is_safe`, `skip_reason`, telemetry emitters) do not
    currently handle exceptions, so this would require a much larger blast
    radius of call-site try/except additions for a spec that only requires
    fail-**closed** classification, not fail-**crash**.
  - *Add a bespoke `is_registered()` gate before every call site*: rejected —
    the whole point of `OperationRegistry` is being the single source of
    truth; a parallel gate re-introduces the drift risk this feature fixes.
- **Explicit classification of the 60 unregistered IDs**: implementation adds
  real `_REGISTRY` entries for all 60 missing keys (not just relying on the
  new fail-closed default), satisfying "all currently reachable `menu_actions`
  must be explicitly classified." The fail-closed default remains as a
  defense-in-depth guardrail for any *future* unclassified addition. The
  preliminary classification below was derived by reading each option's
  handler in `MistHelper.py` and, where relevant, its handler class
  (confirmed against the constitution's Testing section "Skip list:
  Operations 14, 18 (heavy)..."). Per spec Assumptions, exact final
  categories are implementation-time work; this table is the concrete
  starting point for `/speckit.tasks`, not a frozen answer:

  | Menu ID(s) | Preliminary category | Evidence |
  |---|---|---|
  | 1,2,3,4,5,8,9,10,11,12,15,16,17,20,21,22,24,27,28,29,30,31,32,33,34,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,188,193,195 | `safe` | Pure read-only exports; no site/device prompt in the handler. Options 6/7 verified in detail (`SiteExportUtils(...).zone_config_analysis()`, `ExtractedSiteInventoryHealthAnalyzer.analyze(...)`) — both already registered `safe` and iterate `all_sites_fn=APICoreFetchUtils.all_sites_with_limit` automatically. |
  | 14 | `resource_intensive` | `_configure_virtual_chassis_manager().launch_check_status()` — matches constitution "Skip list: Operations 14, 18 (heavy)". |
  | 18 | `resource_intensive` | `_dispatch_gateway_stats_device_stats_with_freshness` — gateway device stats "with freshness check"; same constitution skip-list entry. |
  | 188 | `safe` | Read-only export (ticket listing without mutation) — verify no `_select_ticket`/write call during implementation. |
  | 189 | `destructive` | `OrgTicketManager.create_ticket` (`src/org/org_ticket_manager.py`) — creates a real support ticket, a genuine external side effect. |
  | 190 | `destructive` | `OrgTicketManager.add_comment` — writes a comment to a live ticket. |
  | 191 | `destructive` | `OrgTicketManager.update_ticket` — mutates ticket state. |
  | 192 | `interactive` | `OrgTicketManager.view_ticket` calls `OrgTicketManager._select_ticket(org_id)`, which prompts the user to choose from a list — not automatable non-interactively. |
  | 194 | `destructive` | `DeviceConfigTemplateClonerManager.clone` — requires typed `'CREATE'` confirmation (Constitution III destructive pattern). Matches spec FR-004 exactly. |

  **Note on 35/36**: not individually re-verified by handler inspection in
  this pass (grouped with the "likely safe read export" run of consecutive
  IDs); implementation MUST re-confirm each before adding a `_REGISTRY` entry,
  per spec Assumptions ("classification work happens during implementation,
  not spec/plan time").

## R2. Durable menu/registry coverage guardrail (User Story 1)

- **Decision**: Replace the *representative-sample* pattern
  (`WAVE1_ENTRY_ROUTING_BASELINE`, 11 hand-picked keys —
  `operation_registry.py:278-290`) with a new **exhaustive** guardrail test
  file `tests/guardrails/test_operation_registry_menu_coverage.py` that
  asserts:
  1. `set(MistHelper.menu_actions.keys()) == OperationRegistry.registered_options()`
     (new public classmethod returning `set(cls._REGISTRY.keys())`, added
     alongside the existing `safe_options`/`unsafe_options` classmethods) —
     catches *any* menu addition or removal immediately, not just the 11
     sampled keys.
  2. Every registered category is one of the 8 documented categories in the
     module docstring (`operation_registry.py:8-17`) — catches typo'd or
     invalid category strings.
  3. Every entry with `category == "destructive"` still carries a
     `skip_reason` containing `"DESTRUCTIVE"` (reuses the existing pattern
     from `test_wave1_safety_classification_guardrails.py:24-29`, but applied
     to *all* destructive entries, not a hand-picked list).
  4. Zero entries resolve to `"unregistered"` via `OperationRegistry.get()`
     (i.e., `unsafe_options`/`skip_category` on the full `menu_actions` key
     set never surfaces the fail-closed fallback) — this is the "dangerous
     incomplete categorization" detector: if a future menu addition is
     forgotten, this test fails loudly instead of silently defaulting safe
     *or* silently skipping forever.
- **Rationale**: A brittle partial baseline (11 of 197 keys) is exactly the
  mechanism that let 60 keys go unnoticed. An exhaustive key-parity assertion
  is O(1) to maintain (it has no hand-picked list to update) and fails the
  instant `menu_actions` and `_REGISTRY` diverge in either direction — this
  is the "durable" guardrail the user asked for, replacing rather than
  patching the brittle baseline.
- **Existing tests to reconcile, not treat as unrelated changes** (per spec
  Assumptions/Edge Cases):
  - `tests/guardrails/test_wave1_safety_classification_guardrails.py:9-16`
    iterates `WAVE1_SAFETY_CLASSIFICATION_BASELINE["safe_true"]`, which
    includes the sentinel `"9999"` (`operation_registry.py:294`) — a key that
    does not exist in `menu_actions` at all. Under today's fail-open default,
    `is_safe("9999")` returns `True` by accident. Once the default flips to
    fail-closed, this specific baseline entry must be corrected (removed or
    replaced with a real safe key) as *implementation work for this feature*,
    not an unrelated test change, since the spec's Assumptions explicitly
    call out this baseline as expected to require correction.
  - `tests/guardrails/test_wave1_entry_routing_guardrails.py` (existing
    11-key sample) is retained as a fast smoke check but is superseded as the
    *sole* coverage mechanism by the new exhaustive test in this feature.
- **Alternatives considered**:
  - *Expand the existing baseline dict to all 197 keys*: rejected — still a
    hand-maintained list that silently goes stale on the next menu addition;
    doesn't solve the root problem (no automatic drift detection).
  - *CI-only check (outside pytest) diffing menu_actions vs registry*:
    rejected — spec requires the guardrail to run in the same test layers as
    everything else (`pytest`), and a pytest-based check is simpler to wire
    into the existing `scripts/wave1/run_wave1_gate.ps1` gate runner (R6).

## R3. Isolated venv preflight (User Story 2 / FR-008–FR-012)

- **Decision**: Add a new predicate method `_is_running_in_isolated_venv()`
  to `DependencyCheckOrchestrator` (`src/bootstrap/dependency_check.py`),
  using the already-injected `self.sys_module` field (line 51):
  `self.sys_module.prefix != self.sys_module.base_prefix` (with a
  `getattr(self.sys_module, "real_prefix", None)` fallback check for
  older `virtualenv`, per spec Assumptions). Gate the check behind a new
  env-var override following the existing naming convention
  (`_ENV_DISABLE_AUTO_INSTALL = "DISABLE_AUTO_INSTALL"` at line 11), e.g.
  `_ENV_ALLOW_SYSTEM_PYTHON_INSTALL = "MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL"`.
  Insert the check in `run()` (lines 60-64) immediately alongside the
  existing `_is_auto_install_disabled()` check so both guards short-circuit
  before any install/upgrade action executes.
- **Rationale**: `sys_module` being an injected dependency (not a bare
  `import sys`) means the new predicate is trivially unit-testable by
  injecting a fake namespace object with controlled `prefix`/`base_prefix`
  values — no monkeypatching of the real interpreter needed, consistent with
  how the existing `_is_auto_install_disabled()` is already tested.
- **Distinguishing a genuine venv from a missing/broken `.venv` launcher**:
  the check must fail closed (block auto-install) when `sys.prefix ==
  sys.base_prefix` regardless of *why* — whether the operator never created
  a `.venv`, or the `.venv` launcher (`.venv/Scripts/python.exe` on Windows)
  is broken/missing and the shell silently fell back to system Python. The
  spec does not require distinguishing these two causes in behavior (both
  must block by default); the plan MUST distinguish them only in the
  *diagnostic message* text so an operator can tell "you forgot to activate
  `.venv`" from "your `.venv` looks broken, recreate it" — this is a message
  content requirement, not a branching-logic requirement, keeping the
  predicate itself simple (5-Item-Rule compliant).
- **Ordering defect already confirmed**: `MistHelper.py:950` calls
  `_early_dependency_check()` unconditionally at **module import time**
  (before `--test`/`--testinteractive` arg parsing, before any credential
  code). The fix targets *what `run()` does when unsafe*, not *when it is
  called* — moving the call site out of import-time is out of scope (larger
  blast radius, not required by any FR) and risks breaking other code paths
  that rely on dependencies being ready before `import` continues.
- **Alternatives considered**:
  - *Move `_early_dependency_check()` call later in `main()`*: rejected —
    unnecessary scope expansion; the FRs only require gating the
    install/upgrade *action*, not deferring the whole call.
  - *Detect venv via `os.environ["VIRTUAL_ENV"]` only*: rejected as sole
    signal — not set by all launchers/IDEs; `sys.prefix != sys.base_prefix`
    is the canonical, launcher-independent signal per spec Assumptions.
- **Preserve existing explicit opt-in compatibility**: the existing
  `DISABLE_AUTO_INSTALL` env var must continue to short-circuit installs
  entirely (unchanged); the new venv guard is an *additional* independent
  gate, not a replacement, so operators who already set
  `DISABLE_AUTO_INSTALL=1` see no behavior change.

## R4. Early credential/config preflight (User Story 3 / FR-013–FR-017)

- **Decision — two insertion points, not one, because two distinct failure
  modes exist**:
  1. **Host/token preflight** (FR-013, FR-015, FR-017): add a new preflight
     check at the very top of `_establish_mist_session()`
     (`MistHelper.py:5201`), before either the `--login` branch or the
     token branch, calling a new `_preflight_verify_credentials()` helper
     that reuses `_parse_api_tokens()` (`MistHelper.py:2567-2583`) to read
     `MIST_HOST`/`MIST_APITOKEN`/`MIST_API_TOKEN` and fails closed
     (`sys.exit(1)` with a redacted, actionable message) when the host is
     empty/placeholder or no tokens are present — **before**
     `MistSessionInitializer.initialize()` is ever called. This is the exact
     function whose `_try_single_session_kwargs()`
     (`MistHelper.py:2718-2740`) constructs the real `mistapi.APISession(**kwargs)`
     that triggers the malformed-URL HTTP request when host/token are
     missing or blank — the preflight sits strictly upstream of that call,
     for every mode (`--test`, `--testinteractive`, TUI, CLI, interactive),
     satisfying FR-013's "before mistapi sends HTTP" for the whole app, not
     just systematic mode.
  2. **Org-id preflight for non-interactive runs** (FR-016): harden
     `ConfigUtils._resolve_org_id_via_prompt()`
     (`src/config/config_utils.py:92-111`) with a non-interactive guard: if
     the process is running in a systematic test mode
     (`"--test" in sys.argv or "--testinteractive" in sys.argv` — computed
     locally with the already-imported `sys` module, preserving
     `ConfigUtils`'s explicit "no `import MistHelper`, no reach-back"
     self-containment design per its own module docstring) **and** no org id
     was resolved via cache/env/`.env` (i.e., the call reached the prompt
     fallback at all), fail closed with an actionable message instead of
     calling `mistapi.cli.select_org(cls._apisession)` — which is exactly
     the call that issues the malformed-URL request when `_apisession` was
     constructed with a blank host (the observed 2026-07-16 defect).
     `_resolve_systematic_test_context()` (`MistHelper.py:4801-4806`) is the
     sole call site that reaches this path for `--test`; the interactive-test
     org resolution path (`src/refactors/run_interactive_test.py`) reuses the
     same `ConfigUtils.get_cached_or_prompted_org_id()` via getter/setter
     closures, so hardening `ConfigUtils` once covers both systematic modes
     uniformly, matching the fail-closed-in-both-modes requirement already
     established for the registry in R1.
- **Redaction**: reuse `_redact_tokens()` (`MistHelper.py:2562-2564`,
  `first4...last4` or `***`) verbatim — this is the existing convention
  FR-015 says must not be reinvented.
- **Remediation messaging accuracy (a discovered nuance worth recording)**:
  `deploy/.env.example` documents `MIST_API_TOKEN` and `MIST_ORG_ID`, but the
  code paths that actually resolve these values read `MIST_APITOKEN` **or**
  `MIST_API_TOKEN` for the token (`_parse_api_tokens`,
  `MistHelper.py:2577`) and `org_id`/`ORG_ID` (lowercase/uppercase, **not**
  `MIST_ORG_ID`) or a `.env` line literally named `org_id=` for the org id
  (`ConfigUtils._resolve_org_id_from_dotenv`,
  `src/config/config_utils.py:81-90`, and `get_cached_or_prompted_org_id`,
  lines 113-137). The preflight's remediation message MUST reference the
  variable names the code actually reads, and MUST point the operator at
  `deploy/.env.example` as the file to copy from, while clarifying that the
  org id variable is `org_id` (not `MIST_ORG_ID`) for this resolution path —
  otherwise the "clear operator remediation" requirement (FR-014) would
  itself be misleading.
- **Zero-HTTP-call guarantee in tests**: `_check_token_rate_limit()`
  (`MistHelper.py:2586-2605`) makes a real `requests.get()` call and MUST
  NEVER be exercised by the new preflight or by any unit test of it — the
  preflight only performs local string/format validation (non-empty,
  non-placeholder, well-formed) and never imports `requests` or calls
  `mistapi`. SC-004's "assert zero outbound HTTP calls" is achieved
  structurally (the preflight function has no network-capable import), not
  by mocking, which is the more durable guarantee.
- **Alternatives considered**:
  - *Single combined preflight function covering host+token+org*: rejected —
    org-id resolution legitimately differs by mode (interactive CLI/TUI use
    may prompt for org selection after a valid session is established; only
    *non-interactive systematic* runs must fail closed pre-emptively without
    a prompt). Splitting into two checks at their natural call sites avoids
    forcing interactive flows to require an org id before login, which would
    be a regression for legitimate interactive use.
  - *Validate in `MistSessionInitializer.initialize()` instead of
    `_establish_mist_session()`*: rejected — `_establish_mist_session()` is
    the single call site both the `--login` and token branches pass through,
    so putting the check there covers both branches with one change instead
    of two.

## R5. Iterative fix-verify loop protocol (User Story 4 / FR-018–FR-021)

- **Decision**: Document a 4-stage loop in `quickstart.md` (see that file for
  the runnable form) driven entirely by the existing gate runner script
  `scripts/wave1/run_wave1_gate.ps1` plus one additional live-evidence step:
  1. **Static gates** (safe to auto-repeat): `py_compile`, `ruff check`,
     `black --check`, targeted guardrail/unit pytest selection. All are
     read-only against the working tree and safe to re-run automatically
     after each source fix.
  2. **Full test suite** (safe to auto-repeat): `pytest --cov=src --cov=tests
     --cov-report=term-missing` — exercises registry/preflight/venv-guard
     unit tests without touching the network or real credentials.
  3. **Root-cause diagnosis on failure**: any failure in stage 1/2 is
     resolved by reading the failing assertion/traceback/log line, not by
     loosening the assertion or adding a suppression (Constitution "Security
     Findings: Fix Over Suppress" applies to the same spirit here even
     though these are functional, not security, gates).
  4. **Live credentialed run — external gate, not auto-repeated**:
     `python MistHelper.py --test` (the `misthelper_test` step already in
     `run_wave1_gate.ps1:18`) requires a real `.env` with a valid
     `MIST_APITOKEN`/`MIST_API_TOKEN` and reachable `MIST_HOST`. When
     credentials are unavailable in the current environment (e.g., this
     agentic/CI context), this step is explicitly treated as **blocked
     pending operator-supplied credentials** — the loop must not fabricate,
     request, or attempt to guess credentials, and must not loop
     indefinitely retrying a step that cannot succeed without external input.
     The plan's quickstart records the exact command an operator runs once
     credentials are available, and the exact evidence to attach (telemetry
     JSONL path printed by `_initialize_systematic_telemetry`,
     `MistHelper.py:4789-4798`, plus the pass/fail summary line from
     `_report_systematic_outcome`).
- **Rationale**: distinguishing "safe to auto-repeat" (stages 1-2, no
  external state, no network) from "external gate" (stage 4, requires a
  human-supplied secret) directly satisfies the requirement to "repeat only
  safe steps automatically" and "treat the eventual valid-credential run as
  an external gate."
- **Alternatives considered**:
  - *Mock/stub credentials to force stage 4 to "pass" in CI*: rejected —
    this would validate a fake success path, not the real fail-closed
    behavior the feature exists to guarantee; SC-006's "clean run" is
    defined as a live sweep with real credentials, which cannot be
    faked without defeating the point of the feature.

## R6. Test layers and exact commands (grounds FR-018/FR-021 and quickstart.md)

- **Decision**: Reuse the exact tool invocations already codified in
  `scripts/wave1/run_wave1_gate.ps1` (verified structure enforced by
  `tests/guardrails/test_wave1_gate_runner.py`) rather than inventing new
  command syntax:
  - `python -m py_compile MistHelper.py`
  - `python -m ruff check MistHelper.py src tests`
  - `python -m black --check MistHelper.py src tests`
  - `python -m mypy src --config-file pyproject.toml`
  - `python -m pytest --cov=src --cov=tests --cov-report=term-missing`
    (targeted subset for fast iteration:
    `pytest tests/guardrails/test_operation_registry_menu_coverage.py
    tests/guardrails/test_wave1_safety_classification_guardrails.py
    tests/bootstrap/ -v` — exact new test file paths added under Phase 2
    tasks)
  - `python MistHelper.py --test` (external gate, R5 stage 4)
- **Tooling confirmed from `pyproject.toml`**: ruff (`[tool.ruff]`, line
  length 120, py313 target), black (`[tool.black]`, line length 120, py313),
  mypy (`[tool.mypy]`, strict, `src` is the enforced target — MistHelper.py
  itself is under a `follow_imports = "skip"` override so mypy strictness
  applies to the new/changed `src/` modules, not to `MistHelper.py`'s
  existing untyped call sites), pytest (`[tool.pytest.ini_options]`,
  `testpaths = ["tests"]`, `-v --tb=short`), coverage
  (`fail_under = 90`, with a long-standing `omit` list that does not
  currently include the files this feature touches, so new code must carry
  real test coverage, not rely on `omit`).
- **Rationale**: reusing the existing gate runner as-is (rather than a
  parallel command set) means this feature's tests slot into
  `run_wave1_gate.ps1` and its guardrail test with zero changes required to
  either, other than adding new pytest files that the existing
  `pytest_cov` step already discovers via `testpaths = ["tests"]`.

## R7. Contracts applicability

- **Decision**: This feature is an internal defect-remediation/hardening
  change to a CLI tool with no externally-consumed network API of its own —
  `contracts/` in the SpecKit sense (request/response schemas for an
  HTTP/RPC surface) does not apply. However, the feature *does* define two
  durable internal behavioral contracts that other code and tests depend on,
  so two short contract documents are included instead of being skipped
  entirely: `contracts/operation_registry_classification_contract.md` (the
  category enum + fail-closed guarantee) and
  `contracts/preflight_failure_contract.md` (the credential/venv preflight
  failure message format, exit codes, and zero-HTTP guarantee). This matches
  the plan template's guidance to include contracts "only when appropriate"
  — appropriate here means "internal contract other tests/tasks must not
  silently violate," not "external API schema."
