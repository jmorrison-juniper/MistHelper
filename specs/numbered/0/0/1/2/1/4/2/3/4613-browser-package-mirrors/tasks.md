# Tasks: Browser package mirrors

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the documents under `design/`.

## Phase 1: Setup

- [x] T001 Record exact job evidence and the prior stall comparison in `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundation

- [x] T002 Resolve the managed feature route and validate the specification in `design/checklists/requirements.md`. (delivered: design/checklists/requirements.md)

## Phase 3: Preserve the browser test budget

**Goal**: Avoid the measured slow endpoint without changing package installation.
**Independent test**: Execute setup against temporary mirror files.

- [x] T003 [US1] Add setup success and failure contracts in `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`. (delivered: tests/guardrails/e2e_timeout_budget/test_browser_installation.py)
- [x] T004 [US1] Add validated mirror preparation before the unchanged installer in `.github/workflows/ci.yml`. (delivered: .github/workflows/ci.yml)

## Phase 4: Preserve validation strength

**Goal**: Keep every existing validation requirement and preserve the WAN upload.
**Independent test**: Reject workflow mutations and compare the baseline and #4208 workflow.

- [x] T005 [US2] Add installation and failure-policy mutation tests in `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`. (delivered: tests/guardrails/e2e_timeout_budget/test_browser_installation.py)
- [x] T006 [US2] Verify the unchanged workflow remainder and #4208 WAN upload in `.github/workflows/ci.yml`. (delivered: .github/workflows/ci.yml)

## Phase 5: Delivery

- [x] T007 Add `changelog.d/issue-4613-browser-package-mirrors.md` and complete the focused offline gates from `design/quickstart.md`. (delivered: changelog.d/issue-4613-browser-package-mirrors.md)
- [ ] T008 Analyze `spec.md`, `plan.md`, and `tasks.md`, commit the change, and open a linked pull request using `.github/PULL_REQUEST_TEMPLATE.md`. Analysis is complete. Publication waits for the coordinator's serial slot, currently assigned to #4604.

## Dependencies and execution

T001 and T002 precede implementation.
T003 precedes T004. T005 and T006 follow T004.
T007 and T008 follow both user stories.
The two stories share the workflow and test module, so implementation remains serial.
Documentation review can run independently from offline test execution.

## Implementation strategy

Deliver the route change and its contracts together.
Do not treat hosted-runner speed as locally verified.
A normal later CI run must measure the runtime criterion. No retry is authorized.
