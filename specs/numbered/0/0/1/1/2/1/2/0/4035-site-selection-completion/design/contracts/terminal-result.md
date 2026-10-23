# Terminal Result Contract

Menu 92 completes when its handler returns a nonblank string identifier.
The portal reports `Site selection completed. No output file is required.`
The output list can remain empty. REST and SSE retain their existing response fields.

A missing, blank, or non-string result does not prove selection.
A different menu cannot use a string result to bypass export evidence checks.
Existing typed outcomes remain authoritative.
Handler exceptions remain failures.
The shared selector still returns a site identifier or `None`.
