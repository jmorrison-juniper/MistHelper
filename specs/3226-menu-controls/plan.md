# Plan: menu controls 6 through 10

## Root cause

`web_portal/services/operation.py` still declared parameter rows for old WebSocket menu numbers 6 through 10. `MistHelper.py` now maps those numbers to site analysis and organization inventory handlers.

## Design

Remove `PARAMETER_REGISTRY` entries for menus 6 through 10. The default portal behavior then renders no controls and passes no answers to handlers that do not prompt.

## Risks

- An open portal pull request also edits `web_portal/services/operation.py`, so the branch must rebase before push.
- Menus 8, 9, and 10 were in the extra-control backlog, so the backlog must shrink with the repair.
