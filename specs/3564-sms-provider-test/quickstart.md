# Quickstart: Test the guest portal SMS provider

## Prerequisites

- Use the worktree `C:\Users\jmorrison\mh-fleet\3564-sms-provider-test`.
- Use `C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe`.
- Do not wire menu 284 in this branch. The integration pull request reads `wiring.md`.

## Validate the package

```powershell
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m py_compile src\mist\intelligence\troubleshooting\sms_provider_test\__init__.py src\mist\intelligence\troubleshooting\sms_provider_test\client.py src\mist\intelligence\troubleshooting\sms_provider_test\inputs.py src\mist\intelligence\troubleshooting\sms_provider_test\model.py src\mist\intelligence\troubleshooting\sms_provider_test\operation.py
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m ruff check src\mist\intelligence\troubleshooting\sms_provider_test tests\unit\troubleshooting\sms_provider_test
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m black --check src\mist\intelligence\troubleshooting\sms_provider_test tests\unit\troubleshooting\sms_provider_test
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m mypy src\mist\intelligence\troubleshooting\sms_provider_test --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\troubleshooting\sms_provider_test
C:\Users\jmorrison\mh-fleet\3564-sms-provider-test\.venv\Scripts\python.exe -m pytest tests\unit\troubleshooting\sms_provider_test -q --timeout=120
```

## Prove the acceptance criteria

- Run the model tests to prove each provider body shape.
- Run the operation tests to prove hidden-input use, confirmation refusal, non-2xx handling, and output rows.
- Inspect `SmsProviderTest.csv` in a mocked exporter test and confirm it has no credential column.

## Manual operation path after integration

1. Run menu `284`.
2. Select `Twilio`, `SMSGlobal`, or `Telstra`.
3. Enter the required values.
4. At the confirmation prompt, enter `y` only when you want Mist to send a test message.
5. Read the printed verdict.
6. Open `data\SmsProviderTest.csv` and confirm it contains no credential.
