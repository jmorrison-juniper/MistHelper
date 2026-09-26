### Test quality baseline in MistHelper

- **Changed**: The test quality ratchet compares each run against
  `.github/test-quality-baseline.json` in this repository instead of the copy
  inside the installed `misthelper-devtools` package. A change to that file
  makes the ratchet check the whole suite. The file drops 335 entries that
  matched no current finding, so the gate reports a repaired finding that
  comes back. Issue #3422.
- **Fixed**: Git ignores `test_quality_analyzer_output/`, so a local analyzer
  run no longer leaves its report as an untracked change. Issue #3421.
