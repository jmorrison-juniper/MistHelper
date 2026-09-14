### Fixed

- The portal now renews the site lock for the whole upgrade run. The operator
  takes the site on the capture page, before any run exists, so the stored lock
  named no run. The heartbeat refuses to renew a lock that names no run, so the
  lock expired about one minute into every run. A second operator could then
  take the site while the first run still wrote firmware. The run now names
  itself in the lock that protects it. Issue #2648.
