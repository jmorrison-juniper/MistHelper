# Analysis: Read-only Mist target discovery for converter proposals

This review compares `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. It lists defects in the existing work and the items that remain open.

## Consistency Review

- Each functional requirement maps to at least one task and one test. The coverage matrix in `tasks.md` shows the mapping. FR-017 maps to the existing nested-package guard (T015), not to a new test.
- Each task names exact paths. The paths for T009 to T014 match the file-by-file change map in `plan.md`.
- The task count is 20: sixteen implementation, test, and guard tasks, plus four delivery tasks (`T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, `T-MERGE`).
- The test count is 24: twenty-two integration tests (TC-01 to TC-22) and two browser tests (TC-23 and TC-24).
- The decision IDs D-1 to D-13 in `research.md` match the references in `spec.md`, `plan.md`, and the contracts.
- The state set matches the issue text: verified, unavailable, denied, and failed. The parity contract also names pending (R04). This record keeps pending as the page label only (D-4).
- The reason codes in `design/contracts/discovery-http.md` match the enumeration in task T009 and the mapping in D-5.
- The route names in the contracts match the rules in the plan and the tests in `tasks.md`.

## Parity Map Deviations

- T019 names `tests/contract/cisco_config_converter/test_discovery.py` (R01). The `tests/contract` folder holds seventeen children (R76). A new child there breaks the constitution rule (R31). This record places the tests under `tests/integration/web_portal/cisco_config_converter/` (D-10).
- T020 names `routes.py` for the discovery code (R02). `ConverterRoutes` holds five members (R15), and the converter root holds five children (R75). This record keeps the handlers in `routes.py` as a new class and places the client in `src/mist/access/targets/` (D-1, D-2).

## Defects in Existing Work

1. The parity task T019 path breaks the Five-Item Rule for `tests/contract` (R31, R76). Correction owner: the parity record. This record does not edit that record.
2. The parity task T020 places discovery code in `routes.py`. The class `ConverterRoutes` already holds five members (R15), so the handlers need their own class. A separate discovery module in the converter root would add a sixth child (R75). Correction owner: the parity record.
3. The issue #4642 comment states that PR #4596 is open and behind `main` (R14). PR #4596 merged on 2026-11-13. Correction owner: the issue author. This record does not edit issues.
4. The sibling record for issue #4636 states in `_meta/4636-summary.md` that it holds 60 remote checks. Its `_meta/4636-STATUS.json` holds 24 remote checks. The two counts disagree. Correction owner: the author of record #4636. This record does not edit that record.
5. The converter test folder `tests/integration/web_portal/cisco_config_converter/` holds two children now (R78). Records #4636, #4641, and #4642 each add one child. The folder then holds five children, which is the limit. Any later child breaks the rule.

## Unresolved Items

- U1 to U8 in `design/research.md` remain open. U1 to U3 belong to issue #4634. U8 belongs to issue #4648.
- The merge order matters. `routes.py` is shared by #4636, #4641, and #4642. The planned order is #4634, then #4641, then #4642, with #4636 merged before #4641 when both are ready.
- The browser tests need the browser runtime from the repository bootstrap. Without it, TC-23 and TC-24 cannot run.
- A target change dispatches an event with no listener until #4641 lands. The review state stays unchanged in that window. The merge order closes that gap.
- No live Mist request was made for this record. Every Mist claim cites the OpenAPI file or the installed SDK.
- No human decision is required for this record. Each decision has an alternative and a reason in `research.md`.
