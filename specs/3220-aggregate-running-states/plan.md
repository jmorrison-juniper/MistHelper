# Implementation Plan: Keep a running multi-site job active

**Issue**: #3220 | **Spec**: [spec.md](spec.md)

## Technical Context

- Python 3.13, Flask, no new dependency.
- Files: `src/firmware/aggregate_upgrade_service.py`,
  `src/upgrade_portal/app/routes/org_upgrade.py`,
  `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`,
  `src/upgrade_portal/app/assets/static/js/portal.js`.
- Evidence: the Mist OpenAPI enums `upgrade_org_devices_upgrade_info.status`,
  `response_site_device_upgrade.status`, and `response_device_upgrade.status`
  in `documentation/mist-api-openapi3json.json`.

## Design

1. Add `CLOUD_RUNNING_WORDS`, `CLOUD_COMPLETED_WORDS`, `CLOUD_FAILED_WORDS`, and
   `CLOUD_KEPT_WORDS` to the service.
2. Add `AggregateUpgradeService._child_state`, one static rule that maps a cloud
   word to the service vocabulary. An unknown word maps to `read_unknown`,
   because that state stays readable and active.
3. Apply the rule in `_read_org_child` and `_read_device_child`. Keep the exact
   word in `cloud_status`.
4. Use the running words in `_combined_site_status`.
5. Change `_operation_is_settled` to read each child. Add
   `FINAL_WRITE_STATES`. Remove `attention_required` from
   `SETTLED_OPERATION_STATES`, which now serves a record with no child only.
6. Remove `attention_required` from `ORG_UPGRADE_FINISHED_STATES` in
   `portal.js`, and show the cloud word in each child row.

## Constitution Check

- Safety first: the change keeps a lock in every doubtful case. A lease that no
  read reconciles expires on its own.
- No wrapper, no shim: the rule lives in the service class.
- Tests: unit tests for each enum word and each lock case, one contract test
  change, and the journeys of #3200.

## Risks

- A child that never reports a final word keeps its sites until the lease
  expires. That is the safe outcome for a write in doubt.
- The contract test for a cancel now expects the locks to stay until the next
  read shows every child final.
