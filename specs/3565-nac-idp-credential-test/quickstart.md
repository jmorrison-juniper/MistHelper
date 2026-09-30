# Quickstart: NAC IDP Credential Test

## Prerequisites

1. Use the worktree at `C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test`.
2. Use `C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe`.
3. Configure a Mist API token in the normal MistHelper environment before a live run.
4. Confirm that the organization has an Access Assurance identity provider under `Organization > Access > Identity Providers`.

## Local validation

Run these commands from the repository root.

```powershell
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m py_compile src\troubleshooting\nac_idp_credential_test\__init__.py src\troubleshooting\nac_idp_credential_test\client.py src\troubleshooting\nac_idp_credential_test\model.py src\troubleshooting\nac_idp_credential_test\operation.py src\troubleshooting\nac_idp_credential_test\prompts.py
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m ruff check src\troubleshooting\nac_idp_credential_test tests\unit\troubleshooting\nac_idp_credential_test
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m black --check src\troubleshooting\nac_idp_credential_test tests\unit\troubleshooting\nac_idp_credential_test
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m mypy src\troubleshooting\nac_idp_credential_test --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m pydocstyle src\troubleshooting\nac_idp_credential_test
C:\Users\jmorrison\mh-fleet\3565-nac-idp-credential-test\.venv\Scripts\python.exe -m pytest tests\unit\troubleshooting\nac_idp_credential_test -q --timeout=120
```

## Live operator flow after integration wiring

1. Start MistHelper.
2. Select menu `285`.
3. Select the identity provider by number.
4. Enter the test username.
5. Enter the password at the hidden prompt.
6. Enter `y` to confirm the credential test.
7. Read the verdict and returned attributes.
8. Confirm that `data/NacIdpCredentialTest.csv` contains no password.

## Expected results

- A success prints the success verdict and safe attributes.
- A failed validation prints the API reason and no traceback.
- A declined confirmation sends no credential.
- The export file contains one row per confirmed test and no password column.
