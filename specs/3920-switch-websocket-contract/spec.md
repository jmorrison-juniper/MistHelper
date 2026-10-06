# Switch WebSocket request contract

## Problem

Switch shell and ARP requests must use the Mist device request contract.
The command stream must subscribe to the documented device command channel.

## Scope

- Preserve the empty request body for a standalone shell session.
- Forward an optional HA node for shell and ARP requests.
- Preserve the exact command channel `/sites/{site_id}/devices/{device_id}/cmd`.
- Test the request body and channel payload without cloud credentials.

## Acceptance criteria

- A standalone shell request sends `{}`.
- A node-scoped shell request sends `{"node": "node0"}` or `{"node": "node1"}`.
- A switch ARP request retains `duration` and `interval` and forwards `node`.
- The stream client sends one JSON subscription for the documented command channel.
