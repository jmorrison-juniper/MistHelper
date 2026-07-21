"""DataCollectionManager -- continuous data collection + support package generation.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 25).
Menu 76 (continuous loop) + Menu 78 (support packages). All methods are
static -- no state is kept on the class. Callers continue to reach it
through the ``MistHelper.DataCollectionManager`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for collection lifecycle events.
import os  # WHY: filesystem existence check for optional speedtest CSV.
import time  # WHY: pace API calls between exporters and back off on failure.
from datetime import datetime  # WHY: timestamp banner per loop iteration.
from typing import Any  # WHY: callable/step tuple lists are duck-typed.

from src.export.org_inventory_exporter import (
    OrgInventoryExporter,  # WHY: 1015 T-06 canonical import (eliminates mh.OrgInventoryExporter).
)

logger = logging.getLogger(__name__)  # WHY: module-scoped logger routes former print notices for capture/redirection.


class DataCollectionManager:
    """Manages automated data collection and support package generation operations.

    Provides methods for:
    - Continuous loop data collection from Mist API
    - Support package generation per site

    All methods are static to avoid unnecessary object instantiation.
    """

    @staticmethod
    def _print_continuous_loop_banner() -> None:  # Print startup banner.
        """Print the startup banner for menu 76's continuous collection loop."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(" Starting continuous data collection loop...")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("   This will collect core organizational data every 5 seconds")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("   Press CTRL+C to stop or create 'stop_loop.txt' file")

    @staticmethod
    def continuous_loop() -> None:  # Run the collection loop.
        """Menu 76: continuously collect site/inventory/device-stat/port-stat/VPN-peer data until stop."""
        logging.info("Starting DataCollectionManager.continuous_loop")  # Log start.
        DataCollectionManager._print_continuous_loop_banner()  # Show the user what's happening.
        loop_count = 0  # Iteration counter.
        try:
            while True:  # Loop until stopped.
                loop_count += 1  # Count the iteration.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.info("\n  Loop iteration %d - %s", loop_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if DataCollectionManager._check_stop_signal():  # Stop requested.
                    break  # Exit the loop.
                DataCollectionManager._execute_collection_cycle(loop_count)  # Run one cycle.
        except KeyboardInterrupt:  # User pressed Ctrl+C.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("\n  Continuous data collection loop stopped by user.")
        except Exception as e:  # Unexpected failure.
            logging.error("Fatal error in continuous loop: %s", e)  # Log the error.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("! Fatal error in continuous loop: %s", e)
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(" Continuous data collection loop ended.")

    @staticmethod
    def _check_stop_signal() -> bool:  # Check the stop signal.
        """Check for stop file signal and remove if found."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils helper.
        return bool(mh.ConfigUtils.check_stop_signal())  # Delegate to config utils.

    @staticmethod
    def _collection_cycle_steps() -> list[tuple[str, Any]]:
        """Return the ordered (label, callable) pairs invoked each iteration of continuous_loop."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of exporter facades.
        return [  # Each tuple = printed banner + exporter function.
            ("  Collecting site list...", mh.OrgSiteExporter.sites),
            ("  Collecting organization inventory...", OrgInventoryExporter.inventory),
            ("  Collecting organization device stats...", mh.OrgDeviceStatsExporter.device_stats),
            ("  Collecting organization device port stats...", mh.OrgDeviceStatsExporter.device_port_stats),
            ("  Collecting VPN peer path stats...", mh.OrgDeviceStatsExporter.vpn_peer_stats),
        ]

    @staticmethod
    def _execute_collection_cycle(loop_count: int) -> None:  # Run one collection cycle.
        """Execute one cycle of data collection with rate limiting."""
        try:
            for banner, step_callable in DataCollectionManager._collection_cycle_steps():
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.info(banner)
                step_callable()  # Invoke the per-step exporter.
                time.sleep(0.75)  # Pace the API between exporters.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  Loop %d completed successfully", loop_count)
        except KeyboardInterrupt:  # Propagate Ctrl+C.
            raise  # Re-raise to outer handler
        except Exception as e:  # Cycle failed.
            logging.error("Error in collection cycle %s: %s", loop_count, e)  # Log the error.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  Error in loop %d: %s", loop_count, e)
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  Continuing to next iteration...")
            time.sleep(5)  # Back off then retry.

    @staticmethod
    def generate_support_packages() -> None:  # Generate support packages.
        """Menu 78: Generate support package CSV for each site with alarms or events.

        Collects and packages:
        - Org alarms, device events
        - Device info, stats, port stats
        - Gateway speedtest results
        """
        logging.info("DataCollectionManager.generate_support_packages starting")  # Log start.

        # Ensure all required data is fresh
        DataCollectionManager._refresh_support_data()  # Refresh support data.

        # Load all data sources
        data_sources = DataCollectionManager._load_support_data_sources()  # Load support sources.

        # Generate packages for sites with alarms or events
        DataCollectionManager._generate_site_packages(data_sources)  # Generate per-site packages.

        logging.info("Support packages generated for applicable sites.")  # Log completion.

    @staticmethod
    def _refresh_support_data() -> None:  # Refresh required CSVs.
        """Refresh all required CSV files for support package generation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of exporter facades + CacheUtils.
        required_files = [  # Required files and fetchers.
            ("OrgAlarms.csv", mh.OrgAlarmEventExporter.alarms),
            ("OrgDeviceEvents.csv", mh.OrgAlarmEventExporter.device_events),
            ("SiteList.csv", mh.OrgSiteExporter.sites),
            ("OrgDevices.csv", OrgInventoryExporter.devices),
            ("OrgDeviceStats.csv", mh.OrgDeviceStatsExporter.device_stats),
            ("OrgDevicePortStats.csv", mh.OrgDeviceStatsExporter.device_port_stats),
            ("AllGatewayTestResults.csv", mh.GatewayTestExporter.test_results_by_site),
        ]

        for filename, func in required_files:  # Refresh each file.
            mh.CacheUtils.check_and_generate_csv(filename, func)  # type: ignore[arg-type]  # function is Callable

    @staticmethod
    def _load_support_data_sources() -> dict:  # type: ignore[type-arg]
        """Load all CSV data sources for support package assembly."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils + FilePathUtils.
        sources = {  # Load the data sources.
            "site_data": mh.CacheUtils.load_csv_grouped_by_key("SiteList.csv", "id"),
            "alarms_data": mh.CacheUtils.load_csv_grouped_by_key("OrgAlarms.csv", "site_id"),
            "events_data": mh.CacheUtils.load_csv_grouped_by_key("OrgDeviceEvents.csv", "site_id"),
            "devices_data": mh.CacheUtils.load_csv_grouped_by_key("OrgDevices.csv", "name"),
            "device_stats_data": mh.CacheUtils.load_csv_grouped_by_key("OrgDeviceStats.csv", "site_id"),
            "port_stats_data": mh.CacheUtils.load_csv_grouped_by_key("OrgDevicePortStats.csv", "site_id"),
            "speedtest_data": {},
        }

        # Load speedtest data if available
        gateway_test_path = mh.FilePathUtils.get_csv_path("AllGatewayTestResults.csv")  # Speedtest CSV path.
        if os.path.exists(gateway_test_path):  # File present.
            sources["speedtest_data"] = mh.CacheUtils.load_csv_grouped_by_key("AllGatewayTestResults.csv", "site_id")

        return sources  # Return the sources.

    @staticmethod
    def _generate_site_packages(data_sources: dict) -> None:  # type: ignore[type-arg]
        """Generate support package for each site with alarms or events."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils.
        site_data = data_sources["site_data"]  # Read the site data.

        for site_id in site_data:  # Walk sites; values are looked up per-site as needed.
            # Skip sites without alarms or events
            has_alarms = bool(data_sources["alarms_data"].get(site_id))  # Has alarms?
            has_events = bool(data_sources["events_data"].get(site_id))  # Has events?

            if not has_alarms and not has_events:  # Nothing to report.
                logging.info("Skipping site %s - no alarms or events", site_id)  # Log the skip.
                continue  # Skip it.

            support_data = {  # Build the support data.
                "alarms": data_sources["alarms_data"].get(site_id, []),
                "events": data_sources["events_data"].get(site_id, []),
                "devices": data_sources["devices_data"].get(site_id, []),
                "device_stats": data_sources["device_stats_data"].get(site_id, []),
                "port_stats": data_sources["port_stats_data"].get(site_id, []),
                "speedtests": data_sources["speedtest_data"].get(site_id, []),
            }

            filename = f"SupportPackage_{site_id}.csv"  # Build the CSV name.
            mh.CacheUtils.write_support_data_to_csv(support_data, filename)  # Write the package.
            logging.info("Support package written for site %s", site_id)  # Log the write.
