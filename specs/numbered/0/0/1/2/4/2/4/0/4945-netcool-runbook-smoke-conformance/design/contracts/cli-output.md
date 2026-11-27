# Contract: CLI Output and Evidence Keys

This contract fixes the operator-visible behavior of `python -m scripts.netcool_runbook_smoke`. The change must keep this behavior (FR-022, SC-007). The baseline comes from the fixed fake-session run in `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py`, recorded in task T003.

## Console lines

1. The console prints each summary line of the run in contract order. The class `RunReport` prints the lines. Its method `print_lines` is defined at `scripts/netcool_runbook_smoke/command.py` line 304 on `main`. After the change, the class lives in `scripts/netcool_runbook_smoke/__main__.py`.
2. The console prints no line that names a module path. A line that names a logger keeps the same text, because the logger prefix stays `scripts.netcool_runbook_smoke`.
3. Each line is ASCII. Principle V of the constitution requires ASCII output.
4. The exit code for each outcome stays the same. The baseline records the exit code of each fake-session outcome.

## Evidence keys

1. The evidence file holds the top-level keys that `EvidenceBuilder.build` creates. The builder is defined at `scripts/netcool_runbook_smoke/checks/__init__.py` line 595 on `main`. After the change, it lives in `scripts/netcool_runbook_smoke/checks/core/context.py`.
2. The metadata section keeps the name `netcool_runbook_smoke` and the module `scripts.netcool_runbook_smoke`. These values appear at `scripts/netcool_runbook_smoke/checks/__init__.py` lines 627 and 628 on `main`.
3. The default evidence path lies under `test-artifacts/netcool-runbook-smoke/`. The function `default_path` is defined at `scripts/netcool_runbook_smoke/documents.py` line 734 on `main`.
4. The file keeps its fixed form, and the output scan of the redactor still removes secrets and identifiers.

## Procedure

1. Run `python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py -q` before the first edit. Save the captured console lines and the evidence keys outside the repository.
2. Run the same command after each phase that changes the command path.
3. Compare the two captures. A difference in a console line, an exit code, or a top-level evidence key stops the change until the owner accepts the difference.
