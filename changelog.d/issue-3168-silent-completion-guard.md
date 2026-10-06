### Fixed

- The web portal now reports a failed run when an operation logs `No org_id available`. Issue
  #3168 recorded that a missing organization identifier reported `Complete` with no output file.
  The classifier reads the missing-input markers before the broad no-output marker.
- The two portal silent-completion guards now reject a zero scope. Issue #3168 recorded that each
  guard printed a count and then passed on an empty scope.

Caution: this repair still matches the log prose, so it is an interim repair. A new message with
different wording can return the same defect. The full repair is the typed `OperationOutcome`
object, and it belongs to a later change behind a written specification.
