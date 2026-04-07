# Contract: API Interactions

- Use existing `mistapi` client wrappers for all Mist API calls.
- All API writes MUST be idempotent where possible and retried per `request_with_retries()`.
- Any API call that modifies site or template state MUST be logged with the full request and success/failure result in `OperationsLog` (redact secrets).
- Bulk operations should be rate-limited and use batching where supported.

