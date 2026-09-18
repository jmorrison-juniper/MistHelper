"""Org-level Zscaler synthetic-probe manager (menu 206).

Builds, merges, or swaps ``synthetic_test.custom_probes`` entries on the
Mist org setting using a curated catalogue of Zscaler Client Connector
destinations shipped with the repo under ``data/``.

Why:
    Operators need a single-command way to keep the Zscaler reachability
    probe fleet in sync with their VLAN topology. Hand-maintaining the
    probe block against Zscaler's evolving Cloud Enforcement Node list is
    error-prone. This module treats the JSON in ``data/`` as the source of
    truth, and marks every probe it writes with the ``zcc-`` name prefix
    so a follow-up run can safely merge or swap without disturbing
    probes authored elsewhere.

Module-import must remain side-effect free (--help guard):
    Only ``import`` statements at module scope. All I/O, prompts, and API
    calls live inside functions invoked from the menu dispatch table.
"""

from __future__ import annotations  # WHY: PEP 604 unions stay available during type checking.

import json  # WHY: menu 206 reads and writes catalogue and setting payloads as JSON.
import logging  # WHY: destructive menu actions must leave an operator trace.
import math  # WHY: site distance calculations use trigonometric helpers.
from pathlib import Path  # WHY: data files must use portable path joins.
from typing import Any  # WHY: Mist API and cache payloads use duck-typed JSON.

# Import mistapi setting/sites modules at module load so tests can monkey-patch
# them via ``patch.object``. All four are side-effect free re-exports.
import mistapi  # WHY: pagination helpers come from the installed Mist SDK.
from mistapi.api.v1.orgs import setting as _mist_setting  # WHY: org setting reads and writes use this SDK module.
from mistapi.api.v1.orgs import sites as _mist_orgs_sites  # WHY: site override selection lists org sites.
from mistapi.api.v1.sites import setting as _mist_site_setting  # WHY: site override writes use this SDK module.

