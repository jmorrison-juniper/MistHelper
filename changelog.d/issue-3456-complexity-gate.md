### Shared complexity gate

- **Changed**: The Radon job pipes its JSON report into the `complexity-gate`
  command of `misthelper-devtools` instead of an inline script. The limit stays
  at 10. Issue #3456.
- **Fixed**: When radon cannot parse a file, the job fails with a report line
  that names the file, instead of with a Python traceback. Issue #3456.
