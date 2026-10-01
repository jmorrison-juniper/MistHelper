# Tasks: Complete Release Note Bodies

**Issue**: [#3431](https://github.com/jmorrison-juniper/MistHelper/issues/3431)

**Spec**: [spec.md](spec.md)

**Plan**: [plan.md](plan.md)

**Branch**: `jmorrison-juniper-complete-release-note-bodies`

**Session**: `514c1e99-d8a8-4af5-a5ac-ecad749e0ecd`

## Ownership and Foundation

- [X] T001 Check the live issue, linked work, and file ownership. Claim the issue and reserve the exact file set.
- [X] T002 Name the app branch before edits. Use only this isolated worktree.
- [X] T003 Complete SpecKit specification, planning, and task generation without shared state changes.
- [X] T004 Prepare this worktree's Python 3.13+ environment after missing-tool evidence.
- [X] T005 Implement semantic source, reference, body, and command owners in scripts/release_body.py.

T002 depends on T001.
T005 depends on T003 and T004.

## Complete Bodies

- [X] T006 [US1] Select a labeled, complete summary for oversized notes in scripts/release_body.py.
- [X] T007 [US1] Preserve the complete comparison and pinned CHANGELOG destination in both output modes.
- [X] T008 [US2] Preserve every fitting source character and complete final line.
- [X] T009 [US2] Measure the exact complete candidate and actual final file under both counting rules.
- [X] T010 [US1] Test the 216840-character source with 1439 complete entries in tests/unit/test_release_body.py.
- [X] T011 [US2] Test exact boundaries, original line endings, and Unicode in tests/unit/test_release_body.py.

T006 through T009 depend on T005.
T010 and T011 depend on T006 through T009.

## Required Failures

- [X] T012 [US3] Reject invalid, empty, unreadable, or ambiguous required source input.
- [X] T013 [US3] Reject invalid refs, misleading links, and conflicting optional metadata.
- [X] T014 [US3] Verify temporary and final UTF-8 bytes and keep file failures nonzero.
- [X] T015 [US3] Report phases, checked counts, and safe measurement logs.
- [X] T016 [US3] Test input, reference, path, output, and log-safety failures in tests/unit/test_release_body.py.

T012 through T015 depend on T005.
T016 depends on T012 through T015.

## Workflow and Documentation

- [X] T017 [US4] Prepare the complete body within the existing publish job in .github/workflows/release.yml.
- [X] T018 [US4] Require the measured body_path and generate_release_notes false.
- [X] T019 [US4] Prove source ownership, failure handling, and the tag-only boundary in tests/contract/test_release_body_workflow.py.
- [X] T020 [P] Explain release behavior in documentation/release-notes.md.
- [X] T021 [P] Add changelog.d/issue-3431-complete-release-note-bodies.md without editing CHANGELOG.md.

T017 and T018 depend on T009 and T014.
T019 depends on T017 and T018.
T020 and T021 depend on T007.

## Final Verification

- [X] T022 Run the targeted suite with branch coverage and record exact complete output measurements.
- [X] T023 Run compile, lint, format, types, security, and dependency checks.
- [X] T024 Run the unchanged repository test-quality ratchet without baseline changes.
- [X] T025 Check related links and STE.
- [X] T026 Run SpecKit analysis and resolve implementation inconsistencies.
- [X] T027 Verify the exact file scope and unchanged non-publish job mappings.

T022 through T025 depend on T016, T019, T020, and T021.
T026 depends on T022 through T025.
T027 depends on T026.

## Delivery Boundary

Commit locally only after final verification.
Wait at queue position 11 for the parent's full verified base.
Then rebase and repeat validation before the first push or pull request.
Use the complete unchanged pull request template with exact command results and honest non-applicable items.
Wait for all required checks, the title check, CodeQL, and the strict current base.
Use a protected exact-head squash without an admin bypass or branch deletion.
Verify the exact merged main tree locally.

No real release, draft, tag, artifact upload, or release dispatch belongs to this work.

## Current Evidence

The focused implementation replaces the earlier nested framework.
The final targeted run passed 143 tests without a skip.
It measured 97.93 percent branch-aware coverage of the helper.
The actual read-only long-gap response produced a complete 401-character local summary.
Both complete links and the terminal LF remain present.
Compile, full and explicit Ruff, full Black, and the configured 611-file type check passed.
The helper security scan checked 271 code lines with zero findings and zero suppressions.
The repository security scan also passed without a policy change.
The full test-quality ratchet checked 949 files and 725 existing findings.
It reported zero new findings, zero parse errors, and 42 existing configured exclusions.
The link scan checked 11 tracked Markdown files with zero broken links.
The STE scan read all 14 related prose files and passed at scores 94 through 98.
Its dictionary check remains unavailable because data/ste_dictionary.json is absent.
The exact 25-line and five-parameter scan checked all three owned Python files without a violation.
The pipeline comparison verified four unchanged non-publish jobs and both unchanged downloads.
It also verified unchanged root settings, publish permissions, dependencies, and artifact entries.

## SpecKit Analysis Resolution

The analysis identified mixed malformed comparison declarations and uncaught JSON decoder-limit failures.
The helper now rejects both cases with fixed failures and checked source counts.
The contract now reports a policy phase and actual counts for early negative decisions.
The contract method split retains the 25-line limit without a new validation framework.
Direct negative tests cover these corrections.

The approved file scope and concise comment policy remain recorded in [plan.md](plan.md).
No unrelated directory restructure, constitution amendment, or shared rule change belongs to this repair.

The direct requirements audit cannot create its copied temporary Mac interpreter.
The approved hashed-closure recovery audited all 105 resolved runtime packages.
It reported zero vulnerabilities and zero skipped runtime packages.
The recovery changes no tracked dependency file.
