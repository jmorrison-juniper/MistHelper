# Spec Conformance Checklist

**Linked Spec Issue**: #3561

Closes #3561

## Summary
- Add `src/mist/intelligence/reports/alert_digest` for menu 280 alert digest output and menu 281 alarm acknowledgement.
- Menu 280 writes `AlertDigest.csv` and `AlertDigest.md` through the owned package.
- Menu 281 is destructive. It changes Mist alarm acknowledgement state, requires `ACK <count>`, supports `--dry-run`, and needs human review before merge.

## Files
- `src/mist/intelligence/reports/alert_digest/**`
- `tests/unit/reports/alert_digest/**`
- `specs/3561-alert-digest-acknowledge/**`
- `changelog.d/issue-3561-alert-digest-acknowledge.md`

## Integration deferral
- Menu wiring is deferred to the tier integration pull request.
- The integration pull request must copy `specs/3561-alert-digest-acknowledge/wiring.md`.
- The deferred wiring covers `MistHelper.py`, `src/foundation/support/utils/operation_registry.py`, primary key strategies, README, and generated menu references.

## Acceptance Criteria
- [x] All acceptance criteria from the linked Spec Issue are met.
- [x] Each criterion has a corresponding test or verification.

## Quality
- [x] Tests added or updated for all changed functionality.
- [x] Coverage meets or exceeds the 80 percent threshold.
- [x] New and changed guards state the measured count where applicable.
- [x] No new Ruff lint violations.
- [x] Code formatted with Black.
- [x] mypy passes for the package.

## Security
- [x] No hardcoded secrets, tokens, or passwords.
- [x] Bandit passes for the package with no new findings.
- [x] No dependency change was made, so pip-audit is not applicable.
- [x] Sensitive data stays in environment variables or the active Mist session.

## Deployment
- [x] Dry-run behavior is verified by unit tests.
- [x] `.env` changes are not required.
- [x] Container files are unchanged.

## UI / E2E Testing
- [x] No web UI changed.

## Documentation
- [x] Release note added as `changelog.d/issue-3561-alert-digest-acknowledge.md`.
- [x] `CHANGELOG.md` is unchanged.
