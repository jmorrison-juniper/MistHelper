# Implementation Plan: Safe, Repeatable MistHelper `--test` Clean-Run Workflow

**Branch**: `1020-safe-test-clean-run` | **Date**: 2026-07-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1020-safe-test-clean-run/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

An observed `MistHelper.py --test` run exited 1 after 48.5s having executed
nothing (no `.env` present), while separately revealing that
`OperationRegistry.get()` (`src/utils/operation_registry.py:310-317`)
defaults **any** unregistered `menu_actions` key to category `safe` — a
fail-**open** default that, with real credentials, would let a credentialed
`--test`/`--testinteractive` run silently invoke any of the 60 currently
unregistered menu options, including destructive menu **194** ("Clone
Device Config to Gateway Template"). The technical approach (fully grounded
in `research.md`) is:

1. Flip the registry default to fail-**closed** (new `unregistered` category
   in `SKIP_CATEGORIES`) and add explicit `_REGISTRY` entries for all 60
   currently-unregistered keys, so both `--test` and `--testinteractive`
   uniformly refuse to run anything not explicitly classified `safe`/
   `interactive_safe` — while keeping genuinely safe read-only exports
   eligible, not accidentally downgraded to skips.
2. Replace the brittle, hand-maintained 11-key
   `WAVE1_ENTRY_ROUTING_BASELINE` sample with a new exhaustive
   `registered_options()`-based coverage guardrail that fails the instant
   `menu_actions` and `OperationRegistry` diverge in either direction.
3. Add an isolated-venv precondition to `DependencyCheckOrchestrator`
   (`src/bootstrap/dependency_check.py`) that blocks automatic
   install/upgrade into system Python by default, distinguishing (in
   message text) "no `.venv`" from "broken `.venv` launcher," while
   preserving the existing `DISABLE_AUTO_INSTALL` opt-out untouched.
4. Add a two-part credential/config preflight — (a) a host/token check at
   the top of `_establish_mist_session()` shared by every mode, and (b) a
   non-interactive org-id guard inside self-contained `ConfigUtils` — that
   fails closed with a redacted, actionable message referencing
   `deploy/.env.example` (and the *actual* variable names the code reads)
   strictly before any `mistapi`/`requests` call can occur.
5. Define exact, reused (not invented) test-layer commands from the
   existing `scripts/wave1/run_wave1_gate.ps1` gate runner, plus new
   guardrail/unit tests for the above.
6. Document a 4-stage iterative loop protocol (static gates → full suite →
   root-cause diagnosis → live credentialed run) that auto-repeats only the
   first two, network-free stages and treats the credentialed
   `MistHelper.py --test` run as an external gate, honestly reported as
   "externally blocked" rather than a false "clean run achieved" when
   credentials are unavailable.

This plan is design-only: no production code is modified by this command.
See `research.md` for full Decision/Rationale/Alternatives detail per area,
`data-model.md` for the concrete entity shapes involved, and
`contracts/` for the two durable internal behavioral contracts this feature
establishes.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution and `pyproject.toml` py313 target).

**Primary Dependencies**: mistapi 0.63.1+, requests, pytest/pytest-cov, ruff/black/mypy (no new dependency added).

**Storage**: N/A (no schema changes; existing JSONL telemetry under `data/` via `TelemetryEmitter`, unchanged shape — see `data-model.md` §3).

**Testing**: pytest (`testpaths = ["tests"]`); new tests are unit/guardrail-only (no `integration` marker; zero credentials/network).

**Target Platform**: Cross-platform CLI (Windows/PowerShell primary; Linux/macOS via existing Containerfile/Dockerfile).

**Project Type**: single (CLI application `MistHelper.py` + `src/` package; web surfaces under `ops-portal`/`web_portal` are out of scope).

**Performance Goals**: N/A (correctness/safety fix, not a performance feature).

**Constraints**: zero outbound HTTP calls from new preflight logic/tests (SC-004, SC-008); zero secret values in output/logs/telemetry (SC-005, reuses existing `_redact_tokens()`); no over-classification of safe exports into skip categories; must not break the existing `scripts/wave1/run_wave1_gate.ps1` 6-step structure.

**Scale/Scope**: 197 `menu_actions` entries (137 registered today, 60 to be newly registered); 2 systematic test modes; 2 new preflight insertion points; 1 new venv-guard predicate; 1 new exhaustive coverage guardrail test file.

