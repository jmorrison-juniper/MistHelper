# Tasks: Correct the documents and map each menu option to its Mist API endpoints

**Issue**: #3411 | **Plan**: [plan.md](plan.md)

## Phase 1: Prepare

- [x] T001 Create issue #3411, the worktree `MistHelper-i3411`, and the branch
  `feat/3411-docs-audit` from `main`.
- [x] T002 Build prototype 2 of the analyzer, and measure each rule.
- [x] T003 Run `npm ci` in `scripts/mermaid`, and record the lint baseline. The
  Mermaid lint parsed 38 blocks in 17 files. The reference lint checked 124
  references in 15 files.

## Phase 2: The endpoint map tool (US2, US5)

- [x] T004 Write `tools/menu_api_map/analysis/` from the prototype.
- [x] T005 Write the SDK index reader, the refresh command, and
  `reference/sdk_index.json`.
- [x] T006 Write `reference/curated.json` with the shared helpers and the dynamic
  dispatch cases.
- [x] T007 Write `tools/menu_api_map/render/` and the command line.
- [x] T008 Write the unit tests. One test proves that `--check` fails on a
  stale page.
- [x] T009 Generate `documentation/menu-api/` and the wiki pages.
- [x] T010 Add the check to the `menu_reference_drift` job.

## Phase 3: The audit fleet (US1, US3, US4)

- [x] T011 Slice A: `README.md` and the wiki.
- [x] T012 Slice B: the core, infrastructure, and operations diagrams.
- [x] T013 Slice C: the class hierarchy diagrams.
- [x] T014 Slice D: the operator guides.
- [x] T015 Slice E: the API and reference documents.
- [x] T016 Slice F: the contributor and internal documents.
- [x] T017 Slice G: the NOC runbooks and the CodeQL verdict register.
- [x] T018 Slice H: the agent instruction files.
- [x] T019 Slice I: the other root files, the platform documents, and the tool
  README files.

## Phase 4: Validate and merge

- [x] T020 Review each ledger, and check a sample of each slice by hand.
- [x] T021 Run every lint, the tool check, the STE linter, and the tests.
- [x] T022 Add the release note under `changelog.d/`.
- [x] T023 Open the pull request, wait for every check, and merge.
