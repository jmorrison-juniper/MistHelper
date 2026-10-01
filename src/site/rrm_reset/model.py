"""Pure model helpers for site RRM optimize or reset plan capture."""

from __future__ import annotations  # WHY: allow compact annotations without runtime imports.

import os  # WHY: read the settle-time environment setting.
from dataclasses import dataclass, field  # WHY: keep run settings and rows explicit.
from typing import Any, ClassVar  # WHY: type dynamic Mist rows without losing structure.

ACTION_OPTIMIZE = "OPTIMIZE"  # WHY: confirmation must match the destructive optimize action.
ACTION_RESET = "RESET"  # WHY: confirmation must match the destructive reset action.
DEFAULT_SETTLE_SECONDS = 300  # WHY: assignment requires a five-minute default settle period.
DEFAULT_BANDS = ("24", "5", "6")  # WHY: OpenAPI examples and schemas use these site bands.
RRM_DIFF_ENDPOINT = "rrm_reset_plan_diff"  # WHY: wiring uses this endpoint name for diff exports.
RRM_BEFORE_FILENAME = "RrmPlanBefore.csv"  # WHY: assignment requires this operator file name.
RRM_AFTER_FILENAME = "RrmPlanAfter.csv"  # WHY: assignment requires this operator file name.
RRM_DIFF_FILENAME = "RrmPlanDiff.csv"  # WHY: assignment requires this operator file name.


@dataclass(frozen=True)
class RrmRunSettings:
    """Hold runtime choices for one RRM operation run."""

    action: str  # WHY: selects the Mist request and typed confirmation word.
    dry_run: bool  # WHY: prevents a destructive Mist request when true.
    settle_seconds: int  # WHY: controls the wait before the after capture.
    bands: tuple[str, ...] = DEFAULT_BANDS  # WHY: both OpenAPI request schemas require bands.

    @classmethod
    def build(cls, action: str, dry_run: bool, environ: dict[str, str] | None = None) -> RrmRunSettings:
        """Build settings from operator input and environment values."""
        source = environ if environ is not None else os.environ  # WHY: tests inject env without mutating process env.
        seconds = RrmSettleTime.resolve(source.get("RRM_SETTLE_SECONDS"))  # WHY: apply the documented override.
        return cls(action=RrmAction.normalize(action), dry_run=dry_run, settle_seconds=seconds)  # WHY: validate action.

    def request_body(self) -> dict[str, list[str]]:
        """Return the OpenAPI-compatible request body for destructive calls."""
        return {"bands": list(self.bands)}  # WHY: Mist requires a JSON array of band names.


class RrmAction:
    """Validate RRM action words."""

    VALID: ClassVar[set[str]] = {ACTION_OPTIMIZE, ACTION_RESET}  # WHY: two destructive choices exist.

    @classmethod
    def normalize(cls, value: str) -> str:
        """Return an uppercase action or raise ValueError."""
        action = value.strip().upper()  # WHY: tolerate lowercase input without changing the confirmation word.
        if action not in cls.VALID:  # WHY: never guess a destructive action.
            raise ValueError(f"Action must be {ACTION_OPTIMIZE} or {ACTION_RESET}.")  # WHY: clear operator message.
        return action  # WHY: downstream comparisons use one canonical value.


class RrmSettleTime:
    """Resolve the RRM settle time."""

    @staticmethod
    def resolve(raw_value: str | None) -> int:
        """Return the settle seconds from the environment or the default."""
        if raw_value is None or raw_value.strip() == "":  # WHY: missing override uses the assignment default.
            return DEFAULT_SETTLE_SECONDS  # WHY: five minutes is the default settle time.
        try:
            seconds = int(raw_value)  # WHY: environment variables arrive as text.
        except ValueError:
            return DEFAULT_SETTLE_SECONDS  # WHY: invalid input must not crash a menu run.
        return seconds if seconds >= 0 else DEFAULT_SETTLE_SECONDS  # WHY: negative waits are not meaningful.


