### Reject failed device discovery responses

- **Fixed**: Service ping discovery rejects HTTP error data before it can enter tenant or service caches. Issue #4512.
- **Changed**: Failed device statistics requests report an error and preserve valid configuration choices. Issue #4512.
