# Parity Contract: Main Decomposition Wave 2

## Purpose

Define deterministic, repeatable parity checks for all 9 decomposition phases so gate decisions are objective and auditable.

## Baseline Source Rules

1. Baseline data must be captured before any phase extraction begins.
2. Baseline artifacts must be stored under `specs/193-main-decomposition-wave-2/checklists/parity-baseline/`.
3. Baselines must include menu behavior traces, API response snapshots (sanitized), and backend output artifacts (CSV/SQLite/polyglot summaries).

## Comparison Dimensions

### 1) Menu Behavior Parity

- Same menu option routes to the same operation path.
- Same required prompts/confirmations are shown.
- Same success/error outcome class is produced for equivalent inputs.

### 2) API Output Parity

- Same endpoint intent and parameter shape.
- Same required keys present in response-derived records.
- No unexpected key removals unless explicitly approved and documented.

### 3) Backend Parity (CSV / SQLite / Polyglot)

- CSV: same header set and stable row invariants for equivalent runs.
- SQLite: same table names, expected primary-key semantics, and row invariants.
- Polyglot (ArangoDB/Redis): same record category intent and aggregate counts/invariants.

## Normalization Rules

- Normalize timestamps to comparable precision or exclude volatile timestamp fields.
- Exclude known nondeterministic fields (run IDs, transient UUIDs, generated file paths).
- Sort records by stable business keys before comparison.
- Redact secrets/tokens before writing artifacts.

## Fail Criteria (Hard Gate)

A phase parity check fails if any of the following occur:

1. Menu routing or required prompt flow drift.
2. Required API-derived keys missing or semantically changed.
3. Backend schema/header/key-contract drift not explicitly approved.
4. Unexpected record-loss beyond documented filter behavior.

## Pass Criteria

A phase parity check passes only when:

1. Menu, API, and backend dimensions all pass.
2. Evidence artifacts are recorded in:
   - `specs/193-main-decomposition-wave-2/checklists/phase-<N>-menu-parity.md`
   - `specs/193-main-decomposition-wave-2/checklists/phase-<N>-output-parity.md`
3. The phase gate file confirms parity pass status.

## Execution Notes

- Parity checks are mandatory at every phase and cannot be deferred.
- Any parity failure must be remediated in the same phase before signoff.
- No progression to the next phase is allowed on parity failure.
