# Implementation Plan: Browser package mirrors

**Branch**: `jmorrison-juniper-browser-dependency-transfer-delays-ci` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

Remove the slow Azure HTTP mirror entry from the runner's existing mirror list before the unchanged Playwright dependency installation.
Keep both existing official HTTPS alternatives and every other entry.
Validate the expected format and create an exclusive backup before writing.
An unfamiliar configuration or an existing backup must fail without a rewrite.

## Technical Context

**Language/Version**: Workflow YAML, Bash, and runner Python 3.
**Primary Dependencies**: Existing Playwright 1.64.1 installer, pytest, and PyYAML.
**Storage**: The ephemeral runner's apt mirror file and an exclusive backup.
**Testing**: Offline execution of the embedded setup against temporary files and workflow mutation contracts.
**Target Platform**: Existing `ubuntu-latest` runner.
**Project Type**: Internal CI configuration.
**Performance Goals**: Avoid the measured slow endpoint without claiming an unmeasured runtime.
**Constraints**: Preserve all test and CI contracts. Do not retry CI, merge, or enable auto-merge.
**Scale/Scope**: One shared matrix setup step and one focused test module.

## Constitution Check

- The branch already exists as an isolated app worktree. Do not create another branch.
- The numeric route came from `create-new-feature.ps1 -DryRun -Number 4613`.
- Keep the feature selector command-scoped. Leave `.specify/feature.json` unchanged.
- The feature root has four children. Supporting documents remain under `design/`.
- The existing `e2e_timeout_budget` test package has capacity for one module.
- Existing workflow and test-directory size violations remain unchanged.
- Separate incremental remediation: consolidate existing workflow setup during a later owner-approved CI maintenance change.
- Only the unique release-note fragment enters the established process folder.
- No Mist Cloud requests, product outputs, service changes, dependency changes, or production operations occur.
- User instructions prohibit retries, merges, and auto-merge. These override the generic delivery defaults.
- No additional agents are necessary because the research and implementation are one continuous trace.

## Project Structure

### Documentation (this feature)

Primary records are `spec.md`, `plan.md`, and `tasks.md`.
Supporting records are `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.
No public interface contract is necessary for this internal configuration change.

### Source Code (repository root)

- `.github/workflows/ci.yml`: Add the validated mirror preparation before `Download the browser`.
- `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`: Execute setup offline and protect the workflow contract.
- `changelog.d/issue-4613-browser-package-mirrors.md`: Describe the setup change.

PR #4208 retains its WAN upload block on its own branch.
This branch does not copy that block because its required screenshots do not exist on this baseline.
Before delivery, apply this patch to the complete #4208 workflow in memory and compare its WAN step unchanged.

## Validation

1. Execute success, invalid input, repeat, and backup-failure scenarios with temporary files.
2. Compare package sources, Playwright commands, selection, timeouts, services, and aggregate behavior with the baseline.
3. Exercise rejected workflow mutations and the existing trigger, partition, and runtime guards.
4. Run Ruff, Black, applicable document checks, and the required test-quality procedure.
5. Open a linked pull request after focused offline validation. Do not claim hosted-runner speed from local measurements.

## Delivery authorization

The coordinator assigned the serial slot to #4613 after #4604 reached its browser job limit.
Verify current main and validate the final commit before publication.
Publish the linked pull request, but do not merge or enable auto-merge.
Hosted transfer speed remains unproven.