from src.utils.input_utils import InputUtils  # WHY: menu 206 prompts must handle EOF in SSH sessions.
from src.utils.zscaler_catalogue import (  # WHY: menu 206 consumes refreshed Zscaler caches.
    ensure_fresh,
    promote_cache_document,
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"  # WHY: catalogue files live under data.
_PROBE_SOURCE_FILE = "zscaler_client_connector_probes.json"  # WHY: static ZCC role data lives in this file.
_CENR_SOURCE_FILE = "zscaler_cenr_hostnames.json"  # WHY: refreshed CENR host data lives in this file.
_TOOL_NAME_PREFIX = "zcc-"  # WHY: tool-authored probes need a stable name prefix.
_TUNNEL_ZEN_ROLE = "tunnel_zen"  # WHY: Only this role expands through CENR hostnames.
_VLAN_MIN = 1  # WHY: IEEE 802.1Q user VLAN identifiers start at 1.
_VLAN_MAX = 4094  # WHY: IEEE 802.1Q user VLAN identifiers end at 4094.
_CRITICAL_AGGRESSIVENESS = "high"  # WHY: Mist UI writes high for a critical custom probe.
_AUTO_AGGRESSIVENESS = "auto"  # WHY: Region-only probes stay unscheduled unless selected per site.
# Priority tiers recognised on READ (schedule/demote decisions). The Mist UI's
# per-probe "Critical" checkbox writes ``"high"`` (verified 2026-07-25 by
# toggling a probe in the UI and dumping the org setting). Older versions of
# this tool wrote ``"critical"`` -- also a real, valid priority tier accepted
# by the API. Both must be treated as priority for read-side decisions so orgs
# carrying the legacy value keep behaving correctly during the transition.
# Writes emit only ``"high"`` (via ``_CRITICAL_AGGRESSIVENESS``) to stay
# byte-identical with UI-authored probes in exported configs and audit dumps.
_PRIORITY_AGGRESSIVENESS: frozenset[str] = frozenset(
    {"critical", "high"}
)  # Preserve the existing behavior during the compliance refactor.

# Region-scoped Samsung ELM activation roles live in the probe source file with
# names like ``samsung_elm_activation_americas``. They are country-specific
# reachability targets, so pushing them at org scope would spray every region's
# endpoints everywhere -- pointless for sites in the wrong region and noisy for
# operators. Instead the org PUT skips them entirely (see ``_build_probe_set``)
# and the site-override flow injects the one matching region based on each
# picked site's ``country_code``.
_SAMSUNG_ELM_ROLE_PREFIX = "samsung_elm_activation_"  # WHY: The prefix identifies regional Samsung ELM roles.
_COUNTRY_CODE_TO_REGION: dict[str, str] = {
    # North America -- pre-1025 baseline.
    "US": "americas",  # United States
    "CA": "americas",  # Canada
    "MX": "americas",  # Mexico
    # South America -- large markets from the pre-1025 baseline.
    "AR": "americas",  # Argentina
    "BR": "americas",  # Brazil
    "CL": "americas",  # Chile
    "CO": "americas",  # Colombia
    "PE": "americas",  # Peru
    "VE": "americas",  # Venezuela
    # South America -- 1025 US2 extension (residual sovereign codes so the
    # continent classifies without falling through to EMEA).
    "BO": "americas",  # Bolivia
    "EC": "americas",  # Ecuador
    "FK": "americas",  # Falkland Islands (Islas Malvinas)
    "GF": "americas",  # French Guiana
    "GY": "americas",  # Guyana
    "PY": "americas",  # Paraguay
    "SR": "americas",  # Suriname
    "UY": "americas",  # Uruguay
    # Central America -- 1025 US2 extension.
    "BZ": "americas",  # Belize
    "CR": "americas",  # Costa Rica
    "GT": "americas",  # Guatemala
    "HN": "americas",  # Honduras
    "NI": "americas",  # Nicaragua
    "PA": "americas",  # Panama
    "SV": "americas",  # El Salvador
    # Caribbean -- 1025 US2 extension (every ISO-listed island so the region
    # never falls through to the EMEA default).
    "AG": "americas",  # Antigua and Barbuda
    "AI": "americas",  # Anguilla
    "AW": "americas",  # Aruba
    "BB": "americas",  # Barbados
    "BL": "americas",  # Saint Barthelemy
    "BM": "americas",  # Bermuda
    "BQ": "americas",  # Bonaire, Sint Eustatius and Saba
    "BS": "americas",  # Bahamas
    "CU": "americas",  # Cuba
    "CW": "americas",  # Curacao
    "DM": "americas",  # Dominica
    "DO": "americas",  # Dominican Republic
    "GD": "americas",  # Grenada
    "GP": "americas",  # Guadeloupe
    "HT": "americas",  # Haiti
    "JM": "americas",  # Jamaica
    "KN": "americas",  # Saint Kitts and Nevis
    "KY": "americas",  # Cayman Islands
    "LC": "americas",  # Saint Lucia
    "MF": "americas",  # Saint Martin (French part)
    "MQ": "americas",  # Martinique
    "MS": "americas",  # Montserrat
    "PR": "americas",  # Puerto Rico
    "SX": "americas",  # Sint Maarten (Dutch part)
    "TC": "americas",  # Turks and Caicos Islands
    "TT": "americas",  # Trinidad and Tobago
    "VC": "americas",  # Saint Vincent and the Grenadines
    "VG": "americas",  # British Virgin Islands
    "VI": "americas",  # United States Virgin Islands
    # China + SARs + Taiwan hit ``.com.cn`` endpoints. EMEA fallback uses
    # ``.com`` so they must be routed to the china role explicitly.
    "CN": "china",  # China (mainland)
    "HK": "china",  # Hong Kong SAR
    "MO": "china",  # Macao SAR
    "TW": "china",  # Taiwan
}
# Anything not listed above falls through to EMEA. EMEA endpoints are the
# broadest surface (Africa, Middle East, Europe, plus every APAC/Oceania code
# we have not explicitly routed to China), so this is the safest default. A
# warning is logged when the fallback fires so operators can spot unmapped
# country codes and extend ``_COUNTRY_CODE_TO_REGION`` if needed.
_DEFAULT_REGION = "emea"  # Preserve the existing behavior during the compliance refactor.


class SyntheticProbeSettingApplier:  # Preserve the existing behavior during the compliance refactor.
    """Build, write, and report one org synthetic probe setting change."""

    @staticmethod
    def build_body(  # Preserve the existing behavior during the compliance refactor.
        setting: dict[str, Any],
        combined_probes: dict[str, dict[str, Any]],
        vlan_ids: list[int],
    ) -> dict[str, Any]:
        """Return the org setting body with the refreshed probe set."""
        logger.info("Building the org synthetic-probe setting body")  # Record the payload build boundary.
        body: dict[str, Any] = json.loads(json.dumps(setting)) if setting else {}  # Deep-copy settings before mutation.
        synthetic = SyntheticProbeSettingApplier._synthetic_section(body)  # Get or create the synthetic_test block.
        existing_tests = SyntheticProbeSettingApplier._existing_tests(synthetic)  # Preserve valid existing tests.
        synthetic["custom_probes"] = combined_probes  # Replace only the managed custom-probes section.
        tests = _merge_zcc_criticals_into_tests(existing_tests, combined_probes, vlan_ids)  # Refresh schedules.
        synthetic["tests"] = tests  # Attach the refreshed schedule rows.
        logger.debug("Built org setting body with probe_count=%s", len(combined_probes))  # Record payload size.
        return body  # Return the PUT body for the caller.

    @staticmethod
    def _synthetic_section(
        body: dict[str, Any],
    ) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
        """Return a mutable synthetic_test section from the org setting body."""
        synthetic = body.get("synthetic_test")  # Reuse the fetched section when it has the expected shape.
        if isinstance(synthetic, dict):  # Preserve sibling keys in a valid synthetic_test block.
            return synthetic  # Return the existing section so caller mutations persist.
        synthetic = {}  # Create the section when Mist returned no object.
        body["synthetic_test"] = synthetic  # Attach the new section to the PUT body.
        return synthetic  # Return the new mutable section.

    @staticmethod
    def _existing_tests(
        synthetic: dict[str, Any],
    ) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
        """Return the existing tests list when Mist supplied one."""
        existing_tests = synthetic.get("tests")  # Read current tests so foreign rows can survive.
        if isinstance(existing_tests, list):  # Preserve only the list shape accepted by the merge helper.
            return existing_tests  # Return the caller-owned list to preserve prior behavior.
        return []  # Use an empty list when the setting lacks a valid tests array.

    @staticmethod
    def write_setting(
        mist_session: Any, org_id: str, body: dict[str, Any]
    ) -> Any:  # Preserve the existing behavior during the compliance refactor.
        """Write one org setting update through the Mist SDK."""
        logger.info("Calling updateOrgSettings for org_id=%s", org_id)  # Record the outbound Mist write.
        response = _mist_setting.updateOrgSettings(mist_session, org_id, body)  # Send the exact updated setting body.
        status = getattr(response, "status_code", None)  # Read the status for safe logging.
        logger.debug("updateOrgSettings returned status=%s", status)  # Record the status.
        return response  # Return the SDK response for status handling.

    @staticmethod
    def report_result(
        response: Any, org_id: str, combined_probes: dict[str, dict[str, Any]]
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print the existing update result text for the operator."""
        status = getattr(response, "status_code", None)  # Read the SDK status safely.
        if status is not None and (status < 200 or status >= 300):  # Preserve the previous non-2xx refusal branch.
            logger.error("updateOrgSettings HTTP %s", status)  # Record the failed Mist write status.
            print(f"  updateOrgSettings failed with HTTP {status}")  # Preserve the operator-visible failure text.
            return  # Return before printing success rows.
        probe_count = len(combined_probes)  # Reuse the count in output and logs.
        print(f"  updateOrgSettings succeeded ({probe_count} probes written)")  # Preserve the success summary text.
        SyntheticProbeSettingApplier._print_probe_names(combined_probes)  # Preserve the sorted per-probe output.
        logger.info("Wrote %d probes via updateOrgSettings", probe_count)  # Record the successful write count.
        logger.debug("Completed updateOrgSettings report for org_id=%s", org_id)  # Record report completion.

    @staticmethod
    def _print_probe_names(
        combined_probes: dict[str, dict[str, Any]],
    ) -> None:  # Preserve the existing behavior during the compliance refactor.
        """Print each written probe name in stable order."""
        for probe_name in sorted(combined_probes):  # Sort names so output stays deterministic.
            print(f"    - {probe_name}")  # Preserve the existing row text.

    @staticmethod
    def append_scheduled_rows(  # Preserve the existing behavior during the compliance refactor.
        surviving: list[dict[str, Any]],
        scheduled_names: list[str],
        vlan_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Append refreshed scheduled probe rows to the surviving tests."""
        template_vlan_ids, template_lan_networks = _derive_test_row_template(surviving)  # Preserve row scoping.
        effective_vlans = template_vlan_ids if template_vlan_ids is not None else list(vlan_ids)  # Keep fallback VLANs.
        for name in scheduled_names:  # Add one Mist-native tests row per scheduled probe.
            new_row: dict[str, Any] = {"probes": [name], "vlan_ids": list(effective_vlans)}  # Preserve row shape.
            if template_lan_networks:  # Carry a LAN network template when a surviving row supplied one.
                new_row["lan_networks"] = list(template_lan_networks)  # Copy LAN network IDs into the new row.
            surviving.append(new_row)  # Append in stable scheduled-name order.
        logger.debug("Appended %d synthetic probe test rows", len(scheduled_names))  # Record emitted row count.
        return surviving  # Return the caller-owned list to preserve behavior.

    @staticmethod
    def observed_target_mode(observed_protocol: str | None) -> str | None:
        """Return the target mode for one observed protocol token."""
        if observed_protocol is None:  # WHY: Missing observations must fall back to catalogue defaults.
            return None  # WHY: The caller handles the fallback branch.
        if observed_protocol in ("HTTPS", "TCP/443"):  # WHY: HTTPS-capable targets keep the existing URL shape.
            return "https"  # WHY: The caller must elide the default 443 port.
        if SyntheticProbeSettingApplier._is_udp_observation(
            observed_protocol
        ):  # WHY: UDP targets need raw reachability.
            return "raw"  # WHY: The caller must preserve the observed port.
        if SyntheticProbeSettingApplier._is_non_https_tcp_observation(
            observed_protocol
        ):  # WHY: Non-443 TCP uses raw reachability.
            return "raw"  # WHY: The caller must preserve the observed port.
        return None  # WHY: Unknown tokens must fall back to catalogue defaults.

    @staticmethod
    def fallback_probe_source(role: dict[str, Any], cenr_source: dict[str, Any]) -> dict[str, Any]:
        """Return the role or CENR fallback probe definition."""
        probe = role.get("probe") or {}  # WHY: Role-specific probe settings take precedence.
        if probe:  # WHY: A role probe must override the CENR default.
            return probe  # WHY: Return the caller-owned mapping to preserve behavior.
        if role.get("role") != _TUNNEL_ZEN_ROLE:  # WHY: Only tunnel ZEN delegates to the CENR default.
            return probe  # WHY: Non-tunnel roles keep the empty probe fallback.
        return cenr_source.get("probe_default") or {}  # WHY: Tunnel ZEN keeps the CENR default path.

    @staticmethod
    def normalized_probe_protocol(probe: dict[str, Any]) -> str:
        """Return a URL-capable probe protocol name."""
        protocol = str(probe.get("protocol") or "https").lower()  # WHY: Missing protocol defaults to HTTPS.
        if protocol == "tcp":  # WHY: Mist synthetic targets use URL schemes, not raw TCP here.
            return "https"  # WHY: Preserve the prior TCP-to-HTTPS fallback.
        if protocol in _SCHEME_DEFAULT_PORT:  # WHY: Known URL schemes keep their configured name.
            return protocol  # WHY: Return the normalized scheme for target construction.
        return "https"  # WHY: Unknown protocols fall back to the safe HTTPS default.

    @staticmethod
    def coerced_probe_port(probe: dict[str, Any], protocol: str) -> int:
        """Return the configured port or the protocol default."""
        port_raw = probe.get("port")  # WHY: The configured port wins when it parses cleanly.
        try:  # WHY: Hand-edited catalogues can hold string ports.
            return (
                int(port_raw) if port_raw is not None else _SCHEME_DEFAULT_PORT[protocol]
            )  # WHY: Preserve port fallback.
        except (TypeError, ValueError):  # WHY: Malformed ports must not stop menu 206.
            return _SCHEME_DEFAULT_PORT[protocol]  # WHY: Preserve the old scheme-default behavior.

    @staticmethod
    def observed_host(entry: Any) -> str | None:
        """Return a host string from one CENR host entry."""
        if isinstance(entry, dict):  # WHY: Version 3 cache entries store the hostname under "host".
            host = entry.get("host")  # WHY: Read the documented host field only.
            return host if isinstance(host, str) else None  # WHY: Ignore malformed host field values.
        if isinstance(entry, str):  # WHY: Version 2 cache entries used bare strings.
            return entry  # WHY: Preserve load-time tolerance for old caches.
        return None  # WHY: Malformed entries do not contribute observations.

    @staticmethod
    def catalogue_host(entry: Any) -> str | None:
        """Return one concrete catalogue host entry."""
        fqdn = entry.get("host") if isinstance(entry, dict) else entry  # WHY: Accept v3 dict and v2 string shapes.
        if not isinstance(fqdn, str):  # WHY: Non-string catalogue entries cannot form Mist targets.
            return None  # WHY: Ignore malformed entries without failing the run.
        if fqdn.startswith("*."):  # WHY: Wildcards are never emitted as concrete probes.
            return None  # WHY: Exclude wildcard-only catalogue rows.
        return fqdn  # WHY: Return the concrete host for observation diffing.

    @staticmethod
    def is_critical_probe_target(critical_role: bool, critical_assigned: bool, critical_target: Any, fqdn: str) -> bool:
        """Return True when this FQDN should spend the role critical slot."""
        if not critical_role:  # WHY: Non-critical roles never spend a critical slot.
            return False  # WHY: Preserve the existing non-critical role behavior.
        if critical_assigned:  # WHY: Each role can assign the critical slot only once.
            return False  # WHY: Preserve the one-critical-per-role rule.
        if critical_target is None:  # WHY: Roles without an explicit target use the first concrete host.
            return True  # WHY: Preserve the first-host fallback.
        return fqdn == critical_target  # WHY: Explicit critical hosts must match exactly.

    @staticmethod
    def probe_body(target: str, role: dict[str, Any], is_critical: bool) -> dict[str, Any]:
        """Return one Mist custom-probe body."""
        probe_body: dict[str, Any] = {  # WHY: Keep the Mist custom-probe body shape centralized.
            "type": _probe_type_for_target(target, role.get("type")),  # WHY: Derive type from the final target shape.
            "target": target,  # WHY: Preserve the target that the dispatch helpers selected.
        }
        probe_body["aggressiveness"] = (
            _CRITICAL_AGGRESSIVENESS if is_critical else _AUTO_AGGRESSIVENESS
        )  # WHY: Preserve scheduling.
        return probe_body  # WHY: Return the body before insertion into the result map.

    @staticmethod
    def is_site_only_role(role_name: Any) -> bool:
        """Return True for Samsung ELM roles that must stay out of org scope."""
        return isinstance(role_name, str) and role_name.startswith(
            _SAMSUNG_ELM_ROLE_PREFIX
        )  # WHY: Regional ELM probes are site scoped.

    @staticmethod
    def city_metadata_or_warn(cenr: dict[str, Any]) -> dict[str, Any] | None:
        """Return city metadata or warn when ZEN scheduling cannot run."""
        city_metadata = cenr.get("city_metadata") or {}  # WHY: ZEN selection requires the enriched city map.
        if isinstance(city_metadata, dict) and city_metadata:  # WHY: Non-empty maps can drive ZEN scheduling.
            return city_metadata  # WHY: Return the original metadata mapping for downstream selectors.
        logger.warning(
            "ZEN scheduling skipped: city_metadata missing from CENR file"
        )  # WHY: Explain the fail-closed path.
        return None  # WHY: The caller skips ZEN scheduling when metadata is absent.

    @staticmethod
    def host_bag(container: dict[str, Any], bag_key: str) -> list[Any]:
        """Return one host bag when it uses the expected list shape."""
        bag = container.get(bag_key) or []  # WHY: Missing bags behave like empty bags.
        return bag if isinstance(bag, list) else []  # WHY: Malformed bags must not stop observation collection.

    @staticmethod
    def catalogue_hosts_for_role(role: dict[str, Any]) -> list[str]:
        """Return concrete catalogue hosts for one role."""
        role_name = role.get("role")  # WHY: Tunnel ZEN gets its hosts from CENR instead of the static catalogue.
        if role_name == _TUNNEL_ZEN_ROLE:  # WHY: Tunnel hosts are already in the CENR observation universe.
            return []  # WHY: Exclude tunnel ZEN from missing-observation warnings.
        entries = role.get("fqdns") or []  # WHY: Missing host lists produce no catalogue hosts.
        hosts = map(
            SyntheticProbeSettingApplier.catalogue_host, entries
        )  # WHY: Normalize each entry shape without a branch.
        return [host for host in hosts if host is not None]  # WHY: Keep only concrete hostnames.

    @staticmethod
    def role_concrete_fqdns(role: dict[str, Any], cenr_source: dict[str, Any]) -> list[str]:
        """Return concrete FQDN strings emitted for one catalogue role."""
        result: list[str] = []  # WHY: Preserve source order for critical-host selection.
        for fqdn in _iter_role_fqdns(role, cenr_source):  # WHY: Expand role-specific and CENR-sourced host lists.
            if isinstance(fqdn, str) and not fqdn.startswith("*."):  # WHY: Only concrete hostnames can form probes.
                result.append(fqdn)  # WHY: Preserve the host for probe-body generation.
        return result  # WHY: Return a concrete list so callers can iterate without type guards.

    @staticmethod
    def buildable_roles(probes_source: dict[str, Any]) -> list[dict[str, Any]]:
        """Return roles that can be emitted at org scope."""
        roles = probes_source.get("roles")  # WHY: Read the optional role bag before validating its shape.
        if not isinstance(roles, list):  # WHY: The shipped catalogue stores roles as a list.
            return []  # WHY: Malformed role containers cannot emit org-scope probes safely.
        result: list[dict[str, Any]] = []  # WHY: Preserve catalogue role order after filtering.
        for role in roles:  # WHY: Walk each supplied role entry once.
            if not isinstance(role, dict):  # WHY: Malformed roles cannot emit probes safely.
                continue  # WHY: Preserve tolerance for hand-edited catalogues.
            role_name = role.get("role")  # WHY: Use the role slug for site-only filtering.
            if SyntheticProbeSettingApplier.is_site_only_role(role_name):  # WHY: Regional ELM roles stay site scoped.
                continue  # WHY: Do not emit site-only roles at org scope.
            result.append(role)  # WHY: Keep this role for org-scope probe generation.
        return result  # WHY: Return only roles that the org builder can process.

    @staticmethod
    def normalized_country_code(site: dict[str, Any]) -> str | None:
        """Return a normalized non-empty country code for one site."""
        raw = site.get("country_code")  # WHY: Mist can omit country_code on incomplete site records.
        if not isinstance(raw, str):  # WHY: Non-string values cannot be classified safely.
            return None  # WHY: Skip malformed records without adding warning noise.
        code = raw.strip().upper()  # WHY: Region maps store ISO codes in uppercase.
        return code or None  # WHY: Blank codes do not have useful operator action.

    @staticmethod
    def merged_probe_aggressiveness(name: str, probe: dict[str, Any], new_probes: dict[str, dict[str, Any]]) -> Any:
        """Return the merged aggressiveness value for one probe."""
        if name in new_probes:  # WHY: Fresh catalogue output is authoritative for current probes.
            authoritative = new_probes[name].get("aggressiveness")  # WHY: Read the value once for fallback handling.
            return (
                authoritative if authoritative is not None else _AUTO_AGGRESSIVENESS
            )  # WHY: Missing values become auto.
        return probe.get("aggressiveness")  # WHY: Dropped catalogue entries keep any existing aggressiveness.

    @staticmethod
    def _is_udp_observation(observed_protocol: str) -> bool:
        """Return True when an observed protocol token names UDP reachability."""
        return observed_protocol == "UDP" or observed_protocol.startswith("UDP/")  # WHY: Both token forms name UDP.

    @staticmethod
    def _is_non_https_tcp_observation(observed_protocol: str) -> bool:
        """Return True when an observed protocol token names non-HTTPS TCP."""
        return (
            observed_protocol.startswith("TCP/") and observed_protocol != "TCP/443"
        )  # WHY: TCP/443 uses HTTPS URL shape.


class SyntheticProbePromptReader:  # Preserve the existing behavior during the compliance refactor.
    """Read menu 206 prompts through the shared EOF-safe input helper."""

    @staticmethod
    def read(prompt: str, context: str) -> str:  # Preserve the existing behavior during the compliance refactor.
        """Return one trimmed operator answer for a named menu 206 prompt."""
        logger.info("Prompting the operator for %s", context)  # Record the prompt boundary for SSH sessions.
        answer = InputUtils.safe_input(prompt, context=context)  # Use the shared EOF-safe prompt helper.
        logger.debug("Completed prompt for %s with answer_present=%s", context, bool(answer))  # Avoid logging values.
        return answer  # Return the trimmed answer so existing prompt behavior stays unchanged.


# Deliberately-unmapped ISO-3166-1 alpha-2 codes. These fall through to
# ``_DEFAULT_REGION`` today by design (they map onto EMEA's ``.com`` endpoint
# surface which is the correct behaviour for Africa, the Middle East, Europe,
# Central/South/Southeast/Northeast Asia, Oceania, and Antarctica -- none of
# which have a dedicated regional Samsung ELM role). Enumerating every
# residual code explicitly (rather than leaving them implicit in the fall-
# through) turns the pairing (``_COUNTRY_CODE_TO_REGION``, this set) into a
# machine-checkable coverage contract: together they must cover every ISO
# alpha-2 code exactly once. See ``iso_coverage_invariant.md`` INV-COVER-1..4
# and the regression suite in ``tests/unit/org/test_country_region_coverage.py``
# which fails CI the moment a code is silently added, removed, or duplicated.
# Membership is a frozenset so downstream helpers cannot mutate the coverage
# invariant at runtime.
_COUNTRY_CODE_INTENTIONAL_GAPS: frozenset[str] = frozenset(
    {
        # Africa (EMEA -- broadest fallback surface today)
        "AO",  # Angola
        "BF",  # Burkina Faso
        "BI",  # Burundi
        "BJ",  # Benin
        "BW",  # Botswana
        "CD",  # DR Congo
        "CF",  # Central African Republic
        "CG",  # Congo
        "CI",  # Cote d'Ivoire
        "CM",  # Cameroon
        "CV",  # Cabo Verde
        "DJ",  # Djibouti
        "DZ",  # Algeria
        "EG",  # Egypt
        "EH",  # Western Sahara
        "ER",  # Eritrea
        "ET",  # Ethiopia
        "GA",  # Gabon
        "GH",  # Ghana
        "GM",  # Gambia
        "GN",  # Guinea
        "GQ",  # Equatorial Guinea
        "GW",  # Guinea-Bissau
        "KE",  # Kenya
        "KM",  # Comoros
        "LR",  # Liberia
        "LS",  # Lesotho
        "LY",  # Libya
        "MA",  # Morocco
        "MG",  # Madagascar
        "ML",  # Mali
        "MR",  # Mauritania
        "MU",  # Mauritius
        "MW",  # Malawi
        "MZ",  # Mozambique
        "NA",  # Namibia
        "NE",  # Niger
        "NG",  # Nigeria
        "RE",  # Reunion
        "RW",  # Rwanda
        "SC",  # Seychelles
        "SD",  # Sudan
        "SH",  # Saint Helena
        "SL",  # Sierra Leone
        "SN",  # Senegal
        "SO",  # Somalia
        "SS",  # South Sudan
        "ST",  # Sao Tome and Principe
        "SZ",  # Eswatini
        "TD",  # Chad
        "TG",  # Togo
        "TN",  # Tunisia
        "TZ",  # Tanzania
        "UG",  # Uganda
        "YT",  # Mayotte
        "ZA",  # South Africa
        "ZM",  # Zambia
        "ZW",  # Zimbabwe
        # Middle East (EMEA -- broadest fallback surface today)
        "AE",  # United Arab Emirates
        "AF",  # Afghanistan
        "BH",  # Bahrain
        "IL",  # Israel
        "IQ",  # Iraq
        "IR",  # Iran
        "JO",  # Jordan
        "KW",  # Kuwait
        "LB",  # Lebanon
        "OM",  # Oman
        "PS",  # Palestine
        "QA",  # Qatar
        "SA",  # Saudi Arabia
        "SY",  # Syria
        "TR",  # Turkey
        "YE",  # Yemen
        # Europe + European overseas / crown dependencies (EMEA)
        "AD",  # Andorra
        "AL",  # Albania
        "AT",  # Austria
        "AX",  # Aland Islands
        "BA",  # Bosnia and Herzegovina
        "BE",  # Belgium
        "BG",  # Bulgaria
        "BV",  # Bouvet Island
        "BY",  # Belarus
        "CH",  # Switzerland
        "CY",  # Cyprus
        "CZ",  # Czechia
        "DE",  # Germany
        "DK",  # Denmark
        "EE",  # Estonia
        "ES",  # Spain
        "FI",  # Finland
        "FO",  # Faroe Islands
        "FR",  # France
        "GB",  # United Kingdom
        "GE",  # Georgia
        "GG",  # Guernsey
        "GI",  # Gibraltar
        "GL",  # Greenland
        "GR",  # Greece
        "GS",  # South Georgia
        "HM",  # Heard and McDonald Islands
        "HR",  # Croatia
        "HU",  # Hungary
        "IE",  # Ireland
        "IM",  # Isle of Man
        "IS",  # Iceland
        "IT",  # Italy
        "JE",  # Jersey
        "LI",  # Liechtenstein
        "LT",  # Lithuania
        "LU",  # Luxembourg
        "LV",  # Latvia
        "MC",  # Monaco
        "MD",  # Moldova
        "ME",  # Montenegro
        "MK",  # North Macedonia
        "MT",  # Malta
        "NL",  # Netherlands
        "NO",  # Norway
        "PL",  # Poland
        "PM",  # Saint Pierre and Miquelon
        "PT",  # Portugal
        "RO",  # Romania
        "RS",  # Serbia
        "RU",  # Russia
        "SE",  # Sweden
        "SI",  # Slovenia
        "SJ",  # Svalbard and Jan Mayen
        "SK",  # Slovakia
        "SM",  # San Marino
        "UA",  # Ukraine
        "VA",  # Vatican City
        # Central Asia (EMEA today. No China routing)
        "AM",  # Armenia
        "AZ",  # Azerbaijan
        "KG",  # Kyrgyzstan
        "KZ",  # Kazakhstan
        "TJ",  # Tajikistan
        "TM",  # Turkmenistan
        "UZ",  # Uzbekistan
        # South Asia (EMEA today)
        "BD",  # Bangladesh
        "BT",  # Bhutan
        "IN",  # India
        "LK",  # Sri Lanka
        "MV",  # Maldives
        "NP",  # Nepal
        "PK",  # Pakistan
        # Southeast Asia (EMEA today. Not classified as China)
        "BN",  # Brunei
        "ID",  # Indonesia
        "KH",  # Cambodia
        "LA",  # Laos
        "MM",  # Myanmar
        "MY",  # Malaysia
        "PH",  # Philippines
        "SG",  # Singapore
        "TH",  # Thailand
        "TL",  # Timor-Leste
        "VN",  # Vietnam
        # Northeast Asia (EMEA today. Not classified as China)
        "JP",  # Japan
        "KP",  # North Korea
        "KR",  # South Korea
        "MN",  # Mongolia
        # Oceania + Pacific outposts (EMEA today)
        "AS",  # American Samoa
        "AU",  # Australia
        "CC",  # Cocos (Keeling) Islands
        "CK",  # Cook Islands
        "CX",  # Christmas Island
        "FJ",  # Fiji
        "FM",  # Micronesia
        "GU",  # Guam
        "IO",  # British Indian Ocean Territory
        "KI",  # Kiribati
        "MH",  # Marshall Islands
        "MP",  # Northern Mariana Islands
        "NC",  # New Caledonia
        "NF",  # Norfolk Island
        "NR",  # Nauru
        "NU",  # Niue
        "NZ",  # New Zealand
        "PF",  # French Polynesia
        "PG",  # Papua New Guinea
        "PN",  # Pitcairn
        "PW",  # Palau
        "SB",  # Solomon Islands
        "TF",  # French Southern Territories
        "TK",  # Tokelau
        "TO",  # Tonga
        "TV",  # Tuvalu
        "UM",  # US Minor Outlying Islands
        "VU",  # Vanuatu
        "WF",  # Wallis and Futuna
        "WS",  # Samoa
        # Antarctica -- no plausible Mist site
        "AQ",  # Antarctica
    }
)

# Default URL scheme / port pairs. Mist's ``target`` field is a URL, so a
# per-role ``probe.protocol`` chosen from the curated JSON maps directly to a
# URL scheme -- with two caveats encoded in ``_probe_target``:
#   1. ``tcp`` is not a valid URL scheme for Mist synthetic tests. Roles that
#      the reachability probing showed only respond to raw TCP/443 (for example
#      ``service_discovery_enrollment_login``) still exercise the same TCP
#      handshake path when probed as HTTPS, so we transparently upgrade to
#      ``https`` for URL construction.
#   2. Ports matching the scheme default (80 for http, 443 for https) are
#      elided from the URL to match Mist's own ``mini-*`` shape (which never
#      writes an explicit ``:443`` on HTTPS targets).
_SCHEME_DEFAULT_PORT: dict[str, int] = {
    "http": 80,
    "https": 443,
}  # Preserve the existing behavior during the compliance refactor.

# UDP/500 (IKE_SA_INIT) is the ZEN VPN service plane. When a VPN-bag host has
# no live UDP observation yet, defaulting to bare ``host:500`` is still
# correct -- the alternative (``https://vpn-host``) was the pre-1023 bug that
# emitted 400+ never-succeed HTTPS probes against IPsec/IKE endpoints. See
# probe_target_url_builder.md SC-001 and the 2026-07-26 regression that
# resurfaced after the schema-v3 cache promotion left ``observed_protocol``
# unpopulated on every VPN host.
_VPN_DEFAULT_PORT = 500  # Preserve the existing behavior during the compliance refactor.


def _fqdn_in_vpn_bag(bag: Any, fqdn: str) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when ``fqdn`` appears as a host entry inside ``bag``."""
    if not isinstance(bag, list):  # Non-list bags cannot hold host entries.
        return False  # Preserve the existing tolerant false result.
    return any(_vpn_bag_entry_matches(entry, fqdn) for entry in bag)  # Stop at the first matching host.


def _vpn_bag_entry_matches(
    entry: Any, fqdn: str
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when one VPN bag entry names ``fqdn``."""
    host = entry.get("host") if isinstance(entry, dict) else entry  # Support v3 dicts and legacy strings.
    return isinstance(host, str) and host == fqdn  # Match only exact string hostnames.


def _is_vpn_host(
    fqdn: str, cenr_source: dict[str, Any]
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True iff ``fqdn`` appears in any ``vpn_hostnames`` bag."""
    top_level_match = _fqdn_in_vpn_bag(cenr_source.get("vpn_hostnames"), fqdn)  # Check the common bag first.
    city_slots = _cenr_city_slots(cenr_source)  # Normalize city slots before the membership scan.
    city_match = any(_fqdn_in_vpn_bag(slot.get("vpn_hostnames"), fqdn) for slot in city_slots)  # Check cities.
    return top_level_match or city_match  # Preserve top-level or city membership semantics.


def _cenr_city_slots(
    cenr_source: dict[str, Any],
) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Return valid city dictionaries from a CENR document."""
    by_city = cenr_source.get("by_city")  # Read the optional by-city container.
    if not isinstance(by_city, dict):  # Treat missing or malformed containers as no city entries.
        return []  # Preserve the prior false result for malformed by_city values.
    return [slot for slot in by_city.values() if isinstance(slot, dict)]  # Keep only city dictionaries.


def _probe_type_for_target(
    target: str, _role_type: str | None = None
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Classify a probe body ``type`` from the emitted target string.

    Why:
        Mist synthetic tests use ``type: "application"`` for URL-based
        checks (HTTP/HTTPS GETs against the ``target`` URL) and
        ``type: "reachability"`` for raw ICMP checks (bare hostname).
        Feature 1024 tightened the classifier to be **shape-based**: the
        target's own shape is the source of truth for the probe type,
        not any upstream ``role_type`` hint. This closes an
        overwrite window where a role tagged ``type: application``
        could re-attach the ``application`` label to a bare-hostname
        VPN target and reintroduce the pre-1024 fake-L4 failure mode
        (INV-2, INV-3). ``role_type`` is retained in the signature for
        backwards compatibility with all three callsites. Its value is
        NOT consulted for the decision.

    Args:
        target: The fully-built probe target string as returned by
            ``_probe_target``. HTTP/HTTPS URLs start with the scheme;
            bare hostnames carry no scheme and no ``":port"`` suffix;
            L4 targets appear as ``host:port`` (no scheme).
        role_type: Legacy hint from role metadata. Ignored — kept only
            so existing callers compile. Removal is a follow-up cleanup.

    Returns:
        ``"application"`` when *target* starts with ``http://`` /
        ``https://`` OR contains a ``":"`` after the last ``"."``
        (a bare ``host:port`` shape). ``"reachability"`` otherwise
        (bare hostname — the post-1024 VPN emission shape).
    """
    # Scheme detection: case-sensitive prefix match. Targets emitted by
    # this codebase are always lowercase. No normalisation required.
    if target.startswith(("http://", "https://")):  # Preserve the existing behavior during the compliance refactor.
        decision = "application"  # Preserve the existing behavior during the compliance refactor.
    else:
        # Port detection: look for ":" AFTER the last "." — a bare host
        # has no ":", a host:port has exactly one ":" after the last dot.
        # This avoids false positives on hypothetical IPv6-literal targets
        # (unsupported by Mist Marvis Minis today. Revisit if support arrives).
        last_dot = target.rfind(".")  # Preserve the existing behavior during the compliance refactor.
        if (
            last_dot != -1 and ":" in target[last_dot:]
        ):  # Preserve the existing behavior during the compliance refactor.
            decision = "application"  # Preserve the existing behavior during the compliance refactor.
        else:
            # Bare hostname — the post-1024 VPN reachability shape.
            decision = "reachability"  # Preserve the existing behavior during the compliance refactor.
    # Debug trace only per contract §Logging. The emitting callsite
    # handles higher-severity logging per Principle VII. Logger is
    # constructed here (not module-scoped) to match the local-scope
    # pattern used by peers like ``_probe_target``.
    logging.getLogger(__name__).debug(
        "probe_type: target=%s -> %s", target, decision
    )  # Preserve the existing behavior during the compliance refactor.
    return decision  # Preserve the existing behavior during the compliance refactor.


def _find_host_in_bags(
    container: dict[str, Any], fqdn: str
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Scan CENR host bags on ``container`` for ``fqdn``."""
    for bag in _host_bags(container):  # Preserve proxy-before-VPN bag search order.
        match = _find_host_in_bag(bag, fqdn)  # Search one normalized list.
        if match is not None:  # Return the first matching v3 host object.
            return match  # Preserve the prior first-match result.
    return None  # Preserve the prior miss result.


def _host_bags(
    container: dict[str, Any],
) -> list[list[Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Return valid host bags from a CENR container."""
    bags: list[list[Any]] = []  # Collect valid bags in prior search order.
    for bag_key in ("proxy_hostnames", "vpn_hostnames"):  # Preserve the original bag order.
        bag = container.get(bag_key) or []  # Treat missing bags as empty.
        if isinstance(bag, list):  # Ignore malformed bags exactly as before.
            bags.append(bag)  # Add the valid bag to the search list.
    return bags  # Return normalized bags to the caller.


def _find_host_in_bag(
    bag: list[Any], fqdn: str
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return the first v3 host entry in one CENR bag."""
    for entry in bag:  # Preserve the existing in-bag order.
        if isinstance(entry, dict) and entry.get("host") == fqdn:  # Legacy strings cannot carry observations.
            return entry  # Return the matching v3 observation object.
    return None  # Return None when no v3 entry matches.


def _lookup_v3_observation(
    fqdn: str, cenr_source: dict[str, Any]
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Locate the v3 host-entry for ``fqdn`` in every CENR bag."""
    hit = _find_host_in_bags(cenr_source, fqdn)  # Search top-level bags first for the common case.
    if hit is not None:  # Preserve the top-level-first result order.
        return hit  # Return the matching top-level observation.
    return _lookup_v3_city_observation(fqdn, cenr_source)  # Search city bags only after top-level miss.


def _lookup_v3_city_observation(
    fqdn: str, cenr_source: dict[str, Any]
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Locate a v3 host-entry for ``fqdn`` under CENR city slots."""
    for city_slot in _cenr_city_slots(cenr_source):  # Search only valid city dictionaries.
        hit = _find_host_in_bags(city_slot, fqdn)  # Search the city proxy and VPN bags.
        if hit is not None:  # Preserve the first city match.
            return hit  # Return the matching city observation.
    return None  # Preserve the prior miss result.


def _extract_observed_protocol_port(  # Preserve the existing behavior during the compliance refactor.
    entry: Any,
) -> tuple[str | None, int | None]:
    """Pull ``observed_protocol`` and ``observed_port`` from a CENR entry.

    Why:
        Extracted from :func:`_probe_target` so its dispatch body stays under
        the Radon CC gate. The type guards mirror the schema: string protocol
        and integer port. Anything else collapses to ``None`` so the caller's
        Branch 3 fallback triggers.

    Args:
        entry: A per-host observation dict from the v3 CENR document, or
            ``None`` / any non-dict when the host is absent.

    Returns:
        ``(observed_protocol, observed_port)``. Either or both fields may be
        ``None``.
    """
    observed_protocol: str | None = None  # Preserve the existing behavior during the compliance refactor.
    observed_port: int | None = None  # Preserve the existing behavior during the compliance refactor.
    if isinstance(entry, dict):  # Preserve the existing behavior during the compliance refactor.
        raw_protocol = entry.get("observed_protocol")  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(raw_protocol, str) and raw_protocol
        ):  # Preserve the existing behavior during the compliance refactor.
            observed_protocol = raw_protocol  # Preserve the existing behavior during the compliance refactor.
        raw_port = entry.get("observed_port")  # Preserve the existing behavior during the compliance refactor.
        if isinstance(raw_port, int):  # Preserve the existing behavior during the compliance refactor.
            observed_port = raw_port  # Preserve the existing behavior during the compliance refactor.
    return observed_protocol, observed_port  # Preserve the existing behavior during the compliance refactor.


def _dispatch_observed_target(  # Preserve the existing behavior during the compliance refactor.
    fqdn: str,
    observed_protocol: str | None,
    observed_port: int | None,
) -> str | None:
    """Apply the non-VPN observation-first Branch 1 / Branch 2 dispatch.

    Why:
        Split out of :func:`_probe_target` so the contract-heavy branch
        selection is one focused function. Returning ``None`` signals that
        the caller must fall through to the Branch 3 role/CENR fallback (no
        recognised observation or missing port).

    Args:
        fqdn: Hostname being rendered.
        observed_protocol: Value from ``observed_protocol`` in the CENR
            observation, or ``None`` when absent.
        observed_port: Value from ``observed_port`` in the CENR observation,
            or ``None`` when absent.

    Returns:
        The composed target string per Branch 1 or Branch 2, or ``None`` when
        the observation is missing / unrecognised (caller runs Branch 3).
    """
    logger = logging.getLogger(__name__)  # Preserve the existing behavior during the compliance refactor.
    if observed_protocol is None:  # Preserve the existing behavior during the compliance refactor.
        return None  # Preserve the existing behavior during the compliance refactor.
    # Branch 2: HTTPS or TCP/443 collapse to the same URL shape so the
    # emitted target matches Mist-authored mini-* rows byte-for-byte
    # (FR-009: any per-run diff of the same host across runs must be
    # empty when the observation is stable).
    mode = SyntheticProbeSettingApplier.observed_target_mode(
        observed_protocol
    )  # WHY: Centralize protocol classification.
    if mode == "https":  # WHY: HTTPS observations keep the URL target shape.
        target = f"https://{fqdn}"  # Preserve the existing behavior during the compliance refactor.
        logger.debug(
            "probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol
        )  # Preserve the existing behavior during the compliance refactor.
        return target  # Preserve the existing behavior during the compliance refactor.
    # Branch 1: UDP family (bare "UDP" or "UDP/<port>") OR non-443 TCP.
    # The port MUST come from observed_port -- observed_protocol may
    # carry no port suffix at all (bare "UDP" token per contract Test
    # Boundaries).
    if mode == "raw" and observed_port is not None:  # WHY: Raw observations require an explicit port.
        # Bare host:port form. NO scheme so Mist runs a raw probe
        # rather than trying TLS on a UDP/IKE endpoint.
        target = f"{fqdn}:{observed_port}"  # Preserve the existing behavior during the compliance refactor.
        logger.debug(
            "probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol
        )  # Preserve the existing behavior during the compliance refactor.
        return target  # Preserve the existing behavior during the compliance refactor.
    return None  # Preserve the existing behavior during the compliance refactor.


def _resolve_fallback_probe(  # Preserve the existing behavior during the compliance refactor.
    role: dict[str, Any],
    cenr_source: dict[str, Any],
) -> tuple[str, int]:
    """Resolve the Branch 3 fallback ``(protocol, port)`` from role + CENR defaults.

    Why:
        Split out of :func:`_build_fallback_target` so the protocol
        normalisation and port coercion do not push the parent above the
        Radon CC gate. ``tunnel_zen`` still delegates to
        ``cenr_source["probe_default"]``. Unknown protocols still coerce to
        ``https``. Non-integer port values still fall back to the scheme
        default.

    Args:
        role: Role dict; ``role["probe"]`` may carry role-specific overrides.
        cenr_source: Loaded v3 CENR document; ``probe_default`` supplies the
            tunnel_zen delegation only.

    Returns:
        ``(protocol, port)`` where ``protocol`` is one of the keys in
        ``_SCHEME_DEFAULT_PORT`` and ``port`` is an integer.
    """
    probe = SyntheticProbeSettingApplier.fallback_probe_source(
        role, cenr_source
    )  # WHY: Resolve role and CENR fallback rules once.
    protocol = SyntheticProbeSettingApplier.normalized_probe_protocol(
        probe
    )  # WHY: Convert catalogue protocol values to target schemes.
    port = SyntheticProbeSettingApplier.coerced_probe_port(
        probe, protocol
    )  # WHY: Preserve configured ports with safe defaults.
    return protocol, port  # Preserve the existing behavior during the compliance refactor.


def _build_fallback_target(  # Preserve the existing behavior during the compliance refactor.
    fqdn: str,
    role: dict[str, Any],
    cenr_source: dict[str, Any],
    observed_protocol: str | None,
) -> str:
    """Compose the Branch 3 fallback target from the role or CENR probe defaults.

    Why:
        Extracted from :func:`_probe_target` so the fallback logic is
        testable in isolation. The VPN pre-check and Branches 1/2 already
        handled everything else. This only fires for non-VPN hosts with
        missing / unrecognised observations.

    Args:
        fqdn: Hostname to render.
        role: Role dict passed through to :func:`_resolve_fallback_probe`.
        cenr_source: Loaded v3 CENR document.
        observed_protocol: Original observation value (may be ``None``). Used
            only in the debug log line.

    Returns:
        Fallback target string, ``"<scheme>://<fqdn>"`` when the port matches
        the scheme default (INV-1 elision) or ``"<scheme>://<fqdn>:<port>"``
        otherwise.
    """
    logger = logging.getLogger(__name__)  # Preserve the existing behavior during the compliance refactor.
    protocol, port = _resolve_fallback_probe(
        role, cenr_source
    )  # Preserve the existing behavior during the compliance refactor.
    if port == _SCHEME_DEFAULT_PORT[protocol]:  # Preserve the existing behavior during the compliance refactor.
        # Default-port elision matches Branch 2's convention so both branches
        # emit identical strings for the common case (INV-1: byte-stable
        # output when the same host+protocol combination reoccurs).
        target = f"{protocol}://{fqdn}"  # Preserve the existing behavior during the compliance refactor.
    else:
        target = f"{protocol}://{fqdn}:{port}"  # Preserve the existing behavior during the compliance refactor.
    # NOTE(1025-US1): warning moved to load-time _emit_load_time_cenr_warning to avoid N*M duplication
    logger.debug(
        "probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol
    )  # Preserve the existing behavior during the compliance refactor.
    return target  # Preserve the existing behavior during the compliance refactor.


def _probe_target(
    fqdn: str, role: dict[str, Any], cenr_source: dict[str, Any]
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Compose the Mist ``target`` string for one FQDN using the observation-first dispatch.

    Why:
        Contract ``probe_target_url_builder.md`` (feature 1023) requires
        three-branch dispatch on the v3 per-host observation for **non-VPN**
        hosts. Contract ``vpn_probe_target_shape.md`` (feature 1024) requires
        the VPN pre-check to run **before** the non-VPN dispatch: a bag
        member always emits as a bare hostname (ICMP reachability), even
        when the host also has a TCP/443 observation (bag wins per
        Ordering Contract).

        Non-VPN dispatch (unchanged from 1023):

        - Branch 1 (UDP-family or non-HTTP TCP): return bare
          ``host:port`` so Mist runs a raw reachability probe (SC-001
          eliminates the ``https://*-vpn.*`` regression).
        - Branch 2 (HTTPS or TCP/443): return ``https://host`` with the
          default port elided (INV-1, FR-009 keep the shipped rows
          byte-identical to previous versions).
        - Branch 3 (no observation, absent key, or unrecognised token):
          fall back to the catalogue default and emit exactly ONE
          ``logger.warning`` so operators notice the cache miss.

        VPN pre-check (new in 1024): if ``_is_vpn_host`` classifies the
        FQDN, return bare ``fqdn`` immediately. Pre-1024 this branch
        returned ``f"{fqdn}:500"`` — the fake-L4 shape that Mist could
        not actually IKE-negotiate. INV-3 forbids any VPN row from
        carrying a scheme or a ``:port`` suffix.

        The function is pure — it never mutates ``cenr_source`` (contract
        Non-Goals) and is deterministic on repeat calls.

    Args:
        fqdn: The hostname to render into a probe target string. Callers
            strip wildcards before invoking this helper.
        role: The role dict from the probe source file. Retained for
            signature parity with previous versions. Branch 3's fallback
            still respects ``role["probe"]`` when present so
            role-specific overrides in the ZCC catalogue continue to
            work.
        cenr_source: Loaded CENR document (v3-shaped). The v2->v3 loader
            adapter guarantees per-host observation objects.

    Returns:
        A non-empty target string. For VPN-classified FQDNs: bare
        ``fqdn`` (no scheme, no port). Otherwise: ``"host:port"``
        (Branch 1) or ``"https://host"`` (Branch 2, default 443 elided)
        or the catalogue default (Branch 3).
    """
    logger = logging.getLogger(__name__)  # module-scoped logger. Matches _warn spec in contract

    # --- VPN pre-check (feature 1024) ---------------------------------------
    # MUST run before the non-VPN 3-branch dispatch so that a host present
    # in a ``vpn_hostnames`` bag AND also observed on TCP/443 (Zscaler admin
    # console) is emitted as a VPN reachability probe. Bag membership wins
    # per contract vpn_probe_target_shape.md §Ordering Contract. Pre-1024
    # this branch returned ``f"{fqdn}:500"``. That fake-L4 shape produced
    # 100% guaranteed-fail probes because Mist cannot speak IKEv2.
    if _is_vpn_host(fqdn, cenr_source):  # Preserve the existing behavior during the compliance refactor.
        logger.info(
            "probe_target(vpn): %s -> bare (reachability)", fqdn
        )  # Preserve the existing behavior during the compliance refactor.
        return fqdn  # Preserve the existing behavior during the compliance refactor.

    entry = _lookup_v3_observation(fqdn, cenr_source)  # Preserve the existing behavior during the compliance refactor.
    observed_protocol, observed_port = _extract_observed_protocol_port(
        entry
    )  # Preserve the existing behavior during the compliance refactor.

    # --- Dispatch on the observed_protocol prefix per contract ---------------
    dispatched = _dispatch_observed_target(
        fqdn, observed_protocol, observed_port
    )  # Preserve the existing behavior during the compliance refactor.
    if dispatched is not None:  # Preserve the existing behavior during the compliance refactor.
        return dispatched  # Preserve the existing behavior during the compliance refactor.

    # Branch 3: no observation OR unrecognised token. Compute the fallback
    # from the role's ``probe`` block (if any) or the CENR probe_default,
    # then log exactly one WARNING so operators spot the cache miss. The
    # VPN pre-check above has already handled bag members, so this branch
    # only fires for non-VPN hosts with missing observations.
    return _build_fallback_target(
        fqdn, role, cenr_source, observed_protocol
    )  # Preserve the existing behavior during the compliance refactor.


def manage_org_synthetic_probes(
    mist_session: Any, org_id: str
) -> None:  # Preserve the existing behavior during the compliance refactor.
    """Interactive entry point for menu 206.

    Why:
        Single public API surface for the feature. The menu dispatch table
        calls this exact callable. Keeping it thin and delegating to the
        ``_``-prefixed helpers below preserves testability -- each helper
        can be exercised directly without stubbing the whole flow.

    Args:
        mist_session: Authenticated ``mistapi`` session object used for
            both the ``getOrgSettings`` read and the ``updateOrgSettings``
            write.
        org_id: Mist organisation UUID whose ``synthetic_test.custom_probes``
            block is being managed.

    Returns:
        None. Side effects (API PUT + stdout prints) are the observable
        outcome.

    Raises:
        FileNotFoundError: If either curated JSON file is missing (bubbled
            from ``_load_probe_sources``).
        ValueError: If either curated JSON file is malformed.
    """
    logger.info(
        "Menu 206: starting org Zscaler synthetic-probe manager"
    )  # Preserve the existing behavior during the compliance refactor.
    logger.debug(
        "ENTRY: manage_org_synthetic_probes(org_id=%s)", org_id
    )  # Preserve the existing behavior during the compliance refactor.

    sources = _load_probe_sources(_DEFAULT_DATA_DIR)  # Preserve the existing behavior during the compliance refactor.
    # NOTE(1025-US1): dedup state for the load-time CENR WARNING lives here so
    # its lifetime is bounded by the invocation (data-model.md §3 INV-D1;
    # FR-012 requires re-emission across back-to-back operator runs).
    warned_cenr_hosts: set[str] = set()  # mutable dedup set, empty per run
    logger.info(  # Constitution VII: BEFORE the load-time diff
        "computing load-time CENR missing-host set for org_id=%s",
        org_id,
    )
    _emit_load_time_cenr_warning(  # single call site per invocation
        _compute_missing_cenr_hosts(  # inner: set difference over frozen universes
            _collect_catalogue_hosts(sources[0]),  # probes side
            _collect_cenr_observed_hosts(sources[1]),  # observations side
        ),
        warned_cenr_hosts,  # dedup state -- mutated in place
    )
    logger.debug(  # Constitution VII: AFTER the load-time emission
        "load-time CENR check complete; warned_cenr_hosts=%s",
        len(warned_cenr_hosts),
    )
    # NOTE(1025-US2): companion dedup state for the load-time
    # country_code warning lives here so its lifetime is bounded by the invocation
    # (data-model.md §3 INV-D1. FR-012 requires re-emission across
    # back-to-back operator runs). Emission itself is delegated to
    # ``_prompt_and_apply_site_overrides`` because that is where the site
    # list is materialised via ``_list_org_sites`` -- the site list is
    # gated behind the operator's site-override opt-in so it is not fetched
    # unless needed. Threading the empty set from here keeps the set
    # lifetime pinned to this invocation as required by FR-012.
    warned_unmapped_codes: set[str] = set()  # mutable dedup set, empty per run
    vlan_ids = _prompt_vlan_list()  # Preserve the existing behavior during the compliance refactor.
    setting = _fetch_setting(mist_session, org_id)  # Preserve the existing behavior during the compliance refactor.
    existing_probes = _detect_existing(setting)  # Preserve the existing behavior during the compliance refactor.
    tool_authored, foreign = _partition_tool_authored(
        existing_probes
    )  # Preserve the existing behavior during the compliance refactor.

    new_probes = _build_probe_set(sources, vlan_ids)  # Preserve the existing behavior during the compliance refactor.

    if tool_authored:  # Preserve the existing behavior during the compliance refactor.
        mode = _prompt_mode(tool_authored)  # Preserve the existing behavior during the compliance refactor.
        if mode == "merge":  # Preserve the existing behavior during the compliance refactor.
            merged_tool = _merge_probes(
                tool_authored, new_probes, vlan_ids
            )  # Preserve the existing behavior during the compliance refactor.
            if merged_tool == tool_authored:  # Preserve the existing behavior during the compliance refactor.
                # Merge is a no-op only if VLANs, aggressiveness, and every
                # other synced field are already aligned. If a probe lost
                # critical status upstream we still need to write.
                print(
                    "  No changes required -- newly-entered VLANs already covered."
                )  # Preserve the existing behavior during the compliance refactor.
                logger.info(
                    "Merge no-op: entered VLANs already covered by all probes"
                )  # Preserve the existing behavior during the compliance refactor.
                return  # Preserve the existing behavior during the compliance refactor.
            resulting_tool = merged_tool  # Preserve the existing behavior during the compliance refactor.
        else:
            resulting_tool = _swap_probes(new_probes)  # Preserve the existing behavior during the compliance refactor.
    else:
        resulting_tool = new_probes  # Preserve the existing behavior during the compliance refactor.

    demoted_foreign = _demote_stale_critical(foreign)  # Preserve the existing behavior during the compliance refactor.
    summary = _summarise(
        resulting_tool, tool_authored, demoted_foreign, foreign
    )  # Preserve the existing behavior during the compliance refactor.
    if not _prompt_confirm(summary):  # Preserve the existing behavior during the compliance refactor.
        print(
            "  Operation cancelled -- no changes were made."
        )  # Preserve the existing behavior during the compliance refactor.
        logger.info(
            "Operator declined final confirmation; no PUT issued"
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.

    # Foreign demotions are merged with the tool-authored set so demoted
    # entries survive the PUT (strict preservation would keep them at their
    # prior priority tier and re-blow the 5-critical cap).
    combined = {**demoted_foreign, **resulting_tool}  # Preserve the existing behavior during the compliance refactor.
    _apply(
        mist_session, org_id, setting, combined, vlan_ids
    )  # Preserve the existing behavior during the compliance refactor.

    # Post-PUT site-override flow: give the operator a chance to push the
    # same probe set into one or more site-level settings so specific
    # sites can override the org-wide config.
    _prompt_and_apply_site_overrides(
        mist_session,
        org_id,
        resulting_tool,
        sources,
        warned_unmapped_codes,  # threaded from load-time scope so lifetime is bounded by this invocation
    )

    logger.debug(
        "EXIT: manage_org_synthetic_probes - success"
    )  # Preserve the existing behavior during the compliance refactor.


def _load_probe_sources(
    data_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Load the two curated Zscaler JSON files from ``data_dir``.

    Why:
        Centralising the file reads gives a single fail-closed choke point
        (edge case: files missing or malformed) and lets tests point the
        module at a fixture directory.

    Args:
        data_dir: Directory containing both curated files.

    Returns:
        A tuple ``(probes, cenr)`` -- the parsed contents of the client
        connector probe file and the CENR hostnames file, respectively.

    Raises:
        FileNotFoundError: If either source file is missing.
        ValueError: If either source file contains invalid JSON.
    """
    probes_path = data_dir / _PROBE_SOURCE_FILE  # Preserve the existing behavior during the compliance refactor.
    cenr_path = data_dir / _CENR_SOURCE_FILE  # Preserve the existing behavior during the compliance refactor.
    for path in (probes_path, cenr_path):  # Preserve the existing behavior during the compliance refactor.
        if not path.is_file():  # Preserve the existing behavior during the compliance refactor.
            raise FileNotFoundError(
                f"Required Zscaler source file is missing: {path}"
            )  # Preserve the existing behavior during the compliance refactor.
    try:
        probes = json.loads(
            probes_path.read_text(encoding="utf-8")
        )  # Preserve the existing behavior during the compliance refactor.
    except json.JSONDecodeError as err:  # Preserve the existing behavior during the compliance refactor.
        raise ValueError(
            f"Malformed JSON in {probes_path}: {err}"
        ) from err  # Preserve the existing behavior during the compliance refactor.
    try:
        cenr = json.loads(
            cenr_path.read_text(encoding="utf-8")
        )  # Preserve the existing behavior during the compliance refactor.
    except json.JSONDecodeError as err:  # Preserve the existing behavior during the compliance refactor.
        raise ValueError(
            f"Malformed JSON in {cenr_path}: {err}"
        ) from err  # Preserve the existing behavior during the compliance refactor.
    # Promote both caches to v3 shape at the earliest possible moment so
    # every downstream reader (URL builder, probe fanout, telemetry) works off
    # dict host entries rather than a mix of flat strings and dicts. Both
    # calls are idempotent for v3+ documents.
    probes = promote_cache_document(probes, kind="zcc")  # legacy ZCC roles bag
    cenr = promote_cache_document(cenr, kind="cenr")  # legacy CENR proxy/vpn bags
    cenr = ensure_fresh(cenr_path, cenr)  # Preserve the existing behavior during the compliance refactor.
    return probes, cenr  # Preserve the existing behavior during the compliance refactor.


def _add_observed_hosts_from_container(  # Preserve the existing behavior during the compliance refactor.
    container: dict[str, Any],
    observed: set[str],
) -> None:
    """Add every host string in ``container``'s proxy/vpn bags to ``observed``.

    Why:
        Extracted from ``_collect_cenr_observed_hosts`` so the top-level
        walk and the by_city walk share one predicate (matches the pattern
        used by ``_find_host_in_bags``). Keeps the caller below Radon
        CC=10.

    Args:
        container: v3-shaped node with ``proxy_hostnames`` / ``vpn_hostnames``
            bags (top-level document or per-city slot).
        observed: Set to add hosts into (mutated in place).
    """
    for bag_key in (
        "proxy_hostnames",
        "vpn_hostnames",
    ):  # Preserve the existing behavior during the compliance refactor.
        bag = SyntheticProbeSettingApplier.host_bag(
            container, bag_key
        )  # WHY: Keep malformed-bag handling in one helper.
        for entry in bag:  # Preserve the existing behavior during the compliance refactor.
            host = SyntheticProbeSettingApplier.observed_host(
                entry
            )  # WHY: Keep v2 and v3 host extraction in one place.
            if host is not None:  # WHY: Malformed entries do not contribute an observation.
                observed.add(host)  # WHY: Add only valid host strings to the observed universe.


def _collect_cenr_observed_hosts(
    cenr_source: dict[str, Any],
) -> frozenset[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return every FQDN that has a CENR observation record.

    Why:
        T011 needs the "known observations" side of the catalogue-minus-observations
        set difference. Rather than teaching ``_compute_missing_cenr_hosts`` about
        the four bag locations (``proxy_hostnames``, ``vpn_hostnames``, and each
        ``by_city[*]`` slot's paired bags), we walk them once here and return a
        frozen set. This mirrors ``_lookup_v3_observation``'s bag traversal so
        the two functions agree on which bags are authoritative.

    Args:
        cenr_source: Loaded CENR document, post v2->v3 loader adapter.

    Returns:
        Frozen set of every host string discovered across all CENR bags.
        Non-dict / non-string / missing-``host`` entries are silently skipped
        (defensive against mid-migration flat strings that slipped past the
        loader adapter).
    """
    observed: set[str] = set()  # accumulator. Frozen at return time for immutability
    _add_observed_hosts_from_container(
        cenr_source, observed
    )  # Preserve the existing behavior during the compliance refactor.
    # by_city bags carry the same shape per cenr_cache_schema_v3.md.
    by_city = cenr_source.get("by_city")  # Preserve the existing behavior during the compliance refactor.
    if isinstance(by_city, dict):  # Preserve the existing behavior during the compliance refactor.
        for city_slot in by_city.values():  # Preserve the existing behavior during the compliance refactor.
            if not isinstance(city_slot, dict):  # Preserve the existing behavior during the compliance refactor.
                continue  # Preserve the existing behavior during the compliance refactor.
            _add_observed_hosts_from_container(
                city_slot, observed
            )  # Preserve the existing behavior during the compliance refactor.
    return frozenset(observed)  # Preserve the existing behavior during the compliance refactor.


def _collect_catalogue_hosts(
    probes_source: dict[str, Any],
) -> frozenset[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return every catalogue FQDN that ``_probe_target`` may consult observations for.

    Why:
        The "catalogue hosts" side of the set difference is every non-wildcard
        FQDN listed on any role in the probe source file. We include role-inline
        FQDNs (all non-tunnel_zen roles) because ``_probe_target`` consults CENR
        for their observed protocol/port even though the role also carries a
        curated ``probe`` block. ``tunnel_zen`` role FQDNs are supplied BY the
        CENR file itself, so by construction they are already observed and
        cannot appear as "missing". Wildcard entries (``"*."``) are filtered
        because they are never emitted as probes (see ``_build_probe_set``
        line ~798).

    Args:
        probes_source: Loaded probe source document (post v2->v3 promotion).

    Returns:
        Frozen set of every non-wildcard catalogue FQDN.
    """
    catalogue: set[str] = set()  # accumulator. Frozen at return time
    for role in probes_source.get("roles", []) or []:  # each catalogue role
        if not isinstance(role, dict):  # WHY: Malformed roles cannot supply host entries.
            continue  # WHY: Keep the warning pre-check tolerant of hand-edited catalogues.
        for fqdn in SyntheticProbeSettingApplier.catalogue_hosts_for_role(role):  # WHY: Reuse concrete-host selection.
            catalogue.add(fqdn)  # add concrete FQDN to the catalogue universe
    return frozenset(catalogue)  # freeze so callers cannot mutate


def _compute_missing_cenr_hosts(  # Preserve the existing behavior during the compliance refactor.
    catalogue_hosts: frozenset[str],
    cenr_observations: frozenset[str],
) -> frozenset[str]:
    """Return catalogue FQDNs that have no CENR observation record.

    Why:
        This is the load-time replacement for the pre-1025 per-emission WARNING
        storm inside ``_probe_target`` (315 sites x 7 missing hosts = 2205
        WARNINGs on the reference org). Computed exactly once per invocation,
        after ``_load_probe_sources`` returns, so the cap becomes M unique
        hosts instead of N*M repeated emissions (research.md R5).

    Args:
        catalogue_hosts: Non-wildcard FQDN universe from
            ``_collect_catalogue_hosts``.
        cenr_observations: Observed FQDN universe from
            ``_collect_cenr_observed_hosts``.

    Returns:
        Frozen set of catalogue hosts absent from ``cenr_observations``. Empty
        set when every catalogue host has an observation (FR-001 zero-emission
        edge case).
    """
    logger.info(  # Constitution VII action-logging: BEFORE the diff
        "computing missing CENR hosts: catalogue=%s observed=%s",
        len(catalogue_hosts),
        len(cenr_observations),
    )
    missing = frozenset(catalogue_hosts - cenr_observations)  # set difference -> frozen
    logger.debug(  # Constitution VII action-logging: AFTER with result summary
        "computed missing CENR hosts: %s missing",
        len(missing),
    )
    return missing  # frozen so callers cannot smuggle in extra hosts


def _emit_load_time_cenr_warning(  # Preserve the existing behavior during the compliance refactor.
    missing_hosts: frozenset[str],
    warned_cenr_hosts: set[str],
) -> None:
    """Emit exactly one WARNING per invocation naming all unwarned missing hosts.

    Why:
        Contract ``log_record_shape.md`` §1.3 mandates a single load-time
        WARNING record that names every missing host and states catalogue-default
        fallback URLs are in use. ``warned_cenr_hosts`` is the mutable dedup
        state owned by ``manage_org_synthetic_probes`` (data-model.md §3 INV-D1)
        -- we mutate it in place so repeat calls within a single invocation
        are no-ops. FR-012: dedup state does NOT persist across invocations
        (caller supplies a fresh set per run).

    Args:
        missing_hosts: Output of ``_compute_missing_cenr_hosts`` for the
            current run.
        warned_cenr_hosts: Per-invocation dedup set. Hosts added here are
            skipped on any subsequent call within the same invocation.
    """
    logger.info(  # Constitution VII: BEFORE the emission decision
        "evaluating CENR load-time warning: missing=%s already_warned=%s",
        len(missing_hosts),
        len(warned_cenr_hosts),
    )
    unwarned = missing_hosts - warned_cenr_hosts  # subtract already-emitted hosts
    if not unwarned:  # zero-emission edge case (FR-001) or repeat call within run
        logger.debug(  # Constitution VII: AFTER, no-op branch
            "CENR load-time warning: no unwarned missing hosts; skipping emission",
        )
        return  # nothing to warn about
    # Sort for deterministic message shape (test assertions and log-grep audits
    # expect a stable ordering across runs regardless of set iteration order).
    ordered = sorted(unwarned)  # ASCII sort per Constitution V log discipline
    # Single WARNING record naming every host, matching log_record_shape.md §1.3.
    # ASCII-only tokens (CENR, using-catalogue-default-URLs) so ``grep -c CENR``
    # in the operator smoke sequence stays deterministic (SC-001).
    logger.warning(  # exactly-one-per-run WARNING per contract §1.3
        "CENR observations missing for %s catalogue host(s); using catalogue-default URLs: %s",
        len(ordered),
        ", ".join(ordered),
    )
    warned_cenr_hosts.update(unwarned)  # mark as warned so a duplicate call is a no-op
    logger.debug(  # Constitution VII: AFTER, emission branch
        "CENR load-time warning emitted for %s hosts; warned_cenr_hosts now %s",
        len(ordered),
        len(warned_cenr_hosts),
    )


def _compute_unmapped_country_codes(  # Preserve the existing behavior during the compliance refactor.
    sites: list[dict[str, Any]],
    region_map: dict[str, str],
    gap_set: frozenset[str],
) -> frozenset[str]:
    """Return unique ISO codes present in ``sites`` but neither region-mapped nor gap-listed.

    Why:
        Load-time counterpart to ``_compute_missing_cenr_hosts`` for the
        country_code axis. Pre-1025, every site with an unmapped code
        triggered a fresh WARNING inside ``_build_region_probes`` (research.md
        R5 quantifies the N*K duplication: 315 sites * K unmapped codes). By
        collapsing to the set of *unique* codes here -- exactly once per
        invocation -- the downstream emitter caps output at K messages
        regardless of how many sites share each code (FR-004, FR-010).
        Codes appearing in ``gap_set`` are silently classified (they are
        deliberately EMEA today by contract INV-COVER-2) and therefore never
        surface here. Only truly-new codes bubble up so the operator gets a
        signal, not noise.

    Args:
        sites: List of site dicts as returned by ``_list_org_sites``. Each
            dict is expected to carry a ``country_code`` string (missing /
            blank entries are treated as "not classifiable" and skipped
            silently -- the region resolver already falls those through to
            the default region and emitting a WARNING for a null value
            would be indistinguishable from an unmapped-code warning).
        region_map: ``_COUNTRY_CODE_TO_REGION`` (passed as an argument so
            tests can exercise the classifier with fixture-scoped maps
            without patching the module-level constant).
        gap_set: ``_COUNTRY_CODE_INTENTIONAL_GAPS`` (same rationale).

    Returns:
        Frozen set of ISO alpha-2 codes appearing in ``sites`` that are
        neither in ``region_map`` nor in ``gap_set``. Empty set when every
        code is classified (FR-005 zero-emission edge case for the LATAM
        fixture after T020).
    """
    logger.info(  # Constitution VII action-logging: BEFORE the scan
        "computing unmapped country codes: sites=%s region_map=%s gap_set=%s",
        len(sites),
        len(region_map),
        len(gap_set),
    )
    seen: set[str] = set()  # accumulator for unique codes across all sites
    for site in sites:  # single pass over the site list
        code = SyntheticProbeSettingApplier.normalized_country_code(site)  # WHY: Share country-code normalization.
        if code is None:  # WHY: Missing or blank codes do not have a useful warning.
            continue  # Preserve the existing behavior during the compliance refactor.
        if code in region_map:  # already region-classified -> silent success
            continue  # Preserve the existing behavior during the compliance refactor.
        if code in gap_set:  # intentional gap -> silently falls through to EMEA
            continue  # Preserve the existing behavior during the compliance refactor.
        seen.add(code)  # genuinely unclassified -> record for warning
    unmapped = frozenset(seen)  # freeze so callers cannot smuggle in extras
    logger.debug(  # Constitution VII: AFTER with unique-code count
        "computed unmapped country codes: %s unique code(s)",
        len(unmapped),
    )
    return unmapped  # frozenset consumed by _emit_load_time_country_code_warning


def _emit_load_time_country_code_warning(  # Preserve the existing behavior during the compliance refactor.
    unmapped_codes: frozenset[str],
    warned_unmapped_codes: set[str],
) -> None:
    """Emit exactly one WARNING per invocation naming all unwarned unmapped codes.

    Why:
        Contract ``log_record_shape.md`` §2.4 mandates a single load-time
        WARNING when at least one site's country_code is neither region-mapped
        nor listed as an intentional gap. The message MUST contain the literal
        token ``country_code`` (test filter anchor from ``_count_country_code_warnings``
        at line 3050) and MUST name every unwarned code plus the default
        region literal so an operator can either extend
        ``_COUNTRY_CODE_TO_REGION`` or add the code to
        ``_COUNTRY_CODE_INTENTIONAL_GAPS`` in the same commit. FR-012 pins
        per-invocation lifetime: ``warned_unmapped_codes`` is caller-owned and
        recreated per run.

    Args:
        unmapped_codes: Output of ``_compute_unmapped_country_codes``.
        warned_unmapped_codes: Per-invocation dedup set (mutated in place).
            Codes added here are skipped on any subsequent call within the
            same invocation. FR-012: caller supplies a fresh empty set per
            run. State MUST NOT persist across runs.
    """
    logger.info(  # Constitution VII: BEFORE the emission decision
        "evaluating country_code load-time warning: unmapped=%s already_warned=%s",
        len(unmapped_codes),
        len(warned_unmapped_codes),
    )
    unwarned = unmapped_codes - warned_unmapped_codes  # subtract codes already emitted this run
    if not unwarned:  # zero-emission (FR-005 LATAM path) or repeat call within run
        logger.debug(  # Constitution VII: AFTER, no-op branch
            "country_code load-time warning: no unwarned unmapped codes; skipping emission",
        )
        return  # nothing to warn about
    # Deterministic ordering so ``grep -c country_code`` in the operator smoke
    # sequence stays stable across runs regardless of set iteration order.
    ordered = sorted(unwarned)  # ASCII sort per Constitution V log discipline
    # Single WARNING record naming every code plus the default region literal
    # so the operator knows exactly which routing decision was made. ASCII
    # tokens only (``country_code``, ``defaulting to region``) so the grep
    # anchor stays deterministic (SC-002, log_record_shape.md §2.4).
    logger.warning(  # exactly-one-per-run WARNING per contract §2.4
        "country_code(s) %s not mapped; defaulting to region %r",
        ", ".join(ordered),
        _DEFAULT_REGION,
    )
    warned_unmapped_codes.update(unwarned)  # mark as warned so a duplicate call is a no-op
    logger.debug(  # Constitution VII: AFTER, emission branch
        "country_code load-time warning emitted for %s code(s); warned_unmapped_codes now %s",
        len(ordered),
        len(warned_unmapped_codes),
    )


def _parse_vlan_token(part: str) -> list[int]:  # Preserve the existing behavior during the compliance refactor.
    """Return the VLAN ids parsed from one comma-split token.

    Why:
        Extracted from :func:`_validate_vlan_input` so the outer parser
        stays under Radon CC>10. Handles both single ids (``"10"``) and
        ranges (``"3-6"``). Invalid tokens return an empty list so the
        caller can drop them silently without adding a branch per case.

    Args:
        part: One already-stripped, non-empty token from the split.

    Returns:
        List of ids from the token, empty on any parse failure or
        reversed range.
    """
    if "-" in part[1:]:  # Preserve the existing behavior during the compliance refactor.
        lo_raw, _, hi_raw = part[1:].partition("-")  # Preserve the existing behavior during the compliance refactor.
        lo_raw = (part[0] + lo_raw).strip()  # Preserve the existing behavior during the compliance refactor.
        hi_raw = hi_raw.strip()  # Preserve the existing behavior during the compliance refactor.
        try:
            lo, hi = int(lo_raw), int(hi_raw)  # Preserve the existing behavior during the compliance refactor.
        except ValueError:  # Preserve the existing behavior during the compliance refactor.
            return []  # Preserve the existing behavior during the compliance refactor.
        return (
            list(range(lo, hi + 1)) if lo <= hi else []
        )  # Preserve the existing behavior during the compliance refactor.
    try:
        return [int(part)]  # Preserve the existing behavior during the compliance refactor.
    except ValueError:  # Preserve the existing behavior during the compliance refactor.
        return []  # Preserve the existing behavior during the compliance refactor.


def _validate_vlan_input(
    raw: str,
) -> tuple[bool, str, list[int]]:  # Preserve the existing behavior during the compliance refactor.
    """Parse and validate VLAN input string.

    Why:
        Mist's UI validator rejects VLAN ids outside 1-4094 (0 and 4095
        are 802.1Q-reserved and 4095 is priority-tagged frames), so any
        out-of-range value would produce a red-banner error on the org
        setting push. Operators frequently paste condensed lists like
        ``"3-6, 10, 200-203"``. Expanding ranges here lets them use the
        same shorthand they use in switch configs. Invalid tokens
        (non-integer, out-of-range endpoints, reversed ranges) are
        silently dropped rather than failing the whole entry so a single
        typo in a long list does not force the operator to re-type
        everything.

    Args:
        raw: Comma-separated VLAN ids and/or ranges (for example ``"3-6, 10"``).

    Returns:
        ``(is_valid, error_message, vlan_ids)``. ``is_valid`` is True
        only when at least one in-range id survived parsing;
        ``vlan_ids`` is sorted and deduplicated. Out-of-range or
        unparseable tokens are dropped silently.
    """
    if not raw.strip():  # Preserve the existing behavior during the compliance refactor.
        return (
            False,
            "VLAN list cannot be empty. Please try again.",
            [],
        )  # Preserve the existing behavior during the compliance refactor.
    ids: list[int] = []  # Preserve the existing behavior during the compliance refactor.
    for part in (
        item.strip() for item in raw.split(",")
    ):  # Preserve the existing behavior during the compliance refactor.
        if part:  # Preserve the existing behavior during the compliance refactor.
            ids.extend(_parse_vlan_token(part))  # Preserve the existing behavior during the compliance refactor.
    ids = [
        vid for vid in ids if _VLAN_MIN <= vid <= _VLAN_MAX
    ]  # Preserve the existing behavior during the compliance refactor.
    if not ids:  # Preserve the existing behavior during the compliance refactor.
        return (  # Preserve the existing behavior during the compliance refactor.
            False,
            f"No valid VLAN ids in [{_VLAN_MIN}, {_VLAN_MAX}] parsed. Please try again.",
            [],
        )
    return True, "", sorted(set(ids))  # Preserve the existing behavior during the compliance refactor.


def _prompt_vlan_list() -> list[int]:  # Preserve the existing behavior during the compliance refactor.
    """Prompt the operator for a comma-separated VLAN id list.

    Why:
        The VLAN list is the only per-invocation parameter. Validating
        the range at prompt time avoids surfacing an opaque API-side
        rejection later. Accepts ranges (``3-6`` expands to ``3,4,5,6``)
        because operators paste condensed lists from switch configs.

    Returns:
        Sorted, deduplicated list of VLAN ids in ``[1, 4094]``. Never
        returns an empty list -- the prompt loops until at least one
        valid id is entered.
    """
    while True:  # Preserve the existing behavior during the compliance refactor.
        raw = SyntheticProbePromptReader.read(  # Capture VLAN input without stranding an SSH session on EOF.
            "  Enter VLAN ids (comma-separated, ranges ok e.g. 3-6, each in [1, 4094]): ",
            "menu_206_vlan_ids",
        )
        is_valid, error, ids = _validate_vlan_input(raw)  # Validate before any Mist setting read or write.
        if is_valid:  # Preserve the existing behavior during the compliance refactor.
            return ids  # Return only checked VLAN identifiers to the destructive path.
        print(f"  {error}")  # Keep the previous operator feedback for invalid input.


def _fetch_setting(
    mist_session: Any, org_id: str
) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Return the current org setting block via mistapi.

    Why:
        Isolating the read call makes it trivial to mock in tests and
        clarifies the get boundary from the put boundary.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist organisation UUID.

    Returns:
        The parsed JSON payload of ``getOrgSettings`` (defensively an
        empty dict if the API returned no body).
    """
    logger.debug(
        "Calling getOrgSettings(org_id=%s)", org_id
    )  # Preserve the existing behavior during the compliance refactor.
    response = _mist_setting.getOrgSettings(
        mist_session, org_id
    )  # Preserve the existing behavior during the compliance refactor.
    data = getattr(response, "data", None)  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(data, dict):  # Preserve the existing behavior during the compliance refactor.
        logger.warning(
            "getOrgSettings returned non-dict payload; treating as empty"
        )  # Preserve the existing behavior during the compliance refactor.
        return {}  # Preserve the existing behavior during the compliance refactor.
    return data  # Preserve the existing behavior during the compliance refactor.


def _detect_existing(
    setting: dict[str, Any],
) -> dict[str, dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Extract ``synthetic_test.custom_probes`` from ``setting``.

    Why:
        Guarded accessor so callers do not have to worry about the
        edge case where either ``synthetic_test`` or ``custom_probes``
        is absent.

    Args:
        setting: Org setting block as returned by ``getOrgSettings``.

    Returns:
        The ``custom_probes`` map (``{name: probe_dict}``) if present,
        otherwise an empty dict.
    """
    synthetic = (
        setting.get("synthetic_test") if isinstance(setting, dict) else None
    )  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(synthetic, dict):  # Preserve the existing behavior during the compliance refactor.
        return {}  # Preserve the existing behavior during the compliance refactor.
    probes = synthetic.get("custom_probes")  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(probes, dict):  # Preserve the existing behavior during the compliance refactor.
        return {}  # Preserve the existing behavior during the compliance refactor.
    return probes  # Preserve the existing behavior during the compliance refactor.


def _partition_tool_authored(  # Preserve the existing behavior during the compliance refactor.
    existing: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Split existing probes into tool-authored and foreign sets.

    Why:
        Foreign probes (any probe whose name lacks the ``zcc-`` prefix)
        must be preserved verbatim through merge and swap so operator-
        authored config survives the tool run. Partitioning up-front
        keeps the downstream helpers pure.

    Args:
        existing: Full ``custom_probes`` map from the org setting.

    Returns:
        ``(tool_authored, foreign)`` -- two disjoint dicts whose union is
        ``existing``.
    """
    tool_authored: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    foreign: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for name, probe in existing.items():  # Preserve the existing behavior during the compliance refactor.
        if isinstance(name, str) and name.startswith(
            _TOOL_NAME_PREFIX
        ):  # Preserve the existing behavior during the compliance refactor.
            tool_authored[name] = probe  # Preserve the existing behavior during the compliance refactor.
        else:
            foreign[name] = probe  # Preserve the existing behavior during the compliance refactor.
    return tool_authored, foreign  # Preserve the existing behavior during the compliance refactor.


def _fqdn_slug(fqdn: str) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Convert an FQDN to the slug segment used in probe names.

    Why:
        Probe names need a stable, filesystem-safe derivation from the
        FQDN so tool-authored probes are recognisable across re-runs.
        Lowercase + ``.`` -> ``-`` is sufficient because Zscaler FQDNs
        are ASCII-only.

    Args:
        fqdn: The concrete hostname (never a wildcard by the time this
            is called).

    Returns:
        Lowercased slug with dots replaced by hyphens.
    """
    return fqdn.lower().replace(".", "-")  # Preserve the existing behavior during the compliance refactor.


def _haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:  # Preserve the existing behavior during the compliance refactor.
    """Great-circle distance in kilometres between two lat/lon pairs.

    Why:
        ZEN city ranking uses geodesic distance from a site's Mist-reported
        ``latlng`` to each candidate ZEN city centre. Haversine is the
        standard closed-form solution: no external dep, no earth-model
        approximation error large enough to affect ranking at the
        continental scale we care about (Zscaler cities are hundreds of
        kilometres apart. Sub-percent radius error is invisible).

    Args:
        lat1: First point latitude in decimal degrees.
        lon1: First point longitude in decimal degrees.
        lat2: Second point latitude in decimal degrees.
        lon2: Second point longitude in decimal degrees.

    Returns:
        Distance in kilometres. Always non-negative.
    """
    # Mean earth radius in km. Using the volumetric mean (IUGG) rather than
    # equatorial keeps error symmetric across hemispheres for our use.
    earth_radius_km = 6371.0088  # Preserve the existing behavior during the compliance refactor.
    phi1 = math.radians(lat1)  # Preserve the existing behavior during the compliance refactor.
    phi2 = math.radians(lat2)  # Preserve the existing behavior during the compliance refactor.
    delta_phi = math.radians(lat2 - lat1)  # Preserve the existing behavior during the compliance refactor.
    delta_lambda = math.radians(lon2 - lon1)  # Preserve the existing behavior during the compliance refactor.
    a = (
        math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )  # Preserve the existing behavior during the compliance refactor.
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Preserve the existing behavior during the compliance refactor.
    return earth_radius_km * c  # Preserve the existing behavior during the compliance refactor.


def _unwrap_v3_hosts(entries: list[Any]) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return concrete hostname strings from a mixed v2/v3 CENR host list.

    Why:
        CENR is mid-migration from a flat ``list[str]`` (v2) to a list of
        ``{"host": str, ...}`` dicts (v3). Every consumer must handle
        both shapes or silently drop hosts, so this helper centralises
        the unwrap so ``_iter_role_fqdns`` and future callers do not
        each reinvent the v3-tolerant read.

    Args:
        entries: A raw list from the CENR file or a role's ``fqdns`` --
            a mix of plain strings (v2), dicts with a ``host`` key (v3),
            and possible falsy entries produced by upstream ``... or
            []`` fallbacks.

    Returns:
        The concrete host string for every truthy entry, with v3 dict
        entries unwrapped to their ``host`` value.
    """
    return [
        e["host"] if isinstance(e, dict) else e for e in entries if e
    ]  # Preserve the existing behavior during the compliance refactor.


def _iter_role_fqdns(
    role: dict[str, Any], cenr: dict[str, Any]
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Yield the concrete FQDN list for a single role, expanding CENR.

    Why:
        Only the ``tunnel_zen`` role expands via the CENR file. Every
        other role carries its FQDNs inline. Centralising the branch
        keeps ``_build_probe_set`` readable.

    Args:
        role: One entry from ``roles[]`` in the probe source file.
        cenr: Parsed CENR hostnames file (for the tunnel_zen expansion).

    Returns:
        A list of concrete FQDN strings (may include wildcards which the
        caller will filter).
    """
    if role.get("role") == _TUNNEL_ZEN_ROLE:  # Preserve the existing behavior during the compliance refactor.
        proxy = cenr.get("proxy_hostnames", []) or []  # v3 dicts or v2 flat strings
        vpn = cenr.get("vpn_hostnames", []) or []  # v3 dicts or v2 flat strings
        return _unwrap_v3_hosts([*proxy, *vpn])  # Preserve the existing behavior during the compliance refactor.
    return _unwrap_v3_hosts(role.get("fqdns") or [])  # Preserve the existing behavior during the compliance refactor.


def _emit_probes_for_role(  # Preserve the existing behavior during the compliance refactor.
    role: dict[str, Any],
    cenr_source: dict[str, Any],
    result: dict[str, dict[str, Any]],
) -> tuple[bool, bool]:
    """Emit every probe body for one role into ``result``.

    Why:
        Extracted from ``_build_probe_set`` so the outer function stays
        under Radon CC=10. Encapsulates the per-role loop (wildcard skip,
        one-critical-per-role selection, mini-* body shape). Returns the
        ``(critical_role, critical_assigned)`` pair so the caller can run
        the "critical role but no explicit FQDN matched" fallback in one
        place.

    Args:
        role: One role entry from ``probes_source["roles"]``.
        cenr_source: Loaded CENR document (for FQDN expansion + target
            resolution).
        result: Aggregating map. Probes are inserted under their
            ``zcc-<role>-<slug>`` keys.

    Returns:
        ``(critical_role, critical_assigned)``. ``critical_role`` is True
        when the role carries ``critical: true``; ``critical_assigned``
        is True when this pass already assigned the role's one critical
        slot.
    """
    role_name = role.get("role") or "unknown"  # Preserve the existing behavior during the compliance refactor.
    critical_role = bool(role.get("critical"))  # Preserve the existing behavior during the compliance refactor.
    critical_target = role.get("critical_fqdn")  # Preserve the existing behavior during the compliance refactor.
    critical_assigned = False  # Preserve the existing behavior during the compliance refactor.
    for fqdn in SyntheticProbeSettingApplier.role_concrete_fqdns(
        role, cenr_source
    ):  # WHY: Keep host filtering outside the loop.
        # Pick exactly one critical FQDN per critical role. Preference
        # order: explicit ``critical_fqdn`` if it appears in the
        # expanded list, otherwise the first non-wildcard hit.
        is_critical = (
            SyntheticProbeSettingApplier.is_critical_probe_target(  # WHY: Keep the critical-slot rule out of the loop.
                critical_role,  # WHY: Non-critical roles cannot spend the slot.
                critical_assigned,  # WHY: Prior assignment blocks a second critical probe.
                critical_target,  # WHY: An explicit critical FQDN has priority.
                fqdn,  # WHY: The current concrete host is the candidate.
            )
        )
        if is_critical:  # WHY: A matching host spends the critical slot.
            critical_assigned = True  # Preserve the existing behavior during the compliance refactor.
        probe_name = f"{_TOOL_NAME_PREFIX}{role_name}-{_fqdn_slug(fqdn)}"
        target = _probe_target(
            fqdn, role, cenr_source
        )  # Preserve the existing behavior during the compliance refactor.
        probe_body = SyntheticProbeSettingApplier.probe_body(
            target, role, is_critical
        )  # WHY: Build one probe body consistently.
        result[probe_name] = probe_body  # Preserve the existing behavior during the compliance refactor.
    return critical_role, critical_assigned  # Preserve the existing behavior during the compliance refactor.


def _promote_first_probe_to_critical(  # Preserve the existing behavior during the compliance refactor.
    result: dict[str, dict[str, Any]],
    role_name: str,
    critical_target: Any,
) -> None:
    """Promote the first probe named for ``role_name`` to critical.

    Why:
        Fallback for ``_build_probe_set`` when a role declared critical
        but the requested ``critical_fqdn`` was absent from the FQDN
        expansion. Extracted so the caller stays under CC=10. Still
        spending the critical slot on the intended role beats silently
        downgrading it.

    Args:
        result: Current probe map (mutated in place).
        role_name: Role slug to search for.
        critical_target: Requested critical FQDN (for the warning only).
    """
    slug_prefix = f"{_TOOL_NAME_PREFIX}{role_name}-"  # Preserve the existing behavior during the compliance refactor.
    for probe_name, probe in result.items():  # Preserve the existing behavior during the compliance refactor.
        if probe_name.startswith(slug_prefix):  # Preserve the existing behavior during the compliance refactor.
            probe["aggressiveness"] = (
                _CRITICAL_AGGRESSIVENESS  # Preserve the existing behavior during the compliance refactor.
            )
            logger.warning(  # Preserve the existing behavior during the compliance refactor.
                "Role %s: critical_fqdn %r not found; promoted %s to critical",
                role_name,
                critical_target,
                probe_name,
            )
            return  # Preserve the existing behavior during the compliance refactor.


def _build_probe_set(  # Preserve the existing behavior during the compliance refactor.
    sources: tuple[dict[str, Any], dict[str, Any]],
    vlan_ids: list[int],
) -> dict[str, dict[str, Any]]:
    """Build the full tool-authored probe set from the curated sources.

    Why:
        Pure function -- no I/O -- so the acceptance tests can pin the
        exact probe body produced for a given VLAN list. The
        ``critical`` / ``critical_fqdn`` flags on each role select
        exactly one probe per critical role to receive
        ``aggressiveness=critical`` so the org-wide 5-critical cap on
        the Mist side is respected without runtime discovery.

    Args:
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
        vlan_ids: Kept for signature/back-compat with the caller. Ignored
            when building probe bodies because VLAN scoping belongs on
            the ``tests[]`` row that references the probe, not on the
            ``custom_probes`` definition itself (matches Mist's own
            ``mini-*`` shape).

    Returns:
        A ``{probe_name: probe_body}`` map ready to be merged into the
        setting block. Wildcard FQDNs are skipped.
    """
    probes_source, cenr_source = sources  # Preserve the existing behavior during the compliance refactor.
    result: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for role in SyntheticProbeSettingApplier.buildable_roles(
        probes_source
    ):  # WHY: Keep malformed and site-only roles out.
        role_name = role.get("role") or "unknown"  # Preserve the existing behavior during the compliance refactor.
        critical_role, critical_assigned = _emit_probes_for_role(
            role, cenr_source, result
        )  # Preserve the existing behavior during the compliance refactor.
        # Fallback: role declared critical but the requested
        # ``critical_fqdn`` was absent from the expansion. Promote the
        # first probe emitted for the role so we still spend a critical
        # slot on the intended role rather than silently downgrading.
        if critical_role and not critical_assigned:  # Preserve the existing behavior during the compliance refactor.
            _promote_first_probe_to_critical(
                result, role_name, role.get("critical_fqdn")
            )  # Preserve the existing behavior during the compliance refactor.
    return result  # Preserve the existing behavior during the compliance refactor.


def _build_region_probes(  # Preserve the existing behavior during the compliance refactor.
    sources: tuple[dict[str, Any], dict[str, Any]],
    country_code: str | None,
) -> dict[str, dict[str, Any]]:
    """Build the Samsung ELM probe set for the region matching ``country_code``.

    Why:
        Region-scoped Samsung ELM roles (``samsung_elm_activation_americas``,
        ``..._emea``, ``..._china``) are skipped by ``_build_probe_set`` at
        org scope because pushing every region's endpoints to every site is
        wasteful noise. The site-override flow calls this helper instead so
        each picked site only receives the ELM role matching its own
        ``country_code``. Unmapped or missing country codes fall back to
        EMEA (the broadest surface). The operator-visible WARNING for the
        unmapped set is now emitted once at load time by
        ``_emit_load_time_country_code_warning`` (1025-US2, FR-004 / FR-010)
        rather than once per site here, so this helper stays silent on the
        fallback path and returns bytes deterministically for INV-1.

    Args:
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
        country_code: ISO 3166-1 alpha-2 code from the site dict (case-
            insensitive. May be ``None`` or an unmapped code -- both fall
            through to EMEA silently. See ``_emit_load_time_country_code_warning``
            for the operator-visible surface).

    Returns:
        A ``{probe_name: probe_body}`` map for the one matching role.
        Empty dict if the probe source file does not ship a role for the
        resolved region (defensive. The shipped catalogue has all three).
    """
    probes_source, _ = sources  # Preserve the existing behavior during the compliance refactor.
    normalised = (country_code or "").strip().upper()  # Preserve the existing behavior during the compliance refactor.
    region = _COUNTRY_CODE_TO_REGION.get(normalised)  # None -> unmapped or intentionally omitted
    if region is None:  # Preserve the existing behavior during the compliance refactor.
        # NOTE(1025-US2): warning moved to load-time
        # ``_emit_load_time_country_code_warning`` to avoid N*K duplication
        # per FR-004 / FR-010 / SC-002. Region-value resolution behaviour is
        # unchanged -- unmapped codes still fall through to _DEFAULT_REGION
        # so regional probes still fire (FR-003 spirit preserved).
        region = _DEFAULT_REGION  # emea fallback -- deliberate, per data-model.md
    target_role_name = (
        f"{_SAMSUNG_ELM_ROLE_PREFIX}{region}"  # Preserve the existing behavior during the compliance refactor.
    )
    for role in probes_source.get("roles", []) or []:  # Preserve the existing behavior during the compliance refactor.
        if role.get("role") == target_role_name:  # Preserve the existing behavior during the compliance refactor.
            return _build_regional_elm_probes(
                role, sources, target_role_name
            )  # Preserve the existing behavior during the compliance refactor.
    return {}  # Preserve the existing behavior during the compliance refactor.


def _build_regional_elm_probes(  # Preserve the existing behavior during the compliance refactor.
    role: dict[str, Any],
    sources: tuple[dict[str, Any], dict[str, Any]],
    target_role_name: str,
) -> dict[str, dict[str, Any]]:
    """Emit the ``{probe_name: probe_body}`` map for one Samsung ELM role.

    Why:
        Extracted from ``_build_region_probes`` so the outer helper can
        stay under the project's CC<=10 gate. The inner loop is
        catalogue-shape-specific (v3 dict / v2 flat unwrap plus wildcard
        filtering), and the two concerns read more cleanly split apart.

    Args:
        role: The matched Samsung ELM role dict from ``probes_source``.
        sources: The ``(probes, cenr)`` tuple. Only ``cenr`` (index 1) is
            passed through to ``_probe_target`` for probe-body wiring.
        target_role_name: Precomputed ``samsung_elm_activation_<region>``
            slug so the probe-name builder does not have to reconstruct
            it.

    Returns:
        A ``{probe_name: probe_body}`` map for the resolved role.
    """
    result: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for entry in role.get("fqdns") or []:  # Preserve the existing behavior during the compliance refactor.
        # Accept both v3 dict {"host": ...} and legacy flat strings so a
        # mid-migration CENR cache does not silently drop every regional
        # ELM host. The isinstance guard below already excludes non-strings,
        # so unwrap up-front and let the wildcard filter proceed as before.
        fqdn = (
            entry.get("host") if isinstance(entry, dict) else entry
        )  # Preserve the existing behavior during the compliance refactor.
        if not _is_concrete_probe_fqdn(fqdn):  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        probe_name = f"{_TOOL_NAME_PREFIX}{target_role_name}-{_fqdn_slug(fqdn)}"
        # Regional ELM probes are never critical (source catalogue omits
        # the flag), so aggressiveness is ``auto``.
        target = _probe_target(fqdn, role, sources[1])  # Preserve the existing behavior during the compliance refactor.
        result[probe_name] = {
            # Same target-shape classification as ``_build_probe_set``:
            # HTTP/S URLs stay ``application``, bare host:port becomes
            # ``reachability``. Regional ELM roles ship as HTTPS today
            # but this future-proofs the emit path.
            "type": _probe_type_for_target(target, role.get("type")),
            "target": target,
            "aggressiveness": _AUTO_AGGRESSIVENESS,
        }
    return result  # Preserve the existing behavior during the compliance refactor.


def _is_concrete_probe_fqdn(fqdn: Any) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return ``True`` for a plain string FQDN that is not a wildcard.

    Why:
        Every probe-emitting loop drops wildcard entries (``*.example.com``)
        because Mist synthetic probes require a resolvable single host.
        Sharing the check centralises the filter and helps helpers stay
        under the CC gate.

    Args:
        fqdn: A candidate value from a v3-dict unwrap or a v2 flat list.

    Returns:
        ``True`` if ``fqdn`` is a ``str`` and does not start with
        ``"*."``. Otherwise ``False``.
    """
    return isinstance(fqdn, str) and not fqdn.startswith(
        "*."
    )  # Preserve the existing behavior during the compliance refactor.


# Compression rule: countries with at most this many distinct ZEN locations
# get ALL of their locations scheduled at every site in-country. Above this
# threshold, we fall back to nearest-N-by-haversine. Two is chosen because
# Zscaler almost always deploys a same-city pair (for example Frankfurt IV + VI at
# identical coords), so a country with only a "two location" footprint really
# has one geographic point + a redundant peer -- probing both is cheap and
# gives operators failover signal.
_ZEN_COMPRESSION_THRESHOLD = 2  # Preserve the existing behavior during the compliance refactor.
# When a site's country has more ZEN locations than the compression threshold,
# we pick this many nearest ZENs by geodesic distance. Two matches the
# threshold so a site in a ZEN-dense country (US, DE, IN...) still gets a
# primary+secondary probe pair rather than just one.
_ZEN_NEAREST_COUNT = 2  # Preserve the existing behavior during the compliance refactor.


def _site_latlng(
    site: dict[str, Any],
) -> tuple[float, float] | None:  # Preserve the existing behavior during the compliance refactor.
    """Extract ``(lat, lon)`` from a Mist site dict, or ``None`` if absent."""
    latlng = site.get("latlng")  # Read the Mist location object.
    if not isinstance(latlng, dict):  # Treat missing or malformed coordinates as absent.
        return None  # Preserve the existing absent-coordinate result.
    lat = latlng.get("lat")  # Read the latitude value.
    lon = latlng.get("lng")  # Read the longitude value.
    return _finite_latlng(lat, lon)  # Validate and normalize the coordinate pair.


def _finite_latlng(
    lat: Any, lon: Any
) -> tuple[float, float] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return finite coordinates, or ``None`` when a value is invalid."""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):  # Require numeric coordinates.
        return None  # Preserve the prior invalid-coordinate result.
    if not math.isfinite(float(lat)) or not math.isfinite(float(lon)):  # Reject NaN and infinite values.
        return None  # Preserve the prior non-finite-coordinate result.
    return (float(lat), float(lon))  # Return normalized float coordinates.


def _distinct_zen_locations(
    city_metadata: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:  # Preserve the existing behavior during the compliance refactor.
    """Group city metadata entries by unique ``(country_code, lat, lon)``."""
    groups: dict[str, list[str]] = {}  # Collect city names by physical ZEN location.
    for city, meta in city_metadata.items():  # Preserve the input metadata traversal.
        key = _zen_location_key(meta)  # Build the rounded location key when coordinates are valid.
        if key is not None:  # Skip malformed metadata exactly as before.
            groups.setdefault(key, []).append(city)  # Group all ZEN names at the same location.
    for names in groups.values():  # Sort each location group for deterministic selection.
        names.sort()  # Preserve stable output for tests and audits.
    return groups  # Return the grouped ZEN location map.


def _zen_location_key(
    meta: dict[str, Any],
) -> str | None:  # Preserve the existing behavior during the compliance refactor.
    """Return a rounded location key for one ZEN metadata record."""
    country = meta.get("country_code")  # Read the country code from the metadata record.
    lat = meta.get("lat")  # Read the ZEN latitude.
    lon = meta.get("lon")  # Read the ZEN longitude.
    if not isinstance(country, str) or _finite_latlng(lat, lon) is None:  # Require country and finite coordinates.
        return None  # Preserve the previous malformed-record skip.
    return f"{country.upper()}:{round(float(lat), 4)}:{round(float(lon), 4)}"  # Preserve the rounded key shape.


def _zens_in_country(  # Preserve the existing behavior during the compliance refactor.
    city_metadata: dict[str, dict[str, Any]],
    normalised_cc: str,
) -> dict[str, dict[str, Any]]:
    """Filter ``city_metadata`` down to entries matching ``normalised_cc``.

    Why:
        Extracted from ``_resolve_zen_cities_for_site`` so the caller stays
        below the Radon CC=10 quality gate. The predicate is one call site
        today but the isolation makes the rule ("case-insensitive match on
        ``country_code`` string") testable in isolation.

    Args:
        city_metadata: ``cenr["city_metadata"]`` mapping.
        normalised_cc: Uppercased ISO country code (empty string disables
            the filter and returns ``{}``).

    Returns:
        Sub-mapping of cities whose ``country_code`` matches. Empty when
        ``normalised_cc`` is empty or no city matches.
    """
    if not normalised_cc:  # Preserve the existing behavior during the compliance refactor.
        return {}  # Preserve the existing behavior during the compliance refactor.
    result: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for city, meta in city_metadata.items():  # Preserve the existing behavior during the compliance refactor.
        meta_cc = meta.get("country_code")  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(meta_cc, str) and meta_cc.upper() == normalised_cc
        ):  # Preserve the existing behavior during the compliance refactor.
            result[city] = meta  # Preserve the existing behavior during the compliance refactor.
    return result  # Preserve the existing behavior during the compliance refactor.


def _pick_zens_from_in_country(  # Preserve the existing behavior during the compliance refactor.
    in_country: dict[str, dict[str, Any]],
    site_coords: tuple[float, float] | None,
    normalised_cc: str,
) -> list[str]:
    """Apply the in-country compression rules (rules 1-3 of ZEN selection).

    Why:
        ``_resolve_zen_cities_for_site`` was CC=13 because the in-country
        branch alone stacks three sub-decisions (threshold vs latlng vs
        fallback). Splitting them out drops the outer function to CC<=10
        and keeps the rule numbering discoverable from one place.

    Args:
        in_country: Result of ``_zens_in_country`` (non-empty).
        site_coords: ``(lat, lon)`` for the site, or ``None``.
        normalised_cc: Uppercased ISO country code (for logging only).

    Returns:
        Sorted, deduped list of ZEN city names per rules 1-3.
    """
    location_groups = _distinct_zen_locations(
        in_country
    )  # Preserve the existing behavior during the compliance refactor.
    if (
        len(location_groups) <= _ZEN_COMPRESSION_THRESHOLD
    ):  # Preserve the existing behavior during the compliance refactor.
        return sorted(in_country.keys())  # Preserve the existing behavior during the compliance refactor.
    if site_coords is not None:  # Preserve the existing behavior during the compliance refactor.
        return _nearest_zens_from_pool(
            in_country, site_coords, _ZEN_NEAREST_COUNT
        )  # Preserve the existing behavior during the compliance refactor.
    logger.info(  # Preserve the existing behavior during the compliance refactor.
        "Site missing latlng but has country %s with %d ZEN locations; " "scheduling all in-country ZENs",
        normalised_cc,
        len(location_groups),
    )
    return sorted(in_country.keys())  # Preserve the existing behavior during the compliance refactor.


def _resolve_zen_cities_for_site(  # Preserve the existing behavior during the compliance refactor.
    site: dict[str, Any],
    cenr: dict[str, Any],
) -> list[str]:
    """Pick the ZEN cities that a site should probe.

    Why:
        Every Mist site probing every one of the ~95 ZEN cities would burn
        bandwidth and generate noisy dashboards. We want the small set that
        matches the site's geography: if the site's country hosts only a
        handful of ZEN locations, probe them all (they are already nearby);
        otherwise pick the geodesically-nearest few. This mirrors what a
        network engineer would do by hand looking at the ZEN map.

    Compression rules (evaluated in order):
        - Country has <= ``_ZEN_COMPRESSION_THRESHOLD`` distinct ZEN
          locations -> return every ZEN name in-country.
        - Country has more, and the site has a valid ``latlng`` -> return
          the ``_ZEN_NEAREST_COUNT`` nearest ZENs by great-circle distance,
          deduped by location (so same-city pairs count once).
        - Country has more but site lacks ``latlng`` -> return the
          country's ZENs anyway (better to over-probe within-country than
          to skip. Operators can trim later).
        - Site has no country match AND has ``latlng`` -> nearest globally.
        - No country match AND no latlng -> empty list + warn.

    Args:
        site: The Mist site dict. Reads ``country_code`` and ``latlng``.
        cenr: Parsed CENR JSON. Reads ``city_metadata``.

    Returns:
        A sorted, deduped list of ZEN city display names. May be empty.
    """
    city_metadata = SyntheticProbeSettingApplier.city_metadata_or_warn(
        cenr
    )  # WHY: Keep ZEN metadata validation out of this selector.
    if city_metadata is None:  # WHY: No metadata means no safe city schedule can be built.
        return []  # Preserve the existing behavior during the compliance refactor.
    country_code = site.get("country_code")  # Preserve the existing behavior during the compliance refactor.
    normalised_cc = (
        country_code.strip().upper() if isinstance(country_code, str) else ""
    )  # Preserve the existing behavior during the compliance refactor.
    site_coords = _site_latlng(site)  # Preserve the existing behavior during the compliance refactor.

    in_country = _zens_in_country(
        city_metadata, normalised_cc
    )  # Preserve the existing behavior during the compliance refactor.
    if in_country:  # Preserve the existing behavior during the compliance refactor.
        return _pick_zens_from_in_country(
            in_country, site_coords, normalised_cc
        )  # Preserve the existing behavior during the compliance refactor.

    if site_coords is not None:  # Preserve the existing behavior during the compliance refactor.
        # Rule 4: no country match but we know where the site is.
        logger.info(  # Preserve the existing behavior during the compliance refactor.
            "Site country %r has no ZEN presence; falling back to nearest " "%d global ZENs by geodesic distance",
            country_code,
            _ZEN_NEAREST_COUNT,
        )
        return _nearest_zens_from_pool(
            city_metadata, site_coords, _ZEN_NEAREST_COUNT
        )  # Preserve the existing behavior during the compliance refactor.

    # Rule 5: nothing to work with.
    logger.warning(  # Preserve the existing behavior during the compliance refactor.
        "ZEN scheduling skipped for site id=%r: no country_code match and " "no latlng",
        site.get("id"),
    )
    return []  # Preserve the existing behavior during the compliance refactor.


def _nearest_zens_from_pool(  # Preserve the existing behavior during the compliance refactor.
    pool: dict[str, dict[str, Any]],
    site_coords: tuple[float, float],
    count: int,
) -> list[str]:
    """Return the ``count`` nearest ZEN city names from a pool.

    Why:
        Same-coord peers (for example Frankfurt IV + Frankfurt VI) should count as
        one location when ranking distance -- otherwise "nearest 2" collapses
        to two names at the same spot. We rank by distinct (lat, lon) groups
        and then re-expand the winning groups back to the full name list so
        operators still get the redundant-peer coverage they expect.

    Args:
        pool: Subset of ``city_metadata`` to consider.
        site_coords: ``(lat, lon)`` for the site.
        count: How many distinct locations to return names for.

    Returns:
        Sorted list of ZEN city names covering the nearest ``count``
        distinct locations. Fewer than ``count`` when the pool has fewer
        distinct locations.
    """
    site_lat, site_lon = site_coords  # Preserve the existing behavior during the compliance refactor.
    # Distance per distinct location key -> representative names.
    per_location: dict[str, tuple[float, list[str]]] = (
        {}
    )  # Preserve the existing behavior during the compliance refactor.
    for city, meta in pool.items():  # Preserve the existing behavior during the compliance refactor.
        lat = meta.get("lat")  # Preserve the existing behavior during the compliance refactor.
        lon = meta.get("lon")  # Preserve the existing behavior during the compliance refactor.
        cc = meta.get("country_code")  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(lat, (int, float)) or not isinstance(
            lon, (int, float)
        ):  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        if not isinstance(cc, str):  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        key = f"{cc.upper()}:{round(float(lat), 4)}:{round(float(lon), 4)}"
        distance = _haversine_km(
            site_lat, site_lon, float(lat), float(lon)
        )  # Preserve the existing behavior during the compliance refactor.
        existing = per_location.get(key)  # Preserve the existing behavior during the compliance refactor.
        if existing is None:  # Preserve the existing behavior during the compliance refactor.
            per_location[key] = (distance, [city])  # Preserve the existing behavior during the compliance refactor.
        else:
            existing[1].append(city)  # Preserve the existing behavior during the compliance refactor.
    # Sort by (distance, key) so ties are deterministic.
    ranked = sorted(
        per_location.items(), key=lambda item: (item[1][0], item[0])
    )  # Preserve the existing behavior during the compliance refactor.
    picked_names: list[str] = []  # Preserve the existing behavior during the compliance refactor.
    for _key, (_distance, names) in ranked[:count]:  # Preserve the existing behavior during the compliance refactor.
        picked_names.extend(names)  # Preserve the existing behavior during the compliance refactor.
    return sorted(picked_names)  # Preserve the existing behavior during the compliance refactor.


def _probe_hostnames_for_city(
    meta: dict[str, Any],
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return the ZEN probe hostnames for one ``city_metadata`` entry.

    Why:
        Extracted from ``_zen_probe_names_for_cities`` so the caller stays
        under Radon CC=10. Encapsulates the v3 (``probe_hostnames`` list)
        vs legacy v2 (``probe_hostname`` scalar) fallback in one place so
        future migrations only touch this helper.

    Args:
        meta: One ``city_metadata`` value (already type-checked as dict).

    Returns:
        Non-empty ``str`` hostnames. Empty list when neither v3 nor legacy
        forms are present.
    """
    hostnames_raw = meta.get("probe_hostnames")  # Preserve the existing behavior during the compliance refactor.
    if isinstance(hostnames_raw, list):  # Preserve the existing behavior during the compliance refactor.
        hostnames = [
            h for h in hostnames_raw if isinstance(h, str) and h
        ]  # Preserve the existing behavior during the compliance refactor.
        if hostnames:  # Preserve the existing behavior during the compliance refactor.
            return hostnames  # Preserve the existing behavior during the compliance refactor.
    legacy = meta.get("probe_hostname")  # Preserve the existing behavior during the compliance refactor.
    if isinstance(legacy, str) and legacy:  # Preserve the existing behavior during the compliance refactor.
        return [legacy]  # Preserve the existing behavior during the compliance refactor.
    return []  # Preserve the existing behavior during the compliance refactor.


def _zen_probe_names_for_cities(  # Preserve the existing behavior during the compliance refactor.
    cities: list[str],
    cenr: dict[str, Any],
) -> list[str]:
    """Map ZEN city names to the matching tool-authored probe names."""
    city_metadata = _city_metadata(cenr)  # Normalize the optional CENR city metadata map.
    result: list[str] = []  # Collect probe names in selected-city order.
    for city in cities:  # Preserve the caller's selected ZEN order.
        result.extend(_zen_probe_names_for_city(city, city_metadata))  # Add each city's representative probes.
    return result  # Return the complete probe-name list.


def _city_metadata(
    cenr: dict[str, Any],
) -> dict[str, Any]:  # Preserve the existing behavior during the compliance refactor.
    """Return CENR city metadata when it has the expected dict shape."""
    city_metadata = cenr.get("city_metadata") or {}  # Read the optional metadata mapping.
    if isinstance(city_metadata, dict):  # Preserve valid metadata for city lookups.
        return city_metadata  # Return the existing metadata mapping.
    return {}  # Preserve the previous empty result for malformed metadata.


def _zen_probe_names_for_city(
    city: str, city_metadata: dict[str, Any]
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return tool-authored probe names for one ZEN city."""
    meta = city_metadata.get(city)  # Read the metadata for the requested city.
    if not isinstance(meta, dict):  # Skip cities that have no valid metadata.
        return []  # Preserve the previous skipped-city behavior.
    return [_zen_probe_name(hostname) for hostname in _probe_hostnames_for_city(meta)]  # Format each probe name.


def _zen_probe_name(hostname: str) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Return the tool-authored ZEN probe name for one hostname."""
    return f"{_TOOL_NAME_PREFIX}{_TUNNEL_ZEN_ROLE}-{_fqdn_slug(hostname)}"  # Preserve the existing name shape.


def _merge_probes(  # Preserve the existing behavior during the compliance refactor.
    existing_tool: dict[str, dict[str, Any]],
    new_probes: dict[str, dict[str, Any]],
    extra_vlans: list[int],
) -> dict[str, dict[str, Any]]:
    """Re-sync tool-authored probes to the mini-* body shape.

    Why:
        Merge is the safe additive path. The correct body shape is
        ``{type, target, aggressiveness}`` only, so this pass strips any
        legacy ``name`` / ``vlan_ids`` fields off existing probes as a
        migration. ``aggressiveness`` is re-synced from ``new_probes`` so
        a probe that lost its "critical" designation upstream is demoted
        here (and the freed critical slot re-lands on the correct probe).

    Args:
        existing_tool: Probes currently on the org matching ``zcc-``.
        new_probes: Freshly-built probe set. Used to look up the
            authoritative ``aggressiveness`` (and ``type``/``target``
            when normalising legacy bodies) for each matching probe.
        extra_vlans: Ignored. Retained for caller signature back-compat.

    Returns:
        Merged probe map. Bodies conform to the mini-* shape:
        ``{type, target, aggressiveness}`` -- no ``name``, no
        ``vlan_ids``.
    """
    del extra_vlans  # Preserve the existing behavior during the compliance refactor.
    merged: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for name, probe in existing_tool.items():  # Preserve the existing behavior during the compliance refactor.
        # Prefer freshly-built type/target (new source of truth). Fall back
        # to on-org values when the probe is not in ``new_probes``.
        template = new_probes.get(name, probe)  # Preserve the existing behavior during the compliance refactor.
        # Resolve target first because the ``type`` classification depends
        # on whether the target string carries an HTTP scheme.
        merged_target = template.get("target") or probe.get(
            "target"
        )  # Preserve the existing behavior during the compliance refactor.
        merged_probe: dict[str, Any] = {
            # Prefer explicit type on the new/existing body when present,
            # but reclassify by target-shape so a body inherited from a
            # pre-1023 push (``type: "application"`` + ``target: "host:500"``)
            # gets corrected to ``reachability`` on merge. Passing the
            # existing body's type as the ``role_type`` preserves overrides
            # for HTTP/S targets while still fixing reachability rows.
            "type": _probe_type_for_target(
                merged_target if isinstance(merged_target, str) else "",
                template.get("type") or probe.get("type"),
            ),
            "target": merged_target,
        }
        # Sync aggressiveness from the freshly-built set so demotions
        # propagate. ``_build_probe_set`` always emits an explicit value;
        # the None branch is defensive against a future refactor dropping
        # the key. Probes with no counterpart in ``new_probes`` (for example a
        # role dropped from the JSON) keep their prior value.
        aggressiveness = SyntheticProbeSettingApplier.merged_probe_aggressiveness(
            name, probe, new_probes
        )  # WHY: Centralize merge priority.
        if aggressiveness is not None:  # WHY: Preserve prior omission when no value exists anywhere.
            merged_probe["aggressiveness"] = aggressiveness  # WHY: Store only explicit or defaulted aggressiveness.
        merged[name] = merged_probe  # Preserve the existing behavior during the compliance refactor.
    return merged  # Preserve the existing behavior during the compliance refactor.


def _swap_probes(  # Preserve the existing behavior during the compliance refactor.
    new_probes: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return the freshly-built probe set unchanged.

    Why:
        Swap is the destructive path. The helper exists purely so the
        dispatch table in ``manage_org_synthetic_probes`` reads as a
        symmetric pair with ``_merge_probes``.

    Args:
        new_probes: Freshly-built probe set from ``_build_probe_set``.

    Returns:
        ``new_probes`` unchanged.
    """
    return new_probes  # Preserve the existing behavior during the compliance refactor.


def _collect_existing_probe_vlans(
    existing_tool: dict[str, dict[str, Any]],
) -> set[int]:  # Preserve the existing behavior during the compliance refactor.
    """Return the VLAN union from existing tool-authored probes."""
    all_vlans: set[int] = set()  # Track unique VLAN IDs across all existing probes.
    for (
        probe
    ) in existing_tool.values():  # Walk only tool-authored probes because foreign probes are preserved separately.
        for vid in probe.get("vlan_ids") or []:  # Accept absent VLAN lists as empty to preserve legacy prompts.
            if isinstance(vid, int):  # Ignore malformed VLAN values so the prompt stays read-only.
                all_vlans.add(vid)  # Store each valid VLAN once for the summary line.
    return all_vlans  # Return the union so the prompt can show operator context.


def _prompt_mode(
    existing_tool: dict[str, dict[str, Any]],
) -> str:  # Preserve the existing behavior during the compliance refactor.
    """Prompt the operator for merge versus swap."""
    all_vlans = _collect_existing_probe_vlans(existing_tool)  # Show the current VLAN surface before selection.
    print(
        f"  Existing tool-authored probes: {len(existing_tool)}"
    )  # Preserve the existing behavior during the compliance refactor.
    print(
        f"  VLAN union across existing probes: {sorted(all_vlans)}"
    )  # Preserve the existing behavior during the compliance refactor.
    while True:  # Preserve the existing behavior during the compliance refactor.
        choice = SyntheticProbePromptReader.read(  # Capture merge or swap selection through the EOF-safe helper.
            "  Choose action [merge/swap] (default: swap): ",
            "menu_206_merge_swap",
        ).lower()
        if choice == "":  # Preserve the existing behavior during the compliance refactor.
            return "swap"  # Preserve the default action from the original prompt.
        if choice in ("merge", "swap"):  # Preserve the existing behavior during the compliance refactor.
            return choice  # Return the exact accepted action string used by the caller.
        print("  Please answer 'merge' or 'swap'.")  # Keep the previous retry message.


def _summarise(  # Preserve the existing behavior during the compliance refactor.
    resulting_tool: dict[str, dict[str, Any]],
    existing_tool: dict[str, dict[str, Any]],
    resulting_foreign: dict[str, dict[str, Any]],
    original_foreign: dict[str, dict[str, Any]],
) -> str:
    """Build the human-readable confirmation summary string.

    Why:
        The operator must see counts of add/remove/update and the
        resulting total before authorising the PUT. Splitting the
        summary out keeps ``_prompt_confirm`` reusable. The
        ``resulting_foreign`` vs ``original_foreign`` split lets the
        operator see how many foreign probes we demoted from
        ``critical`` to make room for the 5 tool-owned criticals.

    Args:
        resulting_tool: The tool-authored probe set that will be written.
        existing_tool: The tool-authored probe set currently on the org.
        resulting_foreign: Foreign probes after stale-critical demotion.
        original_foreign: Foreign probes exactly as fetched (baseline).

    Returns:
        A multi-line string suitable for printing.
    """
    added = set(resulting_tool) - set(existing_tool)  # Preserve the existing behavior during the compliance refactor.
    removed = set(existing_tool) - set(resulting_tool)  # Preserve the existing behavior during the compliance refactor.
    updated = {
        name for name in set(resulting_tool) & set(existing_tool) if resulting_tool[name] != existing_tool[name]
    }  # Preserve the existing behavior during the compliance refactor.
    demoted_foreign = _count_critical_demotions(
        original_foreign, resulting_foreign
    )  # Preserve the existing behavior during the compliance refactor.
    total_after = len(resulting_tool) + len(
        resulting_foreign
    )  # Preserve the existing behavior during the compliance refactor.
    lines = [  # Preserve the existing behavior during the compliance refactor.
        f"  Probes to add:        {len(added)}",
        f"  Probes to remove:     {len(removed)}",
        f"  Probes to update:     {len(updated)}",
        f"  Foreign preserved:    {len(resulting_foreign)}",
        f"  Foreign demoted:      {demoted_foreign} (critical key removed)",
        f"  Resulting total:      {total_after}",
    ]
    return "\n".join(lines)  # Preserve the existing behavior during the compliance refactor.


def _count_critical_demotions(  # Preserve the existing behavior during the compliance refactor.
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> int:
    """Count probes whose aggressiveness changed from ``critical``.

    Why:
        Surface the exact number of foreign probes the operator is
        about to demote so the foreign-preservation relaxation is
        visible in the summary rather than silent.

    Args:
        before: Foreign probes as originally fetched.
        after: Foreign probes after ``_demote_stale_critical``.

    Returns:
        Number of shared names whose aggressiveness moved off ``critical``.
    """
    count = 0  # Preserve the existing behavior during the compliance refactor.
    for name, probe in before.items():  # Preserve the existing behavior during the compliance refactor.
        if (
            probe.get("aggressiveness") not in _PRIORITY_AGGRESSIVENESS
        ):  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        new_probe = after.get(name)  # Preserve the existing behavior during the compliance refactor.
        if new_probe is None:  # Preserve the existing behavior during the compliance refactor.
            continue  # Preserve the existing behavior during the compliance refactor.
        if (
            new_probe.get("aggressiveness") not in _PRIORITY_AGGRESSIVENESS
        ):  # Preserve the existing behavior during the compliance refactor.
            count += 1  # Preserve the existing behavior during the compliance refactor.
    return count  # Preserve the existing behavior during the compliance refactor.


def _demote_stale_critical(  # Preserve the existing behavior during the compliance refactor.
    foreign: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return ``foreign`` with any ``aggressiveness=critical`` demoted to ``auto``.

    Why:
        Mist caps priority probes (both ``critical`` and ``high``) at 5
        per effective config. The tool now claims all 5 slots for the
        curated Zscaler roles, so any foreign probe currently marked
        critical must be demoted or the PUT is rejected. We write the
        literal ``"auto"`` (Mist's own default for non-priority probes)
        rather than dropping the key: it is idempotent across re-runs
        and mirrors the value Mist itself emits on system-generated
        probes. This intentionally relaxes strict foreign preservation
        -- the change is surfaced in ``_summarise`` so the operator
        sees it before confirming.

    Args:
        foreign: Foreign probe map (probes without the ``zcc-`` prefix).

    Returns:
        A new dict where every probe previously at
        ``aggressiveness=critical`` is copied with aggressiveness set to
        ``"auto"``. All other fields survive untouched.
    """
    result: dict[str, dict[str, Any]] = {}  # Preserve the existing behavior during the compliance refactor.
    for name, probe in foreign.items():  # Preserve the existing behavior during the compliance refactor.
        if (
            isinstance(probe, dict) and probe.get("aggressiveness") in _PRIORITY_AGGRESSIVENESS
        ):  # Preserve the existing behavior during the compliance refactor.
            demoted = dict(probe)  # Preserve the existing behavior during the compliance refactor.
            demoted["aggressiveness"] = (
                _AUTO_AGGRESSIVENESS  # Preserve the existing behavior during the compliance refactor.
            )
            result[name] = demoted  # Preserve the existing behavior during the compliance refactor.
            logger.info(  # Preserve the existing behavior during the compliance refactor.
                "Demoting foreign critical probe %r (aggressiveness -> auto)",
                name,
            )
        else:
            result[name] = probe  # Preserve the existing behavior during the compliance refactor.
    return result  # Preserve the existing behavior during the compliance refactor.


def _prompt_confirm(summary: str) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Show ``summary`` and ask the operator to confirm.

    Why:
        Isolated so tests can patch ``input`` without touching the rest
        of the flow. Only exact ``y`` / ``yes`` (case-insensitive)
        answers proceed. Anything else aborts as safe-default.

    Args:
        summary: Multi-line pre-PUT summary from ``_summarise``.

    Returns:
        ``True`` if the operator confirmed, ``False`` otherwise.
    """
    print("  Change summary:")  # Preserve the existing behavior during the compliance refactor.
    print(summary)  # Preserve the existing behavior during the compliance refactor.
    answer = SyntheticProbePromptReader.read(  # Protect the destructive confirmation from EOF.
        "  Proceed with PUT to org settings? [y/N]: ",
        "menu_206_org_put_confirm",
    ).lower()
    return answer in ("y", "yes")  # Keep the original yes-only confirmation semantics.


def _compute_scheduled_probe_names(  # Preserve the existing behavior during the compliance refactor.
    combined_probes: dict[str, dict[str, Any]],
    extra_regular_names: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Return ``(critical_names, regular_names)`` for injection."""
    critical_names = _critical_scheduled_probe_names(combined_probes)  # Select priority probes first.
    regular_names = _regular_scheduled_probe_names(extra_regular_names, set(critical_names))  # Remove duplicates.
    return critical_names, regular_names  # Preserve the existing tuple shape.


def _critical_scheduled_probe_names(
    combined_probes: dict[str, dict[str, Any]],
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return sorted probe names that need priority scheduling."""
    return sorted(  # Sort for stable row ordering across repeated runs.
        name
        for name, probe in combined_probes.items()
        if isinstance(probe, dict) and probe.get("aggressiveness") in _PRIORITY_AGGRESSIVENESS
    )


def _regular_scheduled_probe_names(
    extra_regular_names: list[str] | None, critical_set: set[str]
) -> list[str]:  # Preserve the existing behavior during the compliance refactor.
    """Return sorted non-priority probe names that need scheduling."""
    names = extra_regular_names or []  # Treat a missing optional list as empty.
    selected = {name for name in names if isinstance(name, str) and name not in critical_set}  # Remove duplicates.
    return sorted(selected)  # Preserve deterministic output order.


def _clean_test_row(
    row: Any,
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return a cleaned row copy, or ``None`` if the row should be dropped."""
    if not isinstance(row, dict):  # Non-dict entries cannot become valid Mist test rows.
        return None  # Preserve the previous skip behavior.
    if _is_prior_zcc_test_row(row):  # Drop aggregate rows written by earlier tool versions.
        return None  # Preserve authoritative re-injection behavior.
    cleaned = dict(row)  # Copy the row so the fetched setting is not mutated.
    probes_field = cleaned.get("probes")  # Read the optional probes list.
    if isinstance(probes_field, list):  # Only list-shaped probes need cleanup.
        return _clean_test_row_probes(cleaned, probes_field)  # Strip stale ZCC probe names.
    return cleaned  # Preserve non-list probes fields unchanged.


def _is_prior_zcc_test_row(
    row: dict[str, Any],
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when a tests row is a prior ZCC aggregate row."""
    row_name = row.get("name")  # Read the optional row name.
    if not isinstance(row_name, str) or not row_name.startswith(_TOOL_NAME_PREFIX):  # Keep foreign rows.
        return False  # Preserve the row when it is not tool-authored.
    logger.info("Dropping legacy tool-authored tests[] row %r (aggregate-row migration)", row_name)  # Record drop.
    return True  # Drop the legacy aggregate row.


def _clean_test_row_probes(
    cleaned: dict[str, Any], probes_field: list[Any]
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Strip stale ZCC probe names from a copied tests row."""
    filtered = [probe for probe in probes_field if not _is_tool_probe_name(probe)]  # Keep only foreign probe names.
    if probes_field and not filtered:  # Drop rows that only held prior ZCC probe names.
        return None  # Preserve authoritative re-injection behavior.
    cleaned["probes"] = filtered  # Store the filtered foreign probe list.
    return cleaned  # Return the cleaned row to the caller.


def _is_tool_probe_name(probe: Any) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """Return True when a probe field value is a ZCC probe name."""
    return isinstance(probe, str) and probe.startswith(_TOOL_NAME_PREFIX)  # Match only string ZCC probe names.


def _filter_surviving_test_rows(
    existing_tests: list[dict[str, Any]],
) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Drop legacy tool-authored rows and strip stale ``zcc-*`` names.

    Why:
        Re-injection below is authoritative -- keeping stale ``zcc-*``
        entries would double-book probes in the eventual PUT body. The
        per-row predicate is delegated to ``_clean_test_row`` so this
        function stays a trivial fold.

    Args:
        existing_tests: The ``tests[]`` list read from the fetched
            setting (may be empty).

    Returns:
        A new list of cleaned row dicts (originals are not mutated).
    """
    surviving: list[dict[str, Any]] = []  # Preserve the existing behavior during the compliance refactor.
    for row in existing_tests:  # Preserve the existing behavior during the compliance refactor.
        cleaned = _clean_test_row(row)  # Preserve the existing behavior during the compliance refactor.
        if cleaned is not None:  # Preserve the existing behavior during the compliance refactor.
            surviving.append(cleaned)  # Preserve the existing behavior during the compliance refactor.
    return surviving  # Preserve the existing behavior during the compliance refactor.


def _first_vlan_template(
    surviving: list[dict[str, Any]],
) -> list[int] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return the first surviving row's ``vlan_ids`` (int-filtered), or ``None``.

    Why:
        Split out of ``_derive_test_row_template`` so each field's
        scanner stays under the CC gate. Non-int entries in ``vlan_ids``
        are dropped defensively -- Mist's schema is ints-only, but
        malformed operator-authored rows should not crash injection.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        A copied int-only list, or ``None`` if no surviving row carried
        a ``vlan_ids`` list.
    """
    for row in surviving:  # Preserve the existing behavior during the compliance refactor.
        row_vlans = row.get("vlan_ids")  # Preserve the existing behavior during the compliance refactor.
        if isinstance(row_vlans, list):  # Preserve the existing behavior during the compliance refactor.
            return [
                v for v in row_vlans if isinstance(v, int)
            ]  # Preserve the existing behavior during the compliance refactor.
    return None  # Preserve the existing behavior during the compliance refactor.


def _first_lan_template(
    surviving: list[dict[str, Any]],
) -> list[str] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return the first surviving row's ``lan_networks`` (str-filtered), or ``None``.

    Why:
        Peer of ``_first_vlan_template``. Non-str entries are dropped
        defensively -- Mist stores network refs as strings but again
        we do not want a malformed row to crash injection.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        A copied str-only list, or ``None`` if no surviving row carried
        a ``lan_networks`` list.
    """
    for row in surviving:  # Preserve the existing behavior during the compliance refactor.
        row_lans = row.get("lan_networks")  # Preserve the existing behavior during the compliance refactor.
        if isinstance(row_lans, list):  # Preserve the existing behavior during the compliance refactor.
            return [
                ln for ln in row_lans if isinstance(ln, str)
            ]  # Preserve the existing behavior during the compliance refactor.
    return None  # Preserve the existing behavior during the compliance refactor.


def _derive_test_row_template(  # Preserve the existing behavior during the compliance refactor.
    surviving: list[dict[str, Any]],
) -> tuple[list[int] | None, list[str] | None]:
    """Return the first surviving row's ``vlan_ids`` and ``lan_networks``.

    Why:
        Injected rows must inherit operator scoping from foreign rows
        so a targeted deployment (for example VLAN 42 only) does not silently
        widen when the tool adds new probes. The two fields are looked
        up independently so a mixed-shape ``tests[]`` list still yields
        a complete template.

    Args:
        surviving: Cleaned rows from ``_filter_surviving_test_rows``.

    Returns:
        Tuple ``(template_vlan_ids, template_lan_networks)`` -- either
        or both may be ``None`` if no surviving row supplied them.
    """
    return _first_vlan_template(surviving), _first_lan_template(
        surviving
    )  # Preserve the existing behavior during the compliance refactor.


def _merge_zcc_criticals_into_tests(  # Preserve the existing behavior during the compliance refactor.
    existing_tests: list[dict[str, Any]],
    combined_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
    extra_regular_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Emit one ``tests[]`` row per scheduled ZCC probe."""
    logger.info("Merging scheduled ZCC probes into synthetic tests")  # Record the schedule merge boundary.
    schedule = _compute_scheduled_probe_names(combined_probes, extra_regular_names)  # Select probes.
    critical_names, regular_names = schedule  # Name each scheduled group for existing order.
    surviving = _filter_surviving_test_rows(existing_tests)  # Preserve foreign rows after cleanup.
    scheduled_names = critical_names + regular_names  # Preserve the existing critical-before-regular order.
    if not scheduled_names:  # Return the preserved foreign rows when no ZCC probe needs scheduling.
        logger.debug("No scheduled ZCC probe rows were needed")  # Record the no-op schedule result.
        return surviving  # Preserve the existing no-op return value.
    result = SyntheticProbeSettingApplier.append_scheduled_rows(surviving, scheduled_names, vlan_ids)  # Append rows.
    logger.debug("Merged %d scheduled ZCC probes into tests", len(scheduled_names))  # Record scheduled count.
    return result  # Return the merged test rows.


def _apply(  # Preserve the existing behavior during the compliance refactor.
    mist_session: Any,
    org_id: str,
    setting: dict[str, Any],
    combined_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
) -> None:
    """PUT the updated setting block via ``updateOrgSettings``."""
    logger.info("Preparing org synthetic-probe update for org_id=%s", org_id)  # Record the write workflow start.
    body = SyntheticProbeSettingApplier.build_body(setting, combined_probes, vlan_ids)  # Build the PUT body.
    response = SyntheticProbeSettingApplier.write_setting(mist_session, org_id, body)  # Send one Mist setting update.
    SyntheticProbeSettingApplier.report_result(response, org_id, combined_probes)  # Print the existing result text.
    logger.debug("Completed org synthetic-probe update for org_id=%s", org_id)  # Record the write workflow end.


def _prompt_and_apply_site_overrides(  # Preserve the existing behavior during the compliance refactor.
    mist_session: Any,
    org_id: str,
    resulting_tool: dict[str, dict[str, Any]],
    sources: tuple[dict[str, Any], dict[str, Any]],
    warned_unmapped_codes: set[str],
) -> None:
    """Offer to push the tool-authored probe set into per-site settings.

    Why:
        Mist site settings can override org-wide ``custom_probes``. After
        a successful org PUT the operator often wants a subset of sites
        (for example those with unusual VLAN topology or higher SLE
        expectations) to carry the same probe set locally so
        site-specific probe/VLAN interactions are testable without
        touching org config. Displaying an indexed table (rather than
        asking for raw UUIDs) removes the copy/paste burden and the
        common "typo'd UUID" failure mode operators reported. A separate
        VLAN prompt is issued after site selection because sites picked
        for an override typically have a *different* VLAN topology than
        the org default -- reusing the org list would defeat the point
        of the override. Regional Samsung ELM probes are injected per-
        site based on each site's ``country_code`` so a site in Germany
        gets EMEA endpoints while a site in the US gets the Americas
        set. This whole flow is optional (default no) so unattended runs
        do not silently mutate site settings.

        1025-US2: the site list is also the natural anchor for the
        load-time ``country_code`` WARNING dedup path -- every site with
        an unmapped code is visible in one place, so a single
        ``_emit_load_time_country_code_warning`` call names every
        offender once instead of once per site. The ``warned_unmapped_codes``
        set is threaded in from ``manage_org_synthetic_probes`` so its
        lifetime is bounded by the invocation (FR-012).

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist org UUID -- required for ``listOrgSites`` so the
            index table shows only the sites the operator can actually
            target.
        resulting_tool: The tool-authored probe map just written to the
            org. Used as the source of truth (name/target/type/
            aggressiveness) to push into each chosen site. Each probe's
            ``vlan_ids`` is replaced with the freshly-prompted list.
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``.
            Passed through to ``_apply_to_site`` so per-region Samsung
            ELM probes can be built from the same source-of-truth
            catalogue.
        warned_unmapped_codes: Load-time dedup set constructed in
            ``manage_org_synthetic_probes`` (1025-US2). Mutated in place
            by ``_emit_load_time_country_code_warning`` so a subsequent
            call in the same invocation would suppress duplicates.
    """
    if not resulting_tool:  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    answer = SyntheticProbePromptReader.read(  # Capture optional site override selection through safe input.
        "  Configure site-level overrides with these same probes? [y/N]: ",
        "menu_206_site_override_offer",
    ).lower()
    if answer not in ("y", "yes"):  # Preserve the existing behavior during the compliance refactor.
        logger.info(
            "Operator declined site overrides"
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    sites = _list_org_sites(mist_session, org_id)  # Preserve the existing behavior during the compliance refactor.
    if not sites:  # Preserve the existing behavior during the compliance refactor.
        print(
            "  No sites found in this org -- skipping site overrides."
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    # NOTE(1025-US2): load-time country_code WARNING emission fires exactly
    # once here, immediately after the site list is materialised and
    # BEFORE per-site region resolution begins in ``_apply_to_site`` ->
    # ``_build_region_probes``. Emitting here (rather than per-site in the
    # resolver) collapses N warnings into 1 (or K, one per distinct
    # unmapped code) and satisfies FR-004 / FR-010 / SC-002.
    logger.info(  # Constitution VII: BEFORE the load-time country_code diff
        "computing load-time country_code unmapped set for %d sites",
        len(sites),
    )
    _emit_load_time_country_code_warning(  # single call site per invocation (FR-012)
        _compute_unmapped_country_codes(  # inner: set difference over frozen universes
            sites,  # the just-loaded site list
            _COUNTRY_CODE_TO_REGION,  # T020-extended region map
            _COUNTRY_CODE_INTENTIONAL_GAPS,  # T021 gap set (Antarctica and so on)
        ),
        warned_unmapped_codes,  # dedup state -- mutated in place
    )
    logger.debug(  # Constitution VII: AFTER the load-time emission
        "load-time country_code check complete; warned_unmapped_codes=%s",
        len(warned_unmapped_codes),
    )
    picked_sites = _prompt_site_indexes(sites)  # Preserve the existing behavior during the compliance refactor.
    if not picked_sites:  # Preserve the existing behavior during the compliance refactor.
        print(
            "  No valid site indexes entered -- skipping site overrides."
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    # Site overrides commonly target sites with distinct VLAN topology, so
    # re-prompt rather than silently reusing the org-scope list.
    print(
        "  Enter the VLAN ids to apply to the selected sites' tests[] rows."
    )  # Preserve the existing behavior during the compliance refactor.
    site_vlan_ids = _prompt_vlan_list()  # Preserve the existing behavior during the compliance refactor.
    for site in picked_sites:  # Preserve the existing behavior during the compliance refactor.
        _apply_to_site(
            mist_session, site, resulting_tool, site_vlan_ids, sources
        )  # Preserve the existing behavior during the compliance refactor.


def _list_org_sites(
    mist_session: Any, org_id: str
) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Return every site in ``org_id`` as a paginated list of dicts.

    Why:
        The indexed site picker needs the full site list up-front so the
        operator can see every option in one screen. Isolating the fetch
        keeps ``_prompt_and_apply_site_overrides`` unit-testable via a
        single patch point, and mirrors the pagination pattern used in
        ``APICoreFetchUtils.all_sites_with_limit``. Errors are logged
        and surfaced as an empty list so callers degrade gracefully
        (skipping the site flow) rather than aborting the whole run.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        org_id: Mist org UUID.

    Returns:
        List of site dicts (``id``, ``name`` at minimum). Empty list on
        API failure or when the org has no sites.
    """
    try:
        response = _mist_orgs_sites.listOrgSites(
            mist_session, org_id
        )  # Preserve the existing behavior during the compliance refactor.
        sites = mistapi.get_all(
            response=response, mist_session=mist_session
        )  # Preserve the existing behavior during the compliance refactor.
    except Exception as err:  # surface any transport error.
        logging.error(
            "listOrgSites(%s) failed: %s", org_id, err
        )  # Preserve the existing behavior during the compliance refactor.
        print(
            f"  listOrgSites failed ({err}); skipping site overrides."
        )  # Preserve the existing behavior during the compliance refactor.
        return []  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(sites, list):  # Preserve the existing behavior during the compliance refactor.
        return []  # Preserve the existing behavior during the compliance refactor.
    return [
        s for s in sites if isinstance(s, dict) and s.get("id")
    ]  # Preserve the existing behavior during the compliance refactor.


def _sort_sites_for_picker(
    sites: list[dict[str, Any]],
) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Return ``sites`` sorted for the interactive index picker.

    Why:
        Extracted so the sort key is unit-testable in isolation and so
        the parent picker's cyclomatic complexity stays under the CI
        gate. Unnamed sites sink to the end (secondary key = 1) so the
        named entries operators actually think about lead the list;
        name comparison is case-folded so ``ACME`` and ``acme`` sort
        together. Id is the final tie-break to keep the ordering stable
        across invocations.

    Args:
        sites: Site dicts as returned by ``_list_org_sites``.

    Returns:
        A new list of site dicts sorted by (named-first, name-casefold,
        id). The input is not mutated.
    """
    sorted_sites = sorted(  # Build a stable display order without mutating the API result.
        sites,
        key=lambda s: (
            0 if (s.get("name") or "").strip() else 1,
            (s.get("name") or "").casefold(),
            s.get("id") or "",
        ),
    )
    logger.debug("Sorted %d site(s) for the menu 206 picker", len(sorted_sites))  # Record picker list size.
    return sorted_sites  # Return the sorted copy for the interactive picker.


def _pick_site_by_index(  # Preserve the existing behavior during the compliance refactor.
    idx: int,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Add ``sorted_sites[idx-1]`` to ``picked_by_id`` if the index is in range.

    Why:
        The bounds-check + id-guard + setdefault triad appeared three
        times in ``_prompt_site_indexes`` (single-int branch, range
        branch, ``all`` branch was similar). Deduplicating it into one
        helper keeps the picker's dispatch small and makes the "silently
        ignore garbage" behaviour uniform across all three input shapes.

    Args:
        idx: 1-based index into ``sorted_sites`` as typed by the operator.
        sorted_sites: The sorted site view (from ``_sort_sites_for_picker``).
        picked_by_id: Mutated in place -- new picks are added via
            ``setdefault`` so earlier entries win on duplicate ids and
            operator input order is preserved.
    """
    if idx < 1 or idx > len(sorted_sites):  # Preserve the existing behavior during the compliance refactor.
        logger.warning(
            "Ignoring out-of-range site index: %d", idx
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    candidate = sorted_sites[idx - 1]  # Preserve the existing behavior during the compliance refactor.
    site_id = candidate.get("id")  # Preserve the existing behavior during the compliance refactor.
    if isinstance(site_id, str) and site_id:  # Preserve the existing behavior during the compliance refactor.
        picked_by_id.setdefault(site_id, candidate)  # Preserve the existing behavior during the compliance refactor.


def _expand_range_token(  # Preserve the existing behavior during the compliance refactor.
    part: str,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Parse a ``lo-hi`` range shorthand token and add each in-range index.

    Why:
        Isolates the two-int parse plus reversed-range guard so the
        parent picker stays under the CC gate. The parse uses ``part[1:]``
        so a leading ``-`` is treated as a negative int -- matching
        ``_validate_vlan_input``'s convention: the value will just fail
        the in-range check inside ``_pick_site_by_index``.

    Args:
        part: The raw comma-separated token (already stripped) that
            contains a ``-`` after the first character.
        sorted_sites: Sorted site view for the range to index into.
        picked_by_id: Mutated in place (see ``_pick_site_by_index``).
    """
    lo_raw, _, hi_raw = part[1:].partition("-")  # Preserve the existing behavior during the compliance refactor.
    lo_raw = (part[0] + lo_raw).strip()  # Preserve the existing behavior during the compliance refactor.
    hi_raw = hi_raw.strip()  # Preserve the existing behavior during the compliance refactor.
    try:
        lo = int(lo_raw)  # Preserve the existing behavior during the compliance refactor.
        hi = int(hi_raw)  # Preserve the existing behavior during the compliance refactor.
    except ValueError:  # Preserve the existing behavior during the compliance refactor.
        logging.warning(
            "Ignoring unparseable site index range token: %r", part
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    if lo > hi:  # Preserve the existing behavior during the compliance refactor.
        logger.warning(
            "Ignoring reversed site index range: %r", part
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    for idx in range(lo, hi + 1):  # Preserve the existing behavior during the compliance refactor.
        _pick_site_by_index(
            idx, sorted_sites, picked_by_id
        )  # Preserve the existing behavior during the compliance refactor.


def _apply_picker_token(  # Preserve the existing behavior during the compliance refactor.
    part: str,
    sorted_sites: list[dict[str, Any]],
    picked_by_id: dict[str, dict[str, Any]],
) -> None:
    """Route one operator-supplied token to the correct index-picker branch.

    Why:
        Consolidates the ``all`` / range / single-int dispatch so the
        parent function's body reduces to ``for part in parts:
        _apply_picker_token(...)``. Keeps all three token shapes in one
        auditable place and drops the picker's CC well under the gate.

    Args:
        part: Stripped, non-empty token from the comma-split raw input.
        sorted_sites: Sorted site view for indexing.
        picked_by_id: Mutated in place with any successful picks.
    """
    if part.lower() == "all":  # Preserve the existing behavior during the compliance refactor.
        for candidate in sorted_sites:  # Preserve the existing behavior during the compliance refactor.
            site_id = candidate.get("id")  # Preserve the existing behavior during the compliance refactor.
            if isinstance(site_id, str) and site_id:  # Preserve the existing behavior during the compliance refactor.
                picked_by_id.setdefault(
                    site_id, candidate
                )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    # Range shorthand like "3-6". Leading '-' is treated as a negative int
    # (out of range anyway), matching _validate_vlan_input's convention.
    if "-" in part[1:]:  # Preserve the existing behavior during the compliance refactor.
        _expand_range_token(
            part, sorted_sites, picked_by_id
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    try:
        idx = int(part)  # Preserve the existing behavior during the compliance refactor.
    except ValueError:  # Preserve the existing behavior during the compliance refactor.
        logging.warning(
            "Ignoring non-numeric site index token: %r", part
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    _pick_site_by_index(
        idx, sorted_sites, picked_by_id
    )  # Preserve the existing behavior during the compliance refactor.


def _prompt_site_indexes(
    sites: list[dict[str, Any]],
) -> list[dict[str, Any]]:  # Preserve the existing behavior during the compliance refactor.
    """Display an indexed site table and return the site dicts the operator picks.

    Why:
        UUID entry proved error-prone in the field (operators pasted
        trailing whitespace, wrong-org UUIDs, or truncated ids). An
        indexed prompt eliminates that class of typo entirely and lets
        the operator eyeball site names before committing. The list is
        sorted by human-readable site name (case-insensitive) so the
        picker matches how operators think about their fleet. Unnamed
        sites sink to the bottom. Full site dicts are returned (not just
        ids) so downstream code can read per-site fields like
        ``country_code`` without a second API round-trip. Accepts range
        shorthand (``3-6`` expands to ``3,4,5,6``) and a literal
        ``all`` token (case-insensitive) that selects every listed site
        -- operators paste condensed lists and frequently want to push
        the override org-wide. Kept in its own helper so tests can
        patch ``input`` for this stage independently of the earlier
        y/N prompt.

    Args:
        sites: List of site dicts as returned by ``_list_org_sites``. The
            function sorts a local copy by name before display, so the
            caller's ordering is irrelevant.

    Returns:
        Deduplicated list of the full site dicts corresponding to valid
        1-based indexes (into the *sorted* view) supplied by the
        operator, preserving operator input order. Empty list if the
        operator supplied nothing or every entry was out of range /
        non-numeric.
    """
    print("  Available sites:")  # Preserve the existing behavior during the compliance refactor.
    sorted_sites = _sort_sites_for_picker(sites)  # Preserve the existing behavior during the compliance refactor.
    width = len(str(len(sorted_sites)))  # Preserve the existing behavior during the compliance refactor.
    for idx, site in enumerate(sorted_sites, start=1):  # Preserve the existing behavior during the compliance refactor.
        name = site.get("name") or "(unnamed)"  # Preserve the existing behavior during the compliance refactor.
        site_id = site.get("id", "")  # Preserve the existing behavior during the compliance refactor.
        print(
            f"    [{idx:>{width}}] {name}  ({site_id})"
        )  # Preserve the existing behavior during the compliance refactor.
    raw = SyntheticProbePromptReader.read(  # Capture site index selection through the EOF-safe helper.
        "  Enter comma-separated site indexes (ranges ok e.g. 3-6, 'all' for every site), "
        "or leave blank to cancel: ",
        "menu_206_site_indexes",
    )
    parts = [item.strip() for item in raw.split(",") if item.strip()]  # Preserve comma parsing and blank filtering.
    picked_by_id: dict[str, dict[str, Any]] = {}  # Keep selection order while deduplicating by site id.
    for part in parts:  # Preserve the existing behavior during the compliance refactor.
        _apply_picker_token(part, sorted_sites, picked_by_id)  # Apply ranges, single numbers, and "all".
    return list(picked_by_id.values())  # Return the selected site dictionaries in operator order.


def _put_site_setting(
    mist_session: Any, site_id: str, body: dict[str, Any]
) -> bool:  # Preserve the existing behavior during the compliance refactor.
    """PUT ``body`` to ``updateSiteSettings`` and log/print any failure.

    Why:
        Extracted from :func:`_apply_to_site` so the outer function stays
        under Radon CC>10. Collapses the transport-error branch and the
        non-2xx status branch into one boolean so the caller has a single
        gate before the success-line print.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site_id: Site UUID string.
        body: Full site-setting payload to PUT.

    Returns:
        ``True`` when the API returned a 2xx status (or no ``status_code``
        attribute at all — same tolerance the inline code had); ``False``
        on any exception or non-2xx status. Errors are already printed and
        logged before returning.
    """
    try:
        put_response = _mist_site_setting.updateSiteSettings(
            mist_session, site_id, body
        )  # Preserve the existing behavior during the compliance refactor.
    except Exception as err:  # surface any transport error.
        print(
            f"  Site {site_id}: updateSiteSettings failed ({err}); skipping."
        )  # Preserve the existing behavior during the compliance refactor.
        logging.error(
            "updateSiteSettings(%s) failed: %s", site_id, err
        )  # Preserve the existing behavior during the compliance refactor.
        return False  # Preserve the existing behavior during the compliance refactor.
    status = getattr(
        put_response, "status_code", None
    )  # Preserve the existing behavior during the compliance refactor.
    if status is not None and not 200 <= status < 300:  # Preserve the existing behavior during the compliance refactor.
        print(
            f"  Site {site_id}: updateSiteSettings HTTP {status}"
        )  # Preserve the existing behavior during the compliance refactor.
        logger.error(
            "updateSiteSettings(%s) HTTP %s", site_id, status
        )  # Preserve the existing behavior during the compliance refactor.
        return False  # Preserve the existing behavior during the compliance refactor.
    return True  # Preserve the existing behavior during the compliance refactor.


def _fetch_site_setting(
    mist_session: Any, site_id: str
) -> dict[str, Any] | None:  # Preserve the existing behavior during the compliance refactor.
    """Return the parsed site-setting dict, or ``None`` on transport failure.

    Why:
        Extracted from :func:`_apply_to_site` so the outer function stays
        under Radon CC>10. Prints and logs the same operator-visible
        message the inline handler used, then returns ``None`` so the
        caller can skip the site without another exception branch.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site_id: Site UUID string, already validated non-empty by caller.

    Returns:
        The ``response.data`` dict (empty dict when the API returned a
        non-dict payload) or ``None`` on any transport error.
    """
    try:
        response = _mist_site_setting.getSiteSetting(
            mist_session, site_id
        )  # Preserve the existing behavior during the compliance refactor.
    except Exception as err:  # surface any transport error.
        print(
            f"  Site {site_id}: getSiteSetting failed ({err}); skipping."
        )  # Preserve the existing behavior during the compliance refactor.
        logging.error(
            "getSiteSetting(%s) failed: %s", site_id, err
        )  # Preserve the existing behavior during the compliance refactor.
        return None  # Preserve the existing behavior during the compliance refactor.
    data = getattr(response, "data", None)  # Preserve the existing behavior during the compliance refactor.
    return data if isinstance(data, dict) else {}  # Preserve the existing behavior during the compliance refactor.


def _apply_to_site(  # Preserve the existing behavior during the compliance refactor.
    mist_session: Any,
    site: dict[str, Any],
    tool_probes: dict[str, dict[str, Any]],
    vlan_ids: list[int],
    sources: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    """PUT ``tool_probes`` plus regional Samsung ELM probes into the site.

    Why:
        Site-level custom_probes lives at ``synthetic_test.custom_probes``
        in the site setting, mirroring the org shape. This helper reuses
        the same partition/demote logic as the org path so Mist's
        5-probe priority cap (which counts both ``critical`` and
        ``high``) is respected on the effective (org + site) config:
        any pre-existing foreign probe with
        ``aggressiveness=critical`` has that key stripped, every
        ``zcc-`` probe is authoritatively replaced, and
        ``synthetic_test.tests[]`` gets regenerated for critical
        probes so the site's schedule actually runs them. On top of the
        org-scope tool set, the region-scoped Samsung ELM probes for the
        site's ``country_code`` are injected here (only) so a site in
        Germany gets EMEA ELM endpoints while a site in the US gets the
        Americas set -- these regional roles never appear at org scope
        because pushing every region's endpoints everywhere is wasteful.
        Additionally, the ``tunnel_zen`` role's ~190 probe definitions
        (already emitted at org scope) are selectively SCHEDULED here per
        site: the geodesically-nearest 1-2 ZEN locations for the site's
        country/latlng get explicit ``tests[]`` rows so operators see
        reachability signal only for ZENs their users would actually route
        to, not the entire global ZEN mesh.

    Args:
        mist_session: Authenticated ``mistapi`` session.
        site: The full site dict from ``_list_org_sites`` -- ``id`` is
            required for the PUT, ``country_code`` (may be absent) drives
            regional ELM probe selection.
        tool_probes: Tool-authored probe set to write.
        vlan_ids: VLAN ids to attach to each generated test row.
        sources: The ``(probes, cenr)`` tuple from ``_load_probe_sources``,
            passed to ``_build_region_probes`` so region roles are read
            from the same source-of-truth catalogue.
    """
    site_id = site.get("id")  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(site_id, str) or not site_id:  # Preserve the existing behavior during the compliance refactor.
        logger.error(
            "Site override skipped: site dict missing id (%r)", site
        )  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    country_code = site.get("country_code")  # Preserve the existing behavior during the compliance refactor.
    logger.info(  # Preserve the existing behavior during the compliance refactor.
        "Applying site override to site_id=%s country_code=%r",
        site_id,
        country_code,
    )
    region_probes = _build_region_probes(
        sources, country_code
    )  # Preserve the existing behavior during the compliance refactor.
    zen_probe_names = _zen_probe_names_for_cities(  # Preserve the existing behavior during the compliance refactor.
        _resolve_zen_cities_for_site(site, sources[1]),
        sources[1],
    )
    site_setting = _fetch_site_setting(
        mist_session, site_id
    )  # Preserve the existing behavior during the compliance refactor.
    if site_setting is None:  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    existing_probes = _detect_existing(site_setting)  # Preserve the existing behavior during the compliance refactor.
    _, foreign = _partition_tool_authored(
        existing_probes
    )  # Preserve the existing behavior during the compliance refactor.
    foreign_demoted = _demote_stale_critical(foreign)  # Preserve the existing behavior during the compliance refactor.
    combined = {
        **foreign_demoted,
        **tool_probes,
        **region_probes,
    }  # Preserve the existing behavior during the compliance refactor.

    body: dict[str, Any] = (
        json.loads(json.dumps(site_setting)) if site_setting else {}
    )  # Preserve the existing behavior during the compliance refactor.
    synthetic = body.get("synthetic_test")  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(synthetic, dict):  # Preserve the existing behavior during the compliance refactor.
        synthetic = {}  # Preserve the existing behavior during the compliance refactor.
        body["synthetic_test"] = synthetic  # Preserve the existing behavior during the compliance refactor.
    synthetic["custom_probes"] = combined  # Preserve the existing behavior during the compliance refactor.
    existing_tests = synthetic.get("tests")  # Preserve the existing behavior during the compliance refactor.
    if not isinstance(existing_tests, list):  # Preserve the existing behavior during the compliance refactor.
        existing_tests = []  # Preserve the existing behavior during the compliance refactor.
    # Region and ZEN probes are auto-priority, so the default critical-only
    # filter would not schedule them. Pass their names explicitly so each
    # gets a tests[] row and actually runs.
    synthetic["tests"] = (
        _merge_zcc_criticals_into_tests(  # Preserve the existing behavior during the compliance refactor.
            existing_tests,
            combined,
            vlan_ids,
            extra_regular_names=[*region_probes.keys(), *zen_probe_names],
        )
    )

    logger.debug(  # Preserve the existing behavior during the compliance refactor.
        "Calling updateSiteSettings(site_id=%s, probe_count=%d)",
        site_id,
        len(combined),
    )
    if not _put_site_setting(
        mist_session, site_id, body
    ):  # Preserve the existing behavior during the compliance refactor.
        return  # Preserve the existing behavior during the compliance refactor.
    print(  # Preserve the existing behavior during the compliance refactor.
        f"  Site {site_id}: override applied "
        f"({len(tool_probes)} tool-authored + {len(region_probes)} regional "
        f"+ {len(zen_probe_names)} ZEN scheduled "
        f"+ {len(foreign_demoted)} preserved)"
    )
