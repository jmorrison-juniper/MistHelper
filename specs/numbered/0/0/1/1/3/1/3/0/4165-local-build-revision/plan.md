# Implementation Plan: Local build revision

**Branch**: `jmorrison-juniper-local-build-revision` | **Date**: 2026-10-31 | **Spec**: [Specification](spec.md)

## Summary

Read the build commit and checkout status before the provider runs.
Pass the revision through a build-only environment variable to the existing compose overlay.
Set the OCI revision label through compose build labels, without changing the container recipe or CI.
Reject dirty labels before the existing clean-commit comparison.

## Technical Context

**Language/Version**: PowerShell 7 and Python 3.13 tests.
**Primary Dependencies**: Git, podman-compose, pytest, and PyYAML.
**Storage**: OCI image configuration only.
**Testing**: Existing packaging contracts plus PowerShell execution with simulated native commands.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Internal deployment helper.
**Performance Goals**: Two bounded local Git reads per build.
**Constraints**: No production container changes, network use in tests, or runtime dependency additions.
**Scale/Scope**: One build path and one revision-check path.

## Constitution Check

- The issue is claimed, and the application-managed branch isolates the work.
- The mandatory branch hook uses the existing application branch instead of creating another branch.
- The optional commit hooks remain deferred until the coherent implementation is ready.
- No open pull request owns the declared implementation paths.
- The managed numeric route has eight base-5 segments.
- Each new feature directory has five children or fewer.
- The existing root and helper script exceed structural limits. This change modifies existing children rather than restructuring unrelated code.
- The new execution test is the fifth tracked packaging file, and its test class has five members.
- The release-note folder has existing child-count debt. This issue adds only its required unique fragment.
- A separate future remediation should divide deployment command blocks and migrate release-note history.
- No Mist Cloud operation, destructive menu, production secret, or public API changes.
- No dependency or container recipe changes.
- Conventional Commit text and the full pull request template apply.

The post-design review passes with the recorded existing structural debt.

## Project Structure

```text
scripts/compose.ps1
compose.build.yml
documentation/container-deployment.md
deploy/.env.example
tests/contract/packaging/test_compose_local_revision.py
changelog.d/issue-4165-local-build-revision.md
specs/numbered/0/0/1/1/3/1/3/0/4165-local-build-revision/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/
    research.md
    data-model.md
    quickstart.md
```

**Structure Decision**: Extend existing files and use the required managed feature route.
The helper is internal, so no additional external interface contract is necessary.
The deployment environment template documents the build-only variable without assigning an operator value.

## Complexity Tracking

| Existing debt | Reason to retain | Separate remediation |
| --- | --- | --- |
| Long script command blocks | Preserve the existing command flow during the narrow repair | Divide deployment command implementations in a separate issue |
| Release-note folder child count | The release process requires a unique fragment | Archive released fragments through the release coordinator |
