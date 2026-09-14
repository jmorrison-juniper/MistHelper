### Fixed

- The post-check capture now reads the same data tier as the pre-check capture
  of the same run. A tier 3 run kept no radio row, no alarm row, no switch port
  row, and no power-over-ethernet row in the second capture, so the comparison
  could not show an access point that returned from a firmware upgrade with a
  radio down. Issue #2624.
- The run history page now counts the devices of each run. Every row printed
  `0`, because the run list query returned no target list. The query now returns
  the length of that list. Issue #2625.
