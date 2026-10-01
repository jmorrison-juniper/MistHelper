"""Pure model logic for the organization switch scorecard report."""

from __future__ import annotations  # WHY: postpone annotations for Python 3.13 runtime clarity.

import logging  # WHY: record threshold fallback decisions for operators.
import os  # WHY: read the operator-configured AP affinity limit.
from collections import Counter, defaultdict  # WHY: compute predominant versions and per-site groups.
from collections.abc import Callable, Mapping, Sequence  # WHY: type JSON-like inputs and tile predicates.
from dataclasses import dataclass  # WHY: group report settings and computed outputs.
from typing import Any  # WHY: Mist API rows are dynamic JSON dictionaries.

logger = logging.getLogger(__name__)  # WHY: name this module in scorecard logs.

AFFINITY_ENV = "SWITCH_AP_AFFINITY_LIMIT"  # WHY: the operator can tune the Mist default.
DEFAULT_AFFINITY_LIMIT = 12  # WHY: Mist Switch-AP Affinity uses 12 APs by default.
SECONDS_PER_DAY = 86400  # WHY: uptime arrives in seconds and the report shows days.
SUCCESS_CONFIG_STATES = {"success", "applied", "synced"}  # WHY: tolerate common success spellings.
NORMAL_STATES = {"", "ok", "up", "good", "normal", "present"}  # WHY: module lists can use several healthy words.

DETAIL_COLUMNS = [  # WHY: keep the detail CSV column order stable for operators.
    "site_id",
    "site_name",
    "switch_name",
    "switch_mac",
    "model",
    "version",
    "predominant_model_version",
    "version_compliant",
    "config_status",
    "config_success",
    "ap_count",
    "affinity_limit",
    "affinity_exceeded",
    "redundant_ap_count",
    "poe_budget_watts",
    "poe_draw_watts",
    "pending_versions",
    "bios_versions",
    "fpga_versions",
    "backup_versions",
    "fan_errors",
    "psu_errors",
    "temperature_errors",
    "uptime_days",
    "last_trouble",
]

SITE_COLUMNS = [  # WHY: keep the site summary CSV column order stable for operators.
    "site_id",
    "site_name",
    "switch_count",
    "switch_ap_affinity_percent",
    "switch_ap_affinity_count",
    "poe_compliance_percent",
    "poe_compliance_count",
    "version_compliance_percent",
    "version_compliance_count",
    "switch_uptime_percent",
    "switch_uptime_count",
    "config_success_percent",
    "config_success_count",
    "config_unknown_count",
    "potential_anomalies_percent",
    "potential_anomalies_count",
]


@dataclass(slots=True)
class ScorecardSettings:
    """Resolved scorecard settings."""

    affinity_limit: int  # WHY: every row records the AP limit used for its affinity decision.
    fallback_note: str = ""  # WHY: invalid environment input must be visible to the operator.


@dataclass(slots=True)
class ScorecardOutput:
    """All rows that one scorecard run produces."""

    detail_rows: list[dict[str, Any]]  # WHY: `SwitchScorecard.csv` holds one switch row.
    site_rows: list[dict[str, Any]]  # WHY: `SwitchScorecardBySite.csv` holds one site row.
    org_summary: dict[str, Any]  # WHY: the console summary uses the same math as the site file.


