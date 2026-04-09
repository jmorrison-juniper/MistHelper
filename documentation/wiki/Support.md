# Support

## Getting Help

1. Run with `--debug` and reproduce the issue
2. Inspect `data/script.log` (search for the failing menu ID)
3. Confirm token validity (does Menu 11 succeed?)
4. Try the alternate output backend (`--output-format csv` vs `sqlite`)
5. Open a [GitHub Issue](https://github.com/jmorrison-juniper/MistHelper/issues) with a log excerpt

**Important**: Redact org/site/device IDs if required by your organization's security policy.

## Quick Diagnostic Commands

```bash
# Check MistHelper version
python MistHelper.py --version

# Run a quick validation (non-destructive)
python MistHelper.py -M 11

# Enable debug logging
python MistHelper.py -M 11 --debug

# Run the full safe test suite
python MistHelper.py --test
```

## Reporting Issues

When opening an issue, include:
- MistHelper version
- Python version
- Operating system
- Output format (CSV or SQLite)
- Relevant log excerpt from `data/script.log`
- Steps to reproduce

See also: [Troubleshooting](Troubleshooting) for common issues and solutions.
