# Implementation Plan: SSH Shell Execution Runtime Package

**Branch**: `4002-ssh-shell-execution-runtime` | **Date**: 2026-10-06

**Input**: Issue #4002 and the routed feature specification in `spec.md`.

## Summary

Move the shell execution package below `ssh/runtime`, update active references, add focused structure coverage, and preserve module symbols.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python standard library, Paramiko, pytest, and repository guard tools

**Testing**: Focused SSH tests, structure and symbol guards, compile, Ruff, Black, Mypy, Bandit, complexity, docstring, changelog, link, and test-quality gates

**Constraints**: Use `git mv`. Preserve source behavior. Add runtime metadata only. Do not add a compatibility wrapper.

## Design Decisions

### Decision: Nest the package under `runtime`

The SSH package currently has six structural children. The move produces five children without changing execution ownership.

### Decision: Use one canonical import path

Every active import and mock target changes to `ssh.runtime.shell_execution`. The old path has no forwarding module.

### Decision: Extend the existing symbol guard

The guard maps both moved Python files exactly, so module-level symbols remain checked at their new paths.

## Implementation Steps

1. Move `shell_execution/` with `git mv`.
2. Update active imports, mock targets, and the T013b comment.
3. Add the SSH structure guard and direct invalid-layout tests.
4. Add the symbol map entries, release note, and routed tasks artifact.
5. Run the required gates, commit locally, and report the commit SHA.
