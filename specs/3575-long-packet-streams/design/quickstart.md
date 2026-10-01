# Local Validation: Long packet streams

## Prerequisites

Use this issue's isolated app worktree and its Python 3.13 environment.
The bootstrap installs the current manifests and Chromium.
No Mist credentials or cloud connection are needed.

## Operator behavior

If you select a packet capture, enter a duration from 60 through 3600 seconds.
The initial duration is 60 seconds.
The capture can end earlier when it reaches the selected packet limit.
If you press Stop, the portal checks the active capture before it requests cloud stop.
If that request fails, the card shows the failure.

## Local commands

Run the focused capture, contract, and browser cases.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q \
  tests/unit/websocket_streams/live/captures \
  tests/contract/websocket_streams/test_long_packet_streams.py \
  tests/e2e/websocket_streams/test_long_packet_streams.py
```

Run adjacent WebSockets cases.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q \
  tests/unit/websocket_streams tests/contract/websocket_streams \
  tests/e2e/test_websockets_page.py tests/e2e/websocket_streams
```

The focused cases must report no failure, error, or skip.
The browser uses the actual controller and card.
Every network request stays on a controlled local fixture.
The local stream and server stop before fixture cleanup ends.

## Required evidence

Record the old cutoff and order failures before implementation.
Record matching records at 59, 61, 119, and 3599 seconds.
Record one confirmed cloud stop and zero unrelated stops.
Record every terminal path's owned connection and thread counts.
Record focused coverage and each required local quality command.
Keep the evidence outside tracked source files.

## Publication

Commit the complete local change.
Do not push or create a pull request without the parent's full verified main SHA grant.
The observed base does not authorize publication.
