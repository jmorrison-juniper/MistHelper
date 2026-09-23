### Fixed

- The web portal no longer walks the test output folders after each operation.
  The upgrade portal test suites write `data/test-artifacts/`, which grew to
  1,522 folders, and the output scan listed every one of them. Each operation
  waited about one minute for that walk. Measured in the container, the scan
  fell from 56 seconds to 8 seconds, and menu 229 fell from 104 seconds to 21
  seconds (#3201).

### Added

- A guard in `tests/unit/web_portal/test_output_scan_runtime_files.py` now
  fails when a test module names a test output folder under `data/` that the
  output scan does not prune. The scanner also publishes the count of folders
  that its last walk listed, so a test can prove that a pruned tree was never
  entered (#3201).
