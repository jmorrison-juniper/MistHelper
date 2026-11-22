# Implementation Plan: Locked Bootstrap Sources

**Branch**: `jmorrison-juniper-fix-locked-bootstrap-mirror` | **Date**: 2026-11-15
**Spec**: [Specification](spec.md)

## Summary

The locked dependency record identifies its registry source.
Changing the primary UV index can make a valid lock appear stale.
The repair must preserve the lock and the contributor's explicit source policy.
The source-policy design remains blocked until both conditions can be met.

## Technical Context

**Language/Version**: Python 3.15 or newer.
**Primary Dependencies**: UV and pip.
**Storage**: The committed `uv.lock` and run-local child environments.
**Testing**: pytest and isolated local package indexes.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Worktree setup command.
**Constraints**: Do not alter dependency records, contact private mirrors, or expose source values.
**Scale/Scope**: One bootstrap policy and its directly related tests and documentation.

## Constitution Check

- The managed numeric route holds the specification.
- The new record does not add a direct child to the noncompliant `specs/` root.
- The existing process-folder debt requires separate incremental remediation.
- The bootstrap module and installation policy already exceed the five-item limits.
- Separate incremental remediation must reduce that debt without expanding this repair.
- No Mist Cloud transport is added.
- Product outputs remain under `data/`.
- A future commit must use the required Conventional Commit format.

## Project Structure

- `scripts/bootstrap_worktree.py`: source policy and locked synchronization.
- `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/`: focused regression tests.
- `documentation/development-setup.md`: contributor source-policy guidance.
- `changelog.d/`: one issue-specific release fragment.

## Design Gate

**Blocked**: A changed default index changes the lock's source identity.
An actual locked install used the locked primary, not the extra index.
Silently selecting the lock's public source can violate an explicit pip source policy.
The implementation must establish a safe source-policy contract before it changes the bootstrap.
