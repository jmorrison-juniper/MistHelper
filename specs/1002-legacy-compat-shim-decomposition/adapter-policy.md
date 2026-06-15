# Adapter Policy

## Allowed temporary adapters

Temporary adapters are allowed only when immediate removal would break behavior parity or test harness stability.

## Mandatory metadata

Every temporary adapter must define:

1. explicit expiry date
2. explicit removal trigger
3. owner
4. rollback note

## Mandatory guardrails

- Adapter use must be logged in `adapter-expiry-ledger.md`.
- CI must fail on retired symbol references.
- New fallback/shim growth is disallowed unless explicitly approved and tracked.

## Removal criteria

An adapter must be removed once:

- canonical callsites are complete,
- parity tests pass,
- migration tracker marks dependent tests as migrated.