<!--
  Expanded detail for the fields above (kept out of the single-line values
  so the SpecKit agent-context extraction script, which reads only the
  first line after each `**Field**:` marker, does not truncate them):

  - Language/Version: constitution Technology Constraints section and
    `pyproject.toml` `requires-python`/ruff+mypy `py313` target both pin
    Python 3.13+.
  - Primary Dependencies: `mistapi` is pinned 0.63.1+ in `pyproject.toml`
    (spec text says "0.59+"; the repo's actual pin is authoritative).
    `requests` remains used only by the existing, untouched token
    rate-limit probe (`_check_token_rate_limit()`). No new third-party
    dependency is introduced by this feature.
  - Storage: no database/schema changes. Telemetry continues to be written
    to existing JSONL files under `data/` via `TelemetryEmitter`.
  - Testing: two test categories are in play — (a) always-runnable
    unit/guardrail tests (registry coverage, preflight logic, venv
    predicate — zero credentials, zero network) and (b) the pre-existing
    `integration` pytest marker for anything needing live credentials; this
    feature adds no new `integration`-marked tests. The live `--test`/
    `--testinteractive` runs remain a manual/operator-driven external gate,
    not a pytest-collected test.
  - Target Platform: no platform-specific behavior is introduced;
    `os.path.join`/`pathlib.Path` conventions are preserved for any new
    path handling (none anticipated — this feature is control-flow/logic
    only).
  - Project Type: the safety defects addressed are specific to the
    `--test`/`--testinteractive` systematic CLI paths; `ops-portal`/
    `web_portal`/`mist-ops-platform` web surfaces are unrelated and
    untouched.
  - Performance Goals: the observed defect run's ~48.5s duration is a
    baseline reference only from the spec's narrative, not a target this
    feature optimizes.
  - Scale/Scope: no change to the number of supported sites/orgs/devices —
    unrelated to this feature's scope.
-->

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate evaluation |
|---|---|
| **I. Five-Item Rule** (functions/classes stay small, single-responsibility, ≤5 major branches/collaborators as a guideline) | **PASS.** Each new unit is a small, single-purpose addition: `OperationRegistry.registered_options()` (one-line accessor), the new `unregistered` fallback branch inside the existing `get()` (no new branching structure, just a changed literal), `_is_running_in_isolated_venv()` (single boolean predicate, mirrors existing `_is_auto_install_disabled()`), `_preflight_verify_credentials()` (single validate-and-exit-or-continue function), and the `ConfigUtils` non-interactive org-id guard (one added conditional inside an existing method). None of these introduce a god-function or god-class. |
| **II. Class-Based Architecture** | **PASS.** All changes extend existing classes (`OperationRegistry`, `DependencyCheckOrchestrator`, `ConfigUtils`) or add module-level helper functions colocated with existing peers (`_establish_mist_session()`'s siblings in `MistHelper.py`) — no new bare/global mutable state is introduced. |
| **III. Safety-First (NON-NEGOTIABLE)** | **PASS — this principle is the direct subject of the feature.** The fail-open→fail-closed registry default, the exhaustive coverage guardrail, the destructive-confirmation preservation for menu 194 (unchanged, still requires typed `'CREATE'`), and the credential/venv preflights are all safety-hardening measures that strictly narrow, never widen, what can execute automatically. No new destructive automatic behavior is introduced. |
| **IV. Full Deployment Pipeline (NON-NEGOTIABLE)** | **PASS — reused, not bypassed.** This feature reuses the existing `scripts/wave1/run_wave1_gate.ps1` 6-step pipeline (`py_compile`→`ruff`→`black_check`→`mypy`→`pytest_cov`→`misthelper_test`) verbatim; no step is skipped, weakened, or replaced by a parallel ad hoc pipeline. |
| **V. Observability & Logging** | **PASS.** The registry fallback emits an actionable warning (as it does today, just with a corrected category); the credential preflight prints a clear, redacted remediation message; the venv guard prints a diagnostic distinguishing missing-vs-broken `.venv`. No new logging framework is introduced — existing `logging`/telemetry conventions (`TelemetryEmitter`, `_redact_tokens()`) are reused. |
| **VI. Inline Comments (NON-NEGOTIABLE)** | **PASS (implementation-time requirement, carried forward).** `research.md`/`data-model.md` document the "why" for every non-obvious change (e.g., why two preflight insertion points instead of one; why `sys.real_prefix` fallback; why the `MIST_ORG_ID` naming nuance must be avoided in remediation text) so implementation tasks can translate these directly into inline comments at the actual code sites, per this principle's requirement that non-obvious logic carry a brief "why" comment. |
| **VII. Action Logging (NON-NEGOTIABLE)** | **PASS.** No new state-mutating action is introduced by this feature (it only narrows what *can* run); the existing action-logging conventions for any operation that does run (e.g., destructive menu 194's existing confirmation/logging) are unchanged. The preflight/guard functions themselves are read-only checks, not loggable mutating actions. |

**Result**: No violations. `Complexity Tracking` below is empty — no
justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/1020-safe-test-clean-run/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── operation_registry_classification_contract.md
│   └── preflight_failure_contract.md
├── checklists/
│   └── requirements.md  # Pre-existing quality checklist (already passing)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

This is a single CLI project (Option 1 shape), using the concrete existing
layout below rather than the generic placeholder tree. Only files actually
touched or added by this feature are marked `[MODIFY]`/`[NEW]`; everything
else is existing, unrelated code shown for orientation only.

```text
MistHelper.py                                  # [MODIFY] _establish_mist_session() (~line 5201): add
                                                #   host/token preflight call at top, before session init.
                                                #   No change to _early_dependency_check() call site (line 950).

src/
├── utils/
│   └── operation_registry.py                  # [MODIFY] get() (310-317): fail-closed default via new
                                                #   "unregistered" category; add 60 new _REGISTRY entries;
                                                #   [NEW] registered_options() classmethod.
├── bootstrap/
│   └── dependency_check.py                    # [MODIFY] DependencyCheckOrchestrator: [NEW]
                                                #   _is_running_in_isolated_venv() predicate + new
                                                #   _ENV_* override var, wired into run().
├── config/
│   └── config_utils.py                        # [MODIFY] _resolve_org_id_via_prompt() /
                                                #   get_cached_or_prompted_org_id() (92-137): add
                                                #   non-interactive fail-closed guard before
                                                #   mistapi.cli.select_org(...).
├── refactors/
│   ├── run_systematic_test.py                 # Unchanged — consumes corrected safe_options() output.
│   ├── run_interactive_test.py                # Unchanged — consumes corrected interactive_safe_options().
│   ├── main_entrypoint.py                      # Unchanged — call-order reference only (confirms
                                                #   _establish_mist_session() runs before dispatch for all modes).
│   └── initialize_mist_session.py              # Unchanged — call-order reference only (confirms this is
                                                #   where the real APISession(...) HTTP call happens).
└── org/
    └── org_ticket_manager.py                   # Unchanged — read for classification evidence only
                                                #   (menu 189-192 write-behavior verification).

tests/
├── guardrails/
│   ├── test_operation_registry_menu_coverage.py        # [NEW] exhaustive key-parity coverage guardrail.
│   ├── test_wave1_safety_classification_guardrails.py  # [MODIFY] correct the "9999" sentinel entry.
│   ├── test_wave1_entry_routing_guardrails.py          # Unchanged — retained as a secondary smoke check.
│   └── test_wave1_gate_runner.py                       # Unchanged — validates the reused gate script.
└── bootstrap/
    └── test_dependency_check_venv_guard.py             # [NEW] unit tests for the isolated-venv predicate.

deploy/
└── .env.example                                # Unchanged (referenced by remediation text only; the
                                                #   MIST_ORG_ID vs org_id naming nuance is documented in
                                                #   research.md, not fixed by this feature).

scripts/wave1/
└── run_wave1_gate.ps1                          # Unchanged — reused verbatim as the test-layer command set.
```

**Structure Decision**: Single-project CLI structure (no `backend`/
`frontend` split applies — the web surfaces under `ops-portal`/
`web_portal`/`mist-ops-platform` are unrelated to this feature and are not
touched). All changes are additive/corrective within the existing
`src/utils`, `src/bootstrap`, `src/config` packages and `tests/guardrails`,
`tests/bootstrap` test packages, following the existing package boundaries
exactly (no new top-level package is introduced).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified — table intentionally left empty.
