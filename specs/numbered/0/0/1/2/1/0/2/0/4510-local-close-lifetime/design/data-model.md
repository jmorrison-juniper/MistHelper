# Connection lifetime model

One connection owns one runtime and one reader.
The reader and connection close path reference the same runtime.
The runtime holds the raw socket, a receive lock, and a close event.

| State | New receive | Close behavior |
| - | - | - |
| Open | Acquire the lock, inspect the event, then read | Set the event and abort |
| Closing | Raise a closed-connection error | Wait for the active read before descriptor release |
| Closed | Raise a closed-connection error | Preserve safe repeated close |

No persistent schema, logger name, class module identity, or public session state changes.
