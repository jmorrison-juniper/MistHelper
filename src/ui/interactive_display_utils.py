"""InteractiveDisplayUtils -- interactive device/site display helpers.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 10).
Groups the interactive_display_* menu handlers (site inventory, device stats,
device tests, device config) so callers can invoke them without reaching into
the monolith. All methods are static -- no state is kept on the class.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper classes without circular load.
import logging  # WHY: emit structured trace for each menu entry.

import mistapi  # WHY: dotted-path API resolution for device stats / test / config endpoints.

from src.refactors.device_data_fetcher import (
    DeviceFetchConfig,
)  # T-01: DeviceFetchConfig now lives with DeviceDataFetcher.


class InteractiveDisplayUtils:
    """Centralized interactive display utilities.

    Groups all interactive_display_* functions for better code organization.
    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def site_inventory() -> None:
        """Prompt the user to select a site and display its device inventory."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils + SiteDeviceExporter.
        logging.info("Prompting user to select a site for device inventory view...")  # Log the prompt.
        print("Select a Site to View Device Inventory:")  # Header.
        site_id = mh.PromptUtils.select_site_id_from_csv()  # Select a site.
        if site_id:  # Site selected.
            logging.info("User selected site_id: %s for inventory display.", site_id)  # Log the selection.
            mh.SiteDeviceExporter.device_inventory(site_id)
        else:
            logging.warning("No site selected or invalid input provided for site selection.")  # Warn none selected.

    @staticmethod
    def device_stats(site_id: str | None = None, device_id: str | None = None) -> None:
        """Fetch and display detailed statistics for a specific device.

        Args:
            site_id: Optional site ID (prompts if not provided)
            device_id: Optional device ID (prompts if not provided)
        """
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of DeviceDataFetcher (still lives in MistHelper.py).
        logging.info("Prompting user to select a device for detailed statistics view...")  # Log the prompt.
        mh.DeviceDataFetcher(  # Fetch and display.
            DeviceFetchConfig(  # Issue #470: bundle fetch params (T-01: imported from src.refactors).
                fetch_function=mistapi.api.v1.sites.stats.getSiteDeviceStats,
                filename="DeviceStats.csv",
                description="Fetching detailed stats",
                site_id=site_id,
                device_id=device_id,
            )
        ).fetch()
        logging.info("Completed device_stats execution.")  # Log completion.

    @staticmethod
    def device_tests() -> None:
        """Prompt user to select a gateway device and display its synthetic test stats."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of DeviceDataFetcher (still lives in MistHelper.py).
        logging.info("Prompting user to select a gateway device for synthetic test stats view...")  # Log the prompt.
        mh.DeviceDataFetcher(  # Fetch and display.
            DeviceFetchConfig(  # Issue #470: bundle fetch params (T-01: imported from src.refactors).
                fetch_function=mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest,
                filename="DeviceTestResults.csv",
                description="Fetching synthetic test stats",
                device_type="gateway",
            )
        ).fetch()
        logging.info("Completed device_tests execution.")  # Log completion.

    @staticmethod
    def device_config() -> None:
        """Prompt user to select a device and display its configuration details."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of DeviceDataFetcher (still lives in MistHelper.py).
        logging.info("Prompting user to select a device for configuration details view...")  # Log the prompt.
        mh.DeviceDataFetcher(  # Fetch and display.
            DeviceFetchConfig(  # Issue #470: bundle fetch params (T-01: imported from src.refactors).
                fetch_function=mistapi.api.v1.sites.devices.getSiteDevice,
                filename="DeviceConfig.csv",
                description="Fetching device configuration",
            )
        ).fetch()
        logging.info("Completed device_config execution.")  # Log completion.
