# Data Model: Discoverable Upgrade Confirmation Navigation

No new persisted entities are introduced.

## Existing values used

- `run.state`: Must equal `awaiting_confirmation` for the new action.
- `run.pre_capture_id`: Must be present to indicate a verified pre-check exists.
- `run.run_id`: Identifies the destination path.
- Confirmation-page safety state: Re-read by the existing confirmation route from the current run and site lock.
