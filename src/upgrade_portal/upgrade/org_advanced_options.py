"""Read, keep, and check the advanced controls of the multi-site upgrade page.

Why:
    Issue #3383. The single-site page offers eleven advanced controls that the
    multi-site page did not paint. An operator who planned several sites lost
    the canary counts, the peer download, the radio batch controls, the stable
    build, and the router release train. This module gives the multi-site
    route one reader, one form view, two plan rules, and one summary of the
    typed confirmation page for those controls. The shared option mapper still
    checks each value, so both pages keep one rule for each control.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each read and each rule without a value from the browser.
from collections.abc import Iterable, Mapping  # Describe the request and the device views without concrete types.
from typing import Any, ClassVar  # The request and the stored record hold values of mixed types.

from src.firmware.org_upgrade_body import (  # The count limit and the field names of the organization body.
    FAILURE_COUNT_HIGHEST,
    PEER_SIZE_FIELDS,
    RADIO_BATCH_FIELDS,
)
from src.firmware.upgrade_service import (  # The shared plan words.
    DEVICE_TYPE_AP,
    VERSION_STABLE,
    GatewayFamily,
    UpgradeOptions,
)
from src.upgrade_portal.upgrade.options import ORG_OPTION_HELP, BadOptionError, advanced_option_values  # Labels.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

# The eleven advanced fields, in the order that the multi-site page paints them.
ADVANCED_FIELDS = ("max_failures", "stable_version", "enable_p2p", *PEER_SIZE_FIELDS, *RADIO_BATCH_FIELDS, "channel")
_CHOICE_FIELDS = ("stable_version", "enable_p2p")  # The two yes or no radio groups of the page.
_TEXT_FIELDS = tuple(name for name in ADVANCED_FIELDS if name not in _CHOICE_FIELDS)  # The other nine controls.
_YES_WORDS = frozenset({"true", "yes", "on", "1"})  # The words that a radio group or a JSON client sends for yes.


class OrgAdvancedOptions:
    """Carry the advanced controls from the page to the plan and back.

    Why:
        The route keeps one flat option record in the signed session. The
        shared option mapper reads the same flat names, so this class copies
        each value without a change. The mapper then applies each rule, and
        the route names the multi-site control in each refusal.
    """

    @staticmethod
    def read(source: Mapping[str, Any]) -> dict[str, Any]:
        """Return each advanced value that the request sets.

        Args:
            source: The JSON object or the form collection of the request.

        Returns:
            The advanced values, keyed by the cloud field name. An empty
            control is absent, so the cloud default applies.
        """
        logger.info("Read the advanced controls of the multi-site request")  # Log before the read.
        values: dict[str, Any] = {}  # Only the controls that the operator set.
        for name in ADVANCED_FIELDS:  # Keep the page order.
            value = source.get(name)  # A form sends text, and a JSON client can send a list or a boolean.
            if isinstance(value, str):  # A text control can hold only spaces.
                value = value.strip()  # Drop the spaces around the value.
            if value is not None and value != "":  # An empty control keeps the cloud default.
                values[name] = value  # The shared mapper checks the value later.
        logger.debug("The multi-site request sets %s advanced control(s)", len(values))  # Log after the read.
        return values  # The caller adds these values to the flat option record.

    @staticmethod
    def site_fields(options: Mapping[str, Any]) -> dict[str, Any]:
        """Return each advanced value that the flat option record holds.

        Why:
            The shared mapper validates each site through the single-site body.
            That body must carry each advanced value, or the plan loses the
            choice with no refusal at all.

        Args:
            options: The flat option record of the multi-site request.

        Returns:
            The advanced values for the single-site body.
        """
        return {name: options[name] for name in ADVANCED_FIELDS if name in options}  # Copy only the set values.

    @staticmethod
    def form_values(options: Mapping[str, Any]) -> dict[str, Any]:
        """Return the value that each advanced control shows after Back or on a retry.

        Why:
            An operator who returns to the form must see every earlier choice.
            A control that reopened empty would send a plan that nobody read.
            The start time, the reboot delay, the phases, and the failure
            percentage keep their own multi-site text, so this method never
            touches them.

        Args:
            options: The flat option record, or the plan options of a retry.

        Returns:
            The text of each text control, and a boolean for each radio group.
        """
        shown = advanced_option_values(options)  # The shared text rule: a list joins with commas.
        values: dict[str, Any] = {name: shown.get(name, "") for name in _TEXT_FIELDS}  # The nine text controls.
        values.update({name: OrgAdvancedOptions.chosen(options.get(name)) for name in _CHOICE_FIELDS})  # Radios.
        return values  # The template reads each value by its cloud field name.

    @staticmethod
    def chosen(value: object) -> bool:
        """Return true when one radio value means yes.

        Args:
            value: A boolean from a JSON client, or the text of a radio group.

        Returns:
            True for a true boolean or a yes word. False for every other value.
        """
        if isinstance(value, bool):  # A JSON client can send a real boolean.
            return value
        return str(value or "").strip().lower() in _YES_WORDS  # A radio group sends a word.


class OrgAdvancedRules:
    """Apply the plan rules that the shared option mapper does not know.

    Why:
        The shared mapper serves the site call. The multi-site plan also sends
        one organization call for every access point, and that call reads a
        narrower schema. These rules stop the plan at the save, before the
        typed confirmation. A refusal at the submit would leave the operator
        with an outcome that nobody can read.
    """

    @staticmethod
    def refuse_stable_access_points(choices: UpgradeOptions, targets: Iterable[Mapping[str, Any]]) -> None:
        """Refuse the vendor stable build for a plan that holds an access point.

        Why:
            The organization access point schema names no stable word. A plan
            that sent the typed version instead would write a build that the
            operator did not choose.

        Args:
            choices: The checked choices of the operator.
            targets: The explicit targets of the plan.

        Raises:
            BadOptionError: If the stable build and an access point meet.
        """
        logger.info("Check the stable build choice against the plan targets")  # Log before the rule.
        holds_ap = any(str(target.get("device_type", "")) == DEVICE_TYPE_AP for target in targets)  # One AP is enough.
        if choices.stable_version and holds_ap:  # The organization call cannot carry this choice.
            logger.warning("The multi-site save refused the stable build for a plan with an access point")
            raise BadOptionError("stable_version", labels=ORG_OPTION_HELP)  # Name the multi-site control.
        logger.debug("The stable build rule passed for the plan")  # Log after the rule.

    @staticmethod
    def refuse_large_failure_counts(choices: UpgradeOptions) -> None:
        """Refuse a failure count above the limit of the organization body.

        Why:
            The shared mapper sets no upper limit on a count. The organization
            body refuses a count above its limit at the submit, which is too
            late for a clear answer.

        Args:
            choices: The checked choices of the operator.

        Raises:
            BadOptionError: If one count is above the limit.
        """
        logger.info("Check the failure count of each canary phase")  # Log before the rule.
        counts = choices.canary.max_failures or ()  # An absent list holds no count.
        if any(count > FAILURE_COUNT_HIGHEST for count in counts):  # The organization body refuses this count.
            logger.warning("The multi-site save refused a failure count above the organization limit")
            raise BadOptionError("max_failures", labels=ORG_OPTION_HELP)  # Name the multi-site control.
        logger.debug("The failure count rule passed for %s count(s)", len(counts))  # Log after the rule.

    @staticmethod
    def holds_router(device_views: Iterable[Mapping[str, Any]]) -> bool:
        """Return true when one selected site holds a session smart router.

        Why:
            Only the router schema reads a release train. The page shows that
            control only for a plan that can hold a router, as the single-site
            page does.

        Args:
            device_views: The device view of each selected site.

        Returns:
            True when one device row names the router family.
        """
        routers = [  # Each router row of every selected site.
            row
            for view in device_views  # One view for each selected site.
            for row in view.get("targets", [])  # One row for each device of the site.
            if row.get("gateway_family") == GatewayFamily.SSR.value  # The row names the router family.
        ]
        logger.debug("The selected sites hold %s session smart router(s)", len(routers))  # Log the result.
        return bool(routers)  # The template shows the release train control for a router.


class OrgAdvancedSummary:
    """Name each advanced value that the saved plan sends, for the typed confirmation page.

    Why:
        Issue #3383. The operator must read each advanced value before the
        typed confirmation. The list reads the stored body of each child job,
        because that body is the exact request that the confirmation sends.
        An earlier rule read only the strategy and the device families. It
        listed the failure counts for a router child and for the per-device
        call, and neither body carries them.
    """

    CHOICE_TEXT: ClassVar[dict[str, dict[str, str]]] = {  # The page text of each word, as the options page shows it.
        "stable_version": {"yes": "Use the vendor stable build"},
        "enable_p2p": {"yes": "Yes, an access point may take the firmware from a neighbor"},
        "rrm_node_order": {
            "center_to_fringe": "Start at the center of each site",
            "fringe_to_center": "Start at the edge of each site",
        },
        "rrm_mesh_upgrade": {
            "parallel": "All mesh access points together",
            "sequential": "One mesh access point at a time",
        },
        "rrm_slow_ramp": {"yes": "Grow each batch slowly", "no": "Grow each batch at the usual rate"},
        "channel": {
            "stable": "Stable, the tested build",
            "beta": "Beta, the build under test",
            "alpha": "Alpha, the earliest build",
        },
    }

    @classmethod
    def lines(cls, view: Mapping[str, Any], children: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
        """Return one summary line for each advanced value that the plan sends.

        Args:
            view: The form view of the saved options.
            children: The child jobs of the saved plan. Each child holds the
                body that the confirmation sends to the cloud.

        Returns:
            One line for each value, with its test identifier, its label, and its text.
        """
        logger.info("Build the advanced summary of the typed confirmation page")  # Log before the build.
        sent = cls._sent_fields(children)  # The fields that one stored child body carries.
        rows = [  # One line for each value that the operator set and that the plan sends.
            cls._row(name, view[name])  # The label and the text of one value.
            for name in ADVANCED_FIELDS  # Keep the order of the options page.
            if name in sent and cls._is_set(view.get(name))  # Skip a value that the plan drops or never held.
        ]
        logger.debug("The advanced summary lists %s value(s)", len(rows))  # Log after the build.
        return rows  # The template paints each line in this order.

    @staticmethod
    def _sent_fields(children: Iterable[Mapping[str, Any]]) -> set[str]:
        """Return each advanced field that one stored child body carries.

        Why:
            Each body builder adds a field only where its call reads it. The
            router body holds no canary count. The per-device call holds no
            orchestration field at all. The stable build shows as the stable
            word in the version field, because the body holds no stable flag.
        """
        sent: set[str] = set()  # A plan with no readable body makes no promise.
        for child in children:  # Read the request of each child job.
            body = child.get("body")  # The body that the confirmation sends to the cloud.
            if not isinstance(body, Mapping):  # A damaged child sends nothing that the page can name.
                continue  # Skip the damaged child and read the next one.
            sent.update(name for name in ADVANCED_FIELDS if name in body)  # Each body key names its own field.
            if body.get("version") == VERSION_STABLE:  # The stable choice replaces the typed version.
                sent.add("stable_version")  # The cloud picks the vendor stable build for this child.
        logger.debug("The stored child bodies carry %s advanced field(s)", len(sent))  # Log the result.
        return sent  # The fields that reach the cloud.

    @classmethod
    def _row(cls, name: str, value: object) -> dict[str, str]:
        """Return the test identifier, the label, and the text of one summary line."""
        word = "yes" if value is True else str(value)  # A radio group keeps a boolean.
        return {  # One line of the summary list.
            "test_id": "org-upgrade-summary-" + name.replace("_", "-"),  # One stable identifier for each field.
            "label": ORG_OPTION_HELP[name][0],  # The label that the options page paints.
            "text": cls.CHOICE_TEXT.get(name, {}).get(word, word),  # A listed word shows its page text.
        }

    @staticmethod
    def _is_set(value: object) -> bool:
        """Return true when one form view value holds a choice of the operator."""
        return value is True or (isinstance(value, str) and value != "")  # A text control or a yes radio.
