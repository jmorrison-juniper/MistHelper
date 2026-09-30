### Added

- Added a WebSockets tab to the Operations portal. An operator can start, watch, and stop each Mist WebSocket stream from one page. The tab covers the 18 subscribe channels, the device utilities, the packet captures, and the remote shells. This fixes #3551.
- Added the `PORTAL_WS_*` settings to `deploy/.env.example`. `PORTAL_WS_ENABLE_CHANGES` and `PORTAL_WS_ENABLE_SHELL` stay off by default. While a flag is off, no utility that changes a device and no remote shell can start. See #3551.
