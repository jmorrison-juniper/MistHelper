# Initial response decision

## Decision

Require a non-Boolean integer status from 200 through 299 before either initial response enters pagination.

## Rationale

Native SDK transport failures retain `status_code=None`.
The previous helper changes missing and malformed values into 200.
The list endpoint has no initial status check.
Both paths can therefore turn a failed response into an empty-result notice.

## Alternatives considered

Changing shared pagination would affect other exporters and later pages outside the assigned scope.
Retaining statusless successful doubles would preserve the false-success path.
Logging arbitrary malformed values could disclose untrusted response content.
Use fixed missing-status wording instead.

## Coordination

The coordinator assigned `tests/unit/export/test_issue_3188_webhook_id_selection.py` to this branch.
Only its successful response doubles need a valid status.
Retain its original selection and exception assertions.
