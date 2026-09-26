"""Collect the option record of each selected site of a multi-site plan.

Why:
    Issue #3389. The multi-site save built one option record for each
    selected site, and it kept the options of the last site only. A site with
    no device answers an empty record, so the choices of the operator became
    the defaults when that site came last. A failed inventory read gave the
    same empty record, and the save dropped the devices of that site with no
    message. This class keeps the options of each site that answers, and it
    names each selected site that the plan cannot cover.

    Issue #3424. A short read keeps the rows of the first page and loses the
    devices of the other pages. The plan then looks complete, and the lost
    devices stay on the old firmware. The mapper marks such a site with the
    partial reasons of its read, and this class names the site in a refusal.

    A retry of issue #3247 is different. The retry chooses the sites of its
    failed devices, and the operator can clear a device type. A site can then
    hold no retry device, and the retry must still plan the other devices.

    The module imports no route module, so a unit test needs no Flask
    application.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each refusal without a device address or a secret.
from collections.abc import Callable, Mapping  # The label reader and the record of one site.
from typing import Any  # A site record holds JSON values of mixed types.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

NAME_SEPARATOR = ", "  # The separator of the site names in a refusal, as the pre-check refusal uses it.
NAME_LIMIT = 10  # The most site names that one refusal shows. A long selection then stays readable.
UNREAD_MESSAGE = (  # The refusal for a site whose inventory read found no device.
    "The portal read no device at these sites: {names}. Save the options again. "
    "If a site holds no device, clear that site on the Sites page."
)
UNPLANNED_MESSAGE = (  # The refusal for a site that holds no device of a checked type with a version.
    "The plan holds no device at these sites: {names}. Check the device types and the target versions. "
    "If a site holds no device of the checked types, clear that site on the Sites page."
)
PARTIAL_REASONS_FIELD = "partial_reasons"  # Issue #3424: the marker field of a site whose read was short.
SHORT_MESSAGE = (  # Issue #3424: the refusal for a site whose read lost one or more pages.
    "The portal did not read the complete device list at these sites: {names}. "
    "Reload this page. Then save the options again."
)

SiteLabels = Callable[[list[str]], list[str]]  # Return one label for each site identifier, in the same order.


class OrgSiteRefusal(ValueError):
    """Refuse a multi-site plan that cannot cover each selected site.

    Why:
        The save route answers each `ValueError` with status 400 and the
        message text, so the page shows the refusal in its flash region.
    """

    def __init__(self, template: str, labels: list[str]) -> None:
        """Build the refusal text from one message and the label of each site.

        Args:
            template: `UNREAD_MESSAGE`, `SHORT_MESSAGE`, or `UNPLANNED_MESSAGE`.
            labels: The name of each refused site, or its identifier.
        """
        self.labels = list(labels)  # Keep a detached copy for a caller that reads the sites.
        super().__init__(template.format(names=OrgSiteRefusal.names_text(self.labels)))  # The text of the page.

    @staticmethod
    def names_text(labels: list[str]) -> str:
        """Return the site labels of one refusal, with the count of each label above the limit.

        Args:
            labels: The label of each refused site.

        Returns:
            The labels up to `NAME_LIMIT`, and then the count of the other sites.
        """
        shown = labels[:NAME_LIMIT]  # The labels that the message names.
        hidden = len(labels) - len(shown)  # The count of the labels that the message does not name.
        text = NAME_SEPARATOR.join(shown)  # One label for each shown site.
        return text if hidden <= 0 else f"{text}, and {hidden} more"  # State the count of the other sites.


class OrgSiteRecords:
    """Collect the targets and the options of each selected site of one save."""

    def __init__(self, every_site_planned: bool = True) -> None:
        """Start with no site.

        Args:
            every_site_planned: Refuse a site that holds no planned device.
                A retry of issue #3247 sets False. The retry chooses its own
                sites, so a cleared device type can leave a site with no
                retry device.
        """
        self.every_site_planned = every_site_planned  # False only for a retry of the failed devices.
        self.targets: list[dict[str, Any]] = []  # Each planned device, with the site that holds it.
        self.options: dict[str, Any] | None = None  # The options of a site that answered, or None.
        self.unread_sites: list[str] = []  # Each site whose record is empty.
        self.short_sites: list[str] = []  # Issue #3424: each site whose inventory read lost one or more pages.
        self.unplanned_sites: list[str] = []  # Each site that answered with no planned device.

    def add(self, site_id: str, built: Mapping[str, Any]) -> None:
        """Add the record of one site.

        Why:
            The shipped mapper returns an empty record when the inventory read
            finds no device. That record holds no options, so it must never
            replace the options of a site that answered. Issue #3424: a record
            that holds partial reasons marks a short read. That site adds no
            target and no options, because its device list is not complete.

        Args:
            site_id: The site of the record.
            built: The record that the option mapper returned for the site.
        """
        if built.get(PARTIAL_REASONS_FIELD):  # Issue #3424: the read kept the first page only.
            self.short_sites.append(site_id)  # The refusal names this site.
            logger.debug("The inventory read of site %s was short", site_id)  # Log the short record.
            return  # A plan of the first page would leave out the devices of the lost pages.
        options = built.get("options")  # The options of the site, or None for an empty record.
        if not isinstance(options, Mapping):  # An empty record, or a value that no mapper writes.
            self.unread_sites.append(site_id)  # The refusal names this site.
            logger.debug("The option record of site %s holds no options", site_id)  # Log the empty record.
            return  # Keep the options of each site that answered.
        entries = [{**dict(target), "site_id": site_id} for target in built.get("targets", [])]  # Name the site.
        if not entries:  # The site holds no device of a checked type with a version.
            self.unplanned_sites.append(site_id)  # A refusal can name this site.
        self.targets.extend(entries)  # Keep the order of the selection and of the inventory.
        self.options = dict(options)  # Each site that answers builds the same options from one form.
        logger.debug("Site %s adds %s target(s) to the plan", site_id, len(entries))  # Log the result count.

    def refusal(self, labels: SiteLabels) -> OrgSiteRefusal | None:
        """Return the refusal for the sites that the plan cannot cover, or None.

        Why:
            An empty record comes first, because a new read can change the
            plan. A short read of issue #3424 comes next, in a retry too, and
            also when no site holds a planned device. A plan of the first page
            leaves out the devices of the lost pages, and a reload is a cheap
            recovery. A site with no planned device stops the save only when
            another site holds one. If no site holds one, the route keeps its
            old refusal, which names the device type control. A retry never
            stops for a site with no planned device. The Sites page ends the
            retry, so the refusal would send the operator to a page that adds
            the healthy devices to the plan again.

        Args:
            labels: Return the label of each site. The call happens only when
                a refusal names one or more sites.

        Returns:
            The refusal, or None when the plan covers each selected site.
        """
        if self.unread_sites:  # One or more sites answered an empty record, in a retry too.
            logger.warning("The save stops, because %s site(s) answered no record", len(self.unread_sites))
            return OrgSiteRefusal(UNREAD_MESSAGE, labels(self.unread_sites))  # Name each unread site.
        if self.short_sites:  # Issue #3424: one or more reads lost pages, in a retry too.
            logger.warning("The save stops, because %s site(s) answered a short read", len(self.short_sites))
            return OrgSiteRefusal(SHORT_MESSAGE, labels(self.short_sites))  # Name each short site.
        if not self.targets or not self.unplanned_sites:  # Each site holds a planned device, or no site holds one.
            return None  # The plan covers each selected site, or the route keeps its old refusal.
        if not self.every_site_planned:  # Issue #3247: a retry plans the failed devices of its own sites.
            logger.info("The retry plan leaves out %s site(s) with no planned device", len(self.unplanned_sites))
            return None  # A cleared device type or a moved device leaves a site with no retry device.
        logger.warning("The save stops, because %s site(s) hold no planned device", len(self.unplanned_sites))
        return OrgSiteRefusal(UNPLANNED_MESSAGE, labels(self.unplanned_sites))  # Name each unplanned site.
