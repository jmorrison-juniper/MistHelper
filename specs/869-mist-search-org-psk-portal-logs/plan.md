# Implementation Plan: searchOrgPskPortalLogs

## Approach

1. Extend the existing `OrgSearchExporter` shared org-search flow with a
   `psk_portal_logs` entry that calls the installed Mist SDK binding.
2. Register menu 250 in `MistHelper.py` because menu 249 is already used by
   `searchOrgDevices` from Spec 863.
3. Keep the existing `searchOrgPskPortalLogs` composite primary-key strategy
   (`id`, `timestamp`) so the standard writers upsert repeat results.
4. Add focused unit tests for endpoint binding, export, pagination, empty data,
   and logged API failures.
5. Update the README, menu references, and changelog, then run the targeted
   tests and quality gates.

## Design Notes

- The shared org resolver uses `safe_input()` through
  `ConfigUtils.get_cached_or_prompted_org_id()`.
- The shared `mistapi.get_all()` call preserves paginated retrieval.
- `DataExporter.write_with_format_selection()` remains the only persistence
  path.
- No live Mist credentials are needed for the tests.
