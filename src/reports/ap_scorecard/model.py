"""Pure model functions for the organization access point scorecard."""

from __future__ import annotations  # WHY: keep annotations lightweight for CLI imports.

from collections import Counter, defaultdict  # WHY: count versions and group rows by site.
from collections.abc import Callable, Iterable, Mapping, Sequence  # WHY: type pure functions over read-only inputs.
from dataclasses import asdict, dataclass  # WHY: produce typed rows and flat export dictionaries.

GREEN_THRESHOLD = 98.5  # WHY: the Mist Access Points page uses this green threshold.
RED_THRESHOLD = 80.0  # WHY: the Mist Access Points page uses this red threshold.
SECONDS_PER_DAY = 86400.0  # WHY: uptime arrives as seconds and the report shows days.

AP_SCORECARD_COLUMNS = [  # WHY: keep ApScorecard.csv in a stable operator-friendly order.
    "site",
    "site_id",
    "ap_name",
    "mac",
    "model",
    "version",
    "predominant_version",
    "version_compliant",
    "status",
    "offline_reason",
    "inactive_wired_vlans",
    "switch_redundancy_count",
    "switch_redundancy_class",
    "power_constrained",
    "power_opmode",
    "power_budget",
    "lldp_power_allocated",
    "lldp_power_needed",
    "config_reverted",
    "last_trouble",
    "expiring_certificate_count",
    "uptime_days",
]

SITE_SCORECARD_COLUMNS = [  # WHY: keep ApScorecardBySite.csv in a stable operator-friendly order.
    "site",
    "site_id",
    "ap_count",
    "connection_status_percent",
    "connection_status_band",
    "vlans_percent",
    "vlans_band",
    "version_compliance_percent",
    "version_compliance_band",
    "switch_redundancy_percent",
    "switch_redundancy_band",
    "potential_anomalies_percent",
    "potential_anomalies_band",
    "switch_redundancy_none_count",
    "switch_redundancy_good_count",
    "switch_redundancy_excellent_count",
]

ORG_SUMMARY_FIELDS = [  # WHY: keep console output aligned with the five required AP tiles.
    "Connection Status",
    "VLANs",
    "Version Compliance",
    "AP Switch Redundancy",
    "Potential Anomalies",
]


@dataclass(frozen=True)
class ApScorecardRow:
    """One export row for one access point."""

    site: str  # WHY: operators sort and filter by site display name.
    site_id: str  # WHY: site identifiers remain stable when names change.
    ap_name: str  # WHY: AP name is the operator-facing device label.
    mac: str  # WHY: MAC address is the stable AP identity in Mist stats.
    model: str  # WHY: model scopes the predominant firmware calculation.
    version: str  # WHY: running version shows the AP firmware state.
    predominant_version: str  # WHY: this is the expected version when no explicit target exists.
    version_compliant: bool  # WHY: this drives the Version Compliance tile.
    status: str  # WHY: connected status drives the Connection Status tile.
    offline_reason: str  # WHY: an offline AP needs the reason next to its status.
    inactive_wired_vlans: str  # WHY: a non-empty list drives the VLAN tile failure.
    switch_redundancy_count: int | None  # WHY: count drives redundancy class and site counts.
    switch_redundancy_class: str  # WHY: operators need none, good, excellent, or unknown.
    power_constrained: bool | None  # WHY: constrained power is a common AP anomaly clue.
    power_opmode: str  # WHY: operating mode explains reduced power behavior.
    power_budget: int | float | str | None  # WHY: the payload can use numeric or empty power values.
    lldp_power_allocated: int | float | str  # WHY: LLDP allocation shows switch power delivery.
    lldp_power_needed: int | float | str  # WHY: requested or needed power shows AP demand.
    config_reverted: bool | None  # WHY: reverted configuration is anomaly evidence.
    last_trouble: str  # WHY: recent trouble is anomaly evidence.
    expiring_certificate_count: int  # WHY: certificate risk needs one sortable count.
    uptime_days: float | str  # WHY: days are easier to compare than seconds.


@dataclass(frozen=True)
class SiteScorecardRow:
    """One site-level AP scorecard row."""

    site: str  # WHY: operators read site names in the summary file.
    site_id: str  # WHY: site identifiers remain stable for database keys.
    ap_count: int  # WHY: every tile percentage needs the denominator.
    connection_status_percent: float  # WHY: connected AP percentage drives the first tile.
    connection_status_band: str  # WHY: color band matches the Mist page.
    vlans_percent: float  # WHY: VLAN health percentage drives the VLAN tile.
    vlans_band: str  # WHY: color band matches the Mist page.
    version_compliance_percent: float  # WHY: version compliance drives the firmware tile.
    version_compliance_band: str  # WHY: color band matches the Mist page.
    switch_redundancy_percent: float  # WHY: redundant AP percentage drives the redundancy tile.
    switch_redundancy_band: str  # WHY: color band matches the Mist page.
    potential_anomalies_percent: float  # WHY: anomaly-free percentage drives the anomalies tile.
    potential_anomalies_band: str  # WHY: color band matches the Mist page.
    switch_redundancy_none_count: int  # WHY: value 1 means no redundancy.
    switch_redundancy_good_count: int  # WHY: value 2 means good redundancy.
    switch_redundancy_excellent_count: int  # WHY: value 3 or more means excellent redundancy.


