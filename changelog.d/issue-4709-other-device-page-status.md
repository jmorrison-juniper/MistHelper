### Other-device event page status

- **Fixed**: The other-device event export checks every page status and writes nothing if a page fails.
  It rejects malformed records, invalid cursors, and repeated cursors.
  Successful empty results remain unchanged. Issue #4709.
