# Issue #3442 — repair every broken Markdown link

### Fixed

- Repaired 87 broken relative links across the documentation tree. The
  `documentation/api/` pages carried `$e/<Tag>/<operationId>` placeholders from
  the upstream Mist OpenAPI spec; these now point at the generated page for the
  same operation. The `documentation/diagrams/` pages promised PNG fallback
  images that no commit ever added; the pages now name the beta Mermaid type
  instead. Planning records under `specs/` used the wrong relative depth, or
  named a contract file that the author never created.

### Added

- Added `tests/guardrails/test_markdown_links.py`. The guardrail follows every
  relative Markdown link and heading anchor in the tracked tree, then fails when
  a target is absent. It also fails on an unresolved OpenAPI cross-reference
  placeholder. `documentation/wiki/` stays exempt, because a wiki page links to
  a bare page name that resolves only on the published wiki.

### Changed

- `scripts/generate_api_docs.py` now resolves an OpenAPI cross-reference
  placeholder to a relative link while it writes a page, so regeneration cannot
  bring the placeholders back.
