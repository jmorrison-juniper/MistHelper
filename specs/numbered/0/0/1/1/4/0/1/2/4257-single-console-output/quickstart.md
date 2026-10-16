# Validate single console output

Use Python 3.13 or newer with the repository runtime and development requirements available.

```powershell
python -m pytest tests\unit\utils\test_console.py tests\unit\refactors\test_main_entrypoint.py -q
```

Expect single-copy output at DEBUG, INFO, and WARNING console thresholds.
Expect unchanged formatted messages, one file copy, and visible unrelated warnings and errors.

The integration tests render the actual menu with the bootstrap logging handlers.
Do not replace or restart the shared container for this check.
