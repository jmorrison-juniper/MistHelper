"""Parsers for Juniper asset records and warranty and contract coverage rows."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from dataclasses import dataclass  # WHY: immutable parsed records.
from typing import Any  # WHY: parsed JSON is loosely typed.

from src.operations.exporting.juniper_rma.model.service_request import (
    FieldReader,  # WHY: the shared typed field reader.
)


@dataclass(frozen=True)
class AssetRecord:
    """Warranty and status summary of one serial number from the asset details operation."""

    serial_number: str  # WHY: natural key of the asset.
    asset_status: str  # WHY: asset status.
    ssrn: str  # WHY: software support reference number.
    registration_date: str  # WHY: registration date as text.
    ship_date: str  # WHY: ship date as text.
    product_sku: str  # WHY: product SKU.
    product_sku_description: str  # WHY: product SKU description.
    eol_date: str  # WHY: end-of-life date as text.
    eos_date: str  # WHY: end-of-sale date as text.
    service_eligible: str  # WHY: service eligibility flag.
    product_line: str  # WHY: product line.
    parent_serial: str  # WHY: parent serial number for a field-replaceable unit.
    parent_sku: str  # WHY: parent SKU.
    installed_at_name: str  # WHY: customer site name, a business value.
    rma_number: str  # WHY: latest RMA number, when the asset has one.
    rma_status: str  # WHY: status of the latest RMA line item.

    @classmethod
    def from_api(cls, asset: dict[str, Any]) -> AssetRecord:
        """Build the record from one asset object of the reply."""
        rma = cls._latest_rma(asset)  # WHY: the RMA summary for the asset.
        return cls(  # WHY: every field is read as text.
            serial_number=FieldReader.text(asset, "serialNumber"),  # WHY: natural key.
            asset_status=FieldReader.text(asset, "assetStatus"),  # WHY: asset status.
            ssrn=FieldReader.text(asset, "softwareSupportReferenceNumber"),  # WHY: support reference.
            registration_date=FieldReader.text(asset, "registrationDate"),  # WHY: date as text.
            ship_date=FieldReader.text(asset, "shipDate"),  # WHY: date as text.
            product_sku=FieldReader.text(asset, "productSKU"),  # WHY: SKU.
            product_sku_description=FieldReader.text(asset, "productSKUDescription"),  # WHY: description.
            eol_date=FieldReader.text(asset, "productSKUEolDate"),  # WHY: date as text.
            eos_date=FieldReader.text(asset, "productSKUEosDate"),  # WHY: date as text.
            service_eligible=FieldReader.text(asset, "serviceEligible"),  # WHY: eligibility.
            product_line=FieldReader.text(asset, "productLine"),  # WHY: product line.
            parent_serial=FieldReader.text(asset, "parentSerialNumber"),  # WHY: parent serial.
            parent_sku=FieldReader.text(asset, "parentProductSKU"),  # WHY: parent SKU.
            installed_at_name=FieldReader.text(asset, "installedAtName"),  # WHY: site name.
            rma_number=FieldReader.text(rma, "rmaNumber"),  # WHY: latest RMA number.
            rma_status=FieldReader.text(rma, "rmaLineItemStatus"),  # WHY: latest RMA status.
        )

    @staticmethod
    def _latest_rma(asset: dict[str, Any]) -> dict[str, Any]:
        """Return the latest RMA summary. The field is one object or a list (O-7)."""
        items = FieldReader.items(asset, "rmaInfo")  # WHY: both variants become a list.
        return items[-1] if items else {}  # WHY: the last entry is the latest in a list.


@dataclass(frozen=True)
class AssetCoverageRow:
    """One warranty row or one contract line of an asset."""

    serial_number: str  # WHY: parent asset, part of the key.
    coverage_kind: str  # WHY: warranty or contract, part of the key.
    index: str  # WHY: source index, part of the key.
    description: str  # WHY: warranty or service description.
    start_date: str  # WHY: start date as text.
    end_date: str  # WHY: end date as text.
    contract_number: str  # WHY: contract number, blank for warranty rows.
    contract_line_item: str  # WHY: contract line item, part of the contract key.
    contract_status: str  # WHY: contract status.
    service_sku: str  # WHY: service SKU.
    service_type: str  # WHY: service type.
    shipment_level: str  # WHY: service shipment level.
    eos_date: str  # WHY: service end-of-sale date as text.
    end_customer_name: str  # WHY: end customer business name.
    reseller_name: str  # WHY: reseller business name.

    @classmethod
    def from_asset(cls, asset: dict[str, Any]) -> list[AssetCoverageRow]:
        """Return the warranty rows and the contract rows of one asset."""
        serial = FieldReader.text(asset, "serialNumber")  # WHY: the parent serial for every row.
        rows = [cls._warranty_row(serial, raw) for raw in FieldReader.items(asset, "warranty")]  # WHY: warranty rows.
        for contract in FieldReader.items(asset, "serviceContract"):  # WHY: one pass per contract.
            rows.extend(cls._contract_rows(serial, contract))  # WHY: one row per contract detail line.
        return rows  # WHY: every coverage row of the asset.

    @classmethod
    def _warranty_row(cls, serial: str, raw: dict[str, Any]) -> AssetCoverageRow:
        """Build one warranty row. Contract fields stay empty for a warranty."""
        return cls(  # WHY: warranty fields only.
            serial_number=serial,  # WHY: parent serial.
            coverage_kind="warranty",  # WHY: the row kind.
            index=FieldReader.text(raw, "index"),  # WHY: source index.
            description=FieldReader.text(raw, "warrantyDescription"),  # WHY: warranty text.
            start_date=FieldReader.text(raw, "warrantyStartDate"),  # WHY: start as text.
            end_date=FieldReader.text(raw, "warrantyEndDate"),  # WHY: end as text.
            contract_number="",  # WHY: no contract on a warranty row.
            contract_line_item="",  # WHY: no contract line on a warranty row.
            contract_status="",  # WHY: no contract status on a warranty row.
            service_sku="",  # WHY: no service SKU on a warranty row.
            service_type="",  # WHY: no service type on a warranty row.
            shipment_level="",  # WHY: no shipment level on a warranty row.
            eos_date="",  # WHY: no service end-of-sale on a warranty row.
            end_customer_name="",  # WHY: no end customer on a warranty row.
            reseller_name="",  # WHY: no reseller on a warranty row.
        )

    @classmethod
    def _contract_rows(cls, serial: str, contract: dict[str, Any]) -> list[AssetCoverageRow]:
        """Build one row for each contract detail line, with the contract's parties."""
        number = FieldReader.text(contract, "contractNumber")  # WHY: contract number for each line.
        customer = FieldReader.text(contract, "endCustomerName")  # WHY: business name, not an address.
        reseller = FieldReader.text(contract, "resellerName")  # WHY: business name, not an address.
        return [
            cls(  # WHY: one contract line per row.
                serial_number=serial,  # WHY: parent serial.
                coverage_kind="contract",  # WHY: the row kind.
                index=FieldReader.text(detail, "index"),  # WHY: source index of the line.
                description=FieldReader.text(detail, "serviceSKUDescription"),  # WHY: service description.
                start_date=FieldReader.text(detail, "contractStartDate"),  # WHY: start as text.
                end_date=FieldReader.text(detail, "contractEndDate"),  # WHY: end as text.
                contract_number=number,  # WHY: contract number.
                contract_line_item=FieldReader.text(detail, "contractLineItemNumber"),  # WHY: line number.
                contract_status=FieldReader.text(detail, "contractStatus"),  # WHY: contract status.
                service_sku=FieldReader.text(detail, "serviceSKU"),  # WHY: service SKU.
                service_type=FieldReader.text(detail, "serviceType"),  # WHY: service type.
                shipment_level=FieldReader.text(detail, "serviceSKUShipmentServiceLevel"),  # WHY: level.
                eos_date=FieldReader.text(detail, "serviceSKUEosDate"),  # WHY: end-of-sale as text.
                end_customer_name=customer,  # WHY: end customer name.
                reseller_name=reseller,  # WHY: reseller name.
            )
            for detail in FieldReader.items(contract, "contractDetails")  # WHY: one row per detail line.
        ]
