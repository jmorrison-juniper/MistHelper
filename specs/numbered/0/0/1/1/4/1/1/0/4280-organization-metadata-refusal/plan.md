# Implementation Plan: Organization metadata refusal

**Branch**: `jmorrison-juniper-organization-metadata-refusal` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

## Summary

Validate status before reading organization metadata.
Retain `Unknown` for refusal, invalid metadata, and supported request failures.
Report failures without response bodies, names, or exception text.
Use native SDK responses in offline tests.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: Existing mistapi 0.64.x and standard logging.
**Storage**: The existing export bundle remains unchanged.
**Testing**: pytest, mocked SDK endpoint, native `APIResponse`, and captured logs.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Existing command-line application.
**Performance Goals**: One metadata request per lookup, with no additional request.
**Constraints**: No production operations, no automatic merge, and no issue closure.
**Scale/Scope**: One existing production method and its existing test module.

## Constitution Check

The predesign and postdesign checks pass for this bounded repair.
The mandatory `before_specify` hook completed in the app-owned isolated branch.
The managed route came from `create-new-feature.ps1 -Number 4280 -DryRun`.
The command used `Resolve-SpecFeaturePath` internally.
PowerShell was absent, so the official arm64 archive supplies a session-local executable.
The tracked feature selector remains unchanged.

The SDK endpoint remains `mistapi.api.v1.orgs.orgs.getOrg`.
No new transport, dependency, database key, or production output enters the change.
The tests cover successful metadata, refusal, server failures, malformed data, exceptions, and safe logging.
The existing import confirmations remain unchanged.
Human review overrides the normal automatic deployment sequence.

Existing structural debt includes the large manager class, the test module, and the changelog folder.
The change adds no production declaration and no new direct test module.
Only one required unique changelog fragment enters the process folder.
A separate future remediation can divide the manager and group its tests.
That remediation must preserve menu confirmation and bundle contracts.

## Project Structure

```text
src/mist/resources/org/org_config_migration_manager.py
tests/unit/org/test_org_config_migration_workflow.py
changelog.d/issue-4280-organization-metadata-refusal.md
specs/numbered/0/0/1/1/4/1/1/0/4280-organization-metadata-refusal/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      metadata.md
    checklists/
      requirements.md
```

**Structure Decision**: Edit the existing lookup and test module to avoid new package children.
Each new specification directory has five children or fewer.

## Complexity Tracking

| Existing debt | Reason for bounded edit | Separate remediation |
| --- | --- | --- |
| Large manager class | The defect belongs to one existing method. | Divide export and import responsibilities under a separate specification. |
| Large test module | Extend the current lookup and export tests without a new module. | Group migration tests without losing collected cases. |
| Changelog process folder | Repository policy requires one unique fragment. | Group release records through a repository-wide policy change. |

## Validation

Use [the offline guide](design/quickstart.md).
First demonstrate failing refusal tests, then apply the production repair.
Run targeted migration tests, SDK compatibility, relevant structural guards, and file-scoped quality gates.
Commit explicit paths before the required test-quality comparison against `origin/main`.
Record exact command results in the handoff.
