# AP warning report validation

Use the worktree virtual environment.
Run the isolated tests without production credentials:

```powershell
rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report -q
rtk proxy .venv\Scripts\python.exe -m ruff check src\operations\exporting\ap_warning_report tests\unit\ap_warning_report tests\integration\ap_warning_report
rtk proxy .venv\Scripts\python.exe -m black --check src\operations\exporting\ap_warning_report tests\unit\ap_warning_report tests\integration\ap_warning_report
```

Expected results: every test passes, no lint errors, and no format changes.
The integration tests use the real CSV and SQLite writers.
Each test writes to its temporary directory, not the product data directory.
The SQLite test verifies replacement without duplicate organization-and-MAC identities.
See [the gate evidence](../analysis.md) for the broader regression selection and source checks.
Run the repository test-quality procedure after committing the intended tests.

Menu 307 runs the report from the command line or the portal.
Confirm the number in the generated menu reference before execution.
Use the existing organization selection and output format prompts.
Review the report timestamp before treating historical trouble evidence as a current failure.
