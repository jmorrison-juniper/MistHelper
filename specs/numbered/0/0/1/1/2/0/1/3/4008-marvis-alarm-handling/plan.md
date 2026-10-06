# Implementation Plan: Marvis Alarm Handling Package

**Branch**: `4008-marvis-alarm-handling` | **Date**: 2026-10-06

## Summary

Move the two Marvis alarm modules into
`src/mist/intelligence/marvis/actions/alarm_handling/`. Update active imports,
test patch targets, logger targets, documentation, and generated menu maps.
Add exact structure and symbol-preservation coverage. Do not add wrappers.

## Technical Context

**Language**: Python 3.13 or newer

**Dependencies**: Existing MistHelper runtime and test dependencies

**Testing**: Focused Marvis tests and repository quality gates

**Target Platform**: Windows 11, macOS, and Linux

## Constitution Check

| Principle | Verdict | Reason |
| --- | --- | --- |
| Five-Item Rule | Pass | The actions package has five structural children. |
| Class-Based Architecture | Pass | The move changes location, not behavior. |
| Safety-First | Pass | Alarm acknowledgement keeps its typed confirmation. |
| Full Deployment Pipeline | Pass | Required local gates run before the commit. |
| Observability | Pass | Existing logger names and calls stay unchanged. |

## File Boundary

Change only the moved modules, their active callers and tests, the focused
guards, active documentation, generated menu maps when changed, the changelog
fragment, and the three routed specification files.
