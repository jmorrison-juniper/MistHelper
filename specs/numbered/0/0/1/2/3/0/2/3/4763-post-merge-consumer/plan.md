# Implementation Plan: Main workflow recovery

**Branch**: `jmorrison-juniper-post-merge-consumer-integration` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

## Summary

Pin the existing reusable auto-merge call to the reviewed revision.
Add `ste-lint.yml` to the existing main workflow list.
Extend the existing consumer guard and preserve all other workflow behavior.

## Technical Context

The change uses GitHub Actions YAML and the existing Python pytest guard.
The workflow list names `ci.yml`, `codeql.yml`, `container-build.yml`, and `ste-lint.yml`.
Each accepts `workflow_dispatch` and a push to main.
The container workflow filters push paths, but manual dispatch has no such filter.
No Mist Cloud transport, data schema, or production operation changes.

## Constitution Check

Use the managed numeric route and one unique release fragment.
The process folder has existing child-count debt.
The separate baseline migration continues to track its incremental reduction.
The existing guard class exceeds the five-member limit.
A separate guard refactor can reduce that debt without expanding this repair.
No product output path or required status name changes.

## Validation

Run the existing guard before and after the consumer edit.
The first run must reject the old pin and the incomplete list.
Check lint, formatting, and the managed record guard where available.
Hosted immediate and delayed acceptance requires a later approved ordinary merge.
