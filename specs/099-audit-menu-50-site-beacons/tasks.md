## Tasks for Export Site Beacons (menu_id:50)

1. Add spec files (specs/099-audit-menu-50-site-beacons) and update menu metadata
   - description: Create spec markdown placeholders and update any menu index referencing menu_id 50
   - depends_on: []

2. Inspect SiteClientExporter.beacons API surface
   - description: Read existing SiteClientExporter and identify endpoint, fields returned, pagination, and rate limits
   - depends_on: ["Add spec files"]

3. Implement flattening helper
   - description: Create a deterministic flatten_dict_for_beacons(record) that maps nested API fields to the flattened schema (includes beacon_id, site_id, timestamp, signal_strength, mac)
   - depends_on: ["Inspect SiteClientExporter.beacons API surface"]

4. Implement exporter function SiteClientExporter.beacons (or the menu wrapper)
   - description: Call API, page through results, call flatten helper, collect rows; call DataExporter.write_with_format_selection with file prefix 'site-{site_id}-beacons'
   - depends_on: ["Implement flattening helper"]

5. Add SQL export support and schema migration
   - description: Define SQLite table for beacons, implement composite_pk primary key (beacon_id, site_id, timestamp), create indexes, implement upsert logic
   - depends_on: ["Implement exporter function SiteClientExporter.beacons"]

6. Unit tests for flattening and upsert logic
   - description: Add unit tests covering normal records, missing optional fields, and timestamp parsing
   - depends_on: ["Implement flattening helper", "Add SQL export support and schema migration"]

7. Integration test for end-to-end export
   - description: Run exporter against sample data (test_input.txt or mocked API), assert CSV columns and SQLite rows/upsert behavior
   - depends_on: ["Unit tests for flattening and upsert logic"]

8. Documentation & README update
   - description: Add a short entry describing the new menu operation and usage examples; update version changelog
   - depends_on: ["Integration test for end-to-end export"]

9. Commit, run python -m py_compile, and push
   - description: Ensure syntax check passes, commit changes with version tag in message, and push
   - depends_on: ["Documentation & README update"]

(Complete all tasks; stop before implementation.)
