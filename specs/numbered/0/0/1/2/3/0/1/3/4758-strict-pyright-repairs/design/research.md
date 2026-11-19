# Original research record

This record describes the initial analysis.
The final combined result is in [analysis.md](../analysis.md).

## Original baseline

The initial task base reported 108 errors with Pyright 1.1.414 and Python 3.15.2.
The final combined candidate starts from `origin/main` commit `26ac261392ac29119fa4f83e30c6ce9a0df12ab3`.
It analyzes the entry point and two shared contracts with zero errors and zero warnings.
The first configuration used an unsupported absolute include and analyzed zero files.
That report is invalid.

## Dynamic access

Production consumers use the existing resolver or direct module access.
The repair makes verified cross-module helpers public and updates their owned consumers.
It removes private declarations only after a tracked reference audit.
It adds no unused reference collection or compatibility alias.

## Ownership

The owners granted narrow handoffs for the portal signature and two annotation-only contracts.
The repair changes no other owner-controlled behavior.

## Prior work

At initial discovery, no local or remote branch named for issue #4758 was available.
The repair preserves earlier refs and commits.