@dataclass(frozen=True)
class OrganizationSummary:
    """Organization-wide AP scorecard percentages."""

    ap_count: int  # WHY: the console summary needs the total AP count.
    connection_status_percent: float  # WHY: summarize connected APs for the organization.
    vlans_percent: float  # WHY: summarize VLAN health for the organization.
    version_compliance_percent: float  # WHY: summarize firmware compliance for the organization.
    switch_redundancy_percent: float  # WHY: summarize redundant switch attachment for the organization.
    potential_anomalies_percent: float  # WHY: summarize anomaly-free APs for the organization.


def tile_color_band(percent: float) -> str:
    """Return the Mist Access Points color band for a percentage."""
    if percent >= GREEN_THRESHOLD:  # WHY: Mist shows green at 98.5 percent or higher.
        return "green"  # WHY: the value meets the healthy tile threshold.
    if percent <= RED_THRESHOLD:  # WHY: Mist shows red at 80 percent or lower.
        return "red"  # WHY: the value meets the unhealthy tile threshold.
    return "orange"  # WHY: values between red and green need the warning band.


def normalize_switch_redundancy(value: object) -> int | None:
    """Return a switch redundancy count from the Mist payload shape."""
    if isinstance(value, bool):  # WHY: bool is an int subclass but not a valid redundancy count.
        return None  # WHY: invalid values must not count as passing redundancy.
    if isinstance(value, int):  # WHY: some payloads carry the count as a number.
        return value if value > 0 else None  # WHY: zero or negative values are invalid.
    if isinstance(value, Mapping):  # WHY: some payloads carry a map of upstream switches.
        count_value = value.get("count") or value.get("num_switches") or len(value)  # WHY: support known shapes.
        return normalize_switch_redundancy(count_value)  # WHY: reuse one validation rule.
    return None  # WHY: unknown shapes are exported as unknown.


def classify_switch_redundancy(count: int | None) -> str:
    """Return the redundancy class for a normalized redundancy count."""
    if count == 1:  # WHY: one switch attachment gives no redundancy.
        return "none"  # WHY: the site summary reports no-redundancy counts.
    if count == 2:  # WHY: two switch attachments meet the good threshold.
        return "good"  # WHY: the site summary reports good-redundancy counts.
    if count is not None and count >= 3:  # WHY: three or more switch attachments exceed the good threshold.
        return "excellent"  # WHY: the site summary reports excellent-redundancy counts.
    return "unknown"  # WHY: missing or invalid source data must not look healthy.


def predominant_versions(rows: Sequence[Mapping[str, object]]) -> dict[str, str]:
    """Return the most common version for each AP model."""
    counters: dict[str, Counter[str]] = defaultdict(Counter)  # WHY: one version counter per AP model.
    for row in rows:  # WHY: each AP contributes at most one model and version pair.
        model = _text(row.get("model"))  # WHY: empty model cannot define a useful version group.
        version = _text(row.get("version"))  # WHY: empty versions are excluded from the expected version.
        if model and version:  # WHY: both fields are required for the predominant version.
            counters[model][version] += 1  # WHY: count the version inside its model group.
    return {model: counter.most_common(1)[0][0] for model, counter in counters.items()}  # WHY: choose the mode.


def build_ap_rows(rows: Sequence[Mapping[str, object]]) -> list[ApScorecardRow]:
    """Build AP scorecard rows from raw AP statistics rows."""
    expected_versions = predominant_versions(rows)  # WHY: version compliance falls back to the predominant version.
    return [_build_ap_row(row, expected_versions) for row in rows]  # WHY: create one output row for each AP.


def ap_rows_as_dicts(rows: Sequence[ApScorecardRow]) -> list[dict[str, object]]:
    """Return AP scorecard rows as dictionaries."""
    return [asdict(row) for row in rows]  # WHY: the shared exporter consumes dictionaries.


def site_rows_as_dicts(rows: Sequence[SiteScorecardRow]) -> list[dict[str, object]]:
    """Return site scorecard rows as dictionaries."""
    return [asdict(row) for row in rows]  # WHY: the shared exporter consumes dictionaries.


