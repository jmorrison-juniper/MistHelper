### Concurrent operations portal requests

- **Fixed**: Simultaneous first requests share one operation executor per application instead of creating duplicate worker pools. Issue #4026.
