# Python Import Contract

The renderer entry point is `src.mist.access.audit.rendering.renderer.AuditReportRenderer`.
It provides the existing `render_mermaid` and `render_html` methods and existing test-visible delta helpers.

The helper modules are `src.mist.access.audit.rendering._renderer_delta`,
`src.mist.access.audit.rendering._renderer_format`, and
`src.mist.access.audit.rendering._renderer_time`.
The HTML and Mermaid clusters are
`src.mist.access.audit.rendering.clusters._renderer_html` and
`src.mist.access.audit.rendering.clusters._renderer_mermaid`.

The former `src.mist.access.audit.renderer` and `src.mist.access.audit._renderer_*` imports are not supported after this change. No compatibility alias is provided.

The WebSocket utility text class is `src.mist.realtime.websocket_streams.catalog.utilities.metadata.utility_text.UtilityText`.
Its `label`, `sentence`, and `hint` methods keep their current results.
The former `src.mist.realtime.websocket_streams.catalog.utility_text` and
`src.mist.realtime.websocket_streams.catalog.utilities.utility_text` imports are not supported after this change.
The utility profile class also moves to `src.mist.realtime.websocket_streams.catalog.utilities.metadata.utility_profile`.
No compatibility alias is provided. Both class `__module__` values and the logger name use the new module paths.
