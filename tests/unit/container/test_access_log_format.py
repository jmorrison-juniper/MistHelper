"""Guard the portal access log fields for issue #3217."""

from pathlib import Path

START_SCRIPT = Path(__file__).resolve().parents[3] / "container" / "scripts" / "start.sh"
ACCESS_LOG_FORMAT = (
    'ACCESS_LOG_FORMAT=\'%(h)s %(l)s %(u)s %(t)s "%(r)s" '
    "status=%(s)s bytes=%(b)s response_time_us=%(D)s "
    "refusal_code=%({X-MistHelper-Refusal-Code}o)s'"
)


def test_start_script_defines_safe_access_fields() -> None:
    """The fixed Gunicorn format names timing and refusal fields."""
    source = START_SCRIPT.read_text(encoding="utf-8")
    assert ACCESS_LOG_FORMAT in source
    assert source.count('--access-logformat "$ACCESS_LOG_FORMAT"') == 2
