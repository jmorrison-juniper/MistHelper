### Bound central database DNS discovery

- **Fixed**: Central database discovery uses a one-second caller budget and a 30-second positive and negative cache.
  Finite shared workers prevent repeated blocked DNS work.
  Central TCP probes reuse numeric addresses.
  ArangoDB, Redis, and capture-store preflights share DNS results without changing configured driver hostnames or URLs. Issue #3318.
