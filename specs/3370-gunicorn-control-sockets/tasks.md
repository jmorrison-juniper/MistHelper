# Tasks: Distinct Gunicorn control sockets

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

## Phase 1: Setup

- [x] T001 Verify issue ownership and every open pull request file list. Reserve the exact feature files. (delivered: `specs/3370-gunicorn-control-sockets/plan.md`)
- [x] T002 Read the actual Gunicorn CLI and complete the isolated specification and plan. (delivered: `specs/3370-gunicorn-control-sockets/spec.md`)

## Phase 2: User Story 1

- [x] T003 Add parsed startup and failure contracts. (delivered: `tests/contract/container/test_gunicorn_control_sockets.py`)
- [x] T004 Add temporary real-master support. (delivered: `tests/contract/container/gunicorn_control_support.py`)
- [x] T005 Record the failing two-master baseline. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)
- [x] T006 Add distinct socket options. (delivered: `container/scripts/start.sh`)
- [x] T007 Verify startup and both SIGHUP orders with the real masters. (delivered: `tests/contract/container/test_gunicorn_control_sockets.py`)

## Phase 3: Delivery

- [x] T008 Update the operator guide and release note. (delivered: `documentation/container-deployment.md`, `changelog.d/issue-3370-gunicorn-control-sockets.md`)
- [x] T009 Run the applicable quality checks and container regressions. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)
- [x] T010 Complete the requirement and task analysis. (delivered: `specs/3370-gunicorn-control-sockets/analysis.md`)
- [x] T011 Review the exact file set and create the local commit with the required co-author. (delivered: `container/scripts/start.sh` and the ten-file local commit)

## Dependencies

T003 and T004 require T002.
T005 requires T003 and T004.
T006 requires the failing proof from T005.
T007 requires T006.
T008 can run after T006 without changing the test implementation.

T009 requires T007 and T008.
T010 and T011 require T009.

## Local Refresh on 2026-10-02

- [x] T012 Preserve the original commit and rebase onto the authorized `0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95`. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)
- [x] T013 Repeat all 22 socket cases and the 293-case current regression scope. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)
- [x] T014 Repeat the isolated native image proof and verify complete cleanup. (delivered: `specs/3370-gunicorn-control-sockets/analysis.md`)
- [x] T015 Run the current gates and prepare the complete offline template. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)
- [x] T016 Record the complete local-only refresh evidence and its publication boundary. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)

## Publication Boundary

Publication is not a local implementation task.
The parent must grant a verified-main release after issue #3215.
Do not push, create a pull request, merge, or deploy before that release.

## Granted Publication on 2026-10-02

The parent grants publication on actual main `66b1a1832e069a467d25034bc6024c2c7353e11e`.
The earlier local-only restrictions no longer block this sole position 21 window.
The production deployment restriction remains unchanged.

- [x] T017 Rebase onto the exact granted base and prove all unowned bytes remain unchanged. (delivered: `specs/3370-gunicorn-control-sockets/analysis.md`)
- [x] T018 Repeat the current host, native image, negative guard, cleanup, and configured quality proof. (delivered: `specs/3370-gunicorn-control-sockets/implementation.md`)

The persistent PR receipt will record the protected merge and actual-main proof.
Those later results must name the actual full revisions and complete source tree.
