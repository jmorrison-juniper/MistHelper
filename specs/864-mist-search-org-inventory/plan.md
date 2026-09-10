# Implementation Plan: searchOrgInventory

1. Add an organization inventory search exporter with EOF-safe prompts for the
   SDK-supported query parameters.
2. Register menu 254 as an interactive read-only operation and route its output
   through `DataExporter.write_with_format_selection`.
3. Confirm the existing composite primary-key strategy for search rows and keep
   its indexes aligned with the inventory fields.
4. Add unit coverage for the SDK call, filter forwarding, empty-org handling,
   empty responses, persistence, and error logging.
5. Update the generated menu reference, README, and changelog, then run the
   targeted tests and repository quality checks.

The installed SDK exposes `model` and `name` for this endpoint. The source
issue lists older `vc_mac` and `master_mac` names, so the implementation follows
the installed SDK signature and its generated API documentation. The repository
already had the composite `searchOrgInventory` key strategy, so no duplicate
catalog entry is added.
