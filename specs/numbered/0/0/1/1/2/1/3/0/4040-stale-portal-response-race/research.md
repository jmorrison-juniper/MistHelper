# Research: Stale Portal Response Ownership

## Decision

Compare each response menu number with the selected menu number before the success or failure path changes page state.

## Rationale

The selected menu changes before its parameter request completes. A response from an earlier request can arrive later and update shared panels. A check at each completion path keeps the current selection as the owner of those panels.

## Alternatives Considered

- Cancel the earlier request. Cancellation alone cannot prevent a response that has already completed from reaching its handler.
- Check only the successful response. A delayed failure can still show an error for the wrong menu.
- Add a request-generation system. The selected menu number already supplies the ownership value.

## Unknowns

No unresolved technical choices remain. The issue assessment reproduced both stale success and stale failure behavior.
