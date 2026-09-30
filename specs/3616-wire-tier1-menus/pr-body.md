# Spec Conformance Checklist

**Linked Spec Issue**: #3616

Closes #3616

## Tier 1 menu wiring

| Menu | Issue | Category | Handler |
| - | - | - | - |
| 271 | #3552 | safe | `SubscriptionExpiryReport.run` |
| 272 | #3553 | safe | `CertificateExpiryReport.run` |
| 273 | #3554 | safe | `AdminTokenHygieneReport.run` |
| 274 | #3555 | safe | `PskHygieneReport.run` |
| 275 | #3556 | safe | `SiteVariableAudit.run` |
| 276 | #3557 | safe | `OrgSecurityPostureChecklist.run` |

The merged feature pull requests are #3594, #3640, #3589, #3636, #3607, and #3639.

Menu 276 now passes `api_function_name="orgSecurityPostureChecklist"`, so the report uses its primary key strategy.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality
- [x] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [ ] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations (`ruff check .`)
- [x] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security
- [x] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment
- [ ] Dry-run verified locally (ran affected menu operations)
- [x] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)
- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation
- [x] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)

## Validation

- `python -m py_compile` passed for each edited Python file.
- `python -m ruff check .` passed.
- `python -m black --check MistHelper.py src/utils/operation_registry.py src/refactors/endpoint_primary_key_strategies.py web_portal/services/operation.py web_portal/menu_registry.py` passed.
- `python -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml` passed.
- `python -m pytest tests/unit/test_menu_entry_metadata.py tests/guardrails tests/unit/utils tests/unit/web_portal -q --timeout=120` passed.
- `python MistHelper.py --help` passed.
- `symbol-diff --base origin/main MistHelper.py` reported no lost names. It reported the six added public handler imports.
- `python -m radon cc MistHelper.py src/utils/operation_registry.py web_portal/services/operation.py -j | complexity-gate --max 10` passed.
