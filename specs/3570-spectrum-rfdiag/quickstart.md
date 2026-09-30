# Quickstart: Spectrum RF Diagnostics Validation

This guide shows how to validate the planned RF diagnostics feature after implementation. It does not include implementation code.

## Prerequisites

- Python 3.13 or newer.
- Project dependencies installed in the active environment.
- No live Mist tenant is needed for unit tests.
- Source package planned at `src/troubleshooting/rf_diagnostics`.
- Unit tests planned at `tests/unit/troubleshooting/rf_diagnostics`.

## Scenario 1: Spectrum analysis success

1. Use a fake site, fake AP, and fake API client.
2. Make the safe input fake choose spectrum mode and answer `y` at confirmation.
3. Make the start call return a `session` value.
4. Make the running-state call return running data first and then a final state.
5. Run the spectrum unit test.

**Expected result**:

- The start request uses `POST /api/v1/sites/{site_id}/analyze_spectrum` shape.
- The body includes `band` and the selected `device_id`.
- Polling uses the body-free running-state GET call.
- The printed result is clear.
- `data/RfDiagnostics.csv` receives one success row in the test data directory.

## Scenario 2: Spectrum analysis declined

1. Use the same fake site and AP.
2. Make the safe input fake answer Enter or `N` at confirmation.
3. Run the decline unit test.

**Expected result**:

- No start call is made.
- No poll call is made.
- One cancelled audit row is written.

## Scenario 3: Recording success

1. Use a fake site, client MAC, API client, wait dependency, and temporary data directory.
2. Make the safe input fake choose recording mode and answer `y` at confirmation.
3. Make start return an RF diagnostic identifier.
4. Make wait complete normally.
5. Make stop succeed.
6. Make download return non-empty bytes.
7. Run the recording success unit test.

**Expected result**:

- The start request uses `startSiteRecording` shape with `name` and `type`.
- The client MAC is normalized for the `mac` field.
- Stop runs after the wait.
- Download bytes are saved under `data/rfdiags/` in the test data directory.
- The saved file name includes site, client MAC, and run time in safe form.
- One success audit row includes the saved path.

## Scenario 4: Recording declined

1. Use fake site and client MAC values.
2. Make the safe input fake answer Enter or `N` at confirmation.
3. Run the recording decline unit test.

**Expected result**:

- No start call is made.
- No stop call is made.
- No download call is made.
- One cancelled audit row is written.

## Scenario 5: Ctrl+C during recording wait

1. Make start return an RF diagnostic identifier.
2. Make the wait dependency raise `KeyboardInterrupt`.
3. Make stop succeed.
4. Run the interrupt unit test.

**Expected result**:

- Stop is requested after the interrupt.
- The operation does not print a false success.
- The audit row shows the final outcome.

## Scenario 6: File and audit safety

1. Use a site name with spaces and unsafe characters.
2. Use a client MAC with separators and mixed case.
3. Make download return bytes.
4. Run the file naming and audit tests.

**Expected result**:

- The file name has no path separators.
- The file path stays under `data/rfdiags/`.
- `data/RfDiagnostics.csv` has exactly one row per run attempt.
- Output and audit values do not contain secrets.

## Suggested local commands after implementation

```powershell
python -m pytest tests/unit/troubleshooting/rf_diagnostics -q
python -m py_compile MistHelper.py
```

Run wider gates as required by the implementation task and pull request workflow.
