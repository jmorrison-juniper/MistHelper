# Owner Release Checklist: Release Publication

**Purpose**: Track the owner-only steps that run after the release merge commit exists.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

**Note**: The boxes stay unchecked until each owner step runs. Each step names its task and its scenario in `design/quickstart.md`.

## Before the Tag

- [ ] The release merge commit SHA is recorded (quickstart Scenario 10).
- [ ] The owner tags the release merge commit, not the current `main` head (OWN-001).
- [ ] The stamp in the CHANGELOG heading equals the stamp in `$STAMP`.
- [ ] No tag matches the release tag (research RC-04).

## Tag and Workflow

- [ ] The annotated tag is pushed (OWN-001).
- [ ] The remote tag peels to the release merge commit (quickstart Scenario 11).
- [ ] The release workflow ends with success (OWN-002).

## Assets and Image

- [ ] The release lists three assets (OWN-003).
- [ ] The stamp tag and the `latest` tag share one digest (OWN-004).
- [ ] The revision label equals the release merge commit (OWN-004).
- [ ] The observed version label is recorded with its cause (U-3).
- [ ] The merge-triggered container build is recorded (D-11, U-4).

## Release Text

- [ ] The title follows the release artifacts contract (OWN-005).
- [ ] The body keeps the compare link and the CHANGELOG link (OWN-005).

## Issue Record

- [ ] The summary comment lists OWN-001 to OWN-005 with each result.
- [ ] The owner files a separate issue for the merge-triggered container build (D-11).
- [ ] The owner reopens issue 4756 when it closed before these steps finished (edge case).
