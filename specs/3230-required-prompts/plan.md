# Implementation Plan: Required portal prompts

## Root cause

`web_portal/services/operation.py` did not declare controls for required plain prompts in menus 235, 237, 238, 242, 247, 259, 260, and 262. `web_input_context` therefore passed an empty answer to a prompt that rejects empty input.

Menus 263 through 268 ask for an endpoint first. The later prompts depend on the selected endpoint. A fixed control list cannot answer those rows safely.

## Design

Add one marked block before `return registry` in `_build_registry()`. The block builds chooser options from `src.export.count_exporter` and `src.export.simple_endpoint_exporter` tables. This keeps the portal choice list aligned with the CLI chooser.

Mark menus 263 through 268 as `cli_only`. The message states the per-choice prompt limit and gives the `python MistHelper.py --menu N` path.

## Risks

- A copied chooser list can drift. The guard test compares the options to the source table.
- A dynamic endpoint family row can still strand an operator. The registry hides Run for those rows.
