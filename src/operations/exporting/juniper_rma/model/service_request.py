"""Parsers for Juniper service requests, RMA records, and RMA items.

Dates stay as text, so a malformed timestamp keeps its raw value (R-09).
Each parser accepts the variants that the Juniper exports document.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import re  # WHY: the identifier rule is a whole-value pattern match.
from dataclasses import dataclass  # WHY: immutable parsed records.
from typing import Any, ClassVar  # WHY: parsed JSON is loosely typed, and class constants need ClassVar.


class IdentifierRule:
    """Check the identifier format of Juniper inputs: 1 to 40 letters, digits, or hyphens."""

    PATTERN = re.compile(r"[A-Za-z0-9-]{1,40}")  # WHY: the input rule of contracts/menu-and-exports.md.

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Return True when the whole value matches the identifier rule."""
        return bool(cls.PATTERN.fullmatch(value))  # WHY: fullmatch rejects any extra character.


class FieldReader:
    """Read typed values from parsed JSON without raising on a missing or unexpected field."""

    @staticmethod
    def text(source: Any, key: str) -> str:
        """Return the field as trimmed text, or an empty string when it is missing."""
        if not isinstance(source, dict):  # WHY: only an object holds fields.
            return ""  # WHY: a missing object reads as empty text.
        value = source.get(key)  # WHY: the raw field value.
        if value is None:  # WHY: a null field reads as empty text.
            return ""  # WHY: no value.
        return str(value).strip()  # WHY: spaces around a value are not part of it.

    @staticmethod
    def mapping(source: Any, key: str) -> dict[str, Any]:
        """Return the nested object, or an empty dict when it is missing or not an object."""
        value = source.get(key) if isinstance(source, dict) else None  # WHY: read the nested field.
        return value if isinstance(value, dict) else {}  # WHY: only an object is a mapping.

    @staticmethod
    def items(source: Any, key: str) -> list[dict[str, Any]]:
        """Return the objects in a list field. A single object counts as a list of one."""
        value = source.get(key) if isinstance(source, dict) else None  # WHY: read the nested field.
        if isinstance(value, dict):  # WHY: the variant where one object replaces the list (R-09).
            return [value]  # WHY: callers iterate the same way for both forms.
        if not isinstance(value, list):  # WHY: a missing or odd field has no items.
            return []  # WHY: nothing to parse.
        return [item for item in value if isinstance(item, dict)]  # WHY: keep only objects.


@dataclass(frozen=True)
class ServiceRequest:
    """One Juniper service request, from the list or the detail operation."""

    request_number: str  # WHY: natural key of the request.
    case_number: str  # WHY: customer case number, the join value (R-05).
    case_type: str  # WHY: case type code.
    priority: str  # WHY: priority code.
    status: str  # WHY: request status.
    synopsis: str  # WHY: short title of the request.
    product_id: str  # WHY: product identifier.
    product_series: str  # WHY: product series.
    platform: str  # WHY: platform name.
    serial_number: str  # WHY: serial number that links to RMA items and assets.
    software: str  # WHY: software name.
    version: str  # WHY: software version.
    release: str  # WHY: software release.
    router_name: str  # WHY: router name.
    last_modified: str  # WHY: last modified date from the list.
    account_name: str  # WHY: account name, a business value.
    link: str  # WHY: portal link to the request.
    rma_numbers: tuple[str, ...] = ()  # WHY: RMA numbers that the detail operation lists.

    @classmethod
    def from_list_row(cls, row: dict[str, Any]) -> ServiceRequest:
        """Build the request from one row of the list operation."""
        return cls(  # WHY: the list row carries the summary fields.
            request_number=FieldReader.text(row, "serviceRequestNumber"),  # WHY: natural key.
            case_number=FieldReader.text(row, "customerCaseNumber"),  # WHY: join value.
            case_type=FieldReader.text(row, "caseTypeCode"),  # WHY: case type code.
            priority=FieldReader.text(row, "priority"),  # WHY: priority code.
            status=FieldReader.text(row, "srStatus"),  # WHY: request status.
            synopsis=FieldReader.text(row, "synopsis"),  # WHY: short title.
            product_id=FieldReader.text(row, "productID"),  # WHY: product identifier.
            product_series=FieldReader.text(row, "productSeries"),  # WHY: product series.
            platform=FieldReader.text(row, "platform"),  # WHY: platform name.
            serial_number=FieldReader.text(row, "serialNumber"),  # WHY: serial number.
            software=FieldReader.text(row, "software"),  # WHY: software name.
            version=FieldReader.text(row, "version"),  # WHY: software version.
            release=FieldReader.text(row, "release"),  # WHY: software release.
            router_name=FieldReader.text(row, "routerName"),  # WHY: router name.
            last_modified=FieldReader.text(row, "lastModifiedDate"),  # WHY: last modified date as text.
            account_name=FieldReader.text(row, "accountName"),  # WHY: account name.
            link=FieldReader.text(row, "linkToCase"),  # WHY: portal link.
        )

    @classmethod
    def from_detail(cls, detail: dict[str, Any]) -> ServiceRequest:
        """Build the request from the detail operation, including its RMA list."""
        case_type = FieldReader.mapping(detail, "caseType")  # WHY: the case type object.
        contact = FieldReader.mapping(detail, "contact")  # WHY: the account object.
        product = FieldReader.mapping(detail, "product")  # WHY: the product object.
        rma_numbers = tuple(  # WHY: keep the RMA numbers in reply order, without blanks.
            number
            for number in (FieldReader.text(item, "rmaNumber") for item in FieldReader.items(detail, "rma"))
            if number
        )
        return cls(  # WHY: the detail carries the complete request.
            request_number=FieldReader.text(detail, "serviceRequestNumber"),  # WHY: natural key.
            case_number=FieldReader.text(detail, "customerCaseNumber"),  # WHY: join value.
            case_type=FieldReader.text(case_type, "caseTypeCode"),  # WHY: case type code.
            priority=FieldReader.text(detail, "priority"),  # WHY: priority code.
            status=FieldReader.text(detail, "srStatus"),  # WHY: request status.
            synopsis=FieldReader.text(detail, "synopsis"),  # WHY: short title.
            product_id=FieldReader.text(product, "productID"),  # WHY: product identifier.
            product_series=FieldReader.text(product, "productSeries"),  # WHY: product series.
            platform=FieldReader.text(product, "platform"),  # WHY: platform name.
            serial_number=FieldReader.text(product, "serialNumber"),  # WHY: serial number.
            software=FieldReader.text(product, "software"),  # WHY: software name.
            version=FieldReader.text(product, "version"),  # WHY: software version.
            release=FieldReader.text(product, "release"),  # WHY: software release.
            router_name=FieldReader.text(product, "routerName"),  # WHY: router name.
            last_modified="",  # WHY: the detail operation does not return a modified date.
            account_name=FieldReader.text(contact, "accountName"),  # WHY: account name.
            link="",  # WHY: the detail operation does not return a portal link.
            rma_numbers=rma_numbers,  # WHY: the RMA list for the fan-out.
        )


