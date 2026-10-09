"""Export rows, log masks, and the retention purge for the Juniper outputs (R-14).

The exports and the optional database mirror keep personal values in full. Log lines
mask them through PersonalDataMasker.for_log, so a log never shows a raw personal value.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log for each retention removal.
import os  # WHY: check and remove export files by path.
import re  # WHY: find e-mail addresses inside free text.
import time  # WHY: the current time for the retention cutoff.
from collections.abc import Callable  # WHY: the type of a log mask.
from typing import Any  # WHY: export rows are loosely typed dictionaries.

from src.operations.exporting.juniper_rma.model.asset import (  # WHY: asset rows read these records.
    AssetCoverageRow,
    AssetRecord,
)
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: rows read these.
    RmaItem,
    RmaRecord,
    ServiceRequest,
)

logger = logging.getLogger(__name__)  # WHY: module logger for the masking and the retention events.


class PersonalDataMasker:
    """Mask personal values for log lines. Business names, codes, and dates stay visible."""

    MASKED_STREET = "[masked]"  # WHY: a street line is never exported in full.
    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")  # WHY: finds addresses in text.

    @staticmethod
    def name(value: str) -> str:
        """Keep the first letter of each word of a person's name and hide the rest."""
        words = [word for word in value.split() if word]  # WHY: skip repeated spaces.
        return " ".join(word[0] + "***" for word in words)  # WHY: first letter stays, the rest is hidden.

    @staticmethod
    def email(value: str) -> str:
        """Keep the first letter of the local part and the whole domain."""
        local, _separator, domain = value.partition("@")  # WHY: split at the first at-sign.
        if not domain:  # WHY: a value without a domain is hidden whole.
            return "***" if value else ""  # WHY: keep the empty case empty.
        return f"{local[:1]}***@{domain}"  # WHY: the domain helps an operator, the local part does not.

    @staticmethod
    def phone(value: str) -> str:
        """Keep the last two digits of a telephone number."""
        digits = value.strip()  # WHY: spaces are not part of the number.
        if len(digits) <= 2:  # WHY: a very short value cannot keep two digits and hide anything.
            return "**" if digits else ""  # WHY: hide the value, keep the empty case empty.
        return "*" * (len(digits) - 2) + digits[-2:]  # WHY: last two digits stay visible.

    @classmethod
    def street(cls, value: str) -> str:
        """Replace a street line with a fixed mask when it has a value."""
        return cls.MASKED_STREET if value else ""  # WHY: an empty line stays empty.

    @classmethod
    def free_text(cls, value: str) -> str:
        """Replace each e-mail address in free text with the masked form. The other words stay visible."""
        return cls.EMAIL_PATTERN.sub(lambda match: cls.email(match.group(0)), value)  # WHY: R-14 for free text.

    @staticmethod
    def ascii_text(value: str) -> str:
        """Return the value with each non-ASCII character replaced by a question mark."""
        return value.encode("ascii", "replace").decode("ascii")  # WHY: FR-029 requires ASCII-only output.

    @staticmethod
    def for_log(column: str, value: Any) -> Any:
        """Return the log form of one value. A business column or a non-text value comes back unchanged."""
        mask = LOG_MASKS.get(column)  # WHY: only the personal columns have a log mask.
        if mask is None or not isinstance(value, str):  # WHY: business and non-text values need no mask.
            return value  # WHY: the value is logged as it is.
        return mask(value)  # WHY: the log form hides the personal part.


