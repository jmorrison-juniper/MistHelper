# Spec Conformance Checklist

**Linked Spec Issue**: #3618

Refs #3618
Part of #3618

## Summary
- Wired Tier 3 menus 283, 284, 285, 288, 289, and 290 into the shared menu files.
- Regenerated the portal menu registry, the menu reference, and the menu API endpoint map.
- Added portal parameters for menu 288 and menu 289 by using the existing site and choice helpers.

## Menus
| Menu | Issue | Category | Skip reason | Handler |
| - | - | - | - | - |
| 283 | #3563 | interactive | Requires a site, an optional device, and a y/N confirmation | `SyntheticTestTrigger.run` |
| 284 | #3564 | interactive | Requires hidden provider credentials and a y/N confirmation | `SmsProviderTest.run` |
| 285 | #3565 | interactive | Requires a provider, a username, a hidden password, and a y/N confirmation | `NacIdpCredentialTest.run` |
| 288 | #3568 | interactive_safe | Prompts before writing `data/SsrRegistrationCommands.txt` with `Write registration commands to data/SsrRegistrationCommands.txt? (y/N):` | `SsrRegistrationCommands.run` |
| 289 | #3569 | interactive_safe | Requires a site prompt and a distinct-field prompt. | `ClientFingerprintCensus.run` |
| 290 | #3570 | interactive | Requires a mode, a site, target values, and a y/N confirmation | `RfDiagnosticsOperation.run` |

## Feature pull requests
- #3592 delivered menu 283.
- #3587 delivered menu 284.
- #3614 delivered menu 285.
- #3585 delivered menu 288.
- #3584 delivered menu 289.
- #3638 delivered menu 290.

## Follow-up menus
Menus 286, 287, 291, 292, 293, 280, and 281 follow after their human reviews.

## Manifest notes
- The menu 284 manifest did not include a skip reason, so this pull request used the prompt flow from its manifest text.
- The menu 285 manifest did not include a skip reason, so this pull request used the prompt flow from its manifest text.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality
- [x] Tests added or updated for all changed functionality
- [x] Coverage meets or exceeds 80% threshold
- [x] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations (`ruff check .`)
- [x] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security
- [x] No hardcoded secrets, tokens, or passwords
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [x] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment
- [x] Dry-run verified locally (ran affected menu operations)
- [x] `.env` changes documented in `deploy/.env.example` (if applicable)
- [x] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)
- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [x] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation
- [x] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Verification
- `py_compile` passed for each edited Python file.
- `ruff check .` passed.
- `black --check MistHelper.py src/utils/operation_registry.py src/refactors/endpoint_primary_key_strategies.py web_portal/services/operation.py web_portal/menu_registry.py` passed.
- `mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml` passed.
- `pytest tests/unit/test_menu_entry_metadata.py tests/guardrails tests/unit/utils tests/unit/web_portal -q --timeout=120` passed.
- `MistHelper.py --help` passed.
- `symbol-diff --base origin/main MistHelper.py` reported no lost names. Added names are expected.
