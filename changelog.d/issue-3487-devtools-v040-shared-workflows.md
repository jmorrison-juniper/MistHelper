### Development tooling on devtools release v0.4.0

- **Changed**: The development requirements pin release v0.4.0 of
  `misthelper-devtools`, and each caller of a shared workflow pins the same
  commit. The workflows for auto-merge, quality-gate issues, stranded branches,
  and STE lint now call the shared workflows of that repository. Issue #3487.
- **Removed**: The stranded branch script and the copies of the tests for the
  tools. The `stranded-branch-report` command of the package replaces the
  script. Issue #3487.