@dataclass(frozen=True)
class RmaRecord:
    """Shipping and contact data of one RMA. Personal fields are kept in full in the exports (R-14)."""

    rma_number: str  # WHY: natural key of the RMA.
    request_number: str  # WHY: parent service request.
    company_name: str  # WHY: company name, a business value.
    contact_name: str  # WHY: personal, kept in full in exports.
    contact_email: str  # WHY: personal, kept in full in exports.
    telephone_country_code: str  # WHY: country code stays visible.
    telephone_number: str  # WHY: personal, kept in full in exports.
    address1: str  # WHY: street line, kept in full in exports.
    address2: str  # WHY: street line, kept in full in exports.
    city: str  # WHY: business location.
    state_code: str  # WHY: state code.
    state: str  # WHY: state name.
    country_code: str  # WHY: country code.
    country: str  # WHY: country name.
    postal_code: str  # WHY: postal code.

    @classmethod
    def from_result(cls, result: dict[str, Any], request_number: str) -> RmaRecord:
        """Build the record from an RMA reply. The address may be nested or flat (R-09)."""
        contact = FieldReader.mapping(result, "rmaContact")  # WHY: the contact object.
        nested = FieldReader.mapping(contact, "address")  # WHY: the nested address variant.
        address = nested if nested else contact  # WHY: a flat address reads from the contact itself.
        return cls(  # WHY: every field is read as text.
            rma_number=FieldReader.text(result, "rmaNumber"),  # WHY: natural key.
            request_number=request_number,  # WHY: parent request from the caller.
            company_name=FieldReader.text(contact, "companyName"),  # WHY: company name.
            contact_name=FieldReader.text(contact, "contactName"),  # WHY: personal.
            contact_email=FieldReader.text(contact, "contactEmail"),  # WHY: personal.
            telephone_country_code=FieldReader.text(contact, "telephoneCountryCode"),  # WHY: visible.
            telephone_number=FieldReader.text(contact, "telephoneNumber"),  # WHY: personal.
            address1=FieldReader.text(address, "address1"),  # WHY: personal street line.
            address2=FieldReader.text(address, "address2"),  # WHY: personal street line.
            city=FieldReader.text(address, "city"),  # WHY: business location.
            state_code=FieldReader.text(address, "stateCode"),  # WHY: state code.
            state=FieldReader.text(address, "state"),  # WHY: state name.
            country_code=FieldReader.text(address, "countryCode"),  # WHY: country code.
            country=FieldReader.text(address, "country"),  # WHY: country name.
            postal_code=FieldReader.text(address, "postalCode"),  # WHY: postal code.
        )


