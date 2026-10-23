# Data Model: Site selection completion

The existing run record retains `handler_outcome` until terminal assessment.
For menu 92 only, a nonblank string represents a selected site identifier.
The portal maps it to the existing `OperationOutcome` completed state.
The completion message does not expose the identifier.

No persistent schema changes.
Invalid selections retain the legacy failure assessment.
Exceptions retain the existing failure path.
Explicit empty-result outcomes and legacy empty-result reasons retain their existing completion paths.