@dataclass(frozen=True)
class RrmRadioPlanRecord:
    """Represent one AP radio row used for diff comparison."""

    site_id: str  # WHY: site scopes AP identifiers and output rows.
    ap: str  # WHY: AP identifies the changed radio owner.
    band: str  # WHY: each AP can have multiple radios.
    channel: str = ""  # WHY: channel is one diff field.
    width: str = ""  # WHY: width is one diff field.
    power: str = ""  # WHY: power is one diff field.
    raw: dict[str, Any] = field(default_factory=dict)  # WHY: preserve source fields for before and after exports.

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> RrmRadioPlanRecord:
        """Build a radio record from a menu-86-style channel planning row."""
        ap_value = str(row.get("ap", row.get("ap_id", row.get("mac", ""))))  # WHY: support known AP key names.
        band_value = str(row.get("band", row.get("usage", row.get("curr_usage", ""))))  # WHY: support known band keys.
        ap_name, band_name = RrmRadioPlanRecord._resolve_identity(ap_value, band_value)  # WHY: fix RRM band map rows.
        channel = RrmRadioPlanRecord._field(row, "curr_channel", "channel")  # WHY: current value is preferred.
        width = RrmRadioPlanRecord._field(row, "curr_bandwidth", "bandwidth", "width")  # WHY: normalize width names.
        power = RrmRadioPlanRecord._field(row, "curr_power", "power")  # WHY: normalize power names.
        return cls(
            str(row.get("site_id", "")), ap_name, band_name, channel, width, power, dict(row)
        )  # WHY: freeze row.

    @staticmethod
    def _field(row: dict[str, Any], *names: str) -> str:
        """Return the first present field as text."""
        for name in names:  # WHY: Mist and flattened rows use different field names.
            value = row.get(name)  # WHY: absent keys return None.
            if value is not None:  # WHY: zero is a valid RF value.
                return str(value)  # WHY: CSV and diff comparison use stable text.
        return ""  # WHY: missing values compare as empty.

    @staticmethod
    def _resolve_identity(ap_value: str, band_value: str) -> tuple[str, str]:
        """Return AP and band values, including menu-86 band-map rows."""
        if ap_value.startswith("band_"):  # WHY: OpenAPI RRM maps bands first, then AP identifiers.
            return band_value, ap_value.replace("band_", "")  # WHY: recover AP id and band number from helper rows.
        return ap_value, band_value  # WHY: menu-86 fixture shape already uses AP then band.

    def identity(self) -> tuple[str, str, str]:
        """Return the stable identity used for diff matching."""
        return (self.site_id, self.ap, self.band)  # WHY: site, AP, and band identify one radio.

    def changed_from(self, other: RrmRadioPlanRecord) -> bool:
        """Return True when RF fields changed."""
        return (self.channel, self.width, self.power) != (other.channel, other.width, other.power)  # WHY: AC fields.


class RrmPlanDiffBuilder:
    """Build changed-radio diff rows."""

    @staticmethod
    def normalize(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], RrmRadioPlanRecord]:
        """Return radio records keyed by site, AP, and band."""
        records = [RrmRadioPlanRecord.from_row(row) for row in rows]  # WHY: normalize every captured row once.
        return {record.identity(): record for record in records if record.ap and record.band}  # WHY: skip metric rows.

    @classmethod
    def build(cls, before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Return rows whose channel, width, or power changed."""
        before = cls.normalize(before_rows)  # WHY: key the before capture for comparison.
        after = cls.normalize(after_rows)  # WHY: key the after capture for comparison.
        keys = sorted(set(before) | set(after))  # WHY: include missing-before and missing-after changes.
        return [cls._diff_row(key, before.get(key), after.get(key)) for key in keys if cls._changed(key, before, after)]

    @staticmethod
    def _changed(
        key: tuple[str, str, str],
        before: dict[tuple[str, str, str], RrmRadioPlanRecord],
        after: dict[tuple[str, str, str], RrmRadioPlanRecord],
    ) -> bool:
        """Return whether one keyed radio changed."""
        if key not in before or key not in after:  # WHY: missing radios matter to the operator.
            return True  # WHY: absence on either side is a change.
        return after[key].changed_from(before[key])  # WHY: compare only channel, width, and power.

    @staticmethod
    def _diff_row(
        key: tuple[str, str, str],
        before: RrmRadioPlanRecord | None,
        after: RrmRadioPlanRecord | None,
    ) -> dict[str, str]:
        """Return one output row for a changed radio."""
        site_id, ap, band = key  # WHY: key values become the output identity.
        change_type = RrmPlanDiffBuilder._change_type(before, after)  # WHY: show why the row exists.
        return {  # WHY: flat dict writes directly to CSV and database backends.
            "site_id": site_id,
            "ap": ap,
            "band": band,
            "change_type": change_type,
            "before_channel": before.channel if before else "",
            "after_channel": after.channel if after else "",
            "before_width": before.width if before else "",
            "after_width": after.width if after else "",
            "before_power": before.power if before else "",
            "after_power": after.power if after else "",
        }

    @staticmethod
    def _change_type(before: RrmRadioPlanRecord | None, after: RrmRadioPlanRecord | None) -> str:
        """Return the reason a diff row exists."""
        if before is None:  # WHY: the after capture has a radio absent from the before capture.
            return "missing_before"  # WHY: operator can separate new radios from changed radios.
        if after is None:  # WHY: the after capture lost a radio from the before capture.
            return "missing_after"  # WHY: operator can identify absent radios.
        return "changed"  # WHY: both sides exist and RF fields differ.
