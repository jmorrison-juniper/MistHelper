# Data model: Workflow contracts

No production data model changes.

| Entity | Fields | Validation |
| - | - | - |
| Workflow | Events, jobs, concurrency, checkout references | The YAML root and event maps must be readable |
| Required context | Job ID, display name, reporting application | Preserve 14 CI job names and the CodeQL analysis identity |
| Candidate | Queue reference and candidate SHA | Separate references and checkout of the event commit |
| Evidence | Queue run, required checks, merge, main run | Record only observed values after owner activation |

Preparation progresses from specification to repository validation to coordinator review.
Activation progresses separately from owner approval to queue validation to verified merges.
No successful local contract test advances the activation state.
