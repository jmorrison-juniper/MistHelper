# Research: Reject Conflicting Mist Token Values

## Decision

Reject two non-empty token variables when their normalized token lists differ. Accept one usable variable or equal values during migration.

## Rationale

The owner recorded this policy in issue #2861 on 2026-10-21. A conflict can select the wrong Mist identity. The existing parser already splits comma- and newline-separated token lists and removes surrounding whitespace.

Treat a value that normalizes to an empty list as absent. This preserves existing behavior for empty and delimiter-only configuration values.

## Alternatives Considered

- Prefer one variable silently when both differ. Rejected because it hides ambiguous identity configuration.
- Reject all use of the legacy variable. Rejected because the owner approved a migration period with equal values.
- Make token conflicts a warning. Rejected because the runtime could still select an unintended identity.

## Scope Boundary

This record covers only the MistHelper.py token candidate. It does not change SDK session tokens, other credential providers, or the remaining issue candidates.
