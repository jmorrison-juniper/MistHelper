# Launcher reporting contract

`launch()` continues to return `None`.
It does not propagate an ordinary TUI exception or `KeyboardInterrupt`.
The common exit helper retains its existing no-argument signature.

| Outcome | Success | Fatal error | Interruption | Menu return |
| - | - | - | - | - |
| Normal return | Once | None | None | Once |
| Ordinary exception | None | Once | None | Once |
| Keyboard interrupt | None | None | Once | Once |
| Session initialization failure | None | None | None | None |

Console handlers return before the success and menu return messages.
File handlers remain attached during the TUI run.
Debug timestamps remain available on all three completion paths.