def build_site_rows(rows: Sequence[ApScorecardRow]) -> list[SiteScorecardRow]:
    """Build one site scorecard row for each site with APs."""
    grouped: dict[tuple[str, str], list[ApScorecardRow]] = defaultdict(list)  # WHY: group AP rows by site.
    for row in rows:  # WHY: each AP belongs to exactly one site in the scorecard.
        grouped[(row.site_id, row.site)].append(row)  # WHY: keep display name beside the stable site ID.
    return [_build_site_row(site_id, site, site_rows) for (site_id, site), site_rows in sorted(grouped.items())]


def build_organization_summary(rows: Sequence[ApScorecardRow]) -> OrganizationSummary:
    """Build organization-wide scorecard percentages."""
    total = len(rows)  # WHY: every organization tile uses all AP rows as its denominator.
    return OrganizationSummary(  # WHY: console output uses one typed summary object.
        ap_count=total,
        connection_status_percent=_percent(_count(rows, _is_connected), total),
        vlans_percent=_percent(_count(rows, _vlan_passes), total),
        version_compliance_percent=_percent(_count(rows, lambda row: row.version_compliant), total),
        switch_redundancy_percent=_percent(_count(rows, _redundancy_passes), total),
        potential_anomalies_percent=_percent(_count(rows, _has_no_anomaly), total),
    )


def _build_ap_row(row: Mapping[str, object], expected_versions: Mapping[str, str]) -> ApScorecardRow:
    """Build one AP scorecard row."""
    model = _text(row.get("model"))  # WHY: model scopes version compliance.
    version = _text(row.get("version"))  # WHY: version is compared to the expected version.
    expected_version = _expected_version(row, model, expected_versions)  # WHY: explicit target beats fallback.
    redundancy_count = normalize_switch_redundancy(row.get("switch_redundancy"))  # WHY: normalize source shape.
    lldp_stat = _mapping(row.get("lldp_stat"))  # WHY: missing LLDP must produce empty power fields.
    return ApScorecardRow(  # WHY: one typed row keeps exports and aggregations aligned.
        site=_site_name(row),
        site_id=_text(row.get("site_id")),
        ap_name=_text(row.get("name")),
        mac=_text(row.get("mac")),
        model=model,
        version=version,
        predominant_version=expected_version,
        version_compliant=bool(version and expected_version and version == expected_version),
        status=_text(row.get("status")),
        offline_reason=_offline_reason(row),
        inactive_wired_vlans=_join_values(row.get("inactive_wired_vlans")),
        switch_redundancy_count=redundancy_count,
        switch_redundancy_class=classify_switch_redundancy(redundancy_count),
        power_constrained=_optional_bool(row.get("power_constrained")),
        power_opmode=_text(row.get("power_opmode")),
        power_budget=_scalar_or_empty(row.get("power_budget")),
        lldp_power_allocated=_scalar_or_empty(lldp_stat.get("power_allocated")),
        lldp_power_needed=_scalar_or_empty(lldp_stat.get("power_needed", lldp_stat.get("power_requested"))),
        config_reverted=_optional_bool(row.get("config_reverted")),
        last_trouble=_readable_mapping(row.get("last_trouble")),
        expiring_certificate_count=len(_mapping(row.get("expiring_certs"))),
        uptime_days=_uptime_days(row.get("uptime")),
    )


def _build_site_row(site_id: str, site: str, rows: Sequence[ApScorecardRow]) -> SiteScorecardRow:
    """Build one site summary row from AP rows."""
    total = len(rows)  # WHY: every tile percentage uses the site AP count.
    connection = _percent(_count(rows, _is_connected), total)  # WHY: connected APs drive the first tile.
    vlans = _percent(_count(rows, _vlan_passes), total)  # WHY: no inactive VLANs drives the VLAN tile.
    version = _percent(_count(rows, lambda row: row.version_compliant), total)  # WHY: firmware compliance tile.
    redundancy = _percent(_count(rows, _redundancy_passes), total)  # WHY: two or more switches pass.
    anomalies = _percent(_count(rows, _has_no_anomaly), total)  # WHY: no anomaly signals pass.
    return SiteScorecardRow(  # WHY: one typed row keeps the site export stable.
        site=site,
        site_id=site_id,
        ap_count=total,
        connection_status_percent=connection,
        connection_status_band=tile_color_band(connection),
        vlans_percent=vlans,
        vlans_band=tile_color_band(vlans),
        version_compliance_percent=version,
        version_compliance_band=tile_color_band(version),
        switch_redundancy_percent=redundancy,
        switch_redundancy_band=tile_color_band(redundancy),
        potential_anomalies_percent=anomalies,
        potential_anomalies_band=tile_color_band(anomalies),
        switch_redundancy_none_count=_count(rows, lambda row: row.switch_redundancy_class == "none"),
        switch_redundancy_good_count=_count(rows, lambda row: row.switch_redundancy_class == "good"),
        switch_redundancy_excellent_count=_count(rows, lambda row: row.switch_redundancy_class == "excellent"),
    )


