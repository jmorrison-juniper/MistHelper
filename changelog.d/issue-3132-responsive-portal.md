### Added

- The operations portal now fits a phone, a tablet, and a wide desktop. A new
  stylesheet holds the breakpoints, the touch target sizes, and the stacked
  layout rules. Issue #3132.
- A stacked layout now offers a "Back to the list" control, and it holds the
  run controls against the bottom edge, so the primary action stays reachable.
  Issue #3132.

### Fixed

- Selecting an operation on a phone now shows that operation. The list and the
  run panel stack below 768 pixels, so the Run button sat 609 pixels below the
  fold of a 390 by 844 screen and the page appeared to do nothing. The whole
  panel now fits on one screen after a selection. Issue #3132.
- A control that an operator presses now measures at least 44 pixels on a touch
  screen. The Run button rendered 38 pixels tall. Issue #3132.
