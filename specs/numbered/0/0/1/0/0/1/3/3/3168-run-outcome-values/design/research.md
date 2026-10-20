# Research: Explicit Portal Run Outcomes

## Decision

Use `src.foundation.models.operation_outcome.OperationOutcome` as the result contract. The alert digest handler already returns `no_output`, `missing_input`, `failed`, or `completed`.

## Rationale

The shared model validates its state and text fields. Reusing it avoids a second result type and lets menu 280 prove the migrated path.

## Alternatives Considered

- Add a portal-only result class. Rejected because it duplicates the existing contract.
- Replace marker matching for all handlers. Rejected because other handlers have not migrated.
- Add a test-only fake handler as the sole migrated example. Rejected because menu 280 already returns the production contract.

## Repository Evidence

- `src/mist/intelligence/reports/alert_digest/operation.py` returns an explicit empty-result outcome when no alarm rows exist.
- `web_portal/services/operation.py` currently discards handler return values and classifies empty results from log text.
- `tests/unit/web_portal/test_portal_silent_completion.py` covers the current marker path.

## Constraints

The PowerShell Spec Kit setup script is unavailable in this macOS worktree. The required route was derived with the same eight-digit base-five rule in `spec-route.ps1`. The active feature pointer remains unchanged.
