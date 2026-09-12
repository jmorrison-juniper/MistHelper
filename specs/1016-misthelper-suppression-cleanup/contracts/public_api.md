# Contract: `MistHelper.py` Public API Surface

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Date**: 2026-07-13

**Status**: Frozen for the duration of workflow #1016 per FR-007 / SC-007.

## Purpose

This document is the authoritative baseline for the set of module-level names accessible on the `MistHelper` module object at the start of Story 1. Every PR in this workflow MUST preserve every name in this list; Story 1's `__all__` MUST be a strict superset of the inventory below.

## Method for capturing the inventory

Executed once at Story 1 preparation:

```bash
python -c "import MistHelper; print('\n'.join(sorted(n for n in dir(MistHelper) if not n.startswith('_'))))" > contracts/public_api_snapshot.txt
```

The output of the above command is the ground truth. The tabular inventory below is populated from that snapshot before Story 1 opens its PR.

## Public API inventory

**Snapshot date**: *(to be filled by Story 1 preparation, e.g., 2026-07-14)*

**Total public names**: *(to be filled)*

| Name | Kind (class / function / constant) | Origin (`src/*` subsystem or `MistHelper.py` local) | Notes |
|------|------------------------------------|------------------------------------------------------|-------|
| *(populated from `public_api_snapshot.txt` before Story 1 PR opens)* | | | |

## Verification recipe

To confirm the public API surface is unchanged at any point in the workflow:

```bash
python -c "import MistHelper; print('\n'.join(sorted(n for n in dir(MistHelper) if not n.startswith('_'))))" > /tmp/current_public_api.txt
diff contracts/public_api_snapshot.txt /tmp/current_public_api.txt
```

The `diff` MUST produce empty output. Any diff — including additions — indicates a public-API violation and blocks merge. Additions require a follow-up spec update; they cannot be introduced silently in a suppression-cleanup PR.

## Non-public names (excluded)

Names beginning with `_` are excluded from the frozen surface. This workflow is permitted to add, rename, or remove such names as part of helper extractions (Story 3) or Protocol / subprocess_runner introductions (Stories 4 and 7).
