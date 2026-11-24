# Contract: Menu 309

This contract describes what an operator sees and what the menu returns. Console text is ASCII only. The text uses plain words for a junior NOC engineer.

## Identity

- Number: 309
- Title: `Collect EX switch hardware inventory into one CSV report`
- Registry category: `resource_intensive`
- Skip reason: `Opens a shell on every connected EX switch - resource intensive, requires a typed confirmation`
- Handler: `ExHardwareInventoryReport.run`, a static method with no required parameter.
- Safety flags: `destructive=False`, `supports_fast=False`.
- Start: pick 309 in the menu, or run `python MistHelper.py --menu 309`.

The `--test` and `--testinteractive` sweeps skip this menu and print its skip reason.

## Settings

| Variable | Default | Range | Effect |
|----------|---------|-------|--------|
| `PORTAL_WS_HARDWARE_CONCURRENCY` | 3 | 1 through 5 | The most shells open at the same time. A bad value gives 3 and one warning that names the variable. |
| `org_id` or `ORG_ID` | none | A Mist UUID | The organization for a credential that has several organization grants. Not used in MSP scope. |
| `MIST_APITOKEN` or `MIST_API_TOKEN` | none | A Mist token | The credential. The tool never prints it. |

## Console sequence

The menu prints these steps in order. Names in angle brackets stand for run values.

```text
Step 1 of 4: Check the credential
  Credential: <API token or interactive login> (<organization token or user account>)
  Scope: <organization or MSP>
  Organizations in scope: <count>
  Note: <one sentence, only when a note exists>
Step 2 of 4: Find the connected EX switches
  <organization name>: <count> connected EX switches
  Left out: offline <count>, unknown status <count>, other device types <count>, repeated chassis <count>
  Total targets: <count>
Step 3 of 4: Confirm
  This run opens a read-only shell on each switch and runs one command:
    show chassis hardware detail | display xml | no-more
  Shells open at the same time: <value in use>
  Type RUN <count> TARGETS to start, or press Enter to cancel:
Step 4 of 4: Collect
  <organization name>: collected <count>, failed <count>, skipped <count>, cancelled <count>
Report: <path> (<row count> rows)
Run status: <complete or partial>
```

The `Left out` line appears for each organization with a count above 0. In MSP scope the menu prints one `Step 2` line for each organization and one total. The run status is `partial` when the operator cancelled or any target did not collect. A run with no target prints `No connected EX switch was found. No file was written.` and no `Report` line.

## Confirmation

- The menu reads the phrase through `InputUtils.safe_input` with the context `ex_hardware_confirmation`.
- The phrase is `RUN <count> TARGETS`, where `<count>` is the total of all organizations. The compare is exact after trimming. Case counts.
- Any other text, an empty answer, end of input, or an interrupt cancels the run. The menu prints `Cancelled. No shell was opened and no file was written.` and returns 0.

## Run rules

- The menu runs one organization at a time. Each organization runs as one batch.
- Before an organization starts, the menu previews it again. It runs only targets that the operator confirmed. If a target appears that the operator did not confirm, the menu skips that organization, prints `<organization name>: new switches appeared after the confirmation. Run the menu again.`, and goes on with the next organization.
- A Ctrl+C during the run stops the active batch, skips the remaining organizations, and writes the report with `cancelled` outcome rows.

## Return value and output

- The menu returns the number of report rows. It returns 0 when it wrote no report.
- The report file name is `ExHardwareInventory_<YYYYMMDDTHHMMSSZ>.csv`. The menu forces the CSV format for this file, whatever `OUTPUT_FORMAT` holds. The database backends still receive the rows.
- The run folder of each organization stays under `data/websocket-streams/<run id>/` with the saved XML and the manifest.

## Error messages

| Cause | Message |
|-------|---------|
| The profile cannot be read | `The Mist profile could not be read (HTTP <status>). No shell was opened.` |
| Several organization grants and no `org_id` | `This credential grants several organizations. Set org_id to the one to use.` |
| `org_id` is not among the grants | `org_id is not one of the organizations that this credential grants.` |
| The MSP organization list is denied | `The MSP organization list is not permitted for this account (HTTP 403). The run continues with the organization of the credential.` |
| No connected EX switch | `No connected EX switch was found. No file was written.` |
| More than 1000 targets in one organization | `<organization name> has <count> targets. The limit is 1000 for one batch.` |
| The report check fails | `The report file failed its check and was removed. See the log for the cause.` |
