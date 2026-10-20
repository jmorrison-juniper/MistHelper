# Research: Typed operation outcomes

## Contract Source

**Decision**: Preserve the model shape from the unmerged specification in
[PR #4019](https://github.com/jmorrison-juniper/MistHelper/pull/4019).

**Rationale**: The issue owner already selected the name, four states,
serial producer migrations, and removal of the prose scan.

**Alternatives considered**: The preserved draft at `69d19411` uses string
dictionaries and a prose fallback. Neither satisfies the current decision.
The draft remains unchanged.

## Current Main Inventory

An AST inventory of `MistHelper.py` at commit
`531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede` examined 306 `handler` keyword rows
without parse failures. It counted 114 lambda expressions, 186 attribute
references, and 6 name references.

The six name references point to named dispatch wrappers. Each wrapper has a
`None` annotation and no return statement. An import-based scan resolved 185
attribute handlers. A package lookup resolved the remaining
`RogueDhcpScanOperation.run` in `operation.py`. That handler returns `None`.

Four attribute handlers have value-shaped results:

| Menu | Handler | Return | Caller contract |
| - | - | - | - |
| 274 | `PskHygieneReport.run` | `bool` | The menu discards the value. Unit tests assert it. |
| 280 | `AlertDigestOperation.run_digest` | `bool` | The digest has separate empty-result and failure paths. |
| 276 | `OrgSecurityPostureChecklist.run` | `dict[str, int]` | Callers use the summary counts as structured data. |
| 92 | `PromptUtils.select_site_with_logging` | `str | None` | Multiple operations use the selected site as input. |

This batch migrates menu 274 only. It maps missing organization input to
`missing_input`, empty PSK rows to `no_output`, a rejected non-empty export to
`failed`, and a successful export to `completed`. Core fetch and export
exceptions continue to propagate.

Menu 274 was migrated in PR #4323. Menu 280 is the second bounded batch. It
maps zero alert rows to `no_output` and skips the digest writer. This is a
recorded assumption: the writer previously created an empty-state placeholder
file, and the typed state now reports that no result records exist. A failed
lookback or alarm search and a rejected write map to `failed`. Fetch and
write exceptions propagate. The shared client resolver has no missing-input
signal, so this batch maps no `missing_input` path. Menu 281 keeps its Boolean
return because it is destructive and a separate batch owns it.

Keep menu 92 as an input helper. Keep menus 276 and 280 for later batches.
These counts replace the historical six-value estimate. They do not classify
every `None` handler as migration-ready.

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
