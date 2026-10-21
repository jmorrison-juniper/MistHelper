# Audit Contracts

## Local Command

Planned entry point:

```text
python -m src.foundation.support.code_defaults scan --root .
python -m src.foundation.support.code_defaults guard --root .
```

The scanner reads tracked content from the specified repository worktree.
Reject a nonexistent root or a root that is not a Git worktree.
Use argument lists for Git calls, not a shell expression.
Tests create isolated temporary Git repositories without credentials or network access.

`scan` emits deterministic JSON to standard output with the fields in [data-model.md](../data-model.md).
Use sorted records and reversible ASCII escapes.
Send action logs and errors to standard error.
Repository-wide discovery includes only tracked non-test source files.

`guard` loads the packaged `baseline.json` and enforces its exact five-file scope.
Report discovery and parsed-file counts even when the decision fails.
Do not fetch a remote, inspect another worktree, modify the baseline, or write product data.

| Exit status | Meaning |
| --- | --- |
| 0 | Scan completed, or guard passed |
| 1 | Guard detected a regression |
| 2 | Invalid arguments, unreadable input, parse failure, invalid policy, or incomplete scope |

The guard must reject new high-severity identities even when another candidate disappears.
An unclassified in-scope candidate prevents acceptance.
Other scopes remain visible as outside this batch and cannot alter its accepted total.

## Workflow Boundary

Required inputs are validated before a dependent lookup, comparison, mapping, path, or required collection interpretation.
Absent, null, blank, whitespace-only, and wrong-type values must have explicit cases where the field is required.
Existing optional inputs and valid explicit empty collections retain their results.

Migration failures preserve earlier results and never add a blank mapping.
Preserve existing backup shape, typed confirmations, and output backend behavior.
Tests replace Mist SDK, geocoding, and other external calls.
No verification command is permitted to mutate the cloud or a device.

## Evidence Matrix

| Contract | Required proof |
| --- | --- |
| Required input | Missing-input unit case and mocked caller integration case fail visibly |
| Optional input | Valid empty collection and blank display cases retain their results |
| Historical review | Every historical target has a disposition and evidence |
| Stable inventory | Repeated scans and line-only movements retain candidate identity |
| Guard regression | One new high-severity candidate fails |
| No offset | Removing one accepted candidate cannot hide a different new candidate |
| Invalid input | Missing scope file, parse error, invalid baseline, and empty selection fail |
| Ownership | Sibling and unresolved upgrade-input findings never enter the accepted batch |
| Confidentiality | Diagnostics identify fields without private values |
