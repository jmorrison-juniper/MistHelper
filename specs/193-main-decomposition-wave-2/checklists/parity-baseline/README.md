# Parity Baseline Artifacts

This directory stores pre-refactor and per-phase parity artifacts used by the wave-2 hard gates.

## Required artifact sets

For each phase, capture and compare:

1. Menu behavior parity
2. API-derived output parity
3. Backend parity (CSV / SQLite / polyglot invariants)

## Suggested naming

- `phase-<N>-baseline-menu.md`
- `phase-<N>-baseline-output.md`
- `phase-<N>-comparison-menu.md`
- `phase-<N>-comparison-output.md`

## Contract reference

Use `specs/193-main-decomposition-wave-2/contracts/parity-contract.md` as the source of truth for normalization rules and pass/fail criteria.
