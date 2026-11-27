# Operator Output Checklist: Count export write results

**Purpose**: Check the operator output, the logging, and the inline comments during T002, before the commit.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

**Note**: Check each item during T002, after the code change. Record the evidence in the pull request body.

## Message Contract

- [ ] CHK001 The success notice text is unchanged (`! %d %s records exported to %s`). Evidence: the diff shows no change to that line.
- [ ] CHK002 The failure notice starts with `! Write failed for` and names the operation and the filename. Evidence: the failure cases of T001 pass.
- [ ] CHK003 Each changed or touched line in `count_exporter.py` has an inline comment that explains its purpose (FR-009). Evidence: a reviewer reads the body of `_persist` and confirms one comment for each executable line.
- [ ] CHK004 The info line precedes the writer call, and the debug line follows it (FR-008). Evidence: the logging-order case of T001 passes.
- [ ] CHK005 The regression tests use mocks only, with no file write and no network call (FR-013). Evidence: review of the `fake_mh` fixture and the patches in `test_count_exporter_workflows.py`.
- [ ] CHK006 The operator guide paragraph states that a failed write does not claim success (FR-016). Evidence: the STE gate of T004 passes, and a reader confirms the rule.
- [ ] CHK007 Every new string uses ASCII characters only (Principle V). Evidence: `git diff origin/main` shows no non-ASCII character in an added line.
- [ ] CHK008 No new log line carries a credential, a token, or a full response body (Principle V). Evidence: diff review.
