# Tasks: Source Domain Packages

## Phase 1: Structure

- [x] T001 Create the four domain packages and their group packages.
- [x] T002 Move all current source packages and direct modules through `git mv`.
- [x] T003 Confirm that each new hierarchy level has five children or fewer.

## Phase 2: Import Migration

- [x] T004 Update all Python imports to the new canonical paths.
- [x] T005 Update dynamic import strings and package configuration paths.
- [x] T006 Confirm that no old source import path remains.

## Phase 3: Tests

- [x] T007 Add structural tests for the direct-child limits.
- [x] T008 Add structural tests that reject old source import paths.
- [x] T009 Add representative public-symbol import tests for all domains.
- [x] T010 Run focused behavior tests for all moved domains.

## Phase 4: Documentation

- [x] T011 Update `documentation/CONTRIBUTING-MistHelper.md`.
- [x] T012 Update the source architecture overview and package diagram.
- [x] T013 Add `changelog.d/issue-3574-src-domain-packages.md`.

## Phase 5: Verification

- [x] T014 Run Python compilation for the source tree and entry points.
- [x] T015 Run Ruff, Black, and mypy.
- [x] T016 Run the exhaustive moved-module symbol guard and stable-path `symbol-diff`.
- [x] T017 Run the focused test groups.
- [x] T018 Run both required `pytest-chunks` sweep commands and record the bounded timeout results.
- [x] T019 Run SpecKit analysis and repair each finding.

## Phase 6: Delivery

- [x] T020 Rebase the committed branch onto the current `origin/main`.
- [x] T021 Rerun affected gates after the rebase.
- [x] T022 Push the branch and open a template-compliant pull request.
- [x] T023 Monitor the initial required checks and record each result.
