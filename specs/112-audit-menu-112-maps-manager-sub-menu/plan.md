# Plan: Audit Maps Manager sub-menu (Menu 112)

Goal

Audit code paths for the Maps Manager sub-menu, identify missing tests and export support, and produce tasks to bring the handler to project standards.

Approach

1. Code discovery: locate all Maps Manager handlers in MistHelper.py and maps_manager.py.
2. Static analysis: read code for data-export patterns and identify endpoints that return lists/tables.
3. Test coverage scan: check tests/ for existing test cases that exercise the Maps Manager commands.
4. Create tasks: produce specific tasks to add unit tests, integration tests (mocking Mist API responses), and DataExporter integration.
5. Validation: ensure tasks include file paths, sample input/output, and acceptance criteria.

Milestones

- Discover handlers (1 day)
- Produce tasks and sample test skeletons (1 day)
- Record ENDPOINT_PRIMARY_KEY_STRATEGIES entries required (0.5 day)

Deliverables

- tasks.md with concrete tickets
- sample test skeletons saved under tests/test_maps_manager.py (as a follow-on implementation task)

Risks

- Missing or unclear API endpoints in maps_manager.py
- Tests may require significant mocking for complex map structures

