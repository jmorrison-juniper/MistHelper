# Tasks for Audit - Menu #4: Gateway Management IPs

T001 - Add PK strategy entry
- Update `ENDPOINT_PRIMARY_KEY_STRATEGIES` in MistHelper.py to include `gatewayManagementIPsExport`.
- Choose `composite_pk` with `primary_key`: ["gateway_name", "template_id"] and appropriate indexes.
- Run `pytest tests/unit/test_pk_strategies.py` to ensure structural validation passes.

T002 - Update management_ips export call
- Replace `DataExporter.save_data_to_output(final_results, "GatewayManagementIPs.csv")` with:
  ```python
  DataExporter.write_with_format_selection(final_results, "GatewayManagementIPs.csv", api_function_name="gatewayManagementIPsExport")
  ```
- Ensure column names in `final_results` match PK strategy (include `gateway_name`, `template_id`, `site_id` if used).

T003 - Fix device lookup bug and improve robustness
- Replace unused dict comprehension with `device_lookup = {dev.get('name'): dev for dev in gateway_devices}`.
- Use `device_lookup` for status resolution and add fallback by MAC or ID if duplicate names detected.
- Add logging warnings for duplicated gateway names.

T004 - Add unit tests
- Create `tests/unit/test_gateway_management_ips.py` to cover:
  - Normal mapping and output to DataExporter (mocked)
  - Missing management IPs
  - Duplicate gateway names across different site_ids
  - Ensure DataExporter.write_with_format_selection receives correct `api_function_name`

T005 - Update documentation
- Update README.md or relevant spec files noting the new PK strategy and dual-output compliance for menu #4.

T006 - Run test suite and validations
- Run `python -m py_compile MistHelper.py` to ensure syntax
- Run `pytest -q` and fix any failures.

T007 - PR and changelog
- Commit changes with message: `version YY.MM.DD.HH.MM - Add SQL export support for gateway management IPs` (UTC timestamp)
- Include `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` in commit trailer.
- Push branch and open PR for review.


Priority ordering: T001 -> T002 -> T003 -> T004 -> T006 -> T005 -> T007

Estimated durations:
- T001: 15-30 minutes
- T002: 30-60 minutes
- T003: 30-60 minutes
- T004: 1-2 hours
- T005: 15-30 minutes
- T006: 15-45 minutes
- T007: 15-30 minutes


-- End of tasks
