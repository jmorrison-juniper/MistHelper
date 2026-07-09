"""OrgAlarmEventExporter -- org-level alarm/event time-series exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 18).
Focused exporter for alarm and event time-series data from the Mist API.
Contains exactly 5 public entry points grouped by the 'event/alert' domain:
alarms(), alarm_templates(), events(), device_events(), device_events_52w().
Callers continue to reach it through the ``MistHelper.OrgAlarmEventExporter``
re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper globals without circular load.
import json  # WHY: debug-dump sample device events.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: api_call is duck-typed mistapi callable.

import mistapi  # WHY: direct SDK access for alarms/events endpoints.

from src.export.device_events_52w_exporter import DeviceEvents52wExporter  # 52-week device events exporter.
from src.time.time_utils import TimeUtils  # WHY: 1014 P6 direct import (FR-005).


class OrgAlarmEventExporter:
    """Focused exporter for alarm and event time-series data from the Mist API.

    Contains exactly 5 public methods grouped by the 'event/alert' domain:
      - alarms()            : Organization alarms (24h, unacknowledged)
      - alarm_templates()   : Alarm rule templates
      - events()            : Organization events (24h)
      - device_events()     : Device events (24h)
      - device_events_52w() : Device events (52 weeks)
    """

    @staticmethod
    def _export_data(api_call: Any, data_type: str, sort_key: str = "name", **api_kwargs: Any) -> None:
        """Generic helper to export organization data via APIDataFetcher.

        Args:
            api_call: The mistapi function to call.
            data_type: Description of the data type.
            sort_key: Field to sort results by.
            **api_kwargs: Additional arguments for the API call.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Starting export of organization %s...", data_type)  # Log export start.
        safe_data_type = data_type.replace(" ", "").replace("-", "").title()  # Sanitize data type for filename.
        filename = f"Org{safe_data_type}.csv"  # Build output CSV name.
        mh.APIDataFetcher(  # Fetch and write the data.
            title=f"Organization {data_type.title()}:",
            api_call=api_call,
            filename=filename,
            sort_key=sort_key,
            limit=1000,
            **api_kwargs,
        ).execute()

    @staticmethod
    def alarms() -> None:
        """Export open organization alarms from the past 24 hours to OrgAlarms.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Menu #20: Starting organization alarms export")  # Log alarms menu start.
        logging.debug("ENTRY: OrgAlarmEventExporter.alarms()")  # Trace entry for debugging.
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve dynamic lookback hours.
        TimeUtils.log_dynamic_lookback("open org alarms export", hours)  # Log chosen lookback window.
        try:
            mh.APIDataFetcher(  # Fetch and write alarms.
                title="Search all Org Alarms:",
                api_call=mistapi.api.v1.orgs.alarms.searchOrgAlarms,
                filename="OrgAlarms.csv",
                limit=1000,
                duration=f"{hours}h",
                acked=False,
            ).execute()
            logging.info("Completed org alarms export and wrote results to OrgAlarms.csv.")
            logging.debug("EXIT: OrgAlarmEventExporter.alarms - success")  # Trace successful exit.
        except Exception as error:  # Catch export errors.
            logging.error("Failed to export open org alarms: %s", error)  # Log export failure.
            logging.debug("EXIT: OrgAlarmEventExporter.alarms - error")  # Trace error exit.
            raise  # Re-raise to caller.

    @staticmethod
    def alarm_templates() -> None:
        """Export alarm templates to OrgAlarmTemplates.csv."""
        OrgAlarmEventExporter._export_data(
            api_call=mistapi.api.v1.orgs.alarmtemplates.listOrgAlarmTemplates,
            data_type="alarm templates",
            sort_key="name",
        )

    @staticmethod
    def events() -> None:
        """Export organization events to OrgEvents.csv."""
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve dynamic lookback hours.
        TimeUtils.log_dynamic_lookback("org events export", hours)  # Log chosen lookback window.
        OrgAlarmEventExporter._export_data(
            api_call=mistapi.api.v1.orgs.events.searchOrgEvents,
            data_type="events",
            sort_key="timestamp",
            duration=f"{hours}h",
        )

    @staticmethod
    def device_events() -> None:
        """Export all device events from the past 24 hours to OrgDeviceEvents.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils/DataExporter + apisession.
        logging.info("Menu #21: Starting device events export")  # Log device events menu start.
        logging.info("Search Org Device Events:")  # Log search start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        hours = TimeUtils.get_dynamic_lookback_hours(24, 1)  # Resolve dynamic lookback hours.
        TimeUtils.log_dynamic_lookback("recent device events export", hours)  # Log chosen lookback window.
        duration_param = f"{hours}h"  # Format duration param.
        response = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(  # Search org device events.
            mh.apisession, org_id, device_type="all", limit=1000, duration=duration_param
        )
        rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all events.
        events = rawdata  # Alias rawdata as events.
        logging.info(
            "Fetched %s device events from the past %s hours (duration=%s).", len(events), hours, duration_param
        )
        mh.DataExporter.write_with_format_selection(events, "OrgDeviceEvents.csv")  # Persist events.
        logging.info("Device events written to OrgDeviceEvents.csv (%s rows).", len(events))
        print(f"! {len(events)} device events exported to OrgDeviceEvents.csv")  # Confirm export to operator.
        logging.info("Menu #21: Device events export completed - %s events", len(events))
        if events:  # Branch: events present.
            logging.debug("Sample device events: %s", json.dumps(events[:3], indent=2))  # Debug-dump sample events.

    @staticmethod
    def device_events_52w() -> None:
        """Delegated 52-week device event export entrypoint."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + globals for exporter deps.
        exporter = DeviceEvents52wExporter(  # Build the 52w exporter.
            apisession=mh.apisession,
            mistapi=mistapi,
            org_id=mh.ConfigUtils.get_cached_or_prompted_org_id(),
            data_processing_utils=mh.DataProcessingUtils,
            data_exporter=mh.DataExporter,
            output_format=mh.OUTPUT_FORMAT,
            database_path=mh.DATABASE_PATH,
            logger=logging,
        )
        exporter.export()  # Run the export.
