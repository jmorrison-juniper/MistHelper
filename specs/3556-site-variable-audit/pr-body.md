# Spec Conformance Checklist

**Linked Spec Issue**: #3556

Closes #3556

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met in the owned package and tests.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [ ] Coverage meets or exceeds 80% threshold. Targeted coverage was not run.
- [x] New or changed guards state the measured count and prove one failing path. No new guard was added.
- [x] No new Ruff lint violations for the owned package and tests.
- [x] Code formatted with Black for the owned package and tests.
- [x] mypy passes for the owned package.

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [ ] Bandit passes with no new findings. Bandit was not run.
- [ ] pip-audit clean. pip-audit was not run.
- [x] Sensitive data uses existing environment configuration only.

## Deployment

- [ ] Dry-run verified locally. Menu 275 wiring is deferred to the integration pull request.
- [x] `.env` changes documented in `deploy/.env.example` if applicable. No `.env` change exists.
- [x] Container builds successfully if Containerfile changed. No container file changed.

## UI / E2E Testing

- [x] Playwright E2E tests added or updated if web UI changed. No web UI changed.
- [x] Stable `data-testid` attributes added if needed. No web UI changed.
- [x] Browser selectors verified if web UI changed. No web UI changed.
- [x] Screenshots or traces captured if web UI changed. No web UI changed.

## Documentation

- [ ] README.md updated. The integration pull request owns README wiring.
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the issue number.
- [x] `CHANGELOG.md` is unchanged by this branch.

## Files

- `src/reports/site_variable_audit/`
- `tests/unit/reports/site_variable_audit/`
- `specs/3556-site-variable-audit/`
- `changelog.d/issue-3556-site-variable-audit.md`

## Deferred wiring

The integration pull request owns Menu 275 registration and generated references. Use `specs/3556-site-variable-audit/wiring.md` for the exact values.