@dataclass(frozen=True)
class RmaItem:
    """One defective, replacement, or customer-engineer item of an RMA."""

    rma_number: str  # WHY: parent RMA, part of the key.
    item_type: str  # WHY: defective, replacement, or ce, part of the key.
    item_number: str  # WHY: item number, part of the key.
    defective_item_number: str  # WHY: parent defective item for replacement and CE items.
    product_id: str  # WHY: product identifier.
    serial_number: str  # WHY: serial number that links to asset data.
    carrier: str  # WHY: carrier description.
    tracking_number: str  # WHY: tracking number.
    date_time: str  # WHY: created date, kept as text.
    received_date: str  # WHY: received date, kept as text.
    ship_date: str  # WHY: ship date, kept as text.
    delivered_date: str  # WHY: delivered date, kept as text (may be malformed).
    shipment_level: str  # WHY: shipment service level.
    status: str  # WHY: item status, normalized to one column.
    received_by: str  # WHY: personal name, kept in full in exports.
    vendor_name: str  # WHY: field service vendor.
    vendor_phone: str  # WHY: personal telephone, kept in full in exports.
    service_requested_date: str  # WHY: CE request date.
    actual_serviced_date: str  # WHY: CE service date.
    contacted_date: str  # WHY: CE contact date.
    estimated_arrival_date: str  # WHY: CE arrival estimate.

    SECTIONS: ClassVar[tuple[tuple[str, str, str], ...]] = (  # WHY: list key, item type, and status key.
        ("defectiveItems", "defective", "defectiveItemStatus"),
        ("replacementItems", "replacement", "replacementStatus"),
        ("ceItems", "ce", "engineerStatus"),
    )

    @classmethod
    def parse_all(cls, rma_number: str, result: dict[str, Any]) -> list[RmaItem]:
        """Return every item of the RMA reply, in the order defective, replacement, and CE."""
        items: list[RmaItem] = []  # WHY: collect the items across the three lists.
        for list_key, item_type, status_key in cls.SECTIONS:  # WHY: one pass per item list.
            for index, raw in enumerate(FieldReader.items(result, list_key), start=1):  # WHY: index for unique keys.
                items.append(cls._from_raw(rma_number, item_type, status_key, raw, index))  # WHY: one record per item.
        return items  # WHY: every item of the RMA.

    @classmethod
    def _from_raw(
        cls,
        rma_number: str,
        item_type: str,
        status_key: str,
        raw: dict[str, Any],
        index: int,
    ) -> RmaItem:
        """Build one item. A CE item has no item number, so the parent number and the index make the key."""
        defective_number = FieldReader.text(raw, "defectiveItemNumber")  # WHY: parent item for replacement and CE.
        item_number = (
            FieldReader.text(raw, "itemNumber") or defective_number or f"{item_type}-{index}"
        )  # WHY: unique key.
        return cls(  # WHY: every field is read as text.
            rma_number=rma_number,  # WHY: parent RMA.
            item_type=item_type,  # WHY: item type.
            item_number=item_number,  # WHY: item number with a fallback key.
            defective_item_number=defective_number,  # WHY: parent defective item.
            product_id=FieldReader.text(raw, "productID"),  # WHY: product identifier.
            serial_number=FieldReader.text(raw, "serialNumber"),  # WHY: serial number.
            carrier=FieldReader.text(raw, "carrierDescription"),  # WHY: carrier.
            tracking_number=FieldReader.text(raw, "trackingNumber"),  # WHY: tracking number.
            date_time=FieldReader.text(raw, "dateTime"),  # WHY: created date as text.
            received_date=FieldReader.text(raw, "receivedDate"),  # WHY: received date as text.
            ship_date=FieldReader.text(raw, "shipDate"),  # WHY: ship date as text.
            delivered_date=FieldReader.text(raw, "deliveredDate"),  # WHY: delivered date as text.
            shipment_level=FieldReader.text(raw, "shipmentServiceLevel"),  # WHY: shipment level.
            status=FieldReader.text(raw, status_key),  # WHY: the status under its item-type key.
            received_by=FieldReader.text(raw, "receivedBy"),  # WHY: personal name.
            vendor_name=FieldReader.text(raw, "vendorName"),  # WHY: vendor name.
            vendor_phone=FieldReader.text(raw, "vendorPhone"),  # WHY: personal telephone.
            service_requested_date=FieldReader.text(raw, "serviceRequestedDate"),  # WHY: CE date as text.
            actual_serviced_date=FieldReader.text(raw, "actualServicedDate"),  # WHY: CE date as text.
            contacted_date=FieldReader.text(raw, "contactedDate"),  # WHY: CE date as text.
            estimated_arrival_date=FieldReader.text(raw, "estimatedArrivalDate"),  # WHY: CE date as text.
        )
