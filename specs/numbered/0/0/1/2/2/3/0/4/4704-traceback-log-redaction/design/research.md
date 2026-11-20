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

## Independent Findings

The original separator used `\s`, which includes newlines.
A safe exception ending in `Invalid token` could therefore consume the start of the next chain separator.
Restrict ordinary value separators to horizontal whitespace.

The original key rule matched only `auth` within `Authorization`.
The remaining letters stopped the required separator from matching.
Add the complete key and a dedicated rule for a scheme and its value.
Apply that rule before the ordinary value rule.
Match header names without case sensitivity.
Keep the rule on one line and retain cached exception protection.
Issue #4705 owns this additional labeled-header gap.
Arbitrary unlabeled secrets remain outside the protection contract.

## Structured Header Decision

Digest and AWS4 values contain several parameters, quoted strings, and commas.
A scheme-plus-token rule leaves later parameters visible.
Redact through the end of the labeled line instead.
Do not cross CR or LF.
This intentionally removes any same-line diagnostic after a header.
Tests must prove that subsequent diagnostic lines and safe exception chains remain complete.
