# Implementation Plan: Reject Missing Created Identifiers

## Approach

Keep the current per-object batch recovery.

Make the response reader raise `ValueError` when the created identifier is absent.

Let the existing bound handler record the failed object and continue the batch.

Add a completion reporter that distinguishes success, partial failure, and total failure.

## File changes

### Source

Update `src/mist/resources/org/org_config_migration_manager.py`.

- Validate the response data shape.
- Validate the created object identifier.
- Name the create-response boundary in the refusal.
- Report a total failure when no object imports.
- Preserve the existing per-object continuation behavior.

### Tests

Update `tests/unit/org/test_org_config_migration_conflicts.py`.

- Replace the two empty-string assertions with refusal assertions.
- Prove the create loop records the refusal as failed.
- Prove the operator sees the missing-identifier reason.
- Prove a total failure does not end with a success message.

### Release note

Add `changelog.d/issue-2753-masking-defaults-batch-1.md`.

## Validation

Run the changed tests first and record the red proof.

After the repair, run the focused test module.

Run full-tree Ruff and Black checks.

Run the applicable type, complexity, security, symbol, and test-quality gates.

## Delivery

Rebase on `origin/main` before the single push.

Use `--force-with-lease`.

Do not add the `auto-merge` label.

State that the branch name is a historical reassignment artifact.
