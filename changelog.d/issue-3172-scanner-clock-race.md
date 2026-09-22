### Fixed

- The portal result panel no longer loses a report that an operation wrote. The
  run-start mark came from the wall clock, and a file carries a time from the
  filesystem clock. The two clocks disagree, so a report written right after the
  mark could carry a time before it. The mark now comes from a probe file, so
  one clock dates the mark and every report. Measured over 1500 runs, the loss
  rate fell from 0.80 percent to zero. Issue #3172.
