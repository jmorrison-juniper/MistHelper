### Required Mist API token resolution

- **Fixed**: The backend rejects missing, blank, and non-string tokens before session construction.
  Unusable cache and Vault values permit the next configured source.
  Accepted token values, provider order, cache behavior, and exception handlers remain unchanged.
  Part of issue #2861.
