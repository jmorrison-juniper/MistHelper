# Tasks: Reject Missing Created Identifiers

## Phase 1: Failure proof

- T001 Replace the missing-identifier empty-string assertion with a refusal assertion.
- T002 Replace the wrong-shape empty-string assertion with a refusal assertion.
- T003 Add a test that proves the create loop records the refusal as failed.
- T004 Add a test that proves a total failure has no success completion message.
- T005 Run the focused tests and record the expected failures.

## Phase 2: Source repair

- T006 Validate that response data is a dictionary.
- T007 Validate that the created identifier is a nonempty string.
- T008 Raise a refusal that names the identifier and the create-response boundary.
- T009 Keep the existing bound handler and failed result row.
- T010 Report total failure when no object imports.
- T011 Report partial failure when some objects import.

## Phase 3: Validation

- T012 Run the focused unit tests.
- T013 Run full-tree Ruff.
- T014 Run full-tree Black.
- T015 Run the applicable local quality gates.
- T016 Add the changelog fragment.

## Phase 4: Delivery

- T017 Rebase on current `origin/main`.
- T018 Commit the six files.
- T019 Push once with `--force-with-lease`.
- T020 Create the pull request without `auto-merge`.
- T021 Verify that the pull request is not a draft.
