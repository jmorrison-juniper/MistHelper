# Implementation Plan: Sign-In Narrow Viewport Layout

**Branch**: `jmorrison-juniper-fix-4539-sign-in-overflow` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/1/1/2/4/4539-fix-signin-overflow/spec.md`.

## Summary

The sign-in page is 400 pixels wide at a 390-pixel viewport because its service table has no scroll container. Use the existing table scroll box and verify the sign-in flow remains usable.

## Technical Context

**Language/Version**: CSS, HTML, and Python 3.13 or newer.

**Primary Dependencies**: Local Bootstrap styles and Playwright browser tests.

**Storage**: Not applicable.

**Testing**: Pytest with Chromium.

**Target Platform**: The upgrade portal in desktop and mobile browsers.

**Project Type**: Web portal.

**Performance Goals**: No performance change.

**Constraints**: Do not contact the Mist cloud. Preserve sign-in behavior. Do not hide overflowing content.

**Scale/Scope**: One portal page, one responsive defect, and one browser regression test.

## Constitution Check

- **Structure**: The new specification uses the required eight-level base-5 route. The feature root will have no more than five children.
- **Process record**: `changelog.d/` has 272 tracked top-level files. The required issue-specific fragment adds one unique record. Directory cleanup is a separate task and remains out of scope.
- **Source scope**: The layout change touches an existing stylesheet. The regression test stays in the existing browser-test directory.
- **Mist Cloud**: The local browser test uses a test portal and makes no live Mist request.
- **Feature pointer**: `.specify/feature.json` points to issue 4258 and is tracked. This change will not overwrite that pointer.
- **Gate**: Pass. The planned work adds no new package, dependency, data store, or external interface.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/1/1/2/4/4539-fix-signin-overflow/
  spec.md
  plan.md
  tasks.md
  design/
    data-model.md
    quickstart.md
    research.md
    checklists/
      requirements.md
```

### Source Code

```text
src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html
tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py
changelog.d/issue-4539-signin-overflow.md
```

**Structure Decision**: Use the existing table scroll box in the sign-in template and keep the regression in the existing journey test. Add only the required issue-specific release note.
