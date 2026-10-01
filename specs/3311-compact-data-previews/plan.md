# Implementation Plan: Compact data previews

**Branch**: `jmorrison-juniper-compact-data-previews`

**Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

## Summary

The shared table rule breaks long preview values across many lines.
The results table already overrides that rule for issue #3048.
Extend those compact rules to the preview table.
Use DOM properties for complete values and a native dialog for keyboard and touch access.

## Technical Context

**Language/Version**: JavaScript, CSS, and Python 3.13.

**Primary Dependencies**: Existing Bootstrap, Flask, pytest, and Playwright.

**Storage**: Unchanged CSV files in temporary test directories.

**Testing**: Offline contracts, the actual Chromium modal, and existing preview and results tests.

**Target Platform**: The general portal normally serves port 8055.
The browser harness uses an assigned loopback port.

**Performance Goals**: Every rendered row stays at or below 60 pixels.

**Constraints**: No backend edits, dependency edits, production stores, or live Mist calls.

**Scale/Scope**: A 43-column file with 112 records and values of at least 558 characters.

## Constitution Check

The repair uses classes for new rendering and dialog behavior.
New methods remain small and use descriptive names.
Untrusted values enter the DOM through text properties.
The existing module has more than five functions.
This surgical repair does not restructure unrelated functions.
A separate future module split can reduce that existing debt.

The app owns the branch name and worktree.
The Unix SpecKit scripts are absent from `.specify/scripts/bash`.
Use the repository templates as file-only artifacts in this unique specification directory.
Do not change shared `.specify` state or rename the branch with Git.

The authenticated claim and exact reservation appear in the issue comment.
The parent controls the remote publication window.
Local implementation and a local commit do not authorize a push.

## Project Structure

### Documentation

```text
specs/3311-compact-data-previews/
  spec.md
  plan.md
  tasks.md
changelog.d/issue-3311-compact-data-previews.md
```

### Source and Tests

```text
web_portal/static/css/portal.css
web_portal/static/js/data_preview.js
tests/unit/web_portal/test_compact_data_preview.py
tests/e2e/test_data_preview_row_height.py
tests/support/data_preview_harness.py
```

## Design

Keep the compact CSS values that the results table uses.
Give preview cells a button with inherited text and a complete title.
Set cell and header text with `textContent`.
Keep button text unchanged so the existing export reads the same values.

A labeled native dialog displays the complete cell text.
It stays outside the table, so opening it does not enlarge a row.
Escape closes that dialog without closing the preview.
The browser restores focus to the cell control.
The dialog uses the existing theme variables.

The browser harness serves the actual templates and static files.
It uses temporary fixture data and no Mist credentials.
The fixture includes quotes, HTML markup, Unicode, newlines, empty values, and long values.

## Validation

Record the failing geometry before editing production CSS or JavaScript.
Keep the 60-pixel budget fixed.
Measure all rendered rows at each required width and in every shipped theme.
Check all column boundaries and both scroll directions.
Compare pagination, full-value text, and exported records with the response.

Run existing data browser pagination, column order, row order, and streaming tests.
Run the existing results table browser tests.
Run syntax, Ruff, Black, configured types, Bandit, and the configured test-quality ratchet.
Run Markdown link checks and the configured STE linter.
Report `dictionary_unavailable` as partial STE evidence, not complete dictionary grading.
Audit the current runtime dependency manifest without changing its versions.

## Release and Coordination

Add one release-note fragment for issue #3311.
Commit only the reserved paths with a Conventional Commit and the required coauthor trailer.
Report the local commit, measured bounds, artifacts, and exact validation commands.
Stop before a push or pull request until the parent gives an explicit publication grant.
