"""Build and verify authoritative previews for bulk run actions."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from src.upgrade_portal.api.run_controls.models import (
    BulkActionPreview,
    BulkPreviewRequest,
    PreviewScope,
    PreviewSelection,
)

logger = logging.getLogger(__name__)
DEFAULT_PREVIEW_LIFETIME = timedelta(minutes=10)


class PreviewError(ValueError):
    """Report one stable preview refusal code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BulkActionPreviewService:
    """Build signed previews from current server-visible run records."""

    def __init__(
        self,
        *,
        run_reader: Callable[[str], Mapping[str, Any] | None],
        visibility_reader: Callable[[Mapping[str, Any], str, str], bool],
        signing_key: str,
        clock: Callable[[], datetime] | None = None,
        lifetime: timedelta = DEFAULT_PREVIEW_LIFETIME,
    ) -> None:
        if not signing_key:
            raise ValueError("The preview signing key is empty.")
        if lifetime <= timedelta(0):
            raise ValueError("The preview lifetime must be positive.")
        self._run_reader = run_reader
        self._visibility_reader = visibility_reader
        self._signing_key = signing_key.encode("utf-8")
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._lifetime = lifetime

    def preview(self, request: BulkPreviewRequest, actor_scope: str) -> BulkActionPreview:
        """Return a signed preview after removing records outside the scope."""
        logger.info("Build one authoritative bulk action preview")
        if not actor_scope:
            raise PreviewError("actor_required")
        retained: list[str] = []
        removed: list[str] = []
        site_counts: dict[str, int] = {}
        for run_id in request.run_ids:
            record = self._run_reader(run_id)
            if record is None or not self._visibility_reader(record, request.organization_id, request.history_scope):
                removed.append(run_id)
                continue
            site_id = str(record.get("site_id") or "")
            if not site_id:
                removed.append(run_id)
                continue
            retained.append(run_id)
            site_counts[site_id] = site_counts.get(site_id, 0) + 1
        if not retained:
            raise PreviewError("preview_empty")
        now = self._utc_now()
        expires_at = now + self._lifetime
        preview_id = secrets.token_urlsafe(24)
        scope = PreviewScope(
            actor_scope=actor_scope,
            organization_id=request.organization_id,
            history_scope=request.history_scope,
            action=request.action,
        )
        selection = PreviewSelection(tuple(retained), tuple(removed), site_counts)
        payload = self._payload(preview_id, scope, selection, expires_at)
        token = self._encode(payload)
        return BulkActionPreview(
            preview_id=preview_id,
            scope=scope,
            selection=selection,
            expires_at=self._format_time(expires_at),
            preview_token=token,
        )

    def verify(
        self,
        token: str,
        *,
        actor_scope: str,
        action: str,
        organization_id: str,
        history_scope: str,
        run_ids: tuple[str, ...],
    ) -> Mapping[str, Any]:
        """Verify token integrity, expiry, actor, scope, action, and order."""
        payload = self._decode(token)
        expected = {
            "actor_scope": actor_scope,
            "action": action,
            "organization_id": organization_id,
            "history_scope": history_scope,
            "run_ids": list(run_ids),
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            raise PreviewError("preview_mismatch")
        expires_at = self._parse_time(payload.get("expires_at"))
        if expires_at <= self._utc_now():
            raise PreviewError("preview_expired")
        site_counts = payload.get("site_counts")
        if not isinstance(site_counts, dict):
            raise PreviewError("preview_invalid")
        if payload.get("run_count") != len(run_ids) or payload.get("site_count") != len(site_counts):
            raise PreviewError("preview_mismatch")
        return payload

    def verify_action(
        self,
        token: str,
        *,
        actor_scope: str,
        action: str,
        run_ids: tuple[str, ...],
    ) -> Mapping[str, Any]:
        """Verify one action request and return its bound server scope."""
        payload = self._decode(token)
        if (
            payload.get("actor_scope") != actor_scope
            or payload.get("action") != action
            or payload.get("run_ids") != list(run_ids)
        ):
            raise PreviewError("preview_mismatch")
        expires_at = self._parse_time(payload.get("expires_at"))
        if expires_at <= self._utc_now():
            raise PreviewError("preview_expired")
        site_counts = payload.get("site_counts")
        if not isinstance(site_counts, dict):
            raise PreviewError("preview_invalid")
        if payload.get("run_count") != len(run_ids) or payload.get("site_count") != len(site_counts):
            raise PreviewError("preview_mismatch")
        required = ("preview_id", "organization_id", "history_scope")
        if any(not isinstance(payload.get(field), str) or not payload.get(field) for field in required):
            raise PreviewError("preview_invalid")
        return payload

    def _payload(
        self,
        preview_id: str,
        scope: PreviewScope,
        selection: PreviewSelection,
        expires_at: datetime,
    ) -> dict[str, Any]:
        return {
            "preview_id": preview_id,
            "actor_scope": scope.actor_scope,
            "organization_id": scope.organization_id,
            "history_scope": scope.history_scope,
            "action": scope.action,
            "run_ids": list(selection.run_ids),
            "run_count": len(selection.run_ids),
            "site_count": len(selection.site_counts),
            "site_counts": dict(selection.site_counts),
            "expires_at": self._format_time(expires_at),
        }

    def _encode(self, payload: Mapping[str, Any]) -> str:
        encoded = self._canonical(payload).encode("utf-8")
        signature = hmac.new(self._signing_key, encoded, hashlib.sha256).hexdigest()
        return f"{encoded.hex()}.{signature}"

    def _decode(self, token: str) -> Mapping[str, Any]:
        try:
            encoded_hex, signature = token.split(".", 1)
            encoded = bytes.fromhex(encoded_hex)
        except (AttributeError, TypeError, ValueError) as exc:
            raise PreviewError("preview_invalid") from exc
        expected = hmac.new(self._signing_key, encoded, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise PreviewError("preview_invalid")
        try:
            payload = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PreviewError("preview_invalid") from exc
        if not isinstance(payload, dict):
            raise PreviewError("preview_invalid")
        return payload

    def _utc_now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("The preview clock must return an aware time.")
        return now.astimezone(UTC)

    @staticmethod
    def _canonical(value: Mapping[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    @staticmethod
    def _format_time(value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_time(value: Any) -> datetime:
        if not isinstance(value, str):
            raise PreviewError("preview_invalid")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PreviewError("preview_invalid") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise PreviewError("preview_invalid")
        return parsed.astimezone(UTC)
