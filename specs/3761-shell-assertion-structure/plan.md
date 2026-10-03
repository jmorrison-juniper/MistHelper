# Implementation Plan

## Approach

Extract the test's existing assertions into a semantic `ShellLogAssertions`
class in the allowed test module. Keep the test's native records as the source
for every production assertion. Separate secret exclusion, event membership,
safe fields, and string bounds into focused assertion methods.

Keep record selection and JSON parsing in the existing native test. Do not
change the shell run, captured log text, completion wait, fixtures, or time
bounds. Add one issue-specific control module only if existing frozen controls
cannot prove the assertion methods' passing and refusal behavior.

## Verification

Run the smallest assertion controls first. Then run the original target test
and the affected native `tests/unit/websocket_streams` and
`tests/contract/websocket_streams` scope. Record ordered test membership and
JUnit results. Measure the target's direct Radon complexity, not the configured
test-excluded CI proxy.

Run compile, Ruff, Black, configured type checking, explicit test typing,
test-quality preflight and census, changed-scope analysis, and applicable
safety gates. Report unavailable gates and known unrelated failures without
repairing them.

## Verified Results

- The approved base is `608b543882932e1370f6fadcc2da7c8bc54f9164`.
- The approved base tree is `80e4e7f541fc51d386642962ec1d91f62e5d47ad`.
- Direct Radon complexity changed from 13 to 5 for the target test.
- AST comparison preserved all 9 original assertions with an identical hash:
  `bda0a5792f9d8acec48cf7408a19e159bf276371d62717a6de12cb23deeeb0b6`.
- The final target source hash is
  `66ac48f4a223c4ae39009b2c8fa9fb869b133b620f14722b0fe8fbc775edfc71`.
- The 9 new controls and the original target test passed.
- The affected native unit and contract scope passed all 383 tests.
- The JUnit report holds 383 unique ordered test names and no skipped tests.
- Its ordered-membership hash is
  `e4a9f14430bc7de835fb691d45b334577a8bc6b3cc8d814807df77a9d718f114`.
- Compile, Ruff, Black, configured mypy, and explicit changed-test mypy passed.
- Analyzer preflight passed with 6 input reads and 3 guide checks.
- The final full analyzer census checked 1,046 files and 725 findings.
- The analyzer parsed 998 files, skipped 48, and found no parse errors.
- The full analyzer gate reported zero new findings and zero stale baseline entries.
- Config hash: `f029baa92240cd534d60f8c8b2c9adf20d2e4b6128e6a7c27e956f4bf97a6e75`.
- Baseline hash: `17cf07c514e8951732f3fffca86d3e5e18ba863c5faa219ceb9b3124215c3745`.
- Direct Bandit reports test-assertion findings. No finding was suppressed.
- The separate #3760 fixture issue remains outside this change. No fixture changed.
- Licensed STE, CodeQL, PowerShell, and VS Code Browser checks were unavailable.
- No release note applies because this change only restructures tests.

The session artifact index holds raw outcomes, hashes, and the post-commit
changed-scope analyzer result. It remains outside the repository.

## Limits

Keep edits within the issue-approved files. Do not publish, open a pull request,
run workflows, deploy, or alter another owner's files. Make one normal local
commit after the applicable checks.
