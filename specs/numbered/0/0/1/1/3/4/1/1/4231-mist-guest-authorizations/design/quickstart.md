# Quickstart: Migrate Mist Guest Authorizations

## 1. Read-only reproduction

Set the GitHub variables from the account name. Do not print the values.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Read the issue:

```powershell
gh issue view 4231 -R jmorrison-juniper/MistHelper --json number,title,state,createdAt,updatedAt,labels
```

Read one remote blob by SHA. Use a SHA from research section 8:

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/blobs/44a9afffb5bd6f774973a845d27343e4e528b6ad --jq .content
```

Hash one installed SDK file. The output must equal R-94 (`708f633d8a8a038117ebad17f391ee51a8d093ae`):

```powershell
git hash-object --no-filters "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\mistapi\api\v1\sites\guests.py"
```

## 2. Planning gate (STE)

Run the STE gate from the local gates table. Each file must score 80 or above:

```text
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
```

## 3. Implementation gates

Run each gate that applies to the changed files. Commands come from the local gates table in `.github/copilot-instructions.md`.

| Gate | Command |
| --- | --- |
| Compile | `python -m py_compile MistHelper.py` |
| Lint | `python -m ruff check .` |
| Format | `python -m black --check .` |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` |
| Changed tests | Run `python -m pytest` on each test file listed in section 4. |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` |
| Complexity | `radon cc src/interfaces/portals/guest_authorizations -j \| complexity-gate --max 10` |
| Security lint | `bandit -c pyproject.toml -r src/interfaces/portals/guest_authorizations src/mist/access/guests -q` |
| Code quality | `pylint src/ --fail-under=9.5` |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` |
| Symbols | `symbol-diff --base main src/interfaces/portals/guest_authorizations.py` |
| Safe sweep | `python MistHelper.py --test` |
| STE | The command in section 2 |

Browser failures keep a screenshot and a trace under `test-artifacts`, which the constitution allows (Data Directory rule).

Test containers join the compose group, as the constitution requires (Test Containers rule). Read the section "Test and debug containers" in `documentation/container-deployment.md` before a container test.

## 4. Test catalog

Each row names one planned test. The test file lists where the case belongs.

