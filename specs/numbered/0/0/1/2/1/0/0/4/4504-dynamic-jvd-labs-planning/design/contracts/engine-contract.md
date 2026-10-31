# Engine Contract

The engine is the `vmm_topology` package. It imports no Flask or MistHelper code.

## Public operations

`capabilities`, `schema`, `validate`, `plan`, `list_drafts`, `get_draft`, `qualify`, `propose`, `approve`, `revoke`, `deploy`, `observe`, `experiment`, `impair`, `restore`, `cleanup`.

Each call takes a typed request and returns a typed result. A result holds the run, the engine revision, the target scope, the intent digest, the operation, the state, and the evidence time.

## Error categories

`invalid-input`, `not-authorized`, `conflict`, `dependency-unavailable`, `capacity`, `timeout`, `remote-refused`, `outcome-uncertain`, `recovery-required`.

## Injected dependencies

| Dependency | Host supplies |
| - | - |
| Mist | An adapter over the host `mistapi` session. Candidate methods are decision D-02. |
| VMM | Server-side configuration and credentials. No Copilot desktop tool and no home-directory file. |
| Guest | Server-side, isolated management network. Tokens never reach the browser. |
| Persistence | Semantic ports that the host implements with ArangoDB. |
| Clock | UTC time source. |

## Safety rules

- Preview, validate, and plan resolve no secret and call no service.
- Each write records intent and a stable request key first, and reconciles an uncertain outcome before any repeat.
- Each destructive action rechecks ownership. A name prefix is never ownership.
- Impairment profiles have strict bounds, declared interfaces, prior-state capture, verification, and restoration. Management interfaces and foreign qdiscs are refused.
- A full-lab request never falls back to a small probe.
- Mist PUT calls keep exact replacement semantics.