class SwitchScorecardSettings:
    """Resolve scorecard settings from the environment."""

    @staticmethod
    def from_environment(environ: Mapping[str, str] | None = None) -> ScorecardSettings:
        """Return the AP affinity limit and any fallback note."""
        values = os.environ if environ is None else environ  # WHY: tests can pass a fake environment.
        raw_value = values.get(AFFINITY_ENV, "")  # WHY: absent means use the Mist default.
        if not raw_value:  # WHY: the normal path must be quiet and deterministic.
            return ScorecardSettings(DEFAULT_AFFINITY_LIMIT)  # WHY: Mist default applies when unset.
        try:
            parsed_value = int(raw_value)  # WHY: the environment carries text only.
        except ValueError:
            return SwitchScorecardSettings._fallback(raw_value)  # WHY: invalid text cannot set the limit.
        if parsed_value <= 0:  # WHY: zero or negative AP limits have no operational meaning.
            return SwitchScorecardSettings._fallback(raw_value)  # WHY: keep the report safe and predictable.
        return ScorecardSettings(parsed_value)  # WHY: a positive integer is a valid operator override.

    @staticmethod
    def _fallback(raw_value: str) -> ScorecardSettings:
        """Return default settings after an invalid environment value."""
        note = (  # WHY: the operation prints one plain reason for the fallback.
            f"{AFFINITY_ENV}={raw_value!r} is invalid; using default {DEFAULT_AFFINITY_LIMIT}."
        )
        logger.warning("%s", note)  # WHY: invalid configuration must be visible in logs.
        return ScorecardSettings(DEFAULT_AFFINITY_LIMIT, note)  # WHY: the report continues with the safe value.


