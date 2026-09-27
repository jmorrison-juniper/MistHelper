### Benchmarks and analyzer settings in MistHelper

- **Changed**: The memory harness, the two overhead benchmarks, and the
  end-to-end store reset command are in `scripts/` again. Each one imports
  MistHelper product code, so the `misthelper-devtools` package could not run
  them. Issue #3466.
- **Changed**: The test quality ratchet reads its rule settings from
  `.github/test-quality-config.toml` in this repository instead of the copy
  inside the installed `misthelper-devtools` package. A change to that file
  makes the ratchet check the whole suite. Issue #3466.
