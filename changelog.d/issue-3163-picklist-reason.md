### Fixed

- An empty selector in the portal now names the reason it holds no row. The
  site, device, and client selectors answered with an empty list and no
  explanation, so an operator read a blank control as a stalled portal. Each
  answer now names the cause. The causes are a missing API session, a missing
  organization identifier, an unchosen site, a failed Mist API call, or a true
  zero count. Issue #3163.
- The portal now reports a failed client lookup at the error level. The old
  code reported it at the debug level through the root logger, so an operator
  never saw the cause. Issue #3163.
