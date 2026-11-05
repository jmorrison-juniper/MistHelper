# Template Contract

A template is declarative data. It holds no command, script, hook, or code reference.

| Field | Rule |
| - | - |
| `template_id`, `version` | Lowercase slug and semantic version. The pair is unique and immutable. |
| `schema_version` | Must match a schema that the engine publishes. |
| `catalog_version` | Version of the catalog that lists the template. |
| `compatibility` | The supported engine, host, schema, and catalog version ranges. |
| `blocks` | A list of building blocks. Each block names a type from the engine capability list. |
| `parameters` | Typed values. Each parameter has a type, bounds, and a default. |

Import rules (limits are decision D-04):

1. Accept `.yaml`, `.yml`, and `.json` only, under a size, depth, and key bound.
2. Use a safe loader. Reject tags, merge keys that expand past the bound, duplicate keys, and unknown keys.
3. Reject any value that names a command, a path outside the resource set, or a URL fetch.
4. Validate against the engine schema, then apply the engine cross-field checks.
5. Store a rejected import nowhere. Return the field path and the reason.

A catalog template and an imported template share one preview path.
