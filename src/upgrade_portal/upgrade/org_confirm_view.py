"""Build safe details for the confirmation page of a multi-site plan.

Why:
    Issue #3222. The page showed aggregate counts but hid the selected sites,
    the rollout controls, and the child jobs. This view converts the durable
    plan into plain labels before the template paints the destructive action.
"""

from __future__ import annotations  # Keep modern annotations independent from the import order.

import logging  # Record each confirmation-view transformation.
from collections.abc import Mapping, Sequence  # Describe durable records without concrete containers.
from typing import Any, ClassVar  # The stored plan holds JSON values of mixed types.

logger = logging.getLogger(__name__)  # Keep the records of this view under one module name.


class OrgConfirmView:
    """Build the sites, options, families, and child jobs for confirmation."""

    FAMILY_LABELS: ClassVar[dict[str, str]] = {  # Use the short operator words from the acceptance criteria.
        "ap": "AP",  # The Mist organization route upgrades access points.
        "switch": "switch",  # The route for a site upgrades switches.
        "gateway": "gateway",  # The route for a site upgrades Junos gateways.
        "ssr": "gateway",  # The organization SSR route is also a gateway route.
    }
    STRATEGY_LABELS: ClassVar[dict[str, str]] = {  # Replace storage words with the options-page labels.
        "canary": "Canary",  # The cloud upgrades increasing percentages.
        "big_bang": "Big bang",  # The cloud starts the selected targets together.
        "rrm": "RRM",  # The cloud uses radio batches that follow the access point layout.
        "serial": "Serial",  # The cloud upgrades targets one at a time.
    }
    ROUTE_LABELS: ClassVar[dict[str, str]] = {  # Name each child route without exposing an SDK symbol.
        "upgradeOrgDevices": "Organization AP upgrade",  # One organization child carries all selected APs.
        "upgradeSiteDevices": "Site device upgrade",  # One site child carries switches or Junos gateways.
        "upgradeOrgSsrs": "Organization gateway upgrade",  # One organization child carries SSR gateways.
    }
    VERSION_FIELDS: ClassVar[dict[str, str]] = {  # Map each durable family to its confirmed version field.
        "ap": "version_ap",  # Access points use their own target version.
        "switch": "version_switch",  # Switches use the Junos target version.
        "gateway": "version_gateway",  # Gateways use the Junos target version.
        "ssr": "version_gateway",  # SSR gateways share the gateway control.
    }

    @classmethod
    def build(
        cls,
        rows: Sequence[Mapping[str, Any]],
        options: Mapping[str, Any],
        operation: Mapping[str, Any] | None,
        families: Sequence[str],
    ) -> dict[str, Any]:
        """Return every confirmation section from trusted server-side values."""
        logger.info("Build the multi-site confirmation details")  # Log before the page transformation.
        children = cls._children(operation)  # Read only valid child records from the durable plan.
        view = {  # Keep the four page sections under one template value.
            "sites": cls._sites(rows),  # Name each selected site in its approved order.
            "families": cls._families(options, families),  # Name each family and its target version.
            "options": cls._options(options, families),  # Name each base rollout choice.
            "children": cls._child_rows(children),  # Name every child job that the confirmation will send.
        }
        logger.debug("The confirmation details hold %s child job(s)", len(view["children"]))  # Log the plan size.
        return view  # The template receives no raw operation record.

    @staticmethod
    def _sites(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Return the selected site names and their inventory counts."""
        return [  # Preserve the approved selection order.
            {  # The template needs only the operator-safe site values.
                "name": str(row.get("name") or row.get("site_id") or "Unknown site"),  # Never show a blank site.
                "device_count": int(row.get("device_count", 0)),  # Keep the inventory count beside the name.
            }
            for row in rows  # Build one visible row for each selected site.
        ]

    @classmethod
    def _families(cls, options: Mapping[str, Any], families: Sequence[str]) -> list[dict[str, str]]:
        """Return each planned device family with its target version."""
        ordered = cls._ordered_families(options, families)  # Follow the order of the options page.
        return [  # Build one visible row for each planned family.
            {  # Keep the stored family word out of the template.
                "label": cls.FAMILY_LABELS.get(family, family),  # Use a known plain label when one exists.
                "version": cls._version(options, family),  # Name the exact target build.
            }
            for family in ordered  # Preserve the deterministic family order.
        ]

    @classmethod
    def _ordered_families(cls, options: Mapping[str, Any], families: Sequence[str]) -> list[str]:
        """Return planned families in the order of the options page."""
        planned = {str(family) for family in families if family}  # Remove duplicates from durable children.
        selected = [str(family) for family in options.get("selected_types", ())]  # Read the checked order.
        if planned:  # A durable plan is the authority for the child families.
            return [family for family in selected if family in planned] + sorted(planned - set(selected))
        return [family for family in selected if options.get(cls.VERSION_FIELDS.get(family, ""))]  # Legacy plan.

    @classmethod
    def _version(cls, options: Mapping[str, Any], family: str) -> str:
        """Return the confirmed target version of one family."""
        field = cls.VERSION_FIELDS.get(family, "")  # Find the form field that belongs to the family.
        if options.get("stable_version") is True and family in {"switch", "gateway", "ssr"}:  # Cloud choice.
            return "Vendor stable build"  # State that the cloud, not the operator, selects the exact build.
        return str(options.get(field) or "Not recorded")  # An older record can hold no family version.

    @classmethod
    def _options(cls, options: Mapping[str, Any], families: Sequence[str]) -> list[dict[str, str]]:
        """Return the base rollout choices that every operator must review."""
        strategy = str(options.get("strategy") or "canary")  # Read the stored strategy word.
        rows = [{"label": "Strategy", "text": cls.STRATEGY_LABELS.get(strategy, strategy)}]  # First choice.
        if strategy == "canary":  # Canary plans carry phase percentages.
            rows.append({"label": "Canary phases", "text": cls._percent_list(options.get("canary_phases"))})
        if strategy != "big_bang":  # Big-bang plans send no percentage failure limit.
            limit = str(options.get("max_failure_percentage", "Not recorded"))  # Read the stored percentage.
            rows.append({"label": "Maximum failure percentage", "text": f"{limit}%"})  # State the unit.
        if {str(family) for family in families} & {"switch", "gateway", "ssr"}:  # Junos choices apply.
            rows.extend(cls._junos_options(options))  # Name the reboot and file action choices.
        rows.append({"label": "Force the firmware write", "text": cls._yes_no(options.get("force", False))})
        return rows  # The template paints the choices in this order.

    @classmethod
    def _junos_options(cls, options: Mapping[str, Any]) -> list[dict[str, str]]:
        """Return the two choices that apply to switches and gateways."""
        return [  # Keep the order of the options page.
            {"label": "Reboot after the firmware write", "text": cls._yes_no(options.get("reboot", True))},
            {"label": "Complete the Junos file action", "text": cls._yes_no(options.get("junos_file_action", True))},
        ]

    @staticmethod
    def _yes_no(value: object) -> str:
        """Return a plain yes or no label for one stored boolean."""
        return "Yes" if value is True else "No"  # Never expose Python boolean words to the operator.

    @staticmethod
    def _percent_list(value: object) -> str:
        """Return a comma-separated list of phase percentages."""
        text = str(value or "").strip()  # The form view already joins a stored list with commas.
        parts = [part.strip() for part in text.split(",") if part.strip()]  # Remove empty phase entries.
        return ", ".join(f"{part}%" for part in parts) if parts else "Not recorded"  # State each unit.

    @staticmethod
    def _children(operation: Mapping[str, Any] | None) -> tuple[Mapping[str, Any], ...]:
        """Return valid child records from the durable operation."""
        entries = operation.get("children", ()) if operation is not None else ()  # Read no browser data.
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):  # Reject damaged data.
            return ()  # A damaged child list makes no display promise.
        return tuple(child for child in entries if isinstance(child, Mapping))  # Keep valid records only.

    @classmethod
    def _child_rows(cls, children: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Return the operator-safe child plan rows."""
        return [cls._child_row(child) for child in children]  # Keep the durable child order.

    @classmethod
    def _child_row(cls, child: Mapping[str, Any]) -> dict[str, Any]:
        """Return one safe row for a child in the plan."""
        family = str(child.get("device_family") or "unknown")  # Read the durable device family.
        route = str(child.get("route") or "Unknown route")  # Read the sanctioned cloud route.
        targets = child.get("target_ids", ())  # Read the explicit target identifiers.
        target_list = isinstance(targets, Sequence) and not isinstance(targets, (str, bytes))  # Validate the list.
        count = len(targets) if target_list else 0  # Count only a real target list.
        return {  # The table needs no child identifier or raw body.
            "site": str(child.get("site_name") or child.get("site_id") or "Selected sites"),  # Name the scope.
            "family": cls.FAMILY_LABELS.get(family, family),  # Use AP, switch, or gateway where known.
            "route": cls.ROUTE_LABELS.get(route, route),  # Use a plain route label where known.
            "target_count": count,  # State how many devices this child can change.
        }
