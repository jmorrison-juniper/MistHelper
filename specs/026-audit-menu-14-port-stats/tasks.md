# Tasks

Each task below is an actionable item to prepare for implementation. Do not implement code in this phase; create only specs, definitions, skeletons, and review artifacts as indicated.

1. id: create-spec-folder-and-file
   - description: Create spec directory specs/026-audit-menu-14-port-stats and add spec.md (from this artifact).
   - complexity: small
   - dependencies: []

2. id: draft-primary-key-strategy_entry
   - description: Draft an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for menu_id=14 with composite_pk and primary_key [device_id, port_id, timestamp]; include recommended indexes and rationale in comments.
   - complexity: small
   - dependencies: [create-spec-folder-and-file]

3. id: define-schema-and-field-mapping
   - description: Produce a JSON/YAML schema mapping of API fields -> export columns (columns, types, nullable flags, example values) and add to spec dir.
   - complexity: medium
   - dependencies: [create-spec-folder-and-file, draft-primary-key-strategy_entry]

4. id: add-test-skeletons-unit-and-integration
   - description: Add pytest skeleton files under tests/test_port_stats_unit.py and tests/test_port_stats_integration.py with placeholders and clear TODOs for assertions (no implementation yet).
   - complexity: small
   - dependencies: [define-schema-and-field-mapping]

5. id: add-sql-verification-test-plan
   - description: Write concrete SQL verification test cases (steps) as a markdown file tests/sql_port_stats_test_cases.md describing setups, inputs, expected DB states, and rollback tests.
   - complexity: small
   - dependencies: [define-schema-and-field-mapping]

6. id: review-dataexporter-contracts
   - description: Review DataExporter.write_with_format_selection and document expected API (parameters, return) and how device_port_stats should invoke it; produce a short integration note in spec dir.
   - complexity: small
   - dependencies: [create-spec-folder-and-file]

7. id: document-migration-and-index-requirements
   - description: Draft migration steps (if any) to create required indexes and constraints for SQLite; include fallback guidance for older SQLite versions.
   - complexity: medium
   - dependencies: [draft-primary-key-strategy_entry, define-schema-and-field-mapping]

8. id: schedule-code-review-and-qa-checkpoints
   - description: Create a checklist and schedule for code reviews and QA validation once implementation is ready; include acceptance criteria mapping to tests.
   - complexity: small
   - dependencies: [add-test-skeletons-unit-and-integration, add-sql-verification-test-plan]

9. id: update-readme-and-menu-metadata
   - description: Draft README/menus.md entry update describing the new menu item (operations, required permissions, example command), add to spec dir as patch to be applied during implement.
   - complexity: small
   - dependencies: [create-spec-folder-and-file]

10. id: obtain-stakeholder-approval
    - description: Circulate spec and plan to stakeholders for review and sign-off.
    - complexity: small
    - dependencies: [create-spec-folder-and-file, define-schema-and-field-mapping, add-test-skeletons-unit-and-integration]

Priority order: create-spec-folder-and-file -> draft-primary-key-strategy_entry -> define-schema-and-field-mapping -> add-test-skeletons-unit-and-integration -> add-sql-verification-test-plan -> review-dataexporter-contracts -> document-migration-and-index-requirements -> update-readme-and-menu-metadata -> schedule-code-review-and-qa-checkpoints -> obtain-stakeholder-approval

Notes:
- None of the above tasks modify production code; they prepare all artifacts and validations so the implement phase can be executed in a single focused PR with clear test coverage and SQL expectations.

