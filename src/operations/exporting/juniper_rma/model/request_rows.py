"""Column tables and row builders for the full-field Juniper Case reads.

Each table entry names one output column and the dotted path of its value in the Juniper
reply. Every field that a reply returns has one column, so each export holds the whole reply.
Personal values stay in full in the exports. Log lines mask them (R-14).
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from collections.abc import Mapping, Sequence  # WHY: typed table entries and reply sources.
from dataclasses import dataclass  # WHY: immutable table entries.
from typing import Any  # WHY: the reply is loosely typed JSON.

from src.operations.exporting.juniper_rma.model.service_request import FieldReader  # WHY: null-safe reads of the reply.


def read_text(source: object, path: str) -> str:
    """Return the text at a dotted path. A missing step or a null value gives an empty string."""
    node: object = source  # WHY: start at the root of the reply.
    for part in path.split("."):  # WHY: walk one object level for each part of the path.
        node = node.get(part) if isinstance(node, dict) else None  # WHY: a missing step ends the walk.
    return "" if node is None else str(node).strip()  # WHY: null is empty, and other values become text.


@dataclass(frozen=True)
class FieldSpec:
    """One output column: its name and the dotted source path of its value in the reply."""

    column: str  # WHY: the header name in the export.
    path: str  # WHY: the dotted path in the reply, for example contact.accountID.


class RecordRowBuilder:
    """Build one export row from a table of field specifications."""

    @staticmethod
    def build(source: Mapping[str, Any], specs: Sequence[FieldSpec], retrieved_at: str) -> dict[str, str]:
        """Return one row with one value for each column."""
        row = {spec.column: read_text(source, spec.path) for spec in specs}  # WHY: one value per column.
        row["retrievedAt"] = retrieved_at  # WHY: the run time in UTC.
        return row  # WHY: the complete row.

    @staticmethod
    def columns(specs: Sequence[FieldSpec], derived: Sequence[str] = ()) -> list[str]:
        """Return the header of a table: the spec columns, the derived columns, then the retrieval time."""
        return [spec.column for spec in specs] + list(derived) + ["retrievedAt"]  # WHY: one header per table.


LIST_SPECS: tuple[FieldSpec, ...] = (  # WHY: every field that the list reply returns, in reply order.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: natural key of the request.
    FieldSpec("customerCaseNumber", "customerCaseNumber"),  # WHY: join value with the Mist ticket.
    FieldSpec("accountID", "accountID"),  # WHY: account identifier.
    FieldSpec("accountName", "accountName"),  # WHY: account name, a business value.
    FieldSpec("customerSourceID", "customerSourceID"),  # WHY: source identifier of the request.
    FieldSpec("caseTypeCode", "caseTypeCode"),  # WHY: case type code.
    FieldSpec("caseTypeDescription", "caseTypeDescription"),  # WHY: case type text.
    FieldSpec("adminSRType", "adminSRType"),  # WHY: admin request type.
    FieldSpec("adminSRSubType", "adminSRSubType"),  # WHY: admin request sub type.
    FieldSpec("priority", "priority"),  # WHY: priority code.
    FieldSpec("srStatus", "srStatus"),  # WHY: request status.
    FieldSpec("synopsis", "synopsis"),  # WHY: free text, kept in full.
    FieldSpec("problemDescription", "problemDescription"),  # WHY: free text, kept in full.
    FieldSpec("contactName", "contactName"),  # WHY: contact name is personal.
    FieldSpec("contactEmail", "contactEmail"),  # WHY: contact e-mail is personal.
    FieldSpec("ccEmail", "ccEmail"),  # WHY: CC addresses are personal.
    FieldSpec("srOwnerEmailAddress", "srOwnerEmailAddress"),  # WHY: owner e-mail.
    FieldSpec("productID", "productID"),  # WHY: product identifier.
    FieldSpec("productSeries", "productSeries"),  # WHY: product series.
    FieldSpec("platform", "platform"),  # WHY: platform name.
    FieldSpec("serialNumber", "serialNumber"),  # WHY: serial number.
    FieldSpec("software", "software"),  # WHY: software name.
    FieldSpec("version", "version"),  # WHY: software version.
    FieldSpec("release", "release"),  # WHY: software release.
    FieldSpec("specialRelease", "specialRelease"),  # WHY: special release, when the request names one.
    FieldSpec("routerName", "routerName"),  # WHY: router name.
    FieldSpec("lastModifiedDate", "lastModifiedDate"),  # WHY: last modified date as text.
    FieldSpec("linkToCase", "linkToCase"),  # WHY: portal link to the request.
)


class RequestListRows:
    """Build the rows of the request list export. Each row keeps every field of one request."""

    DERIVED: tuple[str, ...] = ("rmaNumbers",)  # WHY: RMA numbers joined into one column.
    COLUMNS: list[str] = RecordRowBuilder.columns(LIST_SPECS, DERIVED)  # WHY: the header of the export.

    @classmethod
    def row(cls, raw: Mapping[str, Any], retrieved_at: str) -> dict[str, str]:
        """Return the row of one request from the list reply."""
        row = RecordRowBuilder.build(raw, LIST_SPECS, retrieved_at)  # WHY: the table columns.
        row["rmaNumbers"] = ",".join(_rma_numbers(raw))  # WHY: the RMA list, joined for one column.
        return row  # WHY: the complete row.


def _rma_numbers(source: Mapping[str, Any]) -> list[str]:
    """Return the RMA numbers that a request names, in reply order, without blanks."""
    numbers = [read_text(item, "rmaNumber") for item in FieldReader.items(source, "rma")]  # WHY: one per item.
    return [number for number in numbers if number]  # WHY: drop blank values.


DETAIL_SPECS: tuple[FieldSpec, ...] = (  # WHY: every top-level and product, contact, and case-type field of the detail.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: natural key of the request.
    FieldSpec("customerCaseNumber", "customerCaseNumber"),  # WHY: empty in the detail reply, kept for the record.
    FieldSpec("customerSourceID", "customerSourceID"),  # WHY: source identifier of the reply.
    FieldSpec("customerUniqueTransactionID", "customerUniqueTransactionID"),  # WHY: transaction of the reply.
    FieldSpec("status", "status"),  # WHY: body status text of the reply.
    FieldSpec("statusCode", "statusCode"),  # WHY: body status code of the reply.
    FieldSpec("message", "message"),  # WHY: body message of the reply.
    FieldSpec("responseDateTime", "responseDateTime"),  # WHY: Juniper response time.
    FieldSpec("linkToCase", "linkToCase"),  # WHY: portal link to the request.
    FieldSpec("synopsis", "synopsis"),  # WHY: free text, kept in full.
    FieldSpec("problemDescription", "problemDescription"),  # WHY: free text, kept in full.
    FieldSpec("priority", "priority"),  # WHY: priority code.
    FieldSpec("srStatus", "srStatus"),  # WHY: request status.
    FieldSpec("adminSRType", "adminSRType"),  # WHY: admin request type.
    FieldSpec("adminSRSubType", "adminSRSubType"),  # WHY: admin request sub type.
    FieldSpec("addSenderToEmail", "addSenderToEmail"),  # WHY: notification flag.
    FieldSpec("ccEmail", "ccEmail"),  # WHY: CC addresses are personal.
    FieldSpec("srOwnerFullName", "srOwnerFullName"),  # WHY: owner name is personal.
    FieldSpec("srOwnerEmailAddress", "srOwnerEmailAddress"),  # WHY: owner e-mail.
    FieldSpec("caseTypeCode", "caseType.caseTypeCode"),  # WHY: case type code.
    FieldSpec("caseTypeDescription", "caseType.caseTypeDescription"),  # WHY: case type text.
    FieldSpec("contactAccountID", "contact.accountID"),  # WHY: account identifier.
    FieldSpec("contactAccountName", "contact.accountName"),  # WHY: account name, a business value.
    FieldSpec("contactName", "contact.contactName"),  # WHY: contact name is personal.
    FieldSpec("contactEmail", "contact.contactEmail"),  # WHY: contact e-mail.
    FieldSpec("preferredTelephoneCountryCode", "contact.preferredTelephoneCountryCode"),  # WHY: country code.
    FieldSpec("preferredTelephoneNumber", "contact.preferredTelephoneNumber"),  # WHY: phone.
    FieldSpec("preferredTelephoneExtension", "contact.preferredTelephoneExtension"),  # WHY: extension.
    FieldSpec("productID", "product.productID"),  # WHY: product identifier.
    FieldSpec("productSeries", "product.productSeries"),  # WHY: product series.
    FieldSpec("platform", "product.platform"),  # WHY: platform name.
    FieldSpec("serialNumber", "product.serialNumber"),  # WHY: serial number.
    FieldSpec("software", "product.software"),  # WHY: software name.
    FieldSpec("version", "product.version"),  # WHY: software version.
    FieldSpec("release", "product.release"),  # WHY: software release.
    FieldSpec("specialRelease", "product.specialRelease"),  # WHY: special release.
    FieldSpec("routerName", "product.routerName"),  # WHY: router name.
)
DETAIL_DERIVED: tuple[str, ...] = (  # WHY: counts and lists of the nested records, one column each.
    "rmaCount",
    "rmaNumbers",
    "noteCount",
    "recentNoteCount",
    "attachmentCount",
    "escalationCount",
)


class RequestDetailRows:
    """Build the one-row summary of a request detail. The nested records go to DetailRecordRows."""

    COLUMNS: list[str] = RecordRowBuilder.columns(DETAIL_SPECS, DETAIL_DERIVED)  # WHY: the header of the export.

    @classmethod
    def row(cls, detail: Mapping[str, Any], retrieved_at: str) -> dict[str, str]:
        """Return the summary row of one request detail, with the counts of its nested records."""
        row = RecordRowBuilder.build(detail, DETAIL_SPECS, retrieved_at)  # WHY: the scalar fields.
        row["rmaCount"] = str(len(FieldReader.items(detail, "rma")))  # WHY: how many RMAs the request names.
        row["rmaNumbers"] = ",".join(_rma_numbers(detail))  # WHY: the RMA numbers in one column.
        row["noteCount"] = str(len(FieldReader.items(detail, "notes")))  # WHY: how many notes the reply lists.
        row["recentNoteCount"] = str(len(FieldReader.items(detail, "recentNotes")))  # WHY: recent notes count.
        row["attachmentCount"] = str(len(FieldReader.items(detail, "attachments")))  # WHY: attachments count.
        row["escalationCount"] = str(len(FieldReader.items(detail, "escalate")))  # WHY: escalations count.
        return row  # WHY: the complete summary row.


NOTE_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: a note listed by the detail reply, with its summary text.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request, injected by the builder.
    FieldSpec("recordType", "recordType"),  # WHY: note, recentNote, attachment, escalation, rma, or rmaItem.
    FieldSpec("recordId", "id"),  # WHY: the note identifier.
    FieldSpec("dateTime", "dateTime"),  # WHY: note date as text.
    FieldSpec("title", "title"),  # WHY: note title.
    FieldSpec("description", "description"),  # WHY: note description, free text.
    FieldSpec("originator", "originator"),  # WHY: originator name is personal.
    FieldSpec("originatorRole", "originatorRole"),  # WHY: originator role.
)
RECENT_NOTE_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: a recent note, with its content.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("recordType", "recordType"),  # WHY: record kind.
    FieldSpec("recordId", "id"),  # WHY: the note identifier.
    FieldSpec("dateTime", "dateTime"),  # WHY: note date as text.
    FieldSpec("originator", "originator"),  # WHY: originator name is personal.
    FieldSpec("originatorRole", "originatorRole"),  # WHY: originator role.
    FieldSpec("content", "content"),  # WHY: note content, kept in full.
)
ATTACHMENT_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: an attachment listed by the detail reply.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("recordType", "recordType"),  # WHY: record kind.
    FieldSpec("recordId", "sequenceNumber"),  # WHY: the sequence number names the attachment.
    FieldSpec("path", "path"),  # WHY: attachment path as Juniper returns it.
    FieldSpec("sequenceNumber", "sequenceNumber"),  # WHY: sequence number.
    FieldSpec("sizeInBytes", "sizeInBytes"),  # WHY: size in bytes as text.
    FieldSpec("title", "title"),  # WHY: attachment title.
    FieldSpec("typeDescription", "typeDescription"),  # WHY: attachment type.
    FieldSpec("uploadedBy", "uploadedBy"),  # WHY: uploader name is personal.
    FieldSpec("uploadedDate", "uploadedDate"),  # WHY: upload date as text.
)
ESCALATION_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: an escalation listed by the detail reply.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("recordType", "recordType"),  # WHY: record kind.
    FieldSpec("dateTime", "dateTime"),  # WHY: escalation date as text.
    FieldSpec("description", "description"),  # WHY: escalation description.
    FieldSpec("escalatedBy", "escalatedBy"),  # WHY: escalating person is personal.
    FieldSpec("status", "status"),  # WHY: escalation status.
)
RMA_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: an RMA number listed by the detail reply.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("recordType", "recordType"),  # WHY: record kind.
    FieldSpec("recordId", "rmaNumber"),  # WHY: the RMA number names the record.
    FieldSpec("rmaNumber", "rmaNumber"),  # WHY: the RMA number.
)
RMA_ITEM_RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: an item of an RMA listed by the detail reply.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("recordType", "recordType"),  # WHY: record kind.
    FieldSpec("recordId", "itemNumber"),  # WHY: the item number names the record.
    FieldSpec("rmaNumber", "rmaNumber"),  # WHY: parent RMA, injected by the builder.
    FieldSpec("itemType", "itemType"),  # WHY: item type.
    FieldSpec("itemNumber", "itemNumber"),  # WHY: item number.
    FieldSpec("itemStatus", "itemStatus"),  # WHY: item status.
)
RECORD_SPECS: tuple[FieldSpec, ...] = (  # WHY: one header for every kind of nested record.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),
    FieldSpec("recordType", "recordType"),
    FieldSpec("recordId", "recordId"),
    FieldSpec("dateTime", "dateTime"),
    FieldSpec("title", "title"),
    FieldSpec("description", "description"),
    FieldSpec("originator", "originator"),
    FieldSpec("originatorRole", "originatorRole"),
    FieldSpec("content", "content"),
    FieldSpec("path", "path"),
    FieldSpec("sequenceNumber", "sequenceNumber"),
    FieldSpec("sizeInBytes", "sizeInBytes"),
    FieldSpec("typeDescription", "typeDescription"),
    FieldSpec("uploadedBy", "uploadedBy"),
    FieldSpec("uploadedDate", "uploadedDate"),
    FieldSpec("escalatedBy", "escalatedBy"),
    FieldSpec("status", "status"),
    FieldSpec("rmaNumber", "rmaNumber"),
    FieldSpec("itemType", "itemType"),
    FieldSpec("itemNumber", "itemNumber"),
    FieldSpec("itemStatus", "itemStatus"),
)


class DetailRecordRows:
    """Flatten the nested lists of a request detail into one row for each record, with every column."""

    COLUMNS: list[str] = RecordRowBuilder.columns(RECORD_SPECS)  # WHY: the header of the records export.
    SOURCES: tuple[tuple[str, str, tuple[FieldSpec, ...]], ...] = (  # WHY: list key, record kind, and table.
        ("notes", "note", NOTE_RECORD_SPECS),
        ("recentNotes", "recentNote", RECENT_NOTE_RECORD_SPECS),
        ("attachments", "attachment", ATTACHMENT_RECORD_SPECS),
        ("escalate", "escalation", ESCALATION_RECORD_SPECS),
        ("rma", "rma", RMA_RECORD_SPECS),
    )

    @classmethod
    def rows(cls, detail: Mapping[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each nested record of the detail, including each RMA item."""
        request_number = read_text(detail, "serviceRequestNumber")  # WHY: every record names its request.
        rows: list[dict[str, str]] = []  # WHY: collect the rows in reply order.
        for list_key, kind, specs in cls.SOURCES:  # WHY: one pass for each kind of record.
            for record in FieldReader.items(detail, list_key):  # WHY: only objects are records.
                source = {**record, "serviceRequestNumber": request_number, "recordType": kind}  # WHY: inject keys.
                rows.append(cls._full_width(RecordRowBuilder.build(source, specs, retrieved_at)))  # WHY: one row.
        rows.extend(cls._item_rows(detail, request_number, retrieved_at))  # WHY: RMA items nest under each RMA.
        return rows  # WHY: every record of the detail.

    @classmethod
    def _item_rows(cls, detail: Mapping[str, Any], request_number: str, retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each item of each RMA, with the parent RMA number."""
        rows: list[dict[str, str]] = []  # WHY: collect the item rows.
        for rma in FieldReader.items(detail, "rma"):  # WHY: each RMA carries its items.
            rma_number = read_text(rma, "rmaNumber")  # WHY: the parent RMA number.
            for item in FieldReader.items(rma, "items"):  # WHY: each item of the RMA.
                source = {  # WHY: the item plus its parents, so one table reads all of them.
                    **item,
                    "serviceRequestNumber": request_number,
                    "recordType": "rmaItem",
                    "rmaNumber": rma_number,
                }
                rows.append(cls._full_width(RecordRowBuilder.build(source, RMA_ITEM_RECORD_SPECS, retrieved_at)))
        return rows  # WHY: the item rows in reply order.

    @classmethod
    def _full_width(cls, row: dict[str, str]) -> dict[str, str]:
        """Return the row with every record column, so each row has the same keys."""
        return {column: row.get(column, "") for column in cls.COLUMNS}  # WHY: one key set for the export.


NOTE_SPECS: tuple[FieldSpec, ...] = (  # WHY: one note read with its reply fields and its detail summary.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("customerCaseNumber", "customerCaseNumber"),  # WHY: the reply case key, empty for these requests.
    FieldSpec("customerSourceID", "customerSourceID"),  # WHY: source identifier of the reply.
    FieldSpec("customerUniqueTransactionID", "customerUniqueTransactionID"),  # WHY: transaction of the reply.
    FieldSpec("responseDateTime", "responseDateTime"),  # WHY: Juniper response time.
    FieldSpec("status", "status"),  # WHY: body status text.
    FieldSpec("statusCode", "statusCode"),  # WHY: body status code.
    FieldSpec("message", "message"),  # WHY: body message.
    FieldSpec("noteId", "id"),  # WHY: the note identifier.
    FieldSpec("noteSource", "noteSource"),  # WHY: notes or recentNotes, from the detail list.
    FieldSpec("dateTime", "dateTime"),  # WHY: note date as text.
    FieldSpec("originatorRole", "originatorRole"),  # WHY: originator role.
    FieldSpec("content", "content"),  # WHY: note content, kept in full.
    FieldSpec("linkToCase", "linkToCase"),  # WHY: portal link to the request.
    FieldSpec("summaryTitle", "summary.title"),  # WHY: title from the detail list.
    FieldSpec("summaryDescription", "summary.description"),  # WHY: description from the detail list.
    FieldSpec("summaryOriginator", "summary.originator"),  # WHY: personal name, kept in full.
    FieldSpec("summaryOriginatorRole", "summary.originatorRole"),  # WHY: role from the detail list.
    FieldSpec("summaryDateTime", "summary.dateTime"),  # WHY: date from the detail list.
    FieldSpec("summaryContent", "summary.content"),  # WHY: recent note content, kept in full.
)


class NoteRows:
    """Build the rows of the note export. Each row keeps the reply and the detail summary of one note."""

    COLUMNS: list[str] = RecordRowBuilder.columns(NOTE_SPECS)  # WHY: the header of the notes export.

    @classmethod
    def row(
        cls, note_id: str, source: str, summary: Mapping[str, Any], reply: Mapping[str, Any], retrieved_at: str
    ) -> dict[str, str]:
        """Return the row of one note, with the note identifier used when the reply omits it."""
        combined = {  # WHY: one source for the table: the reply, the detail summary, and the note source.
            "id": note_id,  # WHY: keep the requested identifier when the reply does not return one.
            **reply,
            "noteSource": source,  # WHY: the detail list that named the note.
            "summary": dict(summary),  # WHY: the summary sits under one key for the dotted paths.
        }
        return RecordRowBuilder.build(combined, NOTE_SPECS, retrieved_at)  # WHY: the row.


RMA_HEADER_SPECS: tuple[FieldSpec, ...] = (  # WHY: every top-level and contact field of an RMA reply.
    FieldSpec("rmaNumber", "rmaNumber"),  # WHY: the RMA number.
    FieldSpec("serviceRequestNumber", "serviceRequestNumber"),  # WHY: parent request.
    FieldSpec("customerCaseNumber", "customerCaseNumber"),  # WHY: case key of the reply.
    FieldSpec("customerSourceID", "customerSourceID"),  # WHY: source identifier of the reply.
    FieldSpec("customerUniqueTransactionID", "customerUniqueTransactionID"),  # WHY: transaction of the reply.
    FieldSpec("linkToCase", "linkToCase"),  # WHY: portal link to the request.
    FieldSpec("status", "status"),  # WHY: body status text.
    FieldSpec("statusCode", "statusCode"),  # WHY: body status code.
    FieldSpec("message", "message"),  # WHY: body message.
    FieldSpec("responseDateTime", "responseDateTime"),  # WHY: Juniper response time.
    FieldSpec("companyName", "rmaContact.companyName"),  # WHY: company name, a business value.
    FieldSpec("contactName", "rmaContact.contactName"),  # WHY: personal name, kept in full.
    FieldSpec("contactEmail", "rmaContact.contactEmail"),  # WHY: personal e-mail, kept in full.
    FieldSpec("telephoneCountryCode", "rmaContact.telephoneCountryCode"),  # WHY: country code.
    FieldSpec("telephoneNumber", "rmaContact.telephoneNumber"),  # WHY: telephone, kept in full.
    FieldSpec("address1", "rmaContact.address.address1"),  # WHY: street line, kept in full.
    FieldSpec("address2", "rmaContact.address.address2"),  # WHY: street line, kept in full.
    FieldSpec("city", "rmaContact.address.city"),  # WHY: city.
    FieldSpec("stateCode", "rmaContact.address.stateCode"),  # WHY: state code.
    FieldSpec("state", "rmaContact.address.state"),  # WHY: state name.
    FieldSpec("countryCode", "rmaContact.address.countryCode"),  # WHY: country code.
    FieldSpec("country", "rmaContact.address.country"),  # WHY: country name.
    FieldSpec("postalCode", "rmaContact.address.postalCode"),  # WHY: postal code.
)
RMA_HEADER_DERIVED: tuple[str, ...] = (  # WHY: one count for each RMA item list.
    "defectiveItemCount",
    "replacementItemCount",
    "ceItemCount",
)


class RmaHeaderRows:
    """Build the one-row summary of an RMA reply, with the count of each item list."""

    COLUMNS: list[str] = RecordRowBuilder.columns(RMA_HEADER_SPECS, RMA_HEADER_DERIVED)  # WHY: the header.

    @classmethod
    def row(cls, result: Mapping[str, Any], retrieved_at: str) -> dict[str, str]:
        """Return the summary row of one RMA reply."""
        row = RecordRowBuilder.build(result, RMA_HEADER_SPECS, retrieved_at)  # WHY: the header fields.
        row["defectiveItemCount"] = str(len(FieldReader.items(result, "defectiveItems")))  # WHY: defective count.
        row["replacementItemCount"] = str(len(FieldReader.items(result, "replacementItems")))  # WHY: replacements.
        row["ceItemCount"] = str(len(FieldReader.items(result, "ceItems")))  # WHY: customer engineer count.
        return row  # WHY: the complete summary row.
