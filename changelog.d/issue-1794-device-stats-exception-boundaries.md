### Device statistics cache errors

- **Fixed**: Device statistics exports now report unexpected cache errors instead
  of treating them as cache misses. File metadata errors still trigger a fetch.
  Issue #1794.
