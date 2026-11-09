# Implementation Plan: Portal input privacy

## Scope

Replace the value-bearing input diagnostic with a constant diagnostic. Do not
change the queue, console fallback, or portal capture service.

## Validation

Use synthetic answers for direct queue tests and a portal execution test.
Check order, conversion, empty queues, console fallback, and concurrent queues.
Inspect both run logs and event payloads. Confirm that the diagnostic remains.

## Constraints

The established test directory and `changelog.d/` exceed five children. This
change adds one unique test module and one required release-note fragment.
Their separate structural remediation is outside this focused repair.
Existing input service structures remain unchanged.
