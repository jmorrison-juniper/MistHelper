"""Frozen dataclass that groups the rarely-used output-backend override options.

``DataExporter.write_with_format_selection`` in ``MistHelper.py`` took 6 parameters,
exceeding the 5-Item Rule's max-5 limit. The two least-used optional parameters --
both of which control the *output backend* rather than the data content or CSV
display -- are grouped here so the public signature drops to 5 parameters while
the common ``(data, filename)`` and ``api_function_name`` / ``fieldnames`` call
shapes are unaffected:

- ``format_override`` selects the backend ("csv" or "sqlite") instead of the
  global ``OUTPUT_FORMAT``.
- ``raw_data`` supplies the unflattened API rows for the polyglot (ArangoDB/Redis)
  backend.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/470
"""

from __future__ import annotations  # Enable PEP 604 union syntax on older runtimes.

from dataclasses import dataclass  # The standard library dataclass decorator.
from typing import Any  # Element type for the raw_data row list.


@dataclass(frozen=True, slots=True)
class ExportBackendOptions:
    """Optional output-backend overrides for DataExporter.write_with_format_selection."""

    format_override: str | None = None  # Force "csv" or "sqlite" instead of the global OUTPUT_FORMAT.
    raw_data: list[dict[str, Any]] | None = None  # Unflattened API rows for the polyglot backend (None -> use data).
