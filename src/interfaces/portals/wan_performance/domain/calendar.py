"""Define UTC calendar periods for source-compatible offline reporting."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, slots=True)
class CalendarPeriod:
    """Represent a half-open UTC day, ISO week, or calendar month."""

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

    @property
    def expected_hours(self) -> int:
        """Count UTC hours without interpreting absent records as observations."""
        return int((self.end - self.start).total_seconds() / 3600)

    def contains(self, instant: datetime) -> bool:
        """Exclude the end boundary so adjacent periods never overlap."""
        return self.start <= instant < self.end
