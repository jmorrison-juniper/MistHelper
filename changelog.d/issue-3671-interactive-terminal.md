### Added

- The WebSockets tab now shows an xterm.js terminal for shell sessions, with
  copy, paste, resize, and history controls. Issue #3671.

### Fixed

- The WebSockets client now removes the `0x00` channel byte and reports an
  empty device close as a normal end. Issue #3659.
- Device commands now wait for the stream subscription before the trigger
  request, so first output lines are no longer lost. Issue #3660.
- A terminal that gets no output from the device now shows a notice after 20
  seconds. When the Mist cloud closes it, the session ends as failed with a
  plain reason. Issue #3710.
