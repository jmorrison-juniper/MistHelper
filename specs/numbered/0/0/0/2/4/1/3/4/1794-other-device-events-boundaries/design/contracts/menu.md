# Menu failure boundary

Selection cancellation returns before any request.
Successful and empty results preserve their existing output behavior.
Endpoint and pagination exceptions return to the menu with fixed messages.
No writer runs after those exceptions.
Transform and writer exceptions reach the caller unchanged.
Exporter logs do not include exception text or tracebacks.

The real SDK contract tests replace the HTTP session, block network access, and use synthetic responses.
They cover first requests, subsequent pages, malformed pages, transport failures, and returned HTTP error statuses.
No new transport or external interface is introduced.
