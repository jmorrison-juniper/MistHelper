"""Define UTC calendar periods for source-compatible offline reporting."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

MAX_HISTORY_WINDOW_DAYS = 397
MAX_HISTORY_RECORDS = MAX_HISTORY_WINDOW_DAYS * 24


class CalendarWindow:
    """Keep reporting horizons aligned to calendar months."""

    @staticmethod
    def thirteen_months_ending(end: datetime) -> tuple[datetime, datetime]:
        """Return a half-open UTC window that ends thirteen calendar months later."""
        if end.tzinfo is None or end.utcoffset() != timedelta(0):
            raise ValueError("History window timestamps must use UTC.")
        end = end.astimezone(UTC)
        month_index = end.year * 12 + end.month - 1 - 13
        start_year, start_month_index = divmod(month_index, 12)
        start_month = start_month_index + 1
        start_day = min(end.day, monthrange(start_year, start_month)[1])
        start = end.replace(year=start_year, month=start_month, day=start_day)
        return start, end


@dataclass(frozen=True, slots=True)
class CalendarPeriod:
    """Represent a half-open UTC calendar or rolling reporting window."""

    kind: str
    start: datetime
    end: datetime

    @classmethod
    def containing(cls, instant: datetime, kind: str) -> "CalendarPeriod":
        """Locate the reporting period without converting ambiguous local time."""
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise ValueError("Calendar timestamps must use UTC.")
        day = instant.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        if kind == "daily":
            return cls(kind, day, day + timedelta(days=1))
        if kind == "weekly":
            start = day - timedelta(days=day.weekday())
            return cls(kind, start, start + timedelta(days=7))
        if kind == "monthly":
            start = day.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
            return cls(kind, start, end)
        raise ValueError("The calendar period must be daily, weekly, or monthly.")

    @classmethod
    def ending_at(cls, end: datetime, kind: str) -> "CalendarPeriod":
        """Return a fixed rolling window that ends at a UTC observation boundary."""
        if end.tzinfo is None or end.utcoffset() != timedelta(0):
            raise ValueError("Rolling window timestamps must use UTC.")
        hours = {"rolling_3h": 3, "rolling_12h": 12, "rolling_24h": 24}.get(kind)
        if hours is None:
            raise ValueError("The rolling window must be 3, 12, or 24 hours.")
        return cls(kind, end.astimezone(UTC) - timedelta(hours=hours), end.astimezone(UTC))

    @property
    def expected_hours(self) -> int:
        """Count UTC hours without interpreting absent records as observations."""
        return int((self.end - self.start).total_seconds() / 3600)

    def contains(self, instant: datetime) -> bool:
        """Exclude the end boundary so adjacent periods never overlap."""
        return self.start <= instant < self.end
