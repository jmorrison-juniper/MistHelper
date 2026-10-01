# Contract: Declared ArangoDB indexes

## Collection opening

`ArangoDBWriter.write(data, collection_name, strategy)` opens the collection with the strategy's declared indexes.
Internal graph and snapshot callers open collections with an empty declaration.
The writer uses its current SDK database handle.

A valid declaration produces one request of this form for each unconfirmed field:

```json
{"type": "persistent", "fields": ["org_id"]}
```

The request supplies no uniqueness, sparse, or background option.
The existing SDK method remains responsible for the equal-index server response.

## Completion and diagnostics

Each request logs an information event before execution and a debug event after success.
Both events identify the collection and field.
The final check event states the number of checked fields and requested fields.

A failed expected request logs an error with the original traceback and attempted count.
It emits no success event for the failed field or complete check.
It propagates the original exception.
It confirms no part of the incomplete extension.

## Existing result semantics

A successful writer call retains its existing `WriteResult`.
An empty write reports zero records written and zero failed.
An index exception stops the call before document preparation, import, and graph population.

The existing router converts an `ArangoError` into this failure shape:

```text
success=False
backend="csv_only"
records_written=0
records_failed=len(data)
error_message=<original driver diagnostic>
```

Other exceptions remain visible to the caller.
The repair adds no success-shaped fallback.

## Retry and process scope

The configured server, database, account, and collection define the confirmation scope.
Same-scope writer instances share completed checks and the reentrant guard.
Separate scopes each request their own declared fields.

A failed first check retries every declared field.
A failed extension retries every unconfirmed field while preserving earlier confirmations.
The writer removes no server index when a later declaration becomes smaller.
The writer invalidates a collection's earlier confirmation when it creates a new collection with that name.

## Isolated integration contract

The integration fixture requires an explicit issue-specific URL.
It rejects any host other than `127.0.0.1` and any port outside 9600 through 9699.
Its database and container resources use the `misthelper-tmp-issue3309-` prefix.
It reads no production environment file.

If the URL is absent, the fixture reports the missing isolated ArangoDB capability.
That result is unmeasured, not passed.
An available store must prove persistent field indexes, equal-index reuse, unchanged documents, and an index-based query plan.
