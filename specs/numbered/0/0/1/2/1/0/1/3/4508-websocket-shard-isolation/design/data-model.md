# Replay State

The shell session owns its identifier and stored bytes.
The terminal controller owns one selected session generation.
A session change invalidates the previous read and creates a new terminal.

The stored replay and rendered rows are separate states.
The native visibility observer can pause the renderer after the bytes enter the buffer.
The test must expose the terminal before it requires rendered text.

The pending paste remains associated with the first shell.
Selecting the second shell closes the confirmation and discards its text.
