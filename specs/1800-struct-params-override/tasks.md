# Tasks: Exempt Third-Party Overrides from STRUCT-PARAMS

**Spec**: `specs/1800-struct-params-override/spec.md`
**Issue**: #1800

## Phase 1: Implementation

- [X] T001 Add `_FIRST_PARTY_ROOTS` naming the packages the repository owns.
- [X] T002 Add `_third_party_import_names` collecting names bound from outside those packages.
- [X] T003 Add `_base_name` resolving a base expression to its leftmost bound name.
- [X] T004 Add `_third_party_override_methods` returning exempt method line numbers.
- [X] T005 Compute the exempt set once in `analyze`.
- [X] T006 Thread it into `_check_function` and fold it into the existing `noqa` path.

## Phase 2: Tests

- [X] T007 Cover a foreign from-import.
- [X] T008 Cover a first-party import, which must not be foreign.
- [X] T009 Cover a relative import, which is always first-party.
- [X] T010 Cover plain and aliased `import` forms.
- [X] T011 Cover a method on a third-party subclass, the real case.
- [X] T012 Cover a method on a first-party subclass, which stays subject to the rule.
- [X] T013 Cover a class with no bases.
- [X] T014 Cover a dotted base such as `requests.adapters.HTTPAdapter`.
- [X] T015 Cover a class nested inside a function.
- [X] T016 Cover a module with no foreign imports.

## Phase 3: Verification

- [X] T017 Confirm the `send` finding is gone and `MistHelper.py` reaches zero high-severity.
- [X] T018 Confirm `STRUCT-PARAMS` still fires repository-wide.
- [X] T019 Confirm the repository-wide score is unchanged.
- [X] T020 Run ruff, black, and mypy.
- [X] T021 Run the full unit and tools suites.
