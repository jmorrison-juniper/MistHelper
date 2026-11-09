# Research: Traceback log redaction

## Decision

Keep the filter's in-place message behavior.
Render missing exception text with the standard logging formatter.
Apply the existing redaction pattern to both new and cached exception text.

## Rationale

`LogRecord.getMessage()` does not include exception text.
`Formatter.format()` appends `exc_text` after the message and caches it on the shared record.
A previous handler can therefore supply raw cached text.
The filter must sanitize that cache even when it did not create it.
Standard exception rendering includes explicit causes, implicit context, exception notes, and exception groups.

The real portal reproduction on the unchanged source reported:

```text
Main message redacted: True
Synthetic token remains in portal traceback: True
Portal traceback present: True
```

The existing focused tests passed: `25 passed, 1 warning`.
Those tests did not send traceback information through the handler.

## Alternatives Considered

- Per-caller redaction leaves other callers unprotected and violates the requested boundary.
- Removing exception information loses useful diagnostics.
- Clearing only the cache lets the formatter create another raw traceback.
- A new formatter requires changes to handler installation and leaves other filter users unprotected.
- Record replacement changes the existing filter contract and is not necessary for standard handler protection.

## Failure Safety

If message or traceback rendering raises, clear exception and stack fields.
Keep only the redaction error type in the replacement diagnostic.
Do not include the error value because it can contain another credential.
