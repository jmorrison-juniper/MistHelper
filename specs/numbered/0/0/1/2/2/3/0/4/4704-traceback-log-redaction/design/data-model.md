# Data Model: Traceback log redaction

## Log Record

`msg` and `args` produce the main message.
`exc_info` holds the exception type, object, and traceback.
`exc_text` holds rendered exception text and can come from an earlier handler.
The portal also reads `run_id` and `site_id`.

## State Changes

1. Read the main message through the existing formatting path.
2. Replace credential-shaped message values only when necessary.
3. If an exception has no cached text, render its complete chain.
4. Sanitize all cached exception text before handler formatting.
5. If any step fails, replace unsafe content with a safe diagnostic.

The filter keeps the original exception objects unchanged.
The standard formatter consumes the sanitized cache instead of rendering raw exception text again.
Unprotected handlers and formatters that deliberately ignore the standard cache are outside this contract.

Authorization matching consumes a scheme and value before ordinary credential replacement.
Neither rule crosses a line boundary.
A safe credential word at the end of an exception therefore leaves the complete chain separator unchanged.
