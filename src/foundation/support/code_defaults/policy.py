"""Apply reviewed consumer classifications and reject baseline regressions."""

from dataclasses import dataclass
from typing import cast

from src.foundation.support.code_defaults.inventory import Candidate, Inventory

FIRST_BATCH_SCOPE = (
    "src/mist/resources/device/ap_profile_migration_manager.py",
    "src/mist/intelligence/analytics/zone_analyzer.py",
    "src/mist/resources/inventory/csv_comparator.py",
    "src/foundation/support/utils/address_utils.py",
    "src/mist/resources/org/org_config_migration_manager.py",
)
_CLASSIFICATION_RULES = {
    FIRST_BATCH_SCOPE[0]: {
        "aps_planned": "already_validated",
        "aps_reassigned": "already_validated",
        "device_id": "already_validated",
        "id": "excluded_ownership",
        "mac": "already_validated",
        "migration_timestamp_utc": "already_validated",
        "name": "display_only",
        "source_profile_id": "already_validated",
        "source_profile_snapshot": "valid_optional",
        "target_profile_id": "already_validated",
    },
    FIRST_BATCH_SCOPE[1]: {
        "analytic": "valid_optional",
        "assets_enabled": "display_only",
        "bounce": "display_only",
        "clients_enabled": "display_only",
        "common_zones": "already_validated",
        "created_time": "display_only",
        "current_config": "already_validated",
        "custom_names": "already_validated",
        "dwell_tag_configs": "already_validated",
        "dwell_tag_names": "valid_optional",
        "dwell_tags": "valid_optional",
        "enabled": "display_only",
        "engaged": "display_only",
        "engagement": "valid_optional",
        "hours": "valid_optional",
        "id": "display_only",
        "map_id": "display_only",
        "min_duration": "display_only",
        "min_duration_values": "already_validated",
        "missing_zones": "already_validated",
        "modified_time": "display_only",
        "name": "display_only",
        "occupancy": "valid_optional",
        "occupancy_configs": "already_validated",
        "passerby": "display_only",
        "sdkclients_enabled": "display_only",
        "site_name": "display_only",
        "sites_missing_common_zones": "already_validated",
        "sites_with_business_hours": "already_validated",
        "sites_with_custom_names": "already_validated",
        "sites_with_dwell_deviations": "already_validated",
        "sites_with_occupancy_deviations": "already_validated",
        "stationed": "display_only",
        "unconnected_clients_enabled": "display_only",
        "vertices": "display_only",
        "zone_count_deviations": "already_validated",
        "zone_count_stats": "already_validated",
        "zone_frequency": "already_validated",
        "zone_names": "already_validated",
        "zones": "valid_optional",
        "<dynamic>": "already_validated",
    },
    FIRST_BATCH_SCOPE[2]: {
        "Address": "valid_optional",
        "City": "valid_optional",
        "Comparison_Address": "display_only",
        "Comparison_City": "display_only",
        "Comparison_State": "display_only",
        "END_CUSTOMER_ACCOUNT_ID": "display_only",
        "END_CUSTOMER_NAME": "display_only",
        "Mist_Address_Line_1": "display_only",
        "Mist_City": "display_only",
        "Mist_State": "display_only",
        "State": "valid_optional",
        "Zip": "already_validated",
        "city": "display_only",
        "display_name": "display_only",
        "id": "display_only",
        "model": "display_only",
        "name": "display_only",
        "serial": "already_validated",
        "site_address": "valid_optional",
        "site_id": "excluded_ownership",
        "site_name": "display_only",
        "state": "display_only",
        "street": "valid_optional",
        "zip_code": "already_validated",
        "<dynamic>": "already_validated",
    },
    FIRST_BATCH_SCOPE[3]: {
        "Skip_Address": "valid_optional",
        "Skip_City": "valid_optional",
        "Skip_State": "valid_optional",
        "Skip_Zip": "valid_optional",
        "address": "valid_optional",
        "address_line_1": "already_validated",
        "address_line_2": "valid_optional",
        "city": "already_validated",
        "class": "display_only",
        "display_name": "display_only",
        "place_type": "valid_optional",
        "postal_code": "already_validated",
        "state": "already_validated",
        "type": "display_only",
        "zip": "already_validated",
        "<dynamic>": "already_validated",
    },
    FIRST_BATCH_SCOPE[4]: {
        "addresses": "valid_optional",
        "id": "excluded_ownership",
        "list_kwargs": "valid_optional",
        "networks": "valid_optional",
        "object_counts": "display_only",
        "reason": "display_only",
        "services": "valid_optional",
        "<dynamic>": "already_validated",
    },
}
_EVIDENCE = {
    "high": "An empty response can hide a failed profile or site lookup.",
    "already_validated": "The consumer validates the field or rejects missing data before use.",
    "valid_optional": "The consumer permits this optional value or explicit empty collection.",
    "display_only": "The value fills a report, display, or descriptive result.",
    "excluded_ownership": "Issue #2863 owns this identifier outside this batch.",
}
_VALID_CLASSES = frozenset(_EVIDENCE)


