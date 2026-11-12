# Offline verification

Use the local locked development environment.
Do not use production credentials or start a real TUI.

Run the new regression module with sockets and DNS blocked before pytest starts.
Use `--confcutdir=tests/unit/config/foundation/support/refactors/runtime/console` to avoid unrelated application initialization.
The module supplies mocked runtime dependencies and TUI behavior.

```text
.venv/bin/python -m pytest --confcutdir=tests/unit/config/foundation/support/refactors/runtime/console tests/unit/config/foundation/support/refactors/runtime/console/test_tui_launcher_failure_status.py
```

The session export includes an offline runner that blocks network access before imports.
Use that runner for the recorded verification.
Confirm failure, normal return, interruption, session failure, debug behavior, and repeated launches.
See the [reporting contract](contracts/reporting.md) for exact expected messages.