| ID | Level | Test file | Expected result | Requirements |
| --- | --- | --- | --- | --- |
| TC-001 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | MAC forms normalize, and malformed values fail | FR-009 |
| TC-002 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | All-zero, broadcast, and multicast values fail | FR-009 |
| TC-003 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | Invalid email format fails, and an empty email passes | FR-009 |
| TC-004 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | Minutes 0 and 259201 fail, and no default applies | FR-009, FR-011 |
| TC-005 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | Minutes 1 and 259200 pass | FR-009 |
| TC-006 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | The typed word matches exactly and is case-sensitive | FR-014 |
| TC-007 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | A reviewed-content hash mismatch refuses the write | FR-014, FR-015 |
| TC-008 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | Length limits apply to company, email, field1, field2, and field3 | FR-009 |
| TC-009 | unit | tests/unit/web_portal/test_guest_authorization_read_model.py | Returned values display, and missing values show unknown | FR-007 |
| TC-010 | unit | tests/unit/web_portal/test_guest_authorization_read_model.py | Future expiry is active, past expiry is expired, and missing expiry is unknown | FR-008 |
| TC-011 | unit | tests/unit/web_portal/test_guest_authorization_journal.py | The intent entry reads back before a write, and a failed read-back starts no write | FR-003, FR-019 |
| TC-012 | unit | tests/unit/web_portal/test_guest_authorization_journal.py | A 5xx response, a missing status, or a timeout gives an unknown outcome with no retry | FR-016, FR-018 |
| TC-013 | unit | tests/unit/web_portal/test_guest_authorization_journal.py | A failed audit write blocks the next write until reconciliation | FR-020 |
| TC-014 | unit | tests/unit/web_portal/test_guest_authorization_audit.py | Audit events mask MAC addresses and omit names, emails, and field values | FR-026, FR-030 |
| TC-015 | unit | tests/unit/web_portal/test_guest_authorization_audit.py | Captured logs and audit events omit tokens, names, emails, and raw payloads | FR-026 |
| TC-016 | unit | tests/unit/web_portal/test_guest_authorization_imports.py | A file above 262144 bytes is rejected before row parsing | FR-022 |
| TC-017 | unit | tests/unit/web_portal/test_guest_authorization_imports.py | More than 500 data rows are rejected | FR-022 |
| TC-018 | unit | tests/unit/web_portal/test_guest_authorization_imports.py | Non-UTF-8 content or an unexpected header is rejected | FR-022 |
| TC-019 | unit | tests/unit/web_portal/test_guest_authorization_imports.py | Duplicate normalized MAC addresses reject every row after the first | FR-023 |
| TC-020 | unit | tests/unit/web_portal/test_guest_authorization_imports.py | A row without minutes is rejected, and no default applies | FR-022 |
| TC-021 | integration | tests/integration/web_portal/test_guest_authorizations.py | Each row gets one validation result, and no write starts before the typed word IMPORT | FR-023, FR-024 |
| TC-022 | contract | tests/contract/guests/test_guest_gateway.py | The gateway imports and calls only allowlisted mistapi functions with keyword arguments | FR-028 |
| TC-023 | contract | tests/contract/guests/test_guest_gateway.py | HTTP 2xx counts as success, and other statuses follow the contract | FR-016 |
| TC-024 | contract | tests/contract/guests/test_guest_gateway.py | No organization-scope write call exists, and no scope fallback runs | FR-017 |
| TC-025 | contract | tests/contract/guests/test_guest_gateway.py | Each write makes exactly one SDK call, and the gateway adds no retry | FR-018, SC-005 |
| TC-026 | contract | tests/contract/guests/test_guest_gateway.py | Client search calls only the site statistics method | FR-021 |
| TC-027 | integration | tests/integration/web_portal/test_guest_authorizations.py | The edit body holds allowlisted fields only, and a name change fails before any call | FR-010 |
| TC-028 | guardrail | tests/guardrails/test_guest_access_topology.py | Compose adds no service and no published port for this feature | FR-002, SC-007 |
| TC-029 | guardrail | tests/guardrails/test_guest_access_topology.py | No Redis guest storage, no direct HTTP client to Mist, and no copied source identifier | FR-004, FR-028, D-13 |
| TC-030 | guardrail | tests/guardrails/test_guest_access_topology.py | Child counts stay within five, and `portals` keeps five | FR-027 |
| TC-031 | integration | tests/integration/web_portal/test_guest_authorizations.py | Guest routes refuse with zero Mist calls when the flag is false or the credential is missing | FR-001 |
| TC-032 | integration | tests/integration/web_portal/test_guest_authorizations.py | Unauthenticated requests are refused before any Mist call | FR-005 |
| TC-033 | integration | tests/integration/web_portal/test_guest_authorizations.py | A permission check fails for organization, site, WLAN, or action before any Mist call | FR-006 |
| TC-034 | integration | tests/integration/web_portal/test_guest_authorizations.py | A canceled review or denied permission sends zero write calls | FR-015 |
| TC-035 | integration | tests/integration/web_portal/test_guest_authorizations.py | A wrong typed word or a name change sends zero write calls | FR-010, FR-014, FR-015 |
| TC-036 | integration | tests/integration/web_portal/test_guest_authorizations.py | A grant writes the intent before the PUT and records the outcome after it | FR-019 |
| TC-037 | integration | tests/integration/web_portal/test_guest_authorizations.py | A successful change records the cloud and audit outcomes | FR-020 |
| TC-038 | integration | tests/integration/web_portal/test_guest_authorizations.py | Revoke sends minutes 0 at site scope after a WLAN check | FR-012 |
| TC-039 | integration | tests/integration/web_portal/test_guest_authorizations.py | Reconciliation shows ended only after an unauthorized read, not ended when still authorized, and not found when absent | FR-013 |
| TC-040 | integration | tests/integration/web_portal/test_guest_authorizations.py | Revoke refuses a record from another WLAN and sends zero writes | FR-012 |
| TC-041 | unit | tests/unit/web_portal/test_guest_authorization_domain.py | Extend shows the UTC expiry before confirmation and sends one PUT | FR-011 |
| TC-042 | integration | tests/integration/web_portal/test_guest_authorizations.py | Import rows run in file order with one final outcome per row | FR-024 |
| TC-043 | integration | tests/integration/web_portal/test_guest_authorizations.py | A final 429 on row 3 stops the run, and rows 4 onward show not attempted | FR-025 |
| TC-044 | integration | tests/integration/web_portal/test_guest_authorizations.py | Client search filters the selected site, masks MAC addresses, and shows an error on Mist failure | FR-021, FR-030 |
| TC-045 | e2e | tests/e2e/web_portal/test_guest_authorizations.py | Each control has a unique data-testid, and the tab shows only when the flag is true | FR-001, FR-029 |
| TC-046 | e2e | tests/e2e/web_portal/test_guest_authorizations.py | The masked table and unknown values render in the browser | FR-007, FR-030 |
| TC-047 | e2e | tests/e2e/web_portal/test_guest_authorizations.py | The grant review shows the full MAC address and requires GRANT | FR-014, FR-029 |
| TC-048 | e2e | tests/e2e/web_portal/test_guest_authorizations.py | The import preview requires the typed word IMPORT in the browser | FR-023 |
| TC-049 | e2e | tests/e2e/web_portal/test_guest_authorizations.py | A failed browser flow keeps a screenshot and a trace under test-artifacts | FR-029 |