@dataclass(frozen=True)
class GuardResult:
    """Return a guard decision with counts and identity-level changes."""

    status: str
    message: str
    parsed_files: int
    accepted_total: int
    new_high: tuple[str, ...] = ()
    removed_high: tuple[str, ...] = ()


class BaselineValidator:
    """Validate inventory completeness and reviewed baseline evidence."""

    def validate(self, inventory: Inventory, baseline: dict[str, object]) -> str:
        """Return the first malformed-scan or baseline reason."""
        for check in (
            self._validate_inventory,
            self._validate_metadata,
            self._validate_dispositions,
        ):
            problem = check(inventory, baseline)
            if problem:
                return problem
        return ""

    @staticmethod
    def accepted_high(baseline: dict[str, object]) -> set[str]:
        """Return high identities after validation has checked their types."""
        return set(cast(list[str], baseline["accepted_high"]))

    @staticmethod
    def accepted_total(baseline: dict[str, object]) -> int:
        """Return the accepted total after validation has checked its type."""
        return cast(int, baseline["accepted_total"])

    @staticmethod
    def disposition_map(baseline: dict[str, object]) -> dict[str, dict[str, object]]:
        """Return disposition rows indexed by their validated identities."""
        rows = cast(list[dict[str, object]], baseline["dispositions"])
        return {cast(str, row["identity"]): row for row in rows}

    @staticmethod
    def _validate_inventory(inventory: Inventory, _baseline: dict[str, object]) -> str:
        """Reject parse failures, duplicates, and incomplete scope selection."""
        identities = [candidate.identity for candidate in inventory.candidates]
        if inventory.parse_failures:
            return inventory.parse_failures[0]
        if len(set(identities)) != len(identities):
            return "inventory contains duplicate candidate identities"
        if tuple(sorted(inventory.selected_paths)) != tuple(sorted(FIRST_BATCH_SCOPE)):
            return "selected files do not match the exact first-batch scope"
        if inventory.parsed_files != len(FIRST_BATCH_SCOPE):
            return "scope did not parse all five expected files"
        return ""

    @staticmethod
    def _validate_metadata(_inventory: Inventory, baseline: dict[str, object]) -> str:
        """Reject a baseline with an unknown schema, revision, or scope."""
        if baseline.get("schema_version") != 1 or baseline.get("criterion_version") != "1":
            return "baseline schema or criterion version is invalid"
        revision = baseline.get("reviewed_revision")
        if not isinstance(revision, str) or not revision:
            return "baseline reviewed revision is missing"
        if baseline.get("scope") != list(FIRST_BATCH_SCOPE):
            return "baseline scope does not match the exact first-batch scope"
        return ""

    def _validate_dispositions(self, _inventory: Inventory, baseline: dict[str, object]) -> str:
        """Require unique, evidenced dispositions and a derived high total."""
        problem, rows, accepted_strings = self._disposition_data(baseline)
        if problem:
            return problem
        checks = (
            self._validate_disposition_rows,
            self._validate_identity_uniqueness,
            self._validate_accepted_high,
            self._validate_accepted_total,
        )
        for check in checks:
            problem = check(rows, accepted_strings, baseline)
            if problem:
                return problem
        return ""

    @staticmethod
    def _disposition_data(
        baseline: dict[str, object],
    ) -> tuple[str, list[dict[str, object]], list[str]]:
        """Validate top-level disposition collections and narrow their types."""
        dispositions = baseline.get("dispositions")
        accepted = baseline.get("accepted_high")
        if not isinstance(dispositions, list) or not isinstance(accepted, list):
            return "baseline dispositions and high identities must be lists", [], []
        accepted_strings = [identity for identity in accepted if isinstance(identity, str)]
        if len(accepted_strings) != len(accepted):
            return "baseline high identities must be strings", [], []
        rows: list[dict[str, object]] = []
        for row in dispositions:
            if not isinstance(row, dict):
                return "baseline disposition rows must be objects", [], []
            rows.append(row)
        return "", rows, accepted_strings

    @staticmethod
    def _validate_disposition_rows(
        rows: list[dict[str, object]],
        _accepted: list[str],
        _baseline: dict[str, object],
    ) -> str:
        """Require each row to carry a known classification, evidence, and owner."""
        for row in rows:
            classification = row.get("classification")
            evidence = row.get("evidence")
            owner = row.get("ownership")
            if not isinstance(classification, str) or classification not in _VALID_CLASSES:
                return "baseline disposition classification is invalid"
            if not isinstance(evidence, str) or not evidence or not isinstance(owner, str):
                return "baseline disposition evidence or ownership is invalid"
            if not isinstance(row.get("identity"), str):
                return "baseline disposition identity is missing"
        return ""

    @staticmethod
    def _validate_identity_uniqueness(
        rows: list[dict[str, object]],
        _accepted: list[str],
        _baseline: dict[str, object],
    ) -> str:
        """Reject duplicate candidate identities in reviewed rows."""
        identities = [cast(str, row["identity"]) for row in rows]
        if len(set(identities)) != len(identities):
            return "baseline disposition identities are missing or duplicated"
        return ""

    @staticmethod
    def _validate_accepted_high(
        rows: list[dict[str, object]],
        accepted: list[str],
        _baseline: dict[str, object],
    ) -> str:
        """Require the accepted high identities to match reviewed rows."""
        baseline_high = {cast(str, row["identity"]) for row in rows if row["classification"] == "high"}
        if set(accepted) != baseline_high or len(accepted) != len(set(accepted)):
            return "baseline high identities do not match reviewed dispositions"
        return ""

    @staticmethod
    def _validate_accepted_total(
        _rows: list[dict[str, object]],
        accepted: list[str],
        baseline: dict[str, object],
    ) -> str:
        """Require the stored high total to match its identity list."""
        total = baseline.get("accepted_total")
        if not isinstance(total, int) or isinstance(total, bool) or total != len(accepted):
            return "baseline accepted total is invalid"
        return ""


