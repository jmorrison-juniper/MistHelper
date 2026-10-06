### Fixed

- The session teardown of the end-to-end suite has a budget of its own. A slow
  teardown does not take the 120 second budget of the final test. The run keeps
  the pytest report (issue #3517).
- The end-to-end suite appends one JSON record for each pytest phase to a file
  in `test-artifacts/`. A terminated run keeps the name and the result of each
  test (issue #3517).