class SwitchScorecardBuilder:
    """Build switch detail, site summary, and organization summary rows."""

    @classmethod
    def build(
        cls,
        switches: Sequence[Mapping[str, Any]],
        settings: ScorecardSettings,
        site_names: Mapping[str, str] | None = None,
    ) -> ScorecardOutput:
        """Return all scorecard output rows for one API result."""
        logger.info("Building switch scorecard rows for %s switches", len(switches))  # WHY: log transform start.
        predominant = cls._predominant_versions(switches)  # WHY: version compliance is per model.
        site_lookup = site_names or {}  # WHY: tests can omit site enrichment while live runs pass names.
        detail_rows = [  # WHY: one enriched detail row is produced for each switch.
            cls._detail_row(row, predominant, settings, site_lookup) for row in switches
        ]
        site_rows = cls._site_rows(detail_rows)  # WHY: site tiles summarize detail row decisions.
        org_summary = cls._summary_row("ORG", "Organization", detail_rows)  # WHY: console summary mirrors site math.
        logger.debug("Built detail=%s site=%s rows", len(detail_rows), len(site_rows))  # WHY: log transform result.
        return ScorecardOutput(detail_rows, site_rows, org_summary)  # WHY: operation writes both row sets.

    @staticmethod
    def _predominant_versions(switches: Sequence[Mapping[str, Any]]) -> dict[str, str]:
        """Return the predominant version for each model."""
        versions: dict[str, Counter[str]] = defaultdict(Counter)  # WHY: group version counts by switch model.
        for row in switches:  # WHY: inspect every switch before building compliance rows.
            model = str(row.get("model") or "")  # WHY: empty models group together without crashing.
            version = str(row.get("version") or "")  # WHY: empty versions must remain comparable.
            if version:  # WHY: a blank version cannot be predominant evidence.
                versions[model][version] += 1  # WHY: count the running versions for this model.
        return {model: SwitchScorecardBuilder._stable_winner(counts) for model, counts in versions.items()}

    @staticmethod
    def _stable_winner(counts: Counter[str]) -> str:
        """Return the most common version, with a stable tie breaker."""
        if not counts:  # WHY: a model can lack version evidence.
            return ""  # WHY: no predominant version is available.
        winners = sorted(counts.items(), key=lambda item: (-item[1], item[0]))  # WHY: ties pick the first text value.
        return winners[0][0]  # WHY: the sorted first item is the stable predominant version.

    @classmethod
    def _detail_row(
        cls,
        row: Mapping[str, Any],
        predominant: Mapping[str, str],
        settings: ScorecardSettings,
        site_names: Mapping[str, str],
    ) -> dict[str, Any]:
        """Return one `SwitchScorecard.csv` row."""
        modules = cls._safe_sequence(row.get("module_stat"))  # WHY: missing module stats are valid.
        model = str(row.get("model") or "")  # WHY: the model selects the predominant version.
        version = str(row.get("version") or "")  # WHY: row and compliance output name the running version.
        expected_version = predominant.get(model, "")  # WHY: absent model version means no compliance evidence.
        ap_count = cls._ap_count(row)  # WHY: AP affinity uses connected AP count.
        module_values = cls._module_values(modules)  # WHY: module lists become flat columns.
        config_success = cls._config_success(row.get("config_status"))  # WHY: keep unknown separate from failure.
        return {  # WHY: the export writer accepts flat dictionaries.
            "site_id": row.get("site_id", ""),
            "site_name": cls._site_name(row, site_names),
            "switch_name": row.get("name") or row.get("hostname") or row.get("device_name") or "",
            "switch_mac": row.get("mac", ""),
            "model": model,
            "version": version,
            "predominant_model_version": expected_version,
            "version_compliant": bool(version and version == expected_version),
            "config_status": row.get("config_status", ""),
            "config_success": config_success,
            "ap_count": ap_count,
            "affinity_limit": settings.affinity_limit,
            "affinity_exceeded": ap_count > settings.affinity_limit,
            "redundant_ap_count": cls._redundant_ap_count(row),
            **module_values,
            "uptime_days": cls._uptime_days(row.get("uptime")),
            "last_trouble": cls._readable_value(row.get("last_trouble")),
        }

    @staticmethod
    def _safe_sequence(value: Any) -> list[Mapping[str, Any]]:
        """Return only mapping items from an optional API list."""
        if not isinstance(value, list):  # WHY: absent or malformed module lists must not crash the report.
            return []  # WHY: empty module output satisfies the acceptance criterion.
        return [item for item in value if isinstance(item, Mapping)]  # WHY: ignore malformed module entries.

    @classmethod
    def _module_values(cls, modules: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Return flattened module evidence columns."""
        poe_budget = sum(cls._number(cls._nested(module, ("poe", "max_power"))) for module in modules)
        poe_draw = sum(cls._number(cls._nested(module, ("poe", "power_draw"))) for module in modules)
        return {
            "poe_budget_watts": poe_budget or "",
            "poe_draw_watts": poe_draw or "",
            "pending_versions": cls._joined_values(modules, ("pending_version",)),
            "bios_versions": cls._joined_values(modules, ("bios_version",)),
            "fpga_versions": cls._joined_values(modules, ("fpga_version",)),
            "backup_versions": cls._joined_values(modules, ("backup_version", "recovery_version")),
            "fan_errors": cls._joined_errors(modules, "fans"),
            "psu_errors": cls._joined_errors(modules, "psus"),
            "temperature_errors": cls._joined_errors(modules, "temperatures"),
        }

    @staticmethod
    def _nested(row: Mapping[str, Any], path: tuple[str, ...]) -> Any:
        """Return a nested value from a mapping path."""
        current: Any = row  # WHY: walk each path without assuming nested keys exist.
        for key in path:  # WHY: each path segment can be absent in Mist API rows.
            if not isinstance(current, Mapping):  # WHY: malformed intermediate values stop the lookup.
                return None  # WHY: no nested value is available.
            current = current.get(key)  # WHY: continue to the next path segment.
        return current  # WHY: the caller decides how to format the value.

    @staticmethod
    def _number(value: Any) -> float:
        """Return a float value or zero for missing API numbers."""
        if isinstance(value, int | float):  # WHY: numeric JSON values can be added directly.
            return float(value)  # WHY: sums can mix int and float safely.
        return 0.0  # WHY: missing power fields contribute no value.

    @classmethod
    def _joined_values(cls, modules: Sequence[Mapping[str, Any]], keys: tuple[str, ...]) -> str:
        """Return unique module values for one or more field names."""
        values = {str(module.get(key)) for module in modules for key in keys if module.get(key)}  # WHY: remove dupes.
        return ", ".join(sorted(values))  # WHY: stable CSV output helps reviews and tests.

    @classmethod
    def _joined_errors(cls, modules: Sequence[Mapping[str, Any]], key: str) -> str:
        """Return non-normal states from module component lists."""
        errors: list[str] = []  # WHY: preserve one readable token for each bad component.
        for module in modules:  # WHY: each FPC can have its own component list.
            for item in cls._safe_sequence(module.get(key)):  # WHY: absent component lists are healthy by omission.
                label = cls._component_label(item)  # WHY: the report names the component and state.
                if label:  # WHY: only non-normal states belong in the error column.
                    errors.append(label)  # WHY: collect all component problems.
        return ", ".join(sorted(errors))  # WHY: stable output keeps tests deterministic.

    @staticmethod
    def _component_label(item: Mapping[str, Any]) -> str:
        """Return a component label when the item is not in a normal state."""
        state = str(item.get("status") or item.get("state") or "").lower()  # WHY: schemas vary by component type.
        if state in NORMAL_STATES:  # WHY: healthy components should not create false alarms.
            return ""  # WHY: empty means no reportable component problem.
        name = item.get("name") or item.get("id") or item.get("slot") or "component"  # WHY: identify the component.
        return f"{name}:{state or 'unknown'}"  # WHY: name and state give enough repair context.

    @staticmethod
    def _ap_count(row: Mapping[str, Any]) -> int:
        """Return the switch AP count from the preferred API fields."""
        redundancy = row.get("ap_redundancy")  # WHY: Mist gives an AP count in the redundancy object.
        if isinstance(redundancy, Mapping) and isinstance(redundancy.get("num_aps"), int):  # WHY: direct field wins.
            return int(redundancy["num_aps"])  # WHY: this is the exact switch AP count.
        total = SwitchScorecardBuilder._nested(row, ("clients_stats", "total", "num_aps"))  # WHY: fallback source.
        if isinstance(total, list):  # WHY: the schema permits an array of AP counts.
            return sum(value for value in total if isinstance(value, int))  # WHY: sum module counts safely.
        return int(total) if isinstance(total, int) else 0  # WHY: missing AP count becomes zero.

    @staticmethod
    def _redundant_ap_count(row: Mapping[str, Any]) -> int:
        """Return APs with switch redundancy."""
        redundancy = row.get("ap_redundancy")  # WHY: redundancy evidence sits in one object.
        if not isinstance(redundancy, Mapping):  # WHY: missing evidence should not crash the report.
            return 0  # WHY: no redundancy evidence is available.
        value = redundancy.get("num_aps_with_switch_redundancy")  # WHY: exact field from the OpenAPI schema.
        return int(value) if isinstance(value, int) else 0  # WHY: malformed values become zero.

    @staticmethod
    def _config_success(value: Any) -> bool | None:
        """Return whether a config status means success."""
        normalized = str(value or "").strip().lower()  # WHY: API status text can vary by case.
        if not normalized:  # WHY: live stats can omit config_status for otherwise healthy switches.
            return None  # WHY: unknown config status must not count as success or failure.
        return normalized in SUCCESS_CONFIG_STATES  # WHY: summary tiles need a boolean.

    @staticmethod
    def _site_name(row: Mapping[str, Any], site_names: Mapping[str, str]) -> str:
        """Return the site display name for one switch row."""
        site_id = str(row.get("site_id") or "")  # WHY: site_id is the only field always present in live stats.
        return str(row.get("site_name") or site_names.get(site_id, site_id))  # WHY: avoid empty site-name cells.

    @staticmethod
    def _uptime_days(value: Any) -> float | str:
        """Return uptime as days, or empty when no uptime exists."""
        if not isinstance(value, int | float):  # WHY: no uptime evidence should stay blank.
            return ""  # WHY: blank is clearer than zero for missing data.
        return round(float(value) / SECONDS_PER_DAY, 2)  # WHY: days are easier for operators to compare.

    @staticmethod
    def _readable_value(value: Any) -> str:
        """Return an API value as compact operator text."""
        if value in (None, "", [], {}):  # WHY: missing trouble means no current trouble.
            return ""  # WHY: blank supports the potential-anomalies calculation.
        return str(value)  # WHY: keep unexpected API shapes visible to the operator.

    @classmethod
    def _site_rows(cls, detail_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Return one summary row for each site."""
        grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)  # WHY: group rows by site.
        for row in detail_rows:  # WHY: every switch contributes to exactly one site row.
            key = (str(row.get("site_id") or ""), str(row.get("site_name") or ""))  # WHY: stable site identity.
            grouped[key].append(row)  # WHY: collect rows before computing percentages.
        return [cls._summary_row(site_id, site_name, rows) for (site_id, site_name), rows in sorted(grouped.items())]

    @classmethod
    def _tile_counts(cls, rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
        """Return the compliant switch count for each scorecard tile."""
        predicates: dict[str, Callable[[Mapping[str, Any]], bool]] = {  # WHY: one predicate per Mist tile.
            "switch_ap_affinity": lambda row: not row.get("affinity_exceeded"),  # WHY: not exceeded means compliant.
            "poe_compliance": cls._poe_compliant,  # WHY: PoE compliance needs power draw within budget.
            "version_compliance": lambda row: bool(row.get("version_compliant")),  # WHY: predominant version per model.
            "switch_uptime": cls._has_positive_uptime,  # WHY: positive uptime means seen as up.
            "potential_anomalies": lambda row: not row.get("last_trouble"),  # WHY: no trouble means no anomaly signal.
        }
        return {
            name: sum(1 for row in rows if check(row)) for name, check in predicates.items()
        }  # WHY: one count per tile.

    @classmethod
    def _summary_row(cls, site_id: str, site_name: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Return one site or organization summary row."""
        total = len(rows)  # WHY: every percentage needs the denominator beside it.
        summary: dict[str, Any] = {
            "site_id": site_id,
            "site_name": site_name,
            "switch_count": total,
        }  # WHY: identity first.
        for name, count in cls._tile_counts(rows).items():  # WHY: each tile gets a percent column and a count column.
            summary[f"{name}_percent"] = cls._percent(count, total)  # WHY: the percent matches the Mist tile value.
            summary[f"{name}_count"] = count  # WHY: the count behind the percent lets an operator check the math.
        config_success_count = sum(1 for row in rows if row.get("config_success") is True)  # WHY: count known passes.
        config_unknown_count = sum(1 for row in rows if row.get("config_success") is None)  # WHY: count unknown rows.
        config_total = total - config_unknown_count  # WHY: unknown rows must not lower the config percentage.
        summary["config_success_percent"] = cls._percent(config_success_count, config_total)  # WHY: known-only score.
        summary["config_success_count"] = config_success_count  # WHY: keep the success count next to the percent.
        summary["config_unknown_count"] = config_unknown_count  # WHY: show rows excluded from the percentage.
        return summary  # WHY: the caller writes this row to the per-site file.

    @staticmethod
    def _poe_compliant(row: Mapping[str, Any]) -> bool:
        """Return whether PoE draw stays within budget, or has no budget evidence."""
        budget = row.get("poe_budget_watts")  # WHY: budget can be blank when no PoE module exists.
        draw = row.get("poe_draw_watts")  # WHY: draw can be blank when no PoE module exists.
        if not isinstance(budget, int | float) or not isinstance(draw, int | float):  # WHY: no evidence means neutral.
            return True  # WHY: avoid marking non-PoE switches as failures.
        return float(draw) <= float(budget)  # WHY: draw above budget is the failure signal.

    @staticmethod
    def _has_positive_uptime(row: Mapping[str, Any]) -> bool:
        """Return whether the row has positive uptime days."""
        uptime = row.get("uptime_days")  # WHY: the detail row already converted seconds to days.
        return isinstance(uptime, int | float) and float(uptime) > 0  # WHY: positive uptime counts as up.

    @staticmethod
    def _percent(count: int, total: int) -> float:
        """Return a rounded percentage for a count and total."""
        if total == 0:  # WHY: zero-switch organizations should not divide by zero.
            return 0.0  # WHY: no data produces a zero percentage summary.
        return round((count / total) * 100, 2)  # WHY: two decimals are readable and stable.
