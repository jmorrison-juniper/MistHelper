# Contract: Restart Workflow

## Retry endpoint

`POST /api/runs/<run_id>/retry`

Accepted source states: `failed`, `stopped`, `cancelled`.

Success: HTTP 201 with `run_id`, `site_id`, `state=created`, `retry_of_run_id`, and schedule notes.

Refusal: HTTP 409 `run_not_retryable` for every live or successful state.

## Browser transition

After HTTP 201, the browser opens:

`/captures/new?site_id=<site_id>&run_id=<new_run_id>&role=pre`

The capture start request carries the new run identifier. When that capture verifies, **Continue the retry** opens `/runs/<new_run_id>/options` and does not call the create-run endpoint.

## Stop timing

A stop request written during a settle phase is observed before the next cloud poll. The driver does not wait for the phase's 30-minute deadline and does not record the interrupted phase as a terminal failure.
