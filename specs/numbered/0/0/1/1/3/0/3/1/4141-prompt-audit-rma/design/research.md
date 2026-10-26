# Research: Juniper RMA prompt audit

## Decision

Repair traversal in the shared development tool.
Count selectable dependent controls in the existing MistHelper guard.

## Evidence

The pinned audit reports `ok` with zero prompts for all seven menus.
The existing guard passes 70 tests because the exemption set excludes these menus.
`PromptWalker._call_name` already recognizes dotted `safe_input` calls.
The walk loses constructor method targets and class context.
Its global plain-name visit set also removes repeated calls.

Menus 295, 297, and 303 place their identifier in `dynamic_parameters`.
Their two identifier choices are mutually exclusive.
Counting only static parameters omits one control.
Adding both identifier branches incorrectly adds two controls.

## Rationale

Changing production imports does not repair the lost instance-method targets.
A shared-tool repair preserves operator behavior and benefits every audit consumer.
Expanding selectable paths preserves control order without executing a workflow.

## Alternatives Considered

- Direct helper imports: insufficient because the walk stops before those calls.
- More exemptions: conceals the reported defect.
- Total of every dependent branch: counts controls that cannot appear together.
- A local audit replacement: duplicates the shared tool and creates maintenance drift.

## Dependencies

The shared-tool prerequisite must merge before the MistHelper pin changes.
The existing synthetic browser harness supplies runtime evidence without credentials.

## Comparison Scope

An experimental expansion of all menus found 65 excess-control comparisons in endpoint-family menus 263 through 267.
Their audit report does not distinguish their selected operation paths.
The experiment did not prove a browser defect.
The final design preserves their existing comparison and adds exact dependent-path checks for the seven Juniper menus.
It adds no exemptions and does not change those unrelated menus.
