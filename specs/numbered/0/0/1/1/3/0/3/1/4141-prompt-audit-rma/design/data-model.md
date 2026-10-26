# Data Model: Prompt and control sequences

## Prompt Report

The shared audit returns a handler, an ordered list of prompt kinds, and a resolution note.
Only an `ok` note supports a comparison.
Every affected Juniper prompt has kind `raw`.

## Control Path

A registry row contains ordered parameters.
A chooser can contain `dynamic_parameters`, keyed by an option value.
One complete path contains the chooser, its selected dependent controls, and the remaining static controls.
An absent dependent branch contributes no controls.
The guard examines every selectable path, not every mapping entry.

## Invariants

- Each Juniper path has the same length as its audited prompt sequence.
- An identifier follows its key-kind chooser and precedes later optional controls.
- Mutually exclusive identifiers never share a path.
- A missing registry row produces one empty path.
- An unresolved audit cannot prove prompt coverage.
