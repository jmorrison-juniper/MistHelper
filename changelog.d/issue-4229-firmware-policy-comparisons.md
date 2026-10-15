### Firmware policy inspection and preparation

- **Added**: Expandable saved, current, and proposed firmware comparisons for
  both workflows, plus read-only historical inspection in recovery. Issue #4229.
- **Changed**: Supported site and inventory lists use 1,000-record pages with
  complete SDK pagination. Progress distinguishes capture, freshness, save,
  and local verification. Issue #4229.
- **Fixed**: Preparation stays locked through readiness and uncertain status.
  Definite preparation failure permits retry. First model selection chooses
  the highest available version without replacing later manual choices. Issue #4229.
