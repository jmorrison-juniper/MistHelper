### Upgrade portal startup dependencies

- **Fixed**: Normal startup now builds authenticated portal services inside
  each request and closes request-owned database clients. Issue #3834.
