"""MarvisClient for MistHelper.

Provides a thin, testable HTTP client wrapper that integrates with a
TokenCache for Authorization headers, basic retry/backoff, and 401-driven
refresh semantics. The implementation favors testability and defensive
fall-back behavior when no real transport is supplied.
"""
from typing import Optional, Any, Dict
import time
import logging

logger = logging.getLogger(__name__)


class MarvisClient:
    def __init__(self, http_client: Optional[Any] = None, token_cache: Optional[Any] = None, default_timeout: int = 30, retry_policy: Optional[Dict] = None):
        self.http_client = http_client
        self.token_cache = token_cache
        self.default_timeout = default_timeout
        self.retry_policy = retry_policy or {"retries": 2, "backoff": 0.5}

    @classmethod
    def from_config(cls, cfg: Dict):
        return cls(default_timeout=cfg.get("api_timeout", 30))

    def _make_request(self, method: str, path: str, params: Optional[Dict], data: Optional[Any], headers: Dict, timeout: int):
        """Invoke the provided http_client in a tolerant way and normalize the response."""
        if not self.http_client:
            return {"status_code": 501, "message": "No http_client provided"}

        # Support common interfaces: session.request(...) or a callable
        request_fn = getattr(self.http_client, "request", None)
        try:
            if callable(request_fn):
                return request_fn(method, path, params=params, json=data, headers=headers, timeout=timeout)
            if callable(self.http_client):
                return self.http_client(method=method, url=path, params=params, json=data, headers=headers, timeout=timeout)
        except Exception:
            logger.exception("HTTP client request failed")
            raise

        return {"status_code": 501, "message": "Unsupported http_client interface"}

    def _extract_status_and_body(self, resp: Any):
        """Return (status_code, body) for a variety of response shapes."""
        if hasattr(resp, "status_code"):
            status = getattr(resp, "status_code")
            # try to extract json/text safely
            body = None
            if hasattr(resp, "json"):
                try:
                    body = resp.json()
                except Exception:
                    body = getattr(resp, "text", None)
            else:
                body = getattr(resp, "text", None) or getattr(resp, "content", None)
            return int(status), body
        if isinstance(resp, dict):
            return int(resp.get("status_code", 200)), resp
        # unknown shape
        return 200, resp

    def call(self, method: str, path: str, params: Optional[Dict] = None, data: Optional[Any] = None, timeout: Optional[int] = None, correlation_id: Optional[str] = None) -> Dict:
        """Make an API call honoring token cache, retries, and 401 refresh.

        Returns a dict with keys: status_code, body, attempt, token_used
        """
        timeout = int(timeout or self.default_timeout)
        headers: Dict[str, str] = {"Accept": "application/json"}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        token = None
        if self.token_cache:
            token = self.token_cache.get_token()
            if not token:
                # Try a synchronous refresh before calling
                try:
                    self.token_cache.attempt_refresh()
                except Exception:
                    logger.exception("Token refresh attempt failed during pre-call refresh")
                token = self.token_cache.get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"

        retries = int(self.retry_policy.get("retries", 2))
        backoff = float(self.retry_policy.get("backoff", 0.5))

        last_status = None
        last_body = None
        for attempt in range(1, retries + 2):
            try:
                resp = self._make_request(method, path, params, data, headers, timeout)
            except Exception as exc:
                last_status = 599
                last_body = {"error": str(exc)}
                if attempt <= retries:
                    time.sleep(backoff * attempt)
                    continue
                return {"status_code": last_status, "body": last_body, "attempt": attempt, "token_used": bool(token)}

            status_code, body = self._extract_status_and_body(resp)
            last_status = status_code
            last_body = body

            # 401: try token refresh and immediate retry (once)
            if status_code == 401 and self.token_cache:
                refreshed = False
                try:
                    refreshed = self.token_cache.attempt_refresh()
                except Exception:
                    logger.exception("Token refresh during 401 handling failed")
                if refreshed:
                    token = self.token_cache.get_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    # retry immediately
                    continue

            # Retry on 5xx
            if 500 <= status_code < 600 and attempt <= retries:
                time.sleep(backoff * attempt)
                continue

            # success or non-retryable
            return {"status_code": int(status_code), "body": body, "attempt": attempt, "token_used": bool(token)}

        # exhausted retries
        return {"status_code": int(last_status or 599), "body": last_body, "attempt": retries + 1, "token_used": bool(token)}
