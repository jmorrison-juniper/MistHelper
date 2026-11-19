# Implementation Plan: Confirmation dialog keyboard focus

**Branch**: `fix/4737-confirmation-keyboard-focus` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

## Summary

Pass the keyword field to the Headless UI dialog as its initial focus target.
Keep the mount-time effect for a keyword that appears in an open dialog.
Keep the exact keyword gate unchanged.

## Technical Context

**Language/Version**: TypeScript 6 and React 19.

**Primary Dependencies**: `@headlessui/react` 2.2.10, Vitest 5, and Testing Library React 16.

**Storage**: None.

**Testing**: Vitest in the jsdom environment with Testing Library.

**Target Platform**: Browsers that load the ops portal.

**Project Type**: Frontend component in `ops-portal/`.

**Performance Goals**: No added render or network work.

**Constraints**: Change one component, its tests, and one changelog fragment.

**Scale/Scope**: One dialog component for destructive actions.

## Constitution Check

This change adds no module, class, setting, network call, or prop.
The spec route is `0/0/1/2/2/4/2/2`, as `Resolve-SpecFeaturePath` calculates it.
The record folder holds three files, which is within the five-child limit.
The release fragment uses the issue name because no pull request exists yet.
The commit title uses Conventional Commits.
Auto-merge stays off.

## Project Structure

- `ops-portal/src/components/ConfirmationDialog.tsx`: Pass the keyword field as `initialFocus`.
- `ops-portal/src/components/ConfirmationDialog.test.tsx`: Settle focus before each focus assertion. Keep the gate tests.
- `ops-portal/src/components/ConfirmationDialog.focus.test.tsx`: Hold the cold-start regression test.
- `changelog.d/issue-4737-confirmation-dialog-keyboard-focus.md`: Add the release note.

## Research and Decisions

The focus trap schedules its initial focus after two animation frames. With `initialFocus`, it focuses that element. Without it, the cold-start case leaves focus on the dialog root.

The first portal of a module instance renders its children after an extra pass. The keyword field does not exist when the mount-time effect runs, so the effect does nothing in that case.

`initialFocus` gives the trap the field directly. The effect stays for a keyword that appears in an open dialog, because the trap does not run again.

A module instance keeps the portal state. The cold-start test therefore lives in its own file, so it renders the first dialog of that module instance.

The browser mechanism is not verified by this candidate. The jsdom result matches the reported browser result, and browser validation remains open.

## Data and Contracts

No data model, API, or prop changes.
The Confirm gate still compares the field value to the keyword with `===`.

## Validation Guide

Run these commands in `ops-portal/`:

```text
npm run typecheck
npm run lint
npm test
```

Run the mutation check. Remove `initialFocus` from the dialog, run `npm test -- src/components/ConfirmationDialog.focus.test.tsx`, and expect a failure. Restore the prop.

## Validation Results

- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0 with two existing warnings in files this change does not touch.
- `npm test`: exit 0. Two test files and 19 tests passed.
- Mutation check: removing `initialFocus` fails the cold-start test and leaves the other 18 tests passing.
- Browser validation: not run.
