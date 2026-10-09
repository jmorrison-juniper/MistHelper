"""Harness for the browser tests of the Juniper RMA menus 294 to 304 (issue #3519).

Why:
    A screenshot of a double shows the double, and not the portal. The browser tests therefore
    run the real Juniper workflows. Only the Juniper gateway is replaced. The replacement answers
    each call from the synthetic replies in tests/unit/juniper_rma/fixtures, so no test reaches
    Juniper or Mist.

Scope:
    The replies contain no customer value. Every e-mail address uses the example.com domain, and
    every link uses the invalid top-level domain. The harness never writes to data/, because the
    test module changes the working directory first, and it switches the database mirror off.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from collections.abc import Callable  # WHY: the body builders are small callables keyed by endpoint.
from dataclasses import replace  # WHY: MenuEntry is frozen, so a new row carries the handler.
from datetime import datetime, timedelta  # WHY: the Mist ticket ages are relative to the run time.
from pathlib import Path  # WHY: the screenshot folder is computed from this file.
from types import SimpleNamespace  # WHY: the session stand-in that the Juniper workflows read.
from typing import Any  # WHY: the synthetic bodies are loosely typed JSON.

from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,
)  # WHY: the failure that a test can queue.
from src.operations.exporting.juniper_rma.api.messages import (
    JuniperTransportReply,
)  # WHY: the reply shape of the real gateway.
from src.operations.exporting.juniper_rma.workflows.access_check import (
    AccessCheckWorkflow,
)  # WHY: menu 301 entry point.
from src.operations.exporting.juniper_rma.workflows.asset_lookup import (
    AssetLookupWorkflow,
)  # WHY: menu 304 entry point.
from src.operations.exporting.juniper_rma.workflows.case_reads import (  # WHY: menus 294 to 297 entry points.
    RequestDetailWorkflow,
    RequestListWorkflow,
    RequestNotesWorkflow,
    RmaDetailWorkflow,
)
from src.operations.exporting.juniper_rma.workflows.correlation import (
    CorrelationWorkflow,
    MistTicket,
)  # WHY: menu 302 and its ticket.
from src.operations.exporting.juniper_rma.workflows.lookup import LookupWorkflow  # WHY: menu 303 entry point.
from src.operations.exporting.juniper_rma.workflows.reference_reads import (  # WHY: menus 298 to 300 entry points.
    AssetBulkWorkflow,
    LovWorkflow,
    SoftwareVersionWorkflow,
)
from src.foundation.support.utils.menu_entry import MenuEntry  # WHY: the row shape that the portal lists and runs.
from tests.unit.juniper_rma.fixtures import read_replies as replies  # WHY: the synthetic replies of the live shape.
from tests.unit.juniper_rma.fixtures.fake_gateway import (  # WHY: the gateway double and its helpers.
    FakeCall,
    FakeGateway,
    build_session,
    make_settings,
)
from web_portal.menu_registry import build_static_menu_actions  # WHY: the static rows that the portal lists.

REPO_ROOT = Path(__file__).resolve().parents[3]  # The folder that holds data/, tests/, and web_portal/.
SCREENSHOT_DIR = REPO_ROOT / "test-artifacts" / "juniper-portal"  # Git ignores this folder.
ASSET_SKU = "EX-SKU-1"  # The synthetic product SKU that every asset of the harness carries.

JUNIPER_HANDLERS: dict[str, Callable[..., None]] = {  # The same entry points that MistHelper.py registers.
    "294": RequestListWorkflow.run,  # The request list.
    "295": RequestDetailWorkflow.run,  # The request detail.
    "296": RmaDetailWorkflow.run,  # The RMA detail.
    "297": RequestNotesWorkflow.run,  # The request notes.
    "298": LovWorkflow.run,  # The list of values.
    "299": SoftwareVersionWorkflow.run,  # The software versions.
    "300": AssetBulkWorkflow.run,  # The bulk snapshot links.
    "301": AccessCheckWorkflow.run,  # The access check.
    "302": CorrelationWorkflow.run,  # The ticket correlation.
    "303": LookupWorkflow.run,  # The request lookup.
    "304": AssetLookupWorkflow.run,  # The asset lookup.
}


def _asset(serial: str) -> dict[str, Any]:
    """Return one synthetic asset record with its warranty row and its contract detail line."""
    return {  # Every key that the asset parser reads, with a synthetic value.
        "serialNumber": serial,
        "assetStatus": "Active",
        "softwareSupportReferenceNumber": "SSRN-EXAMPLE-1",
        "registrationDate": "2024-01-15",
        "shipDate": "2023-11-02",
        "productSKU": ASSET_SKU,
        "productSKUDescription": "Example 24-port switch",
        "productSKUEolDate": "2030-01-01",
        "productSKUEosDate": "2028-01-01",
        "serviceEligible": "Yes",
        "productLine": "EXAMPLE SERIES",
        "parentSerialNumber": "",
        "parentProductSKU": "",
        "installedAtName": "Example Site HQ",
        "rmaInfo": {"rmaNumber": replies.RMA_NUMBER, "rmaLineItemStatus": "Received"},
        "warranty": [
            {
                "index": "1",
                "warrantyDescription": "Return to factory warranty",
                "warrantyStartDate": "2023-11-02",
                "warrantyEndDate": "2026-11-02",
            }
        ],
        "serviceContract": [
            {
                "contractNumber": "CONTRACT-EXAMPLE-1",
                "endCustomerName": "Example End Customer Ltd",
                "resellerName": "Example Reseller Inc",
                "contractDetails": [
                    {
                        "index": "1",
                        "serviceSKUDescription": "Next business day support",
                        "contractStartDate": "2024-01-15",
                        "contractEndDate": "2027-01-15",
                        "contractLineItemNumber": "1",
                        "contractStatus": "Active",
                        "serviceSKU": "SVC-SKU-1",
                        "serviceType": "Support",
                        "serviceSKUShipmentServiceLevel": "NBD",
                        "serviceSKUEosDate": "2029-01-15",
                    }
                ],
            }
        ],
    }


def asset_reply(serials: list[str]) -> dict[str, Any]:
    """Return the asset reply that answers each serial number with one synthetic asset."""
    return {  # The response wrapper of the asset details operation.
        "queryAssetsDetailsResponse": {
            "statusCode": "200",  # The body status that the reader accepts.
            "assets": [_asset(serial) for serial in serials],  # One record for each number that was asked.
            "invalidSerialNumbersOrSSRNs": [],  # Every number of the harness exists.
            "notProcessedSerialNumbersOrSSRNs": [],  # Every number is answered on the first pass.
        }
    }


def _asset_body(call: FakeCall) -> dict[str, Any]:
    """Answer an asset request with one record for each serial number that the service sent."""
    serials = call.body["queryAssetsDetailsRequest"]["serialNumbersOrSSRNs"]  # The numbers in the envelope.
    return asset_reply(list(serials))  # Build the reply for exactly those numbers.


# The synthetic body for each endpoint. A builder receives the call that the service just recorded.
BODY_BUILDERS: dict[str, Callable[[FakeCall], dict[str, Any]]] = {
    "querysrlist": lambda _call: replies.list_reply(),  # The request list, also used by the access check.
    "querysrdetails": lambda _call: replies.detail_reply(),  # The request detail, also used by the lookups.
    "querysrnotedetails": lambda call: replies.note_reply(call.body["querySRNoteRequest"]["noteId"]),
    "queryrmadetails": lambda _call: replies.rma_reply(),  # The RMA detail.
    "getlov": lambda _call: replies.lov_reply(),  # The list of values (a GET).
    "getSoftwareEosLov": lambda _call: replies.eos_reply(),  # The software versions (a GET).
    "queryAssetsBulkData": lambda _call: replies.bulk_reply(),  # The bulk snapshot links.
    "queryAssetsDetails": _asset_body,  # The asset records, one for each serial number.
}


class CannedJuniperGateway(FakeGateway):
    """A gateway that answers every call from the synthetic bodies, and never from a queue.

    Why:
        A browser run can call the same endpoint several times, so a queue would run dry.
        Each reply is built from the call that the service just recorded, so the note
        identifier and the serial numbers in the reply match the request.
    """

    def __init__(self, statuses: dict[str, int], failures: dict[str, str]) -> None:
        """Store the HTTP status and the transport failure to use for each endpoint, when a test sets one."""
        super().__init__()  # The fake keeps its own queues, which this double never uses.
        self._statuses = dict(statuses)  # A copy, so a run cannot change the test's status table.
        self._failures = dict(failures)  # A copy, so a run cannot change the test's failure table.

    def _next_reply(self, endpoint: str, transaction: str) -> JuniperTransportReply:
        """Return the synthetic reply for the call that the service has just recorded."""
        failure = self._failures.get(endpoint)  # A queued failure replaces the reply.
        if failure is not None:  # The gateway raises the failure before any reply exists.
            raise JuniperTransportError(failure)  # The workflow catches it and names the failure in the run log.
        builder = BODY_BUILDERS.get(endpoint)  # The body builder of this endpoint.
        if builder is None:  # An endpoint without a builder is a gap in the harness, so fail loudly.
            raise AssertionError(f"The Juniper browser harness has no reply for the endpoint {endpoint}")
        return JuniperTransportReply(  # The same reply shape that the real gateway returns.
            endpoint=endpoint,
            http_status=self._statuses.get(endpoint, 200),  # A configured status replaces the success status.
            body=builder(self.calls[-1]),  # The body for the call that the service recorded last.
            transaction_id=transaction,
            attempts=1,  # One attempt, because the double never fails transiently.
        )


def sample_tickets(now: datetime) -> list[MistTicket]:
    """Return three Mist tickets: a recent match, an older match, and a ticket that matches no request."""
    return [  # The order is the order that the correlation export lists them.
        MistTicket(  # A recent ticket whose case number matches the one request of the list.
            ticket_id="T-1001",
            case_number=replies.CASE_NUMBER,
            status="open",
            subject="Router reboots after the upgrade",
            created_at=(now - timedelta(days=5)).isoformat(),
        ),
        MistTicket(  # An older ticket, which the correlation resolves through a detail lookup.
            ticket_id="T-0900",
            case_number=replies.CASE_NUMBER,
            status="closed",
            subject="Switch port flaps on the uplink",
            created_at=(now - timedelta(days=200)).isoformat(),
        ),
        MistTicket(  # A ticket whose case number no request of the account carries.
            ticket_id="T-1002",
            case_number="C-EXAMPLE-404",
            status="open",
            subject="Access point offline in the lobby",
            created_at=(now - timedelta(days=3)).isoformat(),
        ),
    ]


class JuniperWorld:
    """The synthetic Juniper and Mist state that every browser run reads.

    Why:
        A test can change one value, such as the HTTP status of one endpoint, and the next run
        reads the change. The owning fixture resets the world after each test that changes it.
    """

    def __init__(self, tickets: list[MistTicket]) -> None:
        """Store the Mist tickets that menu 302 correlates, and start with no status override."""
        self.statuses: dict[str, int] = {}  # HTTP status overrides, keyed by the endpoint name.
        self.failures: dict[str, str] = {}  # Transport failures, keyed by the endpoint name.
        self._tickets = list(tickets)  # The tickets of this world.

    def session(self) -> SimpleNamespace:
        """Return a session for one run. It uses the current status overrides."""
        gateway = CannedJuniperGateway(
            self.statuses, self.failures
        )  # A fresh gateway that reads the current overrides.
        return build_session(gateway, make_settings())  # The real services, wired to the double.

    def tickets(self) -> list[MistTicket]:
        """Return a copy of the Mist tickets, so one run cannot change the world."""
        return list(self._tickets)  # Copy the list, not the tickets, because each ticket is immutable.

    def reset(self) -> None:
        """Remove every status override, so the next test starts from the clean world."""
        self.statuses.clear()  # Forget every override that a previous test set.
        self.failures.clear()  # Forget every failure that a previous test queued.


def juniper_menu_actions() -> dict[str, MenuEntry]:
    """Return the static menu rows, with the eleven Juniper rows bound to their real workflow entry points."""
    actions = build_static_menu_actions()  # The rows that every portal test shares.
    for menu, handler in JUNIPER_HANDLERS.items():  # Bind each Juniper row to its workflow.
        actions[menu] = replace(actions[menu], handler=handler)  # Keep the title and the category, add the handler.
    return actions
