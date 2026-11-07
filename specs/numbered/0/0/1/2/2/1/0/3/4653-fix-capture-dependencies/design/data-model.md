# Data Model: Capture Request Dependencies

**Feature**: [spec.md](../spec.md)

This change adds no persistent data or schema.

## Request Dependency Graph

| Entity | Ownership | Required behavior |
|---|---|---|
| Authenticated operator | Identity registry | Supplies the signed-in operator and borrowed Mist session. |
| Mist session | Identity registry | Remains borrowed and is not closed by request teardown. |
| Database router | Active request | Serves capture persistence and closes during request teardown. |
| Capture service | Active request or explicit test override | Uses the operator session, request router, and audit logger. |

The provider caches the graph for one request. A later request receives a separate graph.
