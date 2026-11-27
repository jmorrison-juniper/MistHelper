# Contract: Python import paths

This contract names the import paths that stay supported after the change. It names the paths that are retired. It names the `__module__` values that change. Each row cites the rule that the record uses.

## Canonical import paths

| Canonical module | Names used by callers and tests | File after the change |
|------------------|---------------------------------|------------------------|
| `src.mist.access.audit.rendering.renderer` | `AuditReportRenderer`, `DiffKeyContext` (listed in `__all__`, line 51) | `src/mist/access/audit/rendering/renderer.py` |
| `src.mist.access.audit.rendering.helpers._renderer_delta` | `DiffKeyContext` | `src/mist/access/audit/rendering/helpers/_renderer_delta.py` |
| `src.mist.access.audit.rendering.helpers._renderer_format` | `format_delta_html`, `_format_dict`, `_render_dict_item`, `_format_list`, `_format_leaf` | `src/mist/access/audit/rendering/helpers/_renderer_format.py` |
| `src.mist.access.audit.rendering.helpers._renderer_time` | `epoch_to_readable`, `epoch_to_short` | `src/mist/access/audit/rendering/helpers/_renderer_time.py` |
| `src.mist.access.audit.rendering.helpers._renderer_html` | `_HtmlCluster`, `_HtmlParts` | `src/mist/access/audit/rendering/helpers/_renderer_html.py` |
| `src.mist.access.audit.rendering.helpers._renderer_mermaid` | `_MermaidCluster`, `MERMAID_NODE_CAP` | `src/mist/access/audit/rendering/helpers/_renderer_mermaid.py` |

The renderer keeps its existing public surface. The change does not add a name to `__all__`.

## Retired import paths

Each path below must fail with an import error after the change. The #3824 structure test checks the same list (TS-07).

1. `src.mist.access.audit.renderer`
2. `src.mist.access.audit._renderer_delta`
3. `src.mist.access.audit._renderer_format`
4. `src.mist.access.audit._renderer_time`
5. `src.mist.access.audit._renderer_html`
6. `src.mist.access.audit._renderer_mermaid`
7. `src.mist.access.audit.rendering._renderer_delta`
8. `src.mist.access.audit.rendering._renderer_format`
9. `src.mist.access.audit.rendering._renderer_time`
10. `src.mist.access.audit.rendering.clusters._renderer_html`
11. `src.mist.access.audit.rendering.clusters._renderer_mermaid`

## Module identity changes

The moved symbols change their `__module__` value. The renderer does not change.

| Symbol | `__module__` before | `__module__` after |
|--------|---------------------|--------------------|
| `DiffKeyContext` | `src.mist.access.audit.rendering._renderer_delta` | `src.mist.access.audit.rendering.helpers._renderer_delta` |
| `format_delta_html` | `src.mist.access.audit.rendering._renderer_format` | `src.mist.access.audit.rendering.helpers._renderer_format` |
| `epoch_to_readable` and `epoch_to_short` | `src.mist.access.audit.rendering._renderer_time` | `src.mist.access.audit.rendering.helpers._renderer_time` |
| `_HtmlCluster` and `_HtmlParts` | `src.mist.access.audit.rendering.clusters._renderer_html` | `src.mist.access.audit.rendering.helpers._renderer_html` |
| `_MermaidCluster` | `src.mist.access.audit.rendering.clusters._renderer_mermaid` | `src.mist.access.audit.rendering.helpers._renderer_mermaid` |
| `AuditReportRenderer` | `src.mist.access.audit.rendering.renderer` | No change |

No code or test in the repository reads the `__module__` value of a moved symbol (search result in `analysis.md`).

## Logger names

No logger name changes. The moved modules hold no logger. The only logger in the audit package is in `src/mist/access/audit/audit_analysis_ops.py` (line 26), and that module does not move.

## Import rules

- Each canonical import uses the absolute form, for example `from src.mist.access.audit.rendering.helpers._renderer_html import _HtmlCluster`, as the existing modules do.
- No alias module, wrapper module, re-export, or fallback import exists at a retired path (FR-007).
