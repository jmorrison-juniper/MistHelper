### Security

- Stop the WebSocket, routing payload, and ARP command code from using the `MIST_APITOKEN` environment token when the active session has no token. A request can no longer run as a different account. Part of #2861.
