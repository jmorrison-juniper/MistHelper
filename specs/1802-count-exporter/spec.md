# Feature Specification: CountExporter

**Issue**: #1802
**Status**: In progress

## Problem

67 open issues each ask for one Mist count endpoint. An audit confirmed that none is
implemented, and that the installed SDK defines 70 count operations in total.

Delivered as the specs describe, that is 67 operations, 67 primary key strategies, 67 menu
entries, and 67 pull requests. The `menu_actions` dict in `MistHelper.py` holds 235 entries
today. Adding 67 would take it to 302, and the operator would scroll past 67 near-identical
rows to reach anything else.

## The family shares one shape

Every count operation takes a session plus one identifier, accepts an optional `distinct`
field, and returns a count distribution rather than a record list. The identifier is an org, a
site, or an MSP.

| Scope | Operations |
| - | - |
| org | 35 |
| site | 32 |
| msp | 3 |

## Requirements

- **FR-001**: Cover every count operation the installed SDK defines, with no gaps.
- **FR-002**: Group the operations by scope and offer one menu entry per scope.
- **FR-003**: Prompt the operator to choose the operation, and abort on any invalid answer.
- **FR-004**: Reuse the existing org and site resolvers rather than adding new prompts.
- **FR-005**: Register a primary key strategy for every operation.

## Non-goals

- **NG-001**: Do not add a menu entry per endpoint.
- **NG-002**: Do not expose the `distinct` parameter yet. Add it when an operator asks.
- **NG-003**: Do not change any existing operation.

## Design

`CountExporter` holds three tables of `_CountOp` rows, each row naming an operationId and the
dotted SDK module that defines it. Menus 235, 236, and 237 map to the org, site, and MSP
entry points.

The module paths were resolved against the installed SDK, not against the spec text, because
#1757 records that 245 endpoint specs name a module path that does not exist.

A count response carries no natural identifier, so every operation uses the
`auto_increment_with_unique` strategy. That matches the 32 count operations already registered.

## Success criteria

- **SC-001**: The table covers all 70 SDK count operations, with none extra.
- **SC-002**: Every table row resolves to a real function in a real module.
- **SC-003**: Every operation has a registered primary key strategy of the auto-increment kind.
- **SC-004**: Menus 235, 236, and 237 resolve, and the registry marks them `interactive_safe`.
- **SC-005**: Every quality gate passes: ruff, black, mypy, radon, vulture, pytest.
- **SC-006**: An invalid or out-of-range selection returns to the menu without raising.
