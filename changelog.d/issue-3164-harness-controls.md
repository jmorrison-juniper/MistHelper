### Changed

- Taught the end-to-end portal harness to answer a parameter control, so a test
  can run an operation that asks for a site, a device, or a client. Round 1 left
  20 operations untested, because the harness stopped at the disabled run
  control. The harness now reports an empty pick list and an unreadable option
  as defects of their own.
- Stopped the harness reporting a false defect for an operation the portal
  refuses on purpose. The portal hides the run control for an operation that
  needs a persistent keyboard and explains that in its place. The harness now
  reads the explanation first. See issue #3148.