# WHY: the personal columns of every Juniper table, each with the mask that its log line uses.
LOG_MASKS: dict[str, Callable[[str], str]] = {
    "contactName": PersonalDataMasker.name,  # WHY: personal name.
    "srOwnerFullName": PersonalDataMasker.name,  # WHY: owner name.
    "originator": PersonalDataMasker.name,  # WHY: note originator name.
    "summaryOriginator": PersonalDataMasker.name,  # WHY: note summary originator name.
    "uploadedBy": PersonalDataMasker.name,  # WHY: attachment uploader name.
    "escalatedBy": PersonalDataMasker.name,  # WHY: escalating person name.
    "receivedBy": PersonalDataMasker.name,  # WHY: replacement receiver name.
    "shipToContact": PersonalDataMasker.name,  # WHY: ship-to contact name.
    "contactEmail": PersonalDataMasker.email,  # WHY: contact e-mail.
    "srOwnerEmailAddress": PersonalDataMasker.email,  # WHY: owner e-mail.
    "preferredTelephoneNumber": PersonalDataMasker.phone,  # WHY: preferred telephone.
    "telephoneNumber": PersonalDataMasker.phone,  # WHY: RMA contact telephone.
    "vendorPhone": PersonalDataMasker.phone,  # WHY: vendor telephone.
    "address1": PersonalDataMasker.street,  # WHY: street line.
    "address2": PersonalDataMasker.street,  # WHY: street line.
    "synopsis": PersonalDataMasker.free_text,  # WHY: free text may hold an address.
    "problemDescription": PersonalDataMasker.free_text,  # WHY: free text may hold an address.
    "ccEmail": PersonalDataMasker.free_text,  # WHY: CC addresses.
    "content": PersonalDataMasker.free_text,  # WHY: note content may hold an address.
    "summaryContent": PersonalDataMasker.free_text,  # WHY: recent note content may hold an address.
}


