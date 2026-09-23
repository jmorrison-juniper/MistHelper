# Tasks: Prune test output from the portal output scan

**Input**: [spec.md](./spec.md) and [plan.md](./plan.md)

## Phase 1: Evidence

- [x] T001 Measure the production scan inside the container. Result: 56.0 seconds warm, 77.6 seconds cold, 802 files.
- [x] T002 Measure the same scan with `test-artifacts` pruned. Result: 3.0 seconds, 673 files.
- [x] T003 Find every test module that writes a test output folder under `data/`. Result: four modules, three folder names.

## Phase 2: Repair (User Story 1)

- [x] T004 Add `test-artifacts` and `test-control-byte-guard` to `EXCLUDED_DIR_NAMES` in `web_portal/services/output_scan.py`.
- [x] T005 Publish `last_walk_directories` from `OutputFileScanner._walk()`.

## Phase 3: Guards (User Stories 1 and 2)

- [x] T006 Test that a file under `test-artifacts/` stays out of the result panel.
- [x] T007 Test that the walk lists the root folder only, when a 40-run test output tree exists.
- [x] T008 Test that every test output folder that a test module names under `data/` is pruned.
- [x] T009 Prove that T006, T007, and T008 fail when the prune is removed.

## Phase 4: Verification

- [x] T010 Run the quality gates locally.
- [x] T011 Deploy the file to the 8055 server, and repeat T001 in the container.
- [x] T012 Time menus 69 and 229 in a browser against the container, before and after.
