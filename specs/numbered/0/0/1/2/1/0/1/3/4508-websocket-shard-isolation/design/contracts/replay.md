# Replay Test Contract

The controlled case keeps automatic scrolling disabled during selection.
It uses the native visibility observer to establish an offscreen terminal.
It holds only the first shell's replay response.

The response must contain the exact banner and prompt.
The terminal must show the banner after the test exposes it.
The pending paste must remain unsent after the second shell becomes active.

Removing the viewport precondition must make the controlled case fail.
The normal case must preserve the existing journey.
