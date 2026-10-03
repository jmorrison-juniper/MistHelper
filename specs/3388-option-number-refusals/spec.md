# Option Number Refusals

## Goal

Reject superscript digits and oversized digit strings before integer conversion.

## Scope

- Keep existing business ranges and defaults.
- Use the shared numeric reader for finite fields.
- Use the active Python representation limit for unbounded fields.
- Return the existing `BadOptionError` without the typed value.

## Acceptance

- Superscript digits produce a named option refusal.
- Values longer than the active or finite representation limit produce a named refusal.
- Valid boundaries remain accepted.
- Stored epoch replay does not apply a clock window when no clock exists.
