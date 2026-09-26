# Spec Conformance Checklist

**Linked Spec Issue**: #<!-- Issue number -->

## Acceptance Criteria
- [ ] All acceptance criteria from the linked Spec Issue are met
- [ ] Each criterion has a corresponding test or verification

## Quality
- [ ] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [ ] New or changed guards state the measured count and prove one failing path
- [ ] No new Ruff lint violations (`ruff check .`)
- [ ] Code formatted with Black (`black --check --diff .`)
- [ ] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security
- [ ] No hardcoded secrets, tokens, or passwords
- [ ] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [ ] Sensitive data handled via `.env` / environment variables only

## Deployment
- [ ] Dry-run verified locally (ran affected menu operations)
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)
- [ ] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [ ] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation
- [ ] README.md updated (if user-facing changes)
- [ ] Release note added as one new fragment under `changelog.d/`
- [ ] The fragment name carries the PR number, the issue number, or the date
- [ ] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)
