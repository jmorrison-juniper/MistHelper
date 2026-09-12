# Mist API Documentation Enrichment Guide

> Phase 2 of the two-phase documentation approach (see R6 in research.md).
> Phase 1 (script generation) produces raw structured markdown from the OpenAPI spec.
> Phase 2 (this guide) describes the AI enrichment workflow for adding domain knowledge.

## Overview

Each of the ~1,013 endpoint markdown files contains four placeholder sections
marked with *To be enriched by AI agent.*:

1. **Usage Context** -- When and why to use this endpoint, common use cases
2. **Gotchas** -- Known pitfalls, non-obvious behaviors, common mistakes
3. **Related Endpoints** -- Cross-references to endpoints commonly used together
4. **MistHelper Notes** -- How MistHelper uses this endpoint, relevant menu operations (per FR-002)

## Batch Strategy (Ascending by Category Size)

Process categories from smallest to largest. The smallest category serves as a
pilot batch to validate the enrichment workflow before scaling up.

| Order | Category    | File Count | Purpose           |
|-------|-------------|------------|-------------------|
| 1     | admins/     | 13         | Pilot batch       |
| 2     | self/       | 18         | Small validation  |
| 3     | installer/  | 23         | Small validation  |
| 4     | constants/  | 27         | Small validation  |
| 5     | msps/       | 50         | Medium batch      |
| 6     | utilities/  | 103        | Medium batch      |
| 7     | sites/      | 330        | Large batch       |
| 8     | orgs/       | 449        | Largest batch     |

**Total**: 1,013 files

## Enrichment Process Per File

For each endpoint file:

1. **Read the raw file** -- Understand the HTTP method, path, parameters, and schemas
2. **Identify usage context** -- What Mist operations use this endpoint? What workflow does it belong to?
3. **Document gotchas** -- Are there non-obvious parameter interactions? Rate limit concerns? Ordering requirements?
4. **Add cross-references** -- Which endpoints are commonly called before/after this one? Which endpoints operate on the same resource?
5. **Add MistHelper notes** -- Which MistHelper menu operation(s) call this endpoint? Any special handling?

## Quality Checklist Per File

Before marking an enriched file as complete, verify:

- [ ] Usage Context section has at least one concrete use case
- [ ] Gotchas section lists at least one pitfall (or explicitly states "No known gotchas")
- [ ] Related Endpoints section links to at least one related endpoint file
- [ ] MistHelper Notes section references the relevant menu operation number (or states "Not currently used by MistHelper")
- [ ] No placeholder text (*To be enriched by AI agent.*) remains
- [ ] All cross-reference links use correct relative paths (e.g., `../sites/GET_sites_site_id.md`)
- [ ] Content is factually accurate and matches the OpenAPI spec data

## Enrichment Sections Template

Replace each placeholder with structured content following these patterns:

### Usage Context

```markdown
## Usage Context

Use this endpoint to [action] when [scenario]. Common use cases:

- [Use case 1 with brief explanation]
- [Use case 2 with brief explanation]
```

### Gotchas

```markdown
## Gotchas

- [Pitfall description and how to avoid it]
- [Non-obvious behavior explanation]
```

### Related Endpoints

```markdown
## Related Endpoints

- [GET_orgs_org_id_sites.md](orgs/GET_orgs_org_id_sites.md) -- List sites before operating on a specific site
- [POST_orgs_org_id_sites.md](orgs/POST_orgs_org_id_sites.md) -- Create a new site
```

### MistHelper Notes

```markdown
## MistHelper Notes

Used by Menu Operation **11** (List Site Devices). MistHelper calls this endpoint
with `type=all` to include switches and gateways (see Device Type Filtering in agents.md).
```

## Regeneration

If the OpenAPI spec is updated, re-run Phase 1 to regenerate raw files:

```bash
python scripts/generate_api_docs.py
```

This overwrites all endpoint files and INDEX.md. **AI-enriched content will be lost**
and must be re-applied. Consider keeping enrichment data in a separate overlay
system if frequent spec updates are expected.
