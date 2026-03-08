"""Change template instantiation service (T096, FR-031).

Renders a config_template by substituting parameter placeholders
with validated values. Produces a ScheduledJob from the result.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.shared.models.governance import ChangeTemplate

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


class TemplateService:
    """Instantiates change templates into deployment payloads."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def instantiate(
        self,
        template: ChangeTemplate,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Render template with provided parameters."""
        self._validate_params(template, parameters)
        rendered = self._render(template.config_template, parameters)
        return rendered

    def _validate_params(
        self,
        template: ChangeTemplate,
        parameters: dict[str, Any],
    ) -> None:
        """Validate parameters against the template schema."""
        schema = template.parameter_schema or {}
        required = schema.get("required", [])
        for key in required:
            if key not in parameters:
                msg = f"Missing required parameter: {key}"
                raise ValueError(msg)

    def _render(
        self, obj: Any, params: dict[str, Any],
    ) -> Any:
        """Recursively render template placeholders."""
        if isinstance(obj, str):
            return self._render_string(obj, params)
        if isinstance(obj, dict):
            return {
                self._render(k, params): self._render(v, params)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._render(item, params) for item in obj]
        return obj

    def _render_string(
        self, text: str, params: dict[str, Any],
    ) -> Any:
        """Replace {{key}} placeholders with parameter values."""
        full_match = _PLACEHOLDER_RE.fullmatch(text)
        if full_match:
            key = full_match.group(1)
            return params.get(key, text)

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            return str(params.get(key, match.group(0)))

        return _PLACEHOLDER_RE.sub(_replacer, text)
