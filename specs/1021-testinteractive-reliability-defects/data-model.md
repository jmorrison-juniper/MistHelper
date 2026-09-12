# Data Model: `--testinteractive` Reliability

This is a behavioral/telemetry model for a future implementation. It does not
add a database, schema migration, or remote storage.

## Value objects

### RunTarget

| Field | Meaning | Validation |
|---|---|---|
| `requested_selector` | `MIST_INTERACTIVE_TEST_SITE`, if supplied | Trimmed; never treated as a partial match. |
| `resolution` | `exact_match`, `default_selection`, or `unresolved` | `unresolved` is terminal when a selector was supplied. |
| `site_id` | Actual selected site UUID | Required for a runnable suite. |
| `site_name` | Actual selected site name | Required whenever `site_id` is present. |

**Transitions**: `unresolved` terminates before the option loop. An empty
selector may retain the existing default-selection behavior. A supplied
selector can transition only to `exact_match` or `unresolved`; it must not
transition to `default_selection`.

### OperationIdentity

| Field | Meaning | Validation |
|---|---|---|
| `menu_option` | Registered interactive-safe option identifier | Must be present in the runner dispatch table. |
| `operation_name` | Operator-visible description | Must be non-empty. |

### OperationContext

| Field | Meaning | Validation |
|---|---|---|
| `site_context` | `injected` or `unavailable` | Derived once from the callable signature. |
| `site_id` | Site passed to the callable | Present only when `site_context` is `injected`. |
| `artifact_path` | Controlled local telemetry destination | Must resolve under `data/`; no external path is accepted. |

### OperationObservation

| Field | Meaning | Validation |
|---|---|---|
| `error_log_count` | `ERROR`+ records captured during this invocation | Non-negative; scoped to one handler call. |
| `input_termination` | `none`, `eof`, or `interrupt` | Produced by the canonical safe-input seam, not parsed from log text. |
| `exception_type` | Escaped exception class name, if any | Omitted for normal returns. |
| `duration_seconds` | Invocation wall-clock duration | Non-negative. |

### OperationOutcome

| Field | Meaning | Derivation |
|---|---|---|
| `identity` | OperationIdentity | Dispatch-table entry. |
| `context` | OperationContext | Signature inspection / run target. |
| `observation` | OperationObservation | Scoped observer and input observation. |
| `completion` | `clean`, `logged_error`, `raised_exception`, or `prompt_cancelled` | Deterministic precedence: exception, logged error, cancellation, clean. |
| `test_mode` | `interactive` | Fixed by this runner. |

`logged_error` and `raised_exception` are failure outcomes. `prompt_cancelled`
is reported distinctly rather than silently upgraded to `clean`; its exit-code
semantics remain limited to the requirements for the issue implementing it.

### RunSummary

| Field | Meaning |
|---|---|
| `target` | RunTarget used or unresolved selection state. |
| `clean_count` | Number of `clean` outcomes. |
| `failure_count` | Number of `logged_error` plus `raised_exception` outcomes. |
| `prompt_cancelled_count` | Number of `prompt_cancelled` outcomes. |
| `without_site_context_count` | Number of outcomes with unavailable site context. |

The suite returns a non-zero result when `failure_count > 0`. This prevents an
all-clean result whenever a handler logged an error, even if that handler did
not raise.

## Relationships

```text
InteractiveTestRun
  ├── 1 RunTarget
  ├── 1..N OperationOutcome
  │     ├── 1 OperationIdentity
  │     ├── 1 OperationContext
  │     └── 1 OperationObservation
  └── 1 RunSummary
```

## Compatibility

Existing JSONL telemetry is append-only. Future event fields are additive and
must not remove the existing identity, duration, test-mode, pass/fail, or
summary fields. Readers that do not understand the new fields can continue to
consume existing fields; updated readers use the explicit outcome/context
fields to avoid false-clean conclusions.
