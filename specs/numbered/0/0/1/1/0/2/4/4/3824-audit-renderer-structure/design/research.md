# Research: Nested Source Package Remediation

## Decision

Place the renderer facade and three shared helpers in `src/mist/access/audit/rendering/`. Place the HTML and Mermaid clusters in `src/mist/access/audit/rendering/clusters/`.

## Rationale

The audit package has 10 structural children. Moving its six renderer modules leaves five. The `rendering` package has five structural children after the two clusters move to `clusters`. This removes one recorded violation without adding a new one.

Keep the renderer facade in `renderer.py` under the new package. This makes the import and `__module__` change explicit and avoids a re-export wrapper.

The WebSocket catalog has six structural children. Move `utility_text.py` into the existing `utilities/` package. That package had four modules and an `__init__.py` marker, so the move raised its total to six direct entries. Group `utility_profile.py` and `utility_text.py` in `utilities/metadata/`. The parent package then has five direct entries, and the catalog move removes one recorded violation.

The utility text module has two source importers and two test importers. Update those four paths. Keep `UtilityText` methods and returned text unchanged. The logger name and both moved classes' `__module__` values change with their new paths.

## Alternatives Considered

- Keep all renderer modules in `audit/`: rejected because the directory remains above the five-child limit.
- Reject an old-path module that re-exports the renderer. The issue removes obsolete paths. The constitution prohibits compatibility wrappers.
- Reject moves to unrelated audit packages. They scatter one rendering task and do not reduce direct-child counts as clearly.
- Move `channels.py` into `registry/`: rejected because it has more active callers than `utility_text.py`.
- Keep `utility_text.py` at the catalog root: rejected because the directory remains above the five-child limit.

## Unknowns

None. The target hierarchy, module imports, and test coverage are defined by the current source and the issue acceptance criteria.
