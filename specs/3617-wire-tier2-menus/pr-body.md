# Spec Conformance Checklist

**Linked Spec Issue**: Refs #3617

Part of #3617.

## Summary

This pull request wires the merged Tier 2 feature modules into the shared menu files.

- Menu 277, issue #3558, category `safe`, handler `SwitchScorecard.run`.
- Menu 278, issue #3559, category `safe`, handler `ApScorecard.run`.
- Menu 279, issue #3560, category `safe`, handler `WanEdgeScorecard.run`.
- Menu 282, issue #3562, category `safe`, handler `RoguePciEvidencePack.run`.

The feature modules merged in #3576, #3610, #3597, and #3579.

Menus 280 and 281 follow in a later pull request after #3637 merges.

## Acceptance Criteria

- [x] All acceptance criteria from the linked Spec Issue are met.
- [x] Each criterion has a corresponding test or verification.

## Quality

- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds 80% threshold.
- [x] New or changed guards state the measured count and prove one failing path.
- [x] No new Ruff lint violations (`ruff check .`).
- [x] Code formatted with Black (`black --check --diff .`).
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`).

## Security

- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit is not required for this menu wiring change.
- [x] pip-audit is not required for this menu wiring change.
- [x] Sensitive data handled via `.env` / environment variables only.

## Deployment

- [x] Dry-run verified locally with `MistHelper.py --help`.
- [x] `.env` changes documented in `deploy/.env.example` (if applicable).
- [x] Container build is not required because no container file changed.

## UI / E2E Testing (if web UI changed)

- [x] Playwright E2E tests are not required for this registry-only portal update.
- [x] Stable `data-testid` attributes are not required for this registry-only portal update.
- [x] Browser selector verification is not required for this registry-only portal update.
- [x] Screenshots/traces are not required for this registry-only portal update.

## Documentation

- [x] README.md updated (if user-facing changes).
- [x] Release note added as one new fragment under `changelog.d/`.
- [x] The fragment name carries the PR number, the issue number, or the date.
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file).
