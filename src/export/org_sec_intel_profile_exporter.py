"""OrgSecIntelProfileExporter -- the ``getOrgSecIntelProfile`` endpoint.

Added for spec 635 and issue #1148. The class wraps the Mist API
``getOrgSecIntelProfile``
(``GET /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}``). An
operator reads one profile through the standard MistHelper menu. The
DataExporter pipeline then writes the result to CSV, SQLite, or ArangoDB.

Why:
    MistHelper already exports the whole profile list through
    ``listOrgSecIntelProfiles``. The list view holds the summary fields only.
    An operator who reviews one profile had to open the Mist portal to read the
    full profile body. This menu closes that gap.

Why the operator picks from a list:
    The endpoint needs a profile identifier, and that identifier is a UUID. A
    junior engineer cannot be expected to know a UUID, and a typed UUID invites
    a typing error. The exporter therefore reads the profile list first, prints
    a numbered table, and asks for a number. The operator never types a UUID.

Shape of the response:
    The endpoint returns one profile object, not a list. The exporter reads
    ``response.data`` directly, because the endpoint is not paginated and
    ``mistapi.get_all`` would return nothing useful.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw profile rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for the two SecIntel profile endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.

# The operationId that selects the primary-key strategy for the written rows.
_OPERATION = "getOrgSecIntelProfile"


class OrgSecIntelProfileExporter:
    """Security intelligence profile exporter for ``getOrgSecIntelProfile``.

    Why:
        Provides the only MistHelper entry point for the single-profile SecIntel
        endpoint. Static methods only, with no per-instance state, matching the
        peer exporters such as ``MSPLicenseExporter``.
    """

    @staticmethod
    def _list_profiles(org_id: str) -> list[dict[str, Any]]:
        """Read every SecIntel profile in one org so the operator can choose one.

        Why:
            The detail endpoint needs a profile UUID. Reading the list first
            lets the operator answer with a number instead of a UUID.

        Args:
            org_id: The organization the operator selected.

        Returns:
            One dict for each profile. The list is empty when the org holds none.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the apisession global.
        logging.info("Calling listOrgSecIntelProfiles for org_id=%s", org_id)  # Pre-call log.
        response = mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles(
            mh.apisession, org_id
        )  # The list endpoint is paginated, so page it through the shared helper.
        rows = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page every profile.
        profiles = [row for row in rows if isinstance(row, dict)]  # Drop any malformed entry before use.
        logging.debug("listOrgSecIntelProfiles returned %d profiles", len(profiles))  # Post-call count.
        return profiles

    @staticmethod
    def _choose_profile(profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Print the numbered profile table and read the operator choice.

        Why:
            One shared prompt keeps the cancel path, the bounds check, and the
            EOF handling in one place.

        Args:
            profiles: The profiles the org holds. Must hold at least one entry.

        Returns:
            The chosen profile, or ``None`` when the operator cancels.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the shared input helper.
        for index, profile in enumerate(profiles, start=1):  # Number the rows from one.
            name = profile.get("name") or "(unnamed)"  # A profile without a name still needs a label.
            print(f"  [{index}] {name}  id={profile.get('id', 'unknown')}")  # Operator-facing choice row.
        answer = str(  # WHY: the lazy module attribute is untyped, so pin the declared str return.
            mh.InputUtils.safe_input(
                f"Select a security intelligence profile (1-{len(profiles)}): ",
                allow_empty=False,  # An empty answer cannot select a profile.
                context="org_sec_intel_profile.selection",
            )
        ).strip()
        logging.debug("Operator answered %r for the profile selection", answer)  # Answer trace.
        if not answer.isdigit():  # A non-numeric answer, an EOF, or an interrupt aborts.
            logging.info("! No profile selected. Returning to the menu.")  # User-facing cancel.
            return None
        position = int(answer)  # Convert once the value is known to be all digits.
        if not 1 <= position <= len(profiles):  # Guard the table bounds before indexing.
            logging.info("! %d is outside 1-%d. Returning to the menu.", position, len(profiles))  # Bounds notice.
            return None
        return profiles[position - 1]  # The printed table starts at one, the list starts at zero.

    @staticmethod
    def _fetch(org_id: str, secintelprofile_id: str) -> dict[str, Any]:
        """Call ``getOrgSecIntelProfile`` for one profile and return the body.

        Why:
            The endpoint returns one object and is not paginated, so the caller
            reads ``response.data`` instead of running ``mistapi.get_all``.

        Args:
            org_id: The organization that owns the profile.
            secintelprofile_id: The profile the operator selected.

        Returns:
            The profile body as a dict, or an empty dict when the body is absent.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the apisession global.
        logging.info(
            "Calling getOrgSecIntelProfile for org_id=%s profile_id=%s", org_id, secintelprofile_id
        )  # Pre-call log.
        response = mistapi.api.v1.orgs.secintelprofiles.getOrgSecIntelProfile(
            mh.apisession, org_id, secintelprofile_id
        )  # The SDK call for the single profile.
        payload = getattr(response, "data", None)  # The SDK exposes the body on .data.
        logging.debug("getOrgSecIntelProfile returned payload_type=%s", type(payload).__name__)  # Post-call trace.
        if not isinstance(payload, dict):  # A list body or a None body means the profile is gone.
            logging.debug("getOrgSecIntelProfile returned no dict body for %s", secintelprofile_id)  # Explain it.
            return {}
        return payload

    @staticmethod
    def _build_row(org_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the one flattened row that the writers persist.

        Why:
            The response holds nested lists, such as the profile matching rules.
            The shared flatten helper turns them into stable columns, so the CSV
            header does not change between two runs of the same profile.

        Args:
            org_id: The organization that owns the profile, added as a column.
            payload: The profile body from the API.

        Returns:
            A list that holds one flattened row, or an empty list for no body.
        """
        if not payload:  # An absent body has nothing to write.
            logging.debug("No SecIntel profile body to flatten")  # Explain the empty result.
            return []
        row = {"org_id": org_id, **payload}  # Tag the row with the org, then copy the profile fields.
        flattened = DataProcessingUtils.flatten_nested_fields([row])  # Flatten every nested field.
        logging.debug("Built %d SecIntel profile row(s)", len(flattened))  # Post-build count trace.
        return flattened

    @staticmethod
    def _persist(rows: list[dict[str, Any]], filename: str) -> None:
        """Escape and persist the profile row, or report that there is none.

        Args:
            rows: The flattened rows to write. May be empty.
            filename: The output filename, used as the CSV name or the table name.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rows:  # No rows, so inform the operator and return.
            logging.info("! No security intelligence profile data found")  # ASCII-only user notice.
            return
        sanitized_data = DataProcessingUtils.escape_multiline(rows)  # Make multiline values CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=_OPERATION
        )
        logging.debug("%s persisted %d rows to %s", _OPERATION, len(rows), filename)  # Post-call count.
        logging.info("! %d security intelligence profile record(s) exported to %s", len(rows), filename)  # Notice.

    @staticmethod
    def profile() -> None:
        """Export one security intelligence profile for an org (menu 240).

        Why:
            Interactive menu entry point. The method owns the prompts, the two
            API calls, and the write, and it keeps every failure inside the menu.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the org resolver.
        logging.info("Organization Security Intelligence Profile:")  # Menu header echoed to the operator.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve which org to read.
        if not org_id:  # The resolver already logged the cancellation.
            return
        try:
            profiles = OrgSecIntelProfileExporter._list_profiles(org_id)  # Read the list once.
            if not profiles:  # An org with no profile is legitimate, so report it plainly.
                logging.info("! This organization holds no security intelligence profile.")  # User notice.
                return
            chosen = OrgSecIntelProfileExporter._choose_profile(profiles)  # Ask which profile to read.
            if chosen is None:  # The prompt helper already logged the cancellation.
                return
            profile_id = str(chosen.get("id", "")).strip()  # The detail call needs the profile UUID.
            if not profile_id:  # A profile row without an id cannot drive the detail call.
                logging.info("! The selected profile carries no id. Returning to the menu.")  # User notice.
                return
            payload = OrgSecIntelProfileExporter._fetch(org_id, profile_id)  # Read the full profile body.
            rows = OrgSecIntelProfileExporter._build_row(org_id, payload)  # Flatten the body into one row.
            OrgSecIntelProfileExporter._persist(rows, f"OrgSecIntelProfile_{profile_id}.csv")  # Write it.
        except Exception as e:  # WHY: surface any SDK or network error, keep the menu alive.
            logging.error("Error fetching the SecIntel profile for org %s: %s", org_id, e)  # Failure context.
            logging.info("! Error fetching security intelligence profile data: %s", e)  # ASCII-only user notice.
