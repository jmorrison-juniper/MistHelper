# Specification: Capture log baseline index

## Goal

Optimize the capture log baseline tool for the real `MistHelper.py` source.
The tool must keep the same rendered JSON output.
The tool must stay sequential.

## Workload

Run `tools.capture_log_baseline` with `--source .\MistHelper.py`.
Write the output JSON to a session artifact.
This input is the production source path for the tool.

## Acceptance criteria

- Measure the unmodified code before any application edit.
- Retain the change only if the end-to-end median wall time improves by at least 5 percent.
- Keep the rendered baseline output byte-identical for the same source file.
- Keep the first call chosen when more than one call starts on one line.
- Do not add parallel execution.