def _expected_version(row: Mapping[str, object], model: str, expected_versions: Mapping[str, str]) -> str:
    """Return the expected version from upgrade data or predominant version."""
    upgrade = _mapping(row.get("auto_upgrade_stat"))  # WHY: some payloads include explicit upgrade evidence.
    explicit = _text(upgrade.get("target_version") or upgrade.get("expected_version"))  # WHY: target wins.
    return explicit or expected_versions.get(model, "")  # WHY: fallback supports payloads without upgrade target.


def _site_name(row: Mapping[str, object]) -> str:
    """Return the site display name for one AP row."""
    return _text(row.get("site_name")) or _text(row.get("site_id"))  # WHY: site_id is the prompt-free fallback.


def _offline_reason(row: Mapping[str, object]) -> str:
    """Return the best available offline reason."""
    return _text(row.get("offline_reason") or row.get("reason")) or _readable_mapping(row.get("last_trouble"))


def _is_connected(row: ApScorecardRow) -> bool:
    """Return true when an AP is connected."""
    return row.status.lower() == "connected"  # WHY: Mist stats use connected for healthy APs.


def _vlan_passes(row: ApScorecardRow) -> bool:
    """Return true when an AP has no inactive wired VLANs."""
    return row.inactive_wired_vlans == ""  # WHY: any listed VLAN is a tile failure.


def _redundancy_passes(row: ApScorecardRow) -> bool:
    """Return true when an AP has two or more switch links."""
    return row.switch_redundancy_count is not None and row.switch_redundancy_count >= 2


def _has_no_anomaly(row: ApScorecardRow) -> bool:
    """Return true when no selected anomaly signal is present."""
    return not row.config_reverted and row.last_trouble == "" and not row.power_constrained


def _count(rows: Iterable[ApScorecardRow], predicate: Callable[[ApScorecardRow], bool]) -> int:
    """Return the number of rows that match a predicate."""
    return sum(1 for row in rows if predicate(row))  # WHY: count passing rows without mutating the input rows.


def _percent(count: int, total: int) -> float:
    """Return a percentage rounded to two decimals."""
    return round((count / total) * 100, 2) if total else 0.0  # WHY: zero rows must not divide by zero.


def _text(value: object) -> str:
    """Return a stripped text value, or an empty string."""
    return str(value).strip() if value is not None else ""  # WHY: exports need empty cells for missing values.


def _mapping(value: object) -> Mapping[str, object]:
    """Return a mapping value, or an empty mapping."""
    return value if isinstance(value, Mapping) else {}  # WHY: missing nested objects must not raise exceptions.


def _readable_mapping(value: object) -> str:
    """Return a compact readable value for a nested object."""
    if isinstance(value, Mapping):  # WHY: last_trouble usually arrives as a small mapping.
        return ",".join(f"{key}={item}" for key, item in sorted(value.items()))  # WHY: stable text aids diffs.
    return _text(value)  # WHY: scalar trouble values can be exported directly.


def _join_values(value: object) -> str:
    """Return a comma-separated list for a sequence value."""
    if isinstance(value, str):  # WHY: text values are already readable.
        return value  # WHY: avoid splitting a VLAN string into characters.
    if isinstance(value, Sequence):  # WHY: Mist returns VLAN IDs as a list.
        return ",".join(str(item) for item in value)  # WHY: one CSV cell lists every VLAN ID.
    return ""  # WHY: missing VLANs mean the AP passes the VLAN tile.


def _scalar_or_empty(value: object) -> int | float | str | None:
    """Return simple scalar values and convert unsupported values to an empty string."""
    if value is None:  # WHY: missing values should produce empty report cells.
        return ""  # WHY: the CSV contract requires empty LLDP cells when LLDP data is missing.
    if isinstance(value, bool | int | float | str):  # WHY: exporter can write simple scalars.
        return value  # WHY: preserve the source scalar exactly.
    return ""  # WHY: complex values do not belong in a scalar report cell.


def _optional_bool(value: object) -> bool | None:
    """Return a boolean value only when the source value is boolean."""
    return value if isinstance(value, bool) else None  # WHY: missing flags must not become false evidence.


def _uptime_days(value: object) -> float | str:
    """Return uptime seconds as days."""
    if isinstance(value, bool):  # WHY: bool is numeric but not a valid uptime.
        return ""  # WHY: invalid uptime should leave the cell empty.
    if isinstance(value, int | float):  # WHY: Mist reports uptime in seconds.
        return round(value / SECONDS_PER_DAY, 2)  # WHY: days are easier for operators to compare.
    return ""  # WHY: missing uptime should leave the cell empty.
