"""Synthetic replies shaped like the live Juniper Case and Asset reads. No value here belongs to a customer.

The key names and the types follow the shape that the live probe recorded. The values are invented.
E-mail addresses use the example.com domain. Links use the invalid top-level domain.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from typing import Any  # WHY: the replies are loosely typed JSON.

SR_NUMBER = "R100000001"  # WHY: synthetic request number used across the fixtures.
CASE_NUMBER = "C-EXAMPLE-1"  # WHY: synthetic customer case number, present on the list row only.
RMA_NUMBER = "R200000001"  # WHY: synthetic RMA number that the request names.
NOTE_ID_ONE = "0D5EXAMPLE001-CustomerNotes"  # WHY: note named by the detail list and the recent list.
NOTE_ID_TWO = "0D5EXAMPLE002-CustomerNotes"  # WHY: a second note named only by the full list.
NOTE_ID_THREE = "0D5EXAMPLE003-CustomerNotes"  # WHY: a third note named only by the recent list.
SIGNED_LINK = "https://files.example.invalid/snap/2026-09-04.json.gz?X-Amz-Signature=SECRET123"  # WHY: masked.


def list_reply() -> dict[str, Any]:
    """Return the list reply with one request. The row holds every field of the live list."""
    row: dict[str, Any] = {  # WHY: every key that the live list returned, with a synthetic value.
        "serviceRequestNumber": SR_NUMBER,
        "customerCaseNumber": CASE_NUMBER,
        "accountID": "0000000000",
        "accountName": "Example Account Ltd",
        "customerSourceID": "example-source",
        "caseTypeCode": "TECH",
        "caseTypeDescription": "Technical support",
        "adminSRType": None,
        "adminSRSubType": None,
        "priority": "P3",
        "srStatus": "Open",
        "synopsis": "Router reboots after upgrade, reply to pat.example@example.com",
        "problemDescription": "Reboots after the upgrade. Owner copy: pat.example@example.com.",
        "contactName": "Pat Example",
        "contactEmail": "pat.example@example.com",
        "ccEmail": "lee.example@example.com; ops.example@example.com",
        "srOwnerEmailAddress": "owner.example@example.com",
        "productID": "EX-PRODUCT-1",
        "productSeries": "EXAMPLE SERIES",
        "platform": "EX-PLATFORM",
        "serialNumber": "SN000000001",
        "software": "example-os",
        "version": "1.0",
        "release": "1.0R1",
        "specialRelease": None,
        "routerName": None,
        "lastModifiedDate": "2026-09-01T10:00:00.000Z",
        "linkToCase": "https://example.invalid/case/1",
        "rma": [{"rmaNumber": RMA_NUMBER}],
    }
    return {"querySRListResponse": {"statusCode": "200", "status": "Success", "cases": [row]}}


def detail_reply() -> dict[str, Any]:
    """Return the detail reply of one request, with every nested record kind the live reply carries."""
    return {
        "serviceRequestNumber": SR_NUMBER,
        "customerCaseNumber": None,
        "customerSourceID": "example-source",
        "customerUniqueTransactionID": None,
        "status": "Success",
        "statusCode": "200",
        "message": "Successfully processed the request",
        "responseDateTime": "2026-09-01T10:00:01.000Z",
        "linkToCase": "https://example.invalid/case/1",
        "synopsis": "Router reboots after upgrade, reply to pat.example@example.com",
        "problemDescription": "Reboots after the upgrade. Owner copy: pat.example@example.com.",
        "priority": "P3",
        "srStatus": "Open",
        "adminSRType": None,
        "adminSRSubType": None,
        "addSenderToEmail": None,
        "ccEmail": "lee.example@example.com",
        "srOwnerFullName": "Lee Example",
        "srOwnerEmailAddress": "owner.example@example.com",
        "caseType": {"caseTypeCode": "TECH", "caseTypeDescription": "Technical support"},
        "contact": {
            "accountID": "0000000000",
            "accountName": "Example Account Ltd",
            "contactName": "Pat Example",
            "contactEmail": "pat.example@example.com",
            "preferredTelephoneCountryCode": "1",
            "preferredTelephoneNumber": "5550100123",
            "preferredTelephoneExtension": None,
        },
        "product": {
            "serialNumber": "SN000000001",
            "productID": "EX-PRODUCT-1",
            "productSeries": "EXAMPLE SERIES",
            "platform": "EX-PLATFORM",
            "version": "1.0",
            "release": "1.0R1",
            "software": "example-os",
            "specialRelease": None,
            "routerName": None,
        },
        "notes": [
            {
                "id": NOTE_ID_ONE,
                "description": "First note",
                "title": "Opened",
                "originator": "Pat Example",
                "dateTime": "2026-09-01T10:00:00.000Z",
                "originatorRole": "Customer",
            },
            {
                "id": NOTE_ID_TWO,
                "description": "Second note",
                "title": "Update",
                "originator": "Lee Example",
                "dateTime": "2026-09-02T10:00:00.000Z",
                "originatorRole": "Engineer",
            },
        ],
        "recentNotes": [
            {
                "id": NOTE_ID_ONE,
                "dateTime": "2026-09-01T10:00:00.000Z",
                "originator": "Pat Example",
                "originatorRole": "Customer",
                "content": "Please mail pat.example@example.com about this",
            },
            {
                "id": NOTE_ID_THREE,
                "dateTime": "2026-09-03T10:00:00.000Z",
                "originator": "Lee Example",
                "originatorRole": "Engineer",
                "content": "Fix scheduled",
            },
        ],
        "attachments": [
            {
                "path": "/files/log.txt",
                "sequenceNumber": "1",
                "sizeInBytes": "2048",
                "title": "log",
                "typeDescription": "text",
                "uploadedBy": "Lee Example",
                "uploadedDate": "2026-09-02",
            },
        ],
        "escalate": [
            {
                "dateTime": "2026-09-04T10:00:00.000Z",
                "description": "Escalated to the team",
                "escalatedBy": "Pat Example",
                "status": "Open",
            },
        ],
        "rma": [
            {
                "rmaNumber": RMA_NUMBER,
                "items": [{"itemNumber": "ITEM-1", "itemStatus": "Received", "itemType": "defective"}],
            },
        ],
    }


def rma_reply() -> dict[str, Any]:
    """Return the RMA reply with its contact block and one defective and one replacement item."""
    return {
        "rmaNumber": RMA_NUMBER,
        "serviceRequestNumber": SR_NUMBER,
        "customerCaseNumber": None,
        "customerSourceID": "example-source",
        "customerUniqueTransactionID": None,
        "linkToCase": "https://example.invalid/case/1",
        "status": "Success",
        "statusCode": "200",
        "message": "Successfully processed the request",
        "responseDateTime": "2026-09-03T10:00:00.000Z",
        "rmaContact": {
            "companyName": "Example Co",
            "contactName": "Pat Example",
            "contactEmail": "pat.example@example.com",
            "telephoneCountryCode": "1",
            "telephoneNumber": "5550100123",
            "address": {
                "address1": "1 Example Way",
                "address2": None,
                "city": "Example City",
                "country": "United States",
                "countryCode": "US",
                "postalCode": "00000",
                "state": "Example State",
                "stateCode": "EX",
            },
        },
        "defectiveItems": [
            {
                "itemNumber": "ITEM-1",
                "productID": "EX-PRODUCT-1",
                "serialNumber": "SN000000001",
                "carrierDescription": None,
                "dateTime": "2026-09-02T10:00:00.000Z",
                "defectiveItemStatus": "Received",
                "receivedDate": None,
                "trackingNumber": None,
            },
        ],
        "replacementItems": [
            {
                "itemNumber": "REPL-1",
                "productID": "EX-PRODUCT-1",
                "serialNumber": "SN000000002",
                "carrierDescription": "Example Carrier",
                "defectiveItemNumber": "ITEM-1",
                "deliveredDate": "2026-09-05",
                "receivedBy": "Dana Example",
                "replacementStatus": "Shipped",
                "shipDate": "2026-09-04",
                "shipmentServiceLevel": "Next day",
                "trackingNumber": "TRK1",
            },
        ],
        "ceItems": [],
    }


def note_reply(note_id: str) -> dict[str, Any]:
    """Return the note reply for one note identifier. The content holds an address."""
    return {
        "responseDateTime": "2026-09-06T10:00:00.000Z",
        "serviceRequestNumber": SR_NUMBER,
        "customerCaseNumber": None,
        "customerUniqueTransactionID": None,
        "customerSourceID": "example-source",
        "message": "Successfully processed the request",
        "status": "Success",
        "statusCode": "200",
        "id": note_id,
        "content": f"Note body for {note_id}, copy pat.example@example.com",
        "dateTime": "2026-09-06T10:00:00.000Z",
        "originatorRole": "Engineer",
        "linkToCase": "https://example.invalid/case/1",
    }


def lov_reply() -> dict[str, Any]:
    """Return the list of values. Its groups mix lists of strings and lists of objects."""
    return {
        "srStatus": ["Open", "Closed"],
        "carrier": [{"description": "Example Carrier", "code": "EC"}],
        "priority": ["P1", "P2", "P3"],
    }


def eos_reply() -> dict[str, Any]:
    """Return the software versions grouped by product series and platform. One platform has no release."""
    return {
        "SoftwareVersions": [
            {
                "Product Series": "EXAMPLE SERIES",
                "Platforms": [
                    {"platform": "EX-PLATFORM", "versionReleases": ["1.0R1", "1.0R2"]},
                    {"platform": "EX-EMPTY", "versionReleases": []},
                ],
            }
        ]
    }


def bulk_reply() -> dict[str, Any]:
    """Return the bulk asset reply with one signed link and one no-data date."""
    return {
        "assetsBulkDataResponse": {
            "responseDateTime": "2026-09-05T10:00:00.000Z",
            "customerSourceID": "example-source",
            "customerUniqueTransactionID": "0" * 32,
            "statusCode": "200",
            "status": "Success",
            "message": "Successfully processed the request",
            "data": {
                "noDataFound": [{"snapshotDate": "2026-09-03", "message": "noDataFound"}],
                "links": [
                    {
                        "url": SIGNED_LINK,
                        "snapshotDate": "2026-09-04",
                        "urlValidFromDateTime": "2026-09-05T00:00:00.000Z",
                        "urlValidToDateTime": "2026-09-12T00:00:00.000Z",
                    }
                ],
            },
        }
    }


def fault_reply(code: str, message: str, wrapper: str = "querySRDetailsResponse") -> dict[str, Any]:
    """Return a body-level fault reply with the given fault code and message."""
    return {  # WHY: the body status is 400 and the fault list names the code.
        wrapper: {
            "statusCode": "400",
            "status": "Error",
            "message": "Error in processing the request",
            "fault": [{"errorCode": code, "errorMessage": message}],
        }
    }
