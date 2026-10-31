# Research: Audit Renderer Structure

## Decision

Place the renderer facade and three shared helpers in `src/mist/access/audit/rendering/`. Place the HTML and Mermaid clusters in `src/mist/access/audit/rendering/clusters/`.

## Rationale

The audit package has 10 structural children. Moving its six renderer modules leaves five. The `rendering` package has five structural children after the two clusters move to `clusters`. This removes one recorded violation without adding a new one.

Keep the renderer facade in `renderer.py` under the new package. This makes the import and `__module__` change explicit and avoids a re-export wrapper.

## Alternatives Considered

- Keep all renderer modules in `audit/`: rejected because the directory remains above the five-child limit.
- Reject an old-path module that re-exports the renderer. The issue removes obsolete paths. The constitution prohibits compatibility wrappers.
- Reject moves to unrelated audit packages. They scatter one rendering task and do not reduce direct-child counts as clearly.

## Unknowns

None. The target hierarchy, module imports, and test coverage are defined by the current source and the issue acceptance criteria.
