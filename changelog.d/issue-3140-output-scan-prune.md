### Fixed

- Cut the portal operation overhead from about 26 minutes to 35 seconds. The
  output scanner walked every entry under the data directory and did so twice
  for each operation. On a 19.9 GB data directory that cost about 17 minutes of
  pure directory reading per run, and the status stayed at `running` with zero
  progress for the whole time. The scanner now skips the large read-only trees
  and reads the directory once. See issue #3140.
- Stopped one operation from claiming the output files of another. The scanner
  reported every file that changed while a run was open, so two runs at the same
  time each listed the other's reports. A file now reaches the panel only when
  its modification time falls after the run started. See issue #3140.
