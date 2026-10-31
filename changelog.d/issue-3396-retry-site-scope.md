### Exact site scope for multi-site retries

- **Fixed**: A retry saves only sites with planned devices after family filtering.
  Confirmation, pre-checks, and locks use that saved scope without changing the operator selection. Issue #3396.
