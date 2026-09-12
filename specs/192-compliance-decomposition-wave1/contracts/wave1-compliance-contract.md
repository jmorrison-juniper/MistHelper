# Contract: Wave 1 Compliance Guardrails

**Feature**: `specs/192-compliance-decomposition-wave1`

## 1) Safe Input Contract (Production Paths)

1. All in-scope production prompt reads MUST use `InputUtils.safe_input(prompt, context=...)`.
2. `context` MUST be explicit and traceable to the prompt path.
3. Normal valid-input behavior MUST remain unchanged from baseline.
4. EOF on in-scope production prompts MUST terminate cleanly without unhandled exceptions.

## 2) Entry Routing Invariant Contract

1. Existing in-scope menu/entry selection -> handler mappings MUST remain unchanged.
2. Guardrail tests MUST assert representative mappings (including boundary-adjacent IDs).
3. Any routing drift is a blocking failure for tranche progression.

## 3) Safety Classification Invariant Contract

1. Existing destructive vs non-destructive classification outcomes MUST remain unchanged.
2. Destructive operations in scope MUST continue to require explicit confirmation flow.
3. Any classification drift is a blocking failure for tranche progression.

## 4) Targeted Logging Envelope Contract

1. For each selected high-risk touched function, meaningful actions MUST emit:
   - pre-action `logging.info(...)`
   - post-action `logging.debug(...)` summary
2. Logs MUST NOT expose secrets or sensitive values.
3. Logging scope is intentionally limited to selected high-risk touched functions in Wave 1.

## 5) Inter-Tranche Verification Gate Contract

Each tranche gate MUST execute and pass all commands below before the next tranche starts:

1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py src tests`
3. `python -m black --check MistHelper.py src tests`
4. `python -m mypy src`
5. `python -m pytest --cov=src --cov=tests --cov-report=term-missing`
6. `python MistHelper.py --test`

**Failure semantics**: Any non-zero exit code is a hard stop. No downstream tranche work is permitted until gates are green.

## 6) Wave 1 Scope Boundary Contract

Wave 1 MUST NOT include:

- packet-capture decomposition,
- broad architecture redesign,
- global script-wide comment/logging sweep,
- behavior redesign unrelated to safety/compliance hardening.
