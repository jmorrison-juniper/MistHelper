# tasks.md

Dependency-ordered, atomic todos for 103-audit-menu-56-msp-info-guidance

Format per todo: id | title | description | path(s) | tests | estimate | acceptance

1) todo: add-msp-selector-class
- title: Add MSPSelector class and unit tests
- description: Create src/msp/selector.py implementing MSPSelector (choose, _format_list, _parse_choice). Add unit tests covering interactive parsing, retries, KeyboardInterrupt, and non-interactive selection via injected input_fn.
- paths: src/msp/selector.py, tests/unit/test_selector.py
- tests: test_selector_valid_choice, test_selector_invalid_retries, test_selector_keyboard_interrupt, test_selector_noninteractive_match, test_selector_noninteractive_not_found
- estimate: 2 (small)
- acceptance: All selector unit tests pass; selector.choose() returns dict for valid selection and raises RuntimeError after 3 invalid attempts.

2) todo: integrate-selector-into-misthelper
- title: Replace in-function prompt in MistHelper.py with MSPSelector usage
- description: Update MistHelper.py to construct MSPSelector using CLI args and env var; handle exceptions and translate to user messages and exit codes. Keep changes minimal and localized.
- paths: MistHelper.py
- tests: test_multiple_msps_valid_selection_exports (uses patched selector), test_keyboard_interrupt_during_selection
- estimate: 2
- acceptance: Unit tests reflect new call path; CLI behavior unchanged for interactive flows.

3) todo: add-cli-flags-and-parse
- title: Add --msp-id and --full-id CLI flags to argument parser
- description: Wire flags into existing CLI parsing logic. Document precedence (CLI > ENV). Update help text as in quickstart.
- paths: MistHelper.py (argparse section), docs/README or quickstart.md update
- tests: test_cli_msp_id_precedence_over_env
- estimate: 1
- acceptance: CLI --msp-id selects MSP non-interactively when provided.

4) todo: harden-api-response-validation
- title: Validate API responses and sanitize records
- description: After calling mistapi.v1.msps.orgs.listMspOrgs, assert response and response.data shape; coerce to list, ensure dict records, fill missing id/name placeholders, add msp_id/msp_name columns.
- paths: MistHelper.py (API handling block), tests/unit/test_api_returns_malformed_data_handles_gracefully.py
- tests: TC-007, TC-008
- estimate: 2
- acceptance: For malformed inputs tests, DataExporter.save_data_to_output is called with sanitized list and no uncaught exceptions.

5) todo: add-export-and-summary-formatting
- title: Implement safe short-id formatting and --full-id behavior
- description: Implement utility function format_org_id(org_id, full=False) and use it for summary display; ensure no slicing errors.
- paths: src/msp/formatting.py (small), MistHelper.py (calls), tests/unit/test_format_org_id.py
- estimate: 1
- acceptance: summary tests show truncated ids by default and full ids with --full-id.

6) todo: add-tests-and-ci
- title: Add unit & integration tests and CI job adjustments
- description: Add the unit tests listed in spec to tests/unit/ and integration test(s) to tests/integration/. Update CI workflow to run pytest and enforce py_compile check. Ensure DataExporter and mistapi are mocked to avoid real IO/network in unit tests.
- paths: tests/unit/*, tests/integration/*, .github/workflows/python-tests.yml (update)
- tests: all TC-001..TC-010
- estimate: 3
- acceptance: Tests run in CI; new CI job passes.

7) todo: update-logging-and-error-codes
- title: Improve logging and document exit codes
- description: Replace broad except with targeted exceptions; log full traceback at error level; print concise messages to user. Add constant EXIT_* codes and use them in MistHelper.py.
- paths: MistHelper.py, src/constants.py (new), tests/unit/test_export_io_error_logged_and_reported.py
- estimate: 1
- acceptance: Errors logged with traceback; user messages concise; tests assert logging called.

8) todo: docs-and-quickstart
- title: Deliver quickstart and update README
- description: Add quickstart.md (done) and add a short note to README explaining --msp-id and MISTHELPER_MSP_ID usage.
- paths: docs/README.md, specs/.../quickstart.md
- estimate: 1
- acceptance: README contains the example; quickstart.md present in spec dir.

CI Steps (to include in CI job description):
- python -m py_compile MistHelper.py
- pytest -q
- flake8 (optional if used in project)

Commit message template (use for each logical commit):

  git commit -m "103-audit-menu-56-msp-info-guidance: <short-description>\n\nversion YY.MM.DD.HH.MM - <description>\n\nCo-authored-by: <Name> <email>"

Notes:
- Keep commits small and logical per todo above. Use the branch: 103-audit-menu-56-msp-info-guidance
- Include Co-authored-by trailer when pairing.


End of tasks.md
