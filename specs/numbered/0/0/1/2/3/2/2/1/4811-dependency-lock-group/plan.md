# Implementation Plan: Dependency lock group

**Branch**: `dependabot/pip/types-paramiko-5.1.0.20261030`

**Date**: 2026-11-15

**Spec**: [Specification](spec.md)

## Summary

Combine the five compatible dependency requests mapped in the specification.
Keep existing package resolutions except for requested updates and required dependency changes.
Generate `uv.lock`, `requirements.txt`, and `requirements-dev.txt` with UV.
Do not edit exporters or application code.

## Technical Context

**Language/Version**: Python 3.15.2.

**Primary Dependencies**: The five requested packages in the specification.

**Storage**: Dependency declarations, generated lock records, generated installation lists, and local recovery references.

**Testing**: Existing dependency guards, Ruff, mypy, SSH tests, and portal tests.

**Target Platform**: macOS for local checks and Linux ARM64 for an isolated container check.
The universal dependency lock retains other supported platform records.

**Project Type**: Existing command-line application and web portals.

**Performance Goals**: No product performance change.

**Constraints**: No publication before the coordinator supplies the serial publication slot.
Do not access another checkout's credentials or data.

**Scale/Scope**: Five requested package updates and five linked quality-gate issues.

## Constitution Check

- The routed feature root has at most five children. Supporting documents use `design/`.
- The existing repository root and `changelog.d/` exceed five children. Change only established dependency files and one unique process fragment.
- Separate remediation remains the existing process-folder migration. Do not expand its baseline or restructure unrelated files.
- Add no functions, classes, or product behavior. Existing dependency guards already prove failure on stale and missing inputs.
- Preserve exact original commits with local recovery references before replacing work.
- Use a Conventional Commit subject and explicit file staging.
- Keep cloud access blocked without authorized credentials and a verified staging organization.
- Use only temporary container resources named `misthelper-tmp-issue4811-*`. Publish no ports and mount no production data.
- The coordinator owns publication, CI, merges, and deployment. This local assignment stops before those steps.

The design review passes these checks. Container and staging prerequisites remain validation conditions, not assumed results.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/2/2/1/4811-dependency-lock-group/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
pyproject.toml
uv.lock
requirements.txt
requirements-dev.txt
changelog.d/pr-4806.md
```

Existing tests remain unchanged unless an introduced behavior requires a focused test.
No new public interface exists, so no interface contract document is required.

## Implementation and Validation

1. Apply the requested direct declaration updates. Use an exact upgrade selector for transitive stevedore.
2. Resolve with the requested UV version. Compare package versions against the original lock and investigate unrelated changes.
3. Generate both exports with `--locked --no-hashes --no-emit-project`, adding `--extra dev` for the development export.
4. Bootstrap this worktree. Run existing lock, export, and declaration guards, including their failure tests.
5. Run Ruff, relevant mypy paths, and SSH and portal compatibility tests. Do not suppress failures.
6. Attempt a project-policy isolated container smoke. Record prerequisites, exact commands, outputs, and cleanup.
7. Record Spec Kit analysis, explicit blockers, the exact local head, and the recovery-reference mapping.

## Complexity Tracking

No new executable abstraction or compatibility fallback is planned.
The only structural exception is the repository-required unique changelog fragment in an established process folder.
