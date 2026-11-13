# Replay Visibility Evidence

## Decision

Ensure that the terminal enters the viewport before the test waits for rendered replay text.
Add a controlled browser case for the native rendering pause.

## Rationale

The original focused test passes in 5.17 seconds.
The original offline shard passes all 201 tests in 240.72 seconds.
These results do not establish shared-state contamination.

The failed CI trace contains three successful initial terminal responses.
Each response contains the same complete 44-byte banner and prompt.
The third response belongs to the selected first shell.
Its new xterm rows remain blank throughout the failed wait.
The page scroll position remains 24 pixels, above the terminal.

The controlled experiment prevents automatic scrolling during the session change.
It holds the replay response until the native visibility observer reports the terminal outside the viewport.
The response then contains the correct bytes, but the rendered rows remain blank.
The banner wait fails.
Scrolling the terminal into view renders the banner without another initial replay request.

The committed control extends the original paste isolation journey.
Before the repair, the normal case passes and the controlled case fails at the same 15-second banner wait.
The TDD run reports one failure and one pass in 23.20 seconds.
After the repair, both cases pass in 9.89 seconds.
The complete offline shard then reports 202 passes in 244.22 seconds.

The configured CI type gate reports no issues in 884 source files.
A separate direct type check of the test module reports seven errors.
The unchanged main version reports the same seven errors through `--shadow-file`.
Those errors do not belong to this repair.
The full test-module complexity scan also reports the unchanged `_assert_form_is_unselected` function at complexity 12.
The changed journey and helper methods pass the complexity threshold of 10.

The fixture creates a new fake cloud and service manager for each journey.
The browser page also has a test-scoped context.
No observed cross-test state explains the recorded failure.
The fake device supports shared records across two connections within this journey.
The repair does not change that existing fixture behavior.

## Alternatives Considered

- Increasing the timeout cannot render a terminal that remains outside the viewport.
- Replacing the service manager does not address the successful stored response.
- Changing the production renderer would remove its intended visibility optimization.
- Retrying the test would conceal the missing display precondition.

## Evidence Location

The source artifact is `e2e-diagnostics-websockets-tab` from [CI run 41004092559](https://github.com/jmorrison-juniper/MistHelper/actions/runs/41004092559).
Local diagnostics remain in the ignored `test-artifacts/` folder.
No credential or signed artifact URL enters a committed record.