class ExportRowBuilder:
    """Build the export rows and the column lists of each Juniper output."""

    @classmethod
    def ascii_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:  # WHY: one place for the ASCII rule.
        """Return copies of the rows with each text value made ASCII-only. Other values pass through."""
        cleaned: list[dict[str, Any]] = []  # WHY: the caller keeps its own rows unchanged.
        for row in rows:  # WHY: clean one row at a time.
            cleaned_row = {  # WHY: a copy of this row with its text made ASCII-only.
                key: PersonalDataMasker.ascii_text(value) if isinstance(value, str) else value  # WHY: text only.
                for key, value in row.items()  # WHY: every column of the row.
            }
            cleaned.append(cleaned_row)  # WHY: keep the cleaned copy.
        return cleaned  # WHY: every cleaned row, in the same order.

    CORRELATION_FIELDS = [  # WHY: the columns of JuniperCorrelation.csv (contracts/menu-and-exports.md).
        "mistTicketId",
        "mistCaseNumber",
        "joinValue",
        "mistSubject",
        "mistStatus",
        "matchStatus",
        "candidateCount",
        "unmatchedReason",
        "serviceRequestNumber",
        "candidateRequests",
        "srStatus",
        "rmaNumber",
        "itemType",
        "itemNumber",
        "serialNumber",
        "productID",
        "carrierDescription",
        "trackingNumber",
        "shipDate",
        "deliveredDate",
        "rmaStatus",
        "shipToCompany",
        "shipToContact",
        "shipToCityState",
        "shipToCountry",
        "runId",
    ]  # WHY: keep the order stable so each run writes the same header.
    REQUEST_FIELDS = [  # WHY: the columns of JuniperServiceRequests.csv and JuniperLookup.csv.
        "serviceRequestNumber",
        "customerCaseNumber",
        "caseTypeCode",
        "priority",
        "srStatus",
        "synopsis",
        "productID",
        "productSeries",
        "platform",
        "serialNumber",
        "software",
        "version",
        "release",
        "routerName",
        "accountName",
        "lastModifiedDate",
        "linkToCase",
        "rmaNumbers",
        "retrievedAt",
    ]
    RMA_ITEM_FIELDS = [  # WHY: the columns of JuniperRmaItems.csv, with the personal fields in full.
        "rmaNumber",
        "serviceRequestNumber",
        "itemType",
        "itemNumber",
        "defectiveItemNumber",
        "productID",
        "serialNumber",
        "carrier",
        "trackingNumber",
        "dateTime",
        "receivedDate",
        "shipDate",
        "deliveredDate",
        "shipmentLevel",
        "status",
        "receivedBy",
        "vendorName",
        "vendorPhone",
        "serviceRequestedDate",
        "actualServicedDate",
        "contactedDate",
        "estimatedArrivalDate",
        "companyName",
        "contactName",
        "contactEmail",
        "telephoneCountryCode",
        "telephoneNumber",
        "address1",
        "address2",
        "city",
        "stateCode",
        "state",
        "countryCode",
        "country",
        "postalCode",
        "retrievedAt",
    ]
    ASSET_FIELDS = [  # WHY: the columns of JuniperAssets.csv.
        "serialNumber",
        "assetStatus",
        "softwareSupportReferenceNumber",
        "registrationDate",
        "shipDate",
        "productSKU",
        "productSKUDescription",
        "productSKUEolDate",
        "productSKUEosDate",
        "serviceEligible",
        "productLine",
        "parentSerialNumber",
        "parentProductSKU",
        "installedAtName",
        "rmaNumber",
        "rmaLineItemStatus",
        "retrievedAt",
    ]
    COVERAGE_FIELDS = [  # WHY: the columns of JuniperAssetCoverage.csv.
        "serialNumber",
        "coverageKind",
        "index",
        "description",
        "startDate",
        "endDate",
        "contractNumber",
        "contractLineItemNumber",
        "contractStatus",
        "serviceSKU",
        "serviceType",
        "shipmentServiceLevel",
        "eosDate",
        "endCustomerName",
        "resellerName",
        "retrievedAt",
    ]
    RUN_FIELDS = [  # WHY: the columns of JuniperRunRecords.csv, in the order of RunRecord.as_row.
        "runId",
        "operation",
        "startedAt",
        "endedAt",
        "ticketCount",
        "matchedCount",
        "unmatchedCount",
        "ambiguousCount",
        "failedCount",
        "requestCount",
        "purgedCount",
        "status",
        "reason",
    ]

    @staticmethod
    def request_row(request: ServiceRequest, retrieved_at: str) -> dict[str, Any]:
        """Return the export row of one service request."""
        return {  # WHY: the request columns, with the RMA numbers joined by commas.
            "serviceRequestNumber": request.request_number,  # WHY: natural key.
            "customerCaseNumber": request.case_number,  # WHY: join value.
            "caseTypeCode": request.case_type,  # WHY: case type code.
            "priority": request.priority,  # WHY: priority code.
            "srStatus": request.status,  # WHY: request status.
            "synopsis": request.synopsis,  # WHY: short title, kept in full.
            "productID": request.product_id,  # WHY: product identifier.
            "productSeries": request.product_series,  # WHY: product series.
            "platform": request.platform,  # WHY: platform name.
            "serialNumber": request.serial_number,  # WHY: serial number.
            "software": request.software,  # WHY: software name.
            "version": request.version,  # WHY: software version.
            "release": request.release,  # WHY: software release.
            "routerName": request.router_name,  # WHY: router name.
            "accountName": request.account_name,  # WHY: account name, a business value.
            "lastModifiedDate": request.last_modified,  # WHY: modified date as text.
            "linkToCase": request.link,  # WHY: portal link.
            "rmaNumbers": ",".join(request.rma_numbers),  # WHY: the RMA list in one column.
            "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
        }

    @classmethod
    def item_row(cls, rma: RmaRecord, item: RmaItem, retrieved_at: str) -> dict[str, Any]:
        """Return the export row of one RMA item, with its personal fields in full."""
        row = cls._item_part(item)  # WHY: the item columns in one helper.
        row.update(cls._shipping_part(rma))  # WHY: the shipping columns in another helper.
        row["retrievedAt"] = retrieved_at  # WHY: the run time in UTC.
        return row  # WHY: the complete row.

    @staticmethod
    def _item_part(item: RmaItem) -> dict[str, Any]:
        """Return the item columns. The received-by name and the vendor telephone are kept in full."""
        return {  # WHY: item fields, with the personal values in full.
            "rmaNumber": item.rma_number,  # WHY: part of the key.
            "itemType": item.item_type,  # WHY: part of the key.
            "itemNumber": item.item_number,  # WHY: part of the key.
            "defectiveItemNumber": item.defective_item_number,  # WHY: parent item.
            "productID": item.product_id,  # WHY: product identifier.
            "serialNumber": item.serial_number,  # WHY: serial number.
            "carrier": item.carrier,  # WHY: carrier.
            "trackingNumber": item.tracking_number,  # WHY: tracking number.
            "dateTime": item.date_time,  # WHY: created date as text.
            "receivedDate": item.received_date,  # WHY: received date as text.
            "shipDate": item.ship_date,  # WHY: ship date as text.
            "deliveredDate": item.delivered_date,  # WHY: delivered date as text, may be malformed.
            "shipmentLevel": item.shipment_level,  # WHY: shipment level.
            "status": item.status,  # WHY: item status.
            "receivedBy": item.received_by,  # WHY: personal name, kept in full.
            "vendorName": item.vendor_name,  # WHY: vendor name.
            "vendorPhone": item.vendor_phone,  # WHY: telephone, kept in full.
            "serviceRequestedDate": item.service_requested_date,  # WHY: CE date as text.
            "actualServicedDate": item.actual_serviced_date,  # WHY: CE date as text.
            "contactedDate": item.contacted_date,  # WHY: CE date as text.
            "estimatedArrivalDate": item.estimated_arrival_date,  # WHY: CE date as text.
        }

    @staticmethod
    def _shipping_part(rma: RmaRecord) -> dict[str, Any]:
        """Return the shipping and contact columns of one RMA. Personal values are kept in full."""
        return {  # WHY: contact and address fields, with personal values in full.
            "serviceRequestNumber": rma.request_number,  # WHY: parent request.
            "companyName": rma.company_name,  # WHY: company name, a business value.
            "contactName": rma.contact_name,  # WHY: personal name, kept in full.
            "contactEmail": rma.contact_email,  # WHY: e-mail, kept in full.
            "telephoneCountryCode": rma.telephone_country_code,  # WHY: country code stays visible.
            "telephoneNumber": rma.telephone_number,  # WHY: telephone, kept in full.
            "address1": rma.address1,  # WHY: street line, kept in full.
            "address2": rma.address2,  # WHY: street line, kept in full.
            "city": rma.city,  # WHY: city is a business location.
            "stateCode": rma.state_code,  # WHY: state code.
            "state": rma.state,  # WHY: state name.
            "countryCode": rma.country_code,  # WHY: country code.
            "country": rma.country,  # WHY: country name.
            "postalCode": rma.postal_code,  # WHY: postal code.
        }

    @staticmethod
    def asset_row(asset: AssetRecord, retrieved_at: str) -> dict[str, Any]:
        """Return the export row of one asset. The site name is a business value."""
        return {  # WHY: the asset columns from the record.
            "serialNumber": asset.serial_number,  # WHY: natural key.
            "assetStatus": asset.asset_status,  # WHY: asset status.
            "softwareSupportReferenceNumber": asset.ssrn,  # WHY: support reference.
            "registrationDate": asset.registration_date,  # WHY: date as text.
            "shipDate": asset.ship_date,  # WHY: date as text.
            "productSKU": asset.product_sku,  # WHY: SKU.
            "productSKUDescription": asset.product_sku_description,  # WHY: description.
            "productSKUEolDate": asset.eol_date,  # WHY: date as text.
            "productSKUEosDate": asset.eos_date,  # WHY: date as text.
            "serviceEligible": asset.service_eligible,  # WHY: eligibility.
            "productLine": asset.product_line,  # WHY: product line.
            "parentSerialNumber": asset.parent_serial,  # WHY: parent serial.
            "parentProductSKU": asset.parent_sku,  # WHY: parent SKU.
            "installedAtName": asset.installed_at_name,  # WHY: site name.
            "rmaNumber": asset.rma_number,  # WHY: latest RMA number.
            "rmaLineItemStatus": asset.rma_status,  # WHY: latest RMA status.
            "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
        }

    @staticmethod
    def coverage_row(row: AssetCoverageRow, retrieved_at: str) -> dict[str, Any]:
        """Return the export row of one warranty or contract line. Contact and address fields are not stored."""
        return {  # WHY: the coverage columns from the record.
            "serialNumber": row.serial_number,  # WHY: parent serial.
            "coverageKind": row.coverage_kind,  # WHY: warranty or contract.
            "index": row.index,  # WHY: source index.
            "description": row.description,  # WHY: description.
            "startDate": row.start_date,  # WHY: start as text.
            "endDate": row.end_date,  # WHY: end as text.
            "contractNumber": row.contract_number,  # WHY: contract number.
            "contractLineItemNumber": row.contract_line_item,  # WHY: contract line.
            "contractStatus": row.contract_status,  # WHY: contract status.
            "serviceSKU": row.service_sku,  # WHY: service SKU.
            "serviceType": row.service_type,  # WHY: service type.
            "shipmentServiceLevel": row.shipment_level,  # WHY: service level.
            "eosDate": row.eos_date,  # WHY: end-of-sale as text.
            "endCustomerName": row.end_customer_name,  # WHY: business name, not an address.
            "resellerName": row.reseller_name,  # WHY: business name, not an address.
            "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
        }


