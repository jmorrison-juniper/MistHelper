# Research

## Baseline

Decision: Use Pyright 1.1.414 with Python 3.15.2 and locked worktree dependencies.
Rationale: This reproduces the coordinator's 108 errors on the exact live main revision.
Alternative: The first configuration used an unsupported absolute include and analyzed zero files.
That report is invalid. The corrected command explicitly selects `MistHelper.py` and analyzes one file.

## Dynamic access

Decision: Preserve dynamically called functions and module context behavior.
Rationale: Runtime consumers use string lookup, which does not establish a static reference.
Alternative: Deleting functions or adding unused reference collections would conceal the contract problem.

## Ownership

Decision: Request a narrow portal signature handoff before edits.
Rationale: `WebPortalApp.create_app` exposes an unparameterized menu dictionary.
Alternative: A caller-side cast would conceal the source contract.

## Prior work

No local or remote branch named for issue #4758 was found.
Unreachable commit subjects did not identify the earlier shared-type repair.
No existing ref was removed or rewritten.
