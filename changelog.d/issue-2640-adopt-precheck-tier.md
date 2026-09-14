### Fixed

- A run now takes the data tier of the pre-check capture that it adopts. The
  upgrade button sends no tier, so a run that adopted a tier 3 capture kept
  tier 2. The post-check capture then held no radio row, no alarm row, no
  switch port row, and no power-over-ethernet row, and the comparison could not
  show an access point that returned from a firmware write with a radio down.
  Issue #2640.
