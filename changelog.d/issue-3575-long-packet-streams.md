### Long packet captures on the WebSockets tab

- **Added**: An operator can select a capture duration from 60 through 3600 seconds.
  The card receives matching packet records throughout that duration. Issue #3575.
- **Fixed**: The portal confirms the regional stream subscription before capture start.
  An early stop checks the active capture identifier and sends a matching cloud stop. Issue #3575.
