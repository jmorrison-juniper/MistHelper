### Fixed

- The capture history page narrowed the run list and the capture list to one
  site, and the audit log still showed rows for other sites. The audit log now
  obeys the same site. The expiry inference still reads the whole trail, so the
  inferred rows do not change. Issue #2596.
