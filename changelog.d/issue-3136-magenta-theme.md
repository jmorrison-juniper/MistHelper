### Added

- The operations portal now ships the magenta brand theme, and it is the
  default. The palette comes from the upgrade capture portal, so the two
  portals on one host carry one brand identity. The three existing themes stay
  selectable and unchanged. Issue #3136.

### Fixed

- The open category heading is now readable in every theme. The heading took
  its color from the accent, and an accent is a fill color that needs 3:1 while
  text needs 4.5:1. Measured on the rendered page, the former accent gave
  4.27:1 on the light theme, 2.58:1 on the dark theme, and 2.60:1 on the high
  contrast theme. Each theme now names its own accent ink, and all four pass.
  Issue #3136.
