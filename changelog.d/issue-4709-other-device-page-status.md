### Other-device event page status

- **Fixed**: The other-device event export checks every page status and writes nothing if a page fails.
  It rejects malformed records, invalid cursors, and repeated cursors.
  Empty-string terminal cursors remain valid. Unexpected local collection defects reach the caller.
  It also writes nothing if a final page shows fewer rows than its total, or bad page headers.
  Successful empty results remain unchanged. Issue #4709.