class PersonalDataRetention:
    """Remove this feature's export files that are older than the retention window (R-14)."""

    OUTPUT_NAMES = (  # WHY: every export that can hold a personal value.
        "JuniperCorrelation.csv",
        "JuniperRmaItems.csv",
        "JuniperLookup.csv",
        "JuniperLookupRmaItems.csv",
        "JuniperRequestList.csv",
        "JuniperRequestDetail.csv",
        "JuniperRequestDetailRecords.csv",
        "JuniperRmaDetail.csv",
        "JuniperRmaDetailItems.csv",
        "JuniperRequestNotes.csv",
        "JuniperAssetBulkLinks.csv",
    )
    SECONDS_PER_DAY = 86400  # WHY: the unit of the retention setting.

    def __init__(self, retention_days: int, output_dir: str = "data") -> None:
        """Store the window and the folder that holds the exports."""
        self._retention_days = retention_days  # WHY: the window from JUNIPER_PII_RETENTION_DAYS.
        self._output_dir = output_dir  # WHY: the export folder that DataExporter writes to.

    def purge(self, now: float | None = None) -> int:
        """Remove each expired export file and return how many files were removed."""
        current = time.time() if now is None else now  # WHY: the current time, or an injected time in tests.
        cutoff = current - self._retention_days * self.SECONDS_PER_DAY  # WHY: files older than this are expired.
        logger.info("Retention purge: removing exports older than %d days", self._retention_days)  # WHY: action log.
        removed = 0  # WHY: count the removals for the run record.
        for name in self.OUTPUT_NAMES:  # WHY: check each known output.
            if self._remove_if_expired(os.path.join(self._output_dir, name), name, cutoff):  # WHY: one file at a time.
                removed += 1  # WHY: count the file.
        logger.debug("Retention purge removed %d file(s)", removed)  # WHY: count only.
        return removed  # WHY: the count goes into the run record.

    @staticmethod
    def _remove_if_expired(path: str, name: str, cutoff: float) -> bool:
        """Remove one file when it is older than the cutoff. Return True when it was removed."""
        if not os.path.isfile(path) or os.path.getmtime(path) >= cutoff:  # WHY: keep files inside the window.
            return False  # WHY: nothing to remove.
        try:  # WHY: a locked file must not stop the run.
            os.remove(path)  # WHY: delete the expired export.
        except OSError as error:  # WHY: log the failure and keep going.
            logger.warning("Retention could not remove %s: %s", name, type(error).__name__)  # WHY: type only.
            return False  # WHY: the file stays.
        logger.info("Retention removed %s", name)  # WHY: action log after the removal.
        return True  # WHY: the file is gone.