class GuardPolicy:
    """Validate reviewed dispositions and compare high-severity identities."""

    def __init__(self) -> None:
        """Keep baseline validation separate from regression decisions."""
        self._baseline_validator = BaselineValidator()

    def evaluate(self, inventory: Inventory, baseline: dict[str, object]) -> GuardResult:
        """Return passed, regression, or invalid-input status for one scan."""
        problem = self._baseline_validator.validate(inventory, baseline)
        if problem:
            return GuardResult("invalid_input", problem, inventory.parsed_files, 0)
        high, unknown = self._classifications(inventory.candidates)
        if unknown:
            return GuardResult(
                "invalid_input",
                f"unclassified in-scope candidate: {unknown[0]}",
                inventory.parsed_files,
                0,
            )
        accepted = self._baseline_validator.accepted_high(baseline)
        added = tuple(sorted(high - accepted))
        removed = tuple(sorted(accepted - high))
        total = len(high)
        regression = self._regression_result(inventory, baseline, total, added, removed)
        if regression:
            return regression
        disposition_problem = self._validate_current_dispositions(inventory, baseline, total)
        if disposition_problem:
            return disposition_problem
        message = f"high candidates: {total}; removed candidates: {len(removed)}"
        return GuardResult("passed", message, inventory.parsed_files, total, (), removed)

    @staticmethod
    def classify(candidate: Candidate) -> tuple[str, str]:
        """Return a reviewed classification and evidence for one candidate."""
        if candidate.path not in FIRST_BATCH_SCOPE:
            return "outside_batch", "The candidate is outside the approved first-batch scope."
        classification = _CLASSIFICATION_RULES.get(candidate.path, {}).get(candidate.input_key, "")
        if candidate.path == FIRST_BATCH_SCOPE[0] and candidate.shape == "attribute" and candidate.input_key == "data":
            classification = "high"
        return classification, _EVIDENCE.get(classification, "")

    @staticmethod
    def _regression_result(
        inventory: Inventory,
        baseline: dict[str, object],
        total: int,
        added: tuple[str, ...],
        removed: tuple[str, ...],
    ) -> GuardResult | None:
        """Return a regression when a new high identity or excess total appears."""
        if not added and total <= BaselineValidator.accepted_total(baseline):
            return None
        message = f"new high candidates: {len(added)}; removed candidates: {len(removed)}"
        return GuardResult("regression", message, inventory.parsed_files, total, added, removed)

    def _validate_current_dispositions(
        self,
        inventory: Inventory,
        baseline: dict[str, object],
        total: int,
    ) -> GuardResult | None:
        """Require each current candidate to match its reviewed policy row."""
        dispositions = self._baseline_validator.disposition_map(baseline)
        for candidate in inventory.candidates:
            problem = self._candidate_disposition_problem(candidate, dispositions)
            if problem:
                return GuardResult("invalid_input", problem, inventory.parsed_files, total)
        return None

    def _candidate_disposition_problem(
        self,
        candidate: Candidate,
        dispositions: dict[str, dict[str, object]],
    ) -> str:
        """Reject absent evidence, changed classifications, or wrong ownership."""
        classification, _evidence = self.classify(candidate)
        disposition = dispositions.get(candidate.identity)
        if disposition is None:
            return f"candidate lacks a reviewed disposition: {candidate.identity}"
        if disposition["classification"] != classification or not disposition["evidence"]:
            return f"candidate disposition no longer matches reviewed policy: {candidate.identity}"
        expected_owner = "issue-2863" if classification == "excluded_ownership" else "issue-2753"
        if disposition["ownership"] != expected_owner:
            return f"candidate ownership does not match reviewed scope: {candidate.identity}"
        return ""

    def _classifications(self, candidates: tuple[Candidate, ...]) -> tuple[set[str], list[str]]:
        """Classify scoped candidates and report missing review rules."""
        high: set[str] = set()
        unknown: list[str] = []
        for candidate in candidates:
            classification, _evidence = self.classify(candidate)
            if not classification:
                unknown.append(candidate.identity)
            elif classification == "high":
                high.add(candidate.identity)
        return high, sorted(unknown)
