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

An AST inventory of `MistHelper.py` at `origin/main` commit
`24e93d2205796f134441f9aed56d5fa88dbffb73` examined 306 `handler` keyword rows
without parse failures. It found 186 attribute references, 114 lambda
expressions, and 6 named references.

The six named references point to dependency-wiring dispatch wrappers. Each
wrapper returns `None` after it calls its operation. The 114 lambdas remain out
of scope because a separate batch owns lambda conversion.

| Menu | Named handler | Result | Caller contract |
| - | - | - | - |
| 31 | `_dispatch_gateway_management_ips` | `None` | The menu invokes the wrapper and consumes no result. |
| 32 | `_dispatch_gateway_templates` | `None` | The menu invokes the wrapper and consumes no result. |
| 35 | `_dispatch_gateway_with_wan_overrides` | `None` | The menu invokes the wrapper and consumes no result. |
| 36 | `_dispatch_gateway_stats_wan_port_conflicts` | `None` | The menu invokes the wrapper and consumes no result. |
| 99 | `_dispatch_gateway_device_configs` | `None` | The menu invokes the wrapper and consumes no result. |
| 163 | `_dispatch_gateway_wan2_variable_migration` | `None` | The menu invokes the destructive wrapper and consumes no result. |

The current attribute handlers with value-shaped results are:

| Menu | Handler | Return | Caller contract |
| - | - | - | - |
| 274 | `PskHygieneReport.run` | `OperationOutcome` | The menu ignores the result. The unit tests assert each state. |
| 280 | `AlertDigestOperation.run_digest` | `OperationOutcome` | The menu ignores the result. The unit tests assert each state. |
| 276 | `OrgSecurityPostureChecklist.run` | `OperationOutcome` | The menu ignores the result. The detail field holds verdict counts. |
| 92 | `PromptUtils.select_site_with_logging` | `str | None` | Callers use the selected site as input for later operations. |

Menus 274, 280, and 276 already return `OperationOutcome`. The current named
operation inventory has no un-migrated value-return producer. Menu 92 remains
an input helper because its return value selects the site for other operations.
Do not convert that input value to an operation outcome.

The next producer work must select a named operation family whose handlers
currently return `None`. It must keep the separate lambda conversion and portal
replacement batches unchanged. This inventory does not claim that issue #3168
is complete.

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

### Third bounded migration: security posture checklist

Menu 276 returned a dictionary of pass, fail, and review counts. Only tests read
it. `OrgSecurityPostureChecklist.run` now returns `OperationOutcome`. A missing
API session or organization ID returns `missing_input`, and a rejected export
returns `failed`. A successful export returns `completed`, and the `detail`
field holds the verdict counts. Both previous exceptions for these two cases
are gone. Errors from the Mist source reads still propagate. The registry always yields
rows, so this batch maps no `no_output` path.
