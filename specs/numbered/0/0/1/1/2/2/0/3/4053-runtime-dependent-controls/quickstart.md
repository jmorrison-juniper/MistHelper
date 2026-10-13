# Quickstart: Runtime-Dependent Portal Controls

## Prerequisites

- Set up the worktree with `python3 scripts/bootstrap_worktree.py`.
- Use mocked Mist responses and temporary local files.
- Do not set a production Mist token for these tests.

## Run Focused Tests

```sh
python -m pytest tests/unit/reports/test_issue_4053_manufacturer_input.py tests/unit/site/address_audit/test_issue_4053_csv_choices.py tests/unit/web_portal/test_issue_4053_runtime_answers.py tests/e2e/web_portal/test_issue_4053_runtime_controls.py tests/e2e/web_portal/test_issue_4029_device_controls.py
```

Expected result: all selected tests pass. The test output must include the E2E checks for menus 91 and 195 and the existing controls for menus 94 through 96.

## Verify the Menu Form

1. Create more than one temporary CSV or TSV under a temporary `data/` directory.
2. Request menu 195 parameters and confirm the file choices use the current filenames.
3. Change the candidate set and submit the old choice. Confirm the operation does not start.
4. Request menu 195 with zero or one candidate. Confirm no primary-file choice appears.
5. Request menu 91 parameters and confirm the manufacturer control is optional.
6. Confirm every new browser control has a stable test identifier.

## Verify Safe Completion

1. Submit a missing or stale required file answer. Confirm the service starts no operation.
2. Omit the write-back answer. Confirm the service selects no.
3. Skip an optional prompt. Confirm later answers still reach their named prompts.
4. Run the existing CLI prompt tests to confirm numeric selections still work.
