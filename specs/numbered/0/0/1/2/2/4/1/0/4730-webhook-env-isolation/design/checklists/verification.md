# Verification Checklist: Webhook config test isolation

**Purpose**: Track the checks that prove the merged repair and the comment-only follow-up.
**Created**: 2026-11-26
**Feature**: `design/quickstart.md`

## Step A: Merged main (gates T009)

- [ ] CHK001 TC-001 reports `1 passed` with `WEBHOOK_SECRET` and `WEBHOOK_ENABLED` unset (quickstart Q-8).
- [ ] CHK002 TC-002 reports `1 passed` with `WEBHOOK_ENABLED=false` (quickstart Q-8).
- [ ] CHK003 TC-003 reports zero failed tests in both states for the whole file (quickstart Q-8).
- [ ] CHK004 TC-004 reports `1 failed` at the `WEBHOOK_ENABLED is True` assertion in the negative control (quickstart Q-9).
- [ ] CHK005 TC-010 prints `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation` (quickstart Q-10).

## Step B: Follow-up branch (gates T-PR)

- [ ] CHK006 TC-005 names only `tests/unit/web_portal/test_webhook_signature.py` in the diff (quickstart Q-11).
- [ ] CHK007 TC-006 shows that each changed line differs only by a trailing inline comment (quickstart Q-11).
- [ ] CHK008 TC-006 symbol gate reports `no module-level name changed` with exit code 0 (quickstart Q-11).
- [ ] CHK009 TC-008 shows an inline comment on each of the 8 code lines in lines 229 to 240 (quickstart Q-11).
- [ ] CHK010 TC-009 shows compile with no output, Ruff with `All checks passed`, and Black with `No file needs a change` (quickstart Q-11).
- [ ] CHK011 TC-012 shows no `core.hooksPath` value and no `commit.gpgsign` value of `false` (quickstart Q-11).
- [ ] CHK012 TC-013 shows no file under `changelog.d/` and the internal-only reason in the pull request body (quickstart Q-11 and Q-12).
- [ ] CHK013 TC-014 reports `gate: 0 new findings vs baseline` (quickstart Q-11).

## Closure and remote evidence

- [ ] CHK014 TC-011 reports state `CLOSED` and no `in-progress` label for issue 4730 after T009 (quickstart Q-6).
- [ ] CHK015 Remote check R-21 still reports success for run 45774119357 (quickstart Q-4).
- [ ] CHK016 Remote check R-08 still reports merge commit `15da34506` as an ancestor of `main` (quickstart Q-5).

## Notes

- Run each check with the procedure named in its row. Record each result in the pull request body or on the issue.
