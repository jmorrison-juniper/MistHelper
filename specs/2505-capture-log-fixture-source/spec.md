# Specification: Capture log fixture source

## Goal

Fix issue #2505. The capture tool must resolve each fixture site against the correct source file.

## Scope

The change applies to `tools/capture_log_baseline.py` and its unit tests.

## Required behavior

- A fixture site with a `source` value uses that source file.
- A fixture site without a `source` value uses the `--source` argument.
- The tool parses each distinct source file one time.
- The tool builds one call index for each parsed source file.
- The tool keeps the current JSON fields and exit codes.
- The tool keeps the current warning text for an unresolved fixture site.

## Error behavior

If a source file is missing, the tool logs a clear read error.
The tool then exits with code 1.
The tool must not print a traceback for that read error.

## Acceptance criteria

- The generated baseline includes the fixture sites that use `source`.
- The generated baseline includes the fixture site that uses `--source`.
- The tests cover both source resolution paths.
- The validation commands in the pull request pass.
