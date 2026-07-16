# Quickstart: Validating the Safe `--test` Clean Run Feature

**Feature**: `1020-safe-test-clean-run`

This is a runnable validation guide, not an implementation spec (see
`plan.md`/`research.md`/`data-model.md`/`contracts/` for design). All
commands are PowerShell, run from the repository root, and reuse the
existing gate-runner conventions in `scripts/wave1/run_wave1_gate.ps1`
rather than inventing new tooling.

## Prerequisites

- Python 3.13+ activated inside a real virtual environment
  (`.venv\Scripts\Activate.ps1`) — required by this very feature's venv
  guard once implemented; verify with:

  ```powershell
  python -c "import sys; print(sys.prefix != sys.base_prefix)"
  ```

  This MUST print `True` before continuing.
- Dependencies installed: `pip install -r requirements.txt` (or `uv sync` if
  using UV, per constitution's tooling preference).
- No real credentials are required for Stages 1-2 below. Stage 3 (live
  credentialed run) requires a valid `deploy/.env` copied from
  `deploy/.env.example` with a real `MIST_HOST`, `MIST_APITOKEN` (or
  `MIST_API_TOKEN`), and `org_id` — see `contracts/preflight_failure_contract.md`
  for the exact variable names the code reads (note: `deploy/.env.example`'s
  `MIST_ORG_ID` is not the variable this code path consumes; use `org_id`).

## Stage 1 — Static gates (safe to re-run automatically after every fix)

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src tests
python -m black --check MistHelper.py src tests
python -m mypy src --config-file pyproject.toml
```

Expected: all four commands exit 0. On failure, fix the exact reported
line/rule; do not add suppressions/`# noqa`/`# type: ignore` without a
justifying comment (Constitution VI/Security Findings policy).

## Stage 2 — Targeted guardrail tests, then full suite (safe to re-run automatically)

```powershell
# Fast, targeted — run first during iteration:
python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py -v
python -m pytest tests/guardrails/test_wave1_safety_classification_guardrails.py -v
python -m pytest tests/guardrails/test_wave1_entry_routing_guardrails.py -v
python -m pytest tests/unit/test_operation_registry_fail_closed.py -v          # fail-closed default (US1)
python -m pytest tests/unit/test_systematic_test_unregistered_semantics.py -v  # skip/telemetry semantics (US1)
python -m pytest tests/bootstrap/test_dependency_check_venv_guard.py -v         # venv preflight unit tests (US2)
python -m pytest tests/unit/test_credential_preflight.py -v                     # credential preflight (US3)
python -m pytest tests/unit/test_config_utils_org_id_preflight.py -v            # org-id preflight (US3)

# Full suite with coverage gate (fail_under = 90 per pyproject.toml):
python -m pytest --cov=src --cov=tests --cov-report=term-missing
```

Expected: `test_operation_registry_menu_coverage.py` asserts exhaustive
key-parity between `MistHelper.menu_actions` and
`OperationRegistry.registered_options()` — this is the durable coverage
guardrail (see `research.md` R2 / `contracts/operation_registry_classification_contract.md`).
All new/updated tests pass with zero real network calls (verify no test in
this run is marked `integration`: `python -m pytest --collect-only -m integration`
should list none of the new tests).

## Stage 3 — Diagnose failures at the root cause

If any Stage 1/2 command fails:
1. Read the exact failing line/assertion/traceback.
2. Fix the underlying code (registry entry, preflight logic, venv predicate)
   — never loosen an assertion or add a blanket skip to make the gate pass.
3. Re-run only the failed command(s) from Stage 1/2 (fast inner loop); once
   green, re-run the full Stage 1 + Stage 2 sequence once before moving on.
4. Repeat until Stage 1 and Stage 2 are both fully green. These two stages
   are the "safe steps" that may be repeated automatically without human
   input, per FR-021.

## Stage 4 — Live credentialed run (external gate — NOT auto-repeated)

```powershell
python MistHelper.py --test
```

- Requires a real `deploy/.env` with valid, reachable credentials (see
  Prerequisites). This is the only step in this quickstart that performs a
  real HTTP call.
- If credentials are unavailable in the current environment, this step is
  **blocked pending operator action** — record that fact and stop; do not
  fabricate credentials, do not loop retrying this step automatically, and
  do not weaken the credential preflight (Stage 1 gates) to force this step
  to "pass" without real credentials.
- On a successful run, capture as evidence:
  - The console pass/fail summary line (from `_report_systematic_outcome`).
  - The telemetry JSONL file path printed at start
    (`_initialize_systematic_telemetry`, written under `data/`).
  - Confirm the summary shows **zero** unexpected skips attributable to
    `unregistered` classification (i.e., every skip has a real, named
    category — `destructive`, `wip`, `resource_intensive`, etc. — not a
    silent fail-open `safe` misclassification, and not an unexplained
    `unregistered` skip that should have been explicitly classified).
- Repeat the analogous check for `--testinteractive`:

  ```powershell
  python MistHelper.py --testinteractive
  ```

## Full gate (equivalent to CI)

```powershell
pwsh scripts/wave1/run_wave1_gate.ps1
```

This single script runs the `py_compile` → `ruff` → `black_check` → `mypy` →
`pytest_cov` → `misthelper_test` sequence in the exact order validated by
`tests/guardrails/test_wave1_gate_runner.py`. Stages 1-2 above map to the
first five steps (auto-repeatable); `misthelper_test` maps to Stage 4 (the
external, credentialed gate).

## Success criteria mapping (traceability to `spec.md`)

| Quickstart stage | Spec success criteria covered |
|---|---|
| Stage 2 (coverage guardrail) | SC-001, SC-002, SC-003, SC-008 |
| Stage 2 (credential preflight tests) | SC-004, SC-005 |
| Stage 4 (`--test`/`--testinteractive` live run) | SC-006, SC-007 |
| Stage 3 (diagnosis discipline) | SC-009 |
