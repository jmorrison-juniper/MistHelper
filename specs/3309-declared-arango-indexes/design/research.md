# Research: Declared ArangoDB indexes

## Existing writer path

**Decision**: Ensure the strategy indexes inside the existing collection-opening path.

**Rationale**: `ArangoDBWriter.write` currently opens its collection before the empty-data check and before document preparation.
That position covers both existing collections and empty writes.
Its graph and snapshot callers supply no strategy indexes.
They must not receive invented field indexes.

**Alternative rejected**: Create indexes after document import.
That approach can report successful storage before a required index fails.

## SDK interface

**Decision**: Use `StandardCollection.add_index` with `type` set to `persistent` and one field in `fields`.

**Rationale**: The installed `python-arango` 8.3.5 exposes this typed interface.
The SDK sends a POST request to `/_api/index` with the collection parameter.
It raises `IndexCreateError` for a failed response.
The older `add_persistent_index` method is deprecated.
The native connection parses the wire JSON before the index formatter reads its required response fields.
The query explanation method returns the plan itself, not the REST response's `plan` wrapper.
The contract tests verify both native shapes.

**Alternative rejected**: Use a deprecated helper or add custom uniqueness, sparse, or background options.
The issue requires only the existing declared non-unique field indexes.

## Failure and retry

**Decision**: Preserve the original expected driver or transport exception.
Log the field, collection, attempted count, and traceback.
Do not import records after the exception.

**Rationale**: The router already converts `ArangoError` into an explicit failed `csv_only` result and marks that backend unavailable.
No existing best-effort policy permits an index failure to become a successful write.
The index manager therefore does not invent one.
The next write retries each field that no complete check confirmed.

**Alternative rejected**: Catch every exception or report success after a failed index request.
Both conceal incomplete behavior.

## Cache and concurrency

**Decision**: Share a reentrant guard and confirmed-field state by configured server, database, and account.
Keep field state separate for each collection.

**Rationale**: Independent same-scope writers must not repeat process-local work.
Each writer continues to use its own live database and collection handle.
The shared state contains no password and retains no SDK connection.
A new collection invalidates the confirmation for its name.
An extended strategy confirms its new fields only after the complete extension succeeds.

**Alternative rejected**: A process-wide set keyed only by collection name.
That set suppresses required work in another database.
An instance-only cache also repeats work across same-scope writers.

## Structure and workflow

**Decision**: Add semantic index classes to `src/foundation/persistence/db/database_schema_utils.py`.
Apply the existing SpecKit templates to this feature directory only.

**Rationale**: `src/foundation/persistence/db` already exceeds the file limit.
The existing schema module is the appropriate free owner.
The legacy Git hook creates branches outside the app's branch manager.
PowerShell is unavailable, and the task prohibits shared `.specify` edits.

**Alternative rejected**: Add a new direct backend module, rename the branch with raw Git, or commit shared feature state.

## Integration isolation

**Decision**: Use a session-only compose overlay with an issue-specific profile and explicitly owned resources.

**Rationale**: Podman responds and already holds the ArangoDB 3.12 image.
The overlay must start only its test service with `--no-deps`.
The service, network, and volume use the `misthelper-tmp-issue3309-` prefix.
The published address must use `127.0.0.1` and a port from 9600 through 9699.

**Alternative rejected**: Access the production store, start default dependencies, or use a container outside a compose group.
