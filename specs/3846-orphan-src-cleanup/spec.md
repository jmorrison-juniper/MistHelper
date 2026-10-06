# Feature Specification: Remove safe orphan source directories

**Feature Directory**: `specs/3846-orphan-src-cleanup/`

**Source Issue**: #3846

**Status**: Ready for implementation

## Context

A branch switch can leave an untracked directory directly under `src`.
An empty directory or a directory with only `__pycache__` files can change Ruff import classification.

The bootstrap must remove only safe orphan directories.
It must preserve committed packages and the source-root cache.

## User Story

As a developer, I want bootstrap to remove stale source directories safely, so local Ruff results match CI.

## Requirements

- **FR-001**: The bootstrap MUST inspect only direct child directories of `src`.
- **FR-002**: The bootstrap MUST consider only directories that Git does not track.
- **FR-003**: The bootstrap MUST remove a candidate only when every file is inside a `__pycache__` directory.
- **FR-004**: The bootstrap MUST preserve `src/foundation`, `src/interfaces`, `src/mist`, and `src/operations`.
- **FR-005**: The bootstrap MUST preserve `src/__pycache__`.
- **FR-006**: The bootstrap MUST print each removed directory name.
- **FR-007**: The bootstrap MUST print the checked candidate count and the removed count.
- **FR-008**: The bootstrap MUST keep a candidate that contains a file outside `__pycache__`.

## Acceptance Scenarios

1. Given an untracked empty directory, bootstrap removes it and reports its name.
2. Given the four canonical packages and `src/__pycache__`, bootstrap preserves all five directories.
3. Given an untracked directory with `module.py`, bootstrap preserves the directory and file.
4. Given three candidates and two safe removals, bootstrap reports three checked and two removed.

## Scope

This feature changes the bootstrap sweep and its focused unit test.
It adds this specification and one release-note fragment.
