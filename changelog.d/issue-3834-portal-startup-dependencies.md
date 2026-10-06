### Request-safe upgrade portal dependencies

- **Fixed**: The portal builds services after authentication, keeps worker storage open during background work, and refuses work when storage is unavailable. Issue #3834.
