# Specification Quality Checklist: Stale and Bulk Run Controls

**Purpose**: Confirm readiness after the final cross-artifact validation.

**Created**: 2026-09-11

**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] The specification has no clarification marker.
- [x] The specification has no placeholder text.
- [x] The requirements are testable.
- [x] The feature keeps active firmware work out of bulk controls.
- [x] All terminal-state checks use `RunStateMachine.TERMINAL`.

## Constitution Alignment

- [x] Constitution version 1.5.0 records a MINOR amendment.
- [x] Existing tracked hierarchy violations are grandfathered debt.
- [x] The feature adds no child to a noncompliant parent.
- [x] New feature code enters compliant nested packages.
- [x] Every new source and test hierarchy has an explicit child layout.
- [x] Every new hierarchy has five direct children or fewer.
- [x] Surgical edits do not increase existing child counts.
- [x] The plan records separate incremental debt remediation.
- [x] API exports and collected API data still require `DataExporter`.
- [x] The operational-store exception defines fail-closed behavior.
- [x] The operational-store exception defines backup and recovery.
- [x] The operational-store exception defines retention.
- [x] The portal cannot claim success without verified persistence.
- [x] Deployment uses a pull request and never pushes directly to `main`.

## Action Schema and Safety

- [x] Bulk actions require source-specific preview fields.
- [x] Reconciliation uses a single-run source with null preview fields.
- [x] Reconciliation does not require a bulk preview.
- [x] Every initialized run starts with one ordered durable outcome.
- [x] Each item has a pending, claimed, or final processing state.
- [x] Refused, failed, and unknown items use outcome-only durable writes.
- [x] Successful mutations commit with their outcomes.
- [x] The action becomes complete only after all items are final.
- [x] Recovery uses compare-and-swap lease takeover.
- [x] Recovery finalizes abandoned claimed items as unknown.
- [x] Recovery resumes only pending items.
- [x] Recovery never repeats a claimed or final mutation.
- [x] Recovery preserves site stop decisions.
- [x] Every initialized requested run reaches one durable final outcome.
- [x] Idempotency uses durable normalized actor identity.
- [x] Another actor cannot discover an action record.
- [x] Duplicate run identifiers cause a request refusal.
- [x] Retry uses the exact allowlist and existing options validator.
- [x] A `stopping` run reaches only proven `stopped`.
- [x] `TargetEvidence` defines every type and required or null rule.
- [x] `ReconciliationEvidence` defines every type and required or null rule.
- [x] The serialized evidence summary contains safe fields only.
- [x] The action and outcome evidence fields have explicit null rules.
- [x] Success and outcome-only writes store evidence atomically.

## E2E Isolation

- [x] Factory overrides install before blueprint registration.
- [x] ArangoDB, Redis, cloud, and file traps are required.
- [x] The child uses explicit unreachable sentinels.
- [x] The child scrubs production credentials and output paths.
- [x] Each server uses unique ports, records, and artifacts.
- [x] E2E responses use a test-only run identifier header.
- [x] No browser command runs before isolation proof.
- [x] The baseline task occurs before the complete E2E suite.
- [x] The persistent count comparison occurs after the complete E2E suite.

## Manifest, Quality, and Traceability

- [x] `feature-files.txt` is the explicit feature allowlist.
- [x] The manifest lists all 79 planned paths before source implementation.
- [x] The changed set includes branch, staged, unstaged, and untracked files.
- [x] The workflow excludes unrelated pre-existing untracked files.
- [x] The workflow updates the manifest before the first edit to a new path.
- [x] The staging command uses the explicit manifest.
- [x] The workflow proves that every changed feature file is staged.
- [x] Each executable manifest file receives all applicable existing gates.
- [x] Feature-caused failures stay in this feature.
- [x] An unrelated failure gets an issue before repair.
- [x] The plan measures both fixed performance workloads.
- [x] The traceability matrix covers FR-001 through FR-076.

## Deployment

- [x] The issue claim occurs before implementation.
- [x] Active worktree, branch, and pull request overlap checks occur before implementation.
- [x] The README, operator guide, and changelog update before local gates.
- [x] The workflow commits the verified feature before rebase.
- [x] The workflow rebases onto `origin/main` before push.
- [x] The pull request title is explicit.
- [x] The pull request requires `Closes #2447`.
- [x] The pull request requires the specification link.
- [x] The pull request requires a changed-file summary.
- [x] The pull request requires acceptance, local gate, CI, security, and UI evidence.
- [x] The pull request requires deployment and rollback notes.
- [x] The pull request requires every applicable template item.
- [x] The pull request requires type, scope, and status labels.
- [x] Required pull request CI must pass.
- [x] Required human approval must exist before auto-merge.
- [x] The `auto-merge` label is added only after all checks pass.
- [x] The workflow uses a squash merge.
- [x] The workflow waits for the merged `main` image build.
- [x] The workflow verifies the exact image revision.
- [x] Deployment occurs only after revision verification.
- [x] Container and portal health checks follow deployment.
- [x] The live Morrison House check remains optional.

## Readiness

- [x] `.specify/feature.json` points to this feature directory.
- [x] The branch starts at current `origin/main`.
- [x] The prior clean-branch blocker is closed.
- [x] Cross-artifact paths, states, reasons, and dependencies agree.
- [x] The fresh traceability review found no uncovered requirement.
- [x] Task numbers are continuous from T001 through T137.
- [x] `.spec-context.json` reports `ready-to-implement`.

## Notes

The internal validation completed on 2026-09-11 after all artifact gaps
closed. Implementation can proceed without another clarification step.
