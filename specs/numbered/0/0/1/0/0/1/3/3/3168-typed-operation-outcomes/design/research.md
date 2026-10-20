# Research: Typed operation outcomes

## Contract Source

**Decision**: Preserve the model shape from the unmerged specification in
[PR #4019](https://github.com/jmorrison-juniper/MistHelper/pull/4019).

**Rationale**: The issue owner already selected the name, four states,
serial producer migrations, and removal of the prose scan.

**Alternatives considered**: The preserved draft at `69d19411` uses string
dictionaries and a prose fallback. Neither satisfies the current decision.
The draft remains unchanged.

## Current Inventory

An AST scan of `MistHelper.py` at `cdc965f5f` examined one file with zero
parse failures. It found 306 `MenuEntry` rows:

| Handler expression | Count |
| - | - |
| Lambda | 114 |
| Attribute | 186 |
| Name | 6 |

These are expression counts, not unique callable counts or migration readiness.
The older 293-row and 112-lambda counts in PR #4019 are not current.

## Model Representation

**Decision**: Use a frozen, slotted dataclass with a `Literal` state annotation.
Reject invalid runtime states and invalid text.

**Rationale**: Static checks detect unsupported state literals. Runtime checks
also reject untyped caller input. Immutable strings preserve the full record.

**Alternatives considered**: A mutable detail dictionary permits later state
evidence changes. An enum adds a second public type without a current need.
An unvalidated dataclass permits invalid states from untyped handlers.

## Integration Boundary

**Decision**: Do not import the new type into a runtime consumer in this batch.

**Rationale**: Removing prose classification before producer migration loses
existing failure behavior. Adding a second classifier violates the no-fallback
decision.

**Alternatives considered**: A partial portal replacement and a temporary
fallback were rejected. The coordinator authorized the contract-only batch.
