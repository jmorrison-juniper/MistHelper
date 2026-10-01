### Preserve read-only retry evidence

- **Fixed**: `APIDataFetcher` retains each failed HTTP status when a later retry succeeds or all attempts fail.
  An absent status is explicit. Retry decisions, response identity, and delays remain unchanged. Part of #2752.
