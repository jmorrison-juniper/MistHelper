"""Row builders for the Juniper reference reads: list of values, software versions, and bulk asset links.

The list-of-values reply has no fixed schema, so its groups are flattened into one row for each
scalar value, with the full dotted path. Signed file links keep their host and path, and their
query string is replaced by a mask, so a credential never reaches an export or the console (R-15).
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from typing import Any  # WHY: the replies are loosely typed JSON.
from urllib.parse import urlsplit  # WHY: split a link into its scheme, host, path, and query.

from src.operations.exporting.juniper_rma.model.service_request import FieldReader  # WHY: null-safe reads of the reply.


class LovRows:
    """Flatten the list-of-values reply into one row for each scalar value, with its full path."""

    COLUMNS: tuple[str, ...] = ("lovGroup", "lovPath", "lovValue", "valueType", "retrievedAt")  # WHY: the header.

    @classmethod
    def rows(cls, payload: dict[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each scalar value. The top-level key names the group of the value."""
        sink: list[dict[str, str]] = []  # WHY: collect the rows in reply order.
        for group, value in payload.items():  # WHY: each top-level key is one group of values.
            cls._walk(str(group), str(group), value, sink, retrieved_at)  # WHY: walk the group from its key.
        return sink  # WHY: every value of every group.

    @classmethod
    def _walk(cls, group: str, path: str, value: Any, sink: list[dict[str, str]], retrieved_at: str) -> None:
        """Visit one node. An object adds a key, a list adds an index, and a scalar becomes one row."""
        if isinstance(value, dict):  # WHY: an object adds each of its keys to the path.
            for key, item in value.items():  # WHY: visit each key of the object.
                cls._walk(group, f"{path}.{key}", item, sink, retrieved_at)  # WHY: recurse into the key.
        elif isinstance(value, list):  # WHY: a list adds each index to the path.
            for index, item in enumerate(value):  # WHY: visit each element in order.
                cls._walk(group, f"{path}[{index}]", item, sink, retrieved_at)  # WHY: recurse into the element.
        else:  # WHY: a scalar is one value of the group.
            sink.append(cls._row(group, path, value, retrieved_at))  # WHY: keep the value and its type.

    @staticmethod
    def _row(group: str, path: str, value: Any, retrieved_at: str) -> dict[str, str]:
        """Return the row of one scalar. The value is text, and its Python type is kept as a column."""
        return {  # WHY: the columns of one value.
            "lovGroup": group,  # WHY: the top-level group.
            "lovPath": path,  # WHY: the full dotted and indexed path.
            "lovValue": "" if value is None else str(value),  # WHY: null stays empty.
            "valueType": type(value).__name__,  # WHY: the type shows how the value was read.
            "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
        }


class SoftwareVersionRows:
    """Flatten the software version reply into one row for each release of each platform of each series."""

    COLUMNS: tuple[str, ...] = ("productSeries", "platform", "versionRelease", "retrievedAt")  # WHY: the header.

    @classmethod
    def rows(cls, payload: dict[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each release. A platform with no release keeps one row with an empty release."""
        sink: list[dict[str, str]] = []  # WHY: collect the rows in reply order.
        for series in FieldReader.items(payload, "SoftwareVersions"):  # WHY: one entry for each product series.
            series_name = FieldReader.text(series, "Product Series")  # WHY: the series key has a space in the name.
            for platform in FieldReader.items(series, "Platforms"):  # WHY: one entry for each platform.
                sink.extend(cls._platform_rows(series_name, platform, retrieved_at))  # WHY: its releases.
        return sink  # WHY: every release in reply order.

    @classmethod
    def _platform_rows(cls, series_name: str, platform: dict[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return the rows of one platform, one for each release."""
        platform_name = FieldReader.text(platform, "platform")  # WHY: the platform name.
        raw_releases = platform.get("versionReleases")  # WHY: the release list may be missing.
        releases = [str(item).strip() for item in raw_releases] if isinstance(raw_releases, list) else []  # WHY.
        values = releases or [""]  # WHY: a platform with no release still appears once.
        return [  # WHY: one row for each release value.
            {
                "productSeries": series_name,  # WHY: the product series.
                "platform": platform_name,  # WHY: the platform.
                "versionRelease": release,  # WHY: one release string.
                "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
            }
            for release in values
        ]


class BulkLinkRows:
    """Build the rows of the bulk asset read: one row for each file link and one for each no-data entry."""

    LINK_COLUMNS: tuple[str, ...] = (  # WHY: the header of the links export.
        "snapshotDate",
        "urlMasked",
        "urlValidFromDateTime",
        "urlValidToDateTime",
        "responseDateTime",
        "customerSourceID",
        "customerUniqueTransactionID",
        "retrievedAt",
    )
    NO_DATA_COLUMNS: tuple[str, ...] = (  # WHY: the header of the no-data export.
        "snapshotDate",
        "message",
        "responseDateTime",
        "customerSourceID",
        "customerUniqueTransactionID",
        "retrievedAt",
    )

    @staticmethod
    def mask_url(value: str) -> str:
        """Return the scheme, host, and path of a link. A query string, which holds the signature, becomes a mask."""
        if not value:  # WHY: an empty link stays empty.
            return ""  # WHY: nothing to mask.
        parts = urlsplit(value)  # WHY: split the link into its parts.
        marker = "?[masked]" if parts.query else ""  # WHY: a signed query is never printed or saved.
        return f"{parts.scheme}://{parts.netloc}{parts.path}{marker}"  # WHY: the link without its credential.

    @staticmethod
    def _data(result: dict[str, Any]) -> dict[str, Any]:
        """Return the nested data object when present, otherwise the top-level result."""
        data = result.get("data")  # WHY: the example nests the lists under data.
        return data if isinstance(data, dict) else result  # WHY: the schema may also place them at the top.

    @classmethod
    def _shared(cls, result: dict[str, Any], retrieved_at: str) -> dict[str, str]:
        """Return the reply fields that every row of one reply shares."""
        return {  # WHY: the reply identifiers and times repeat on each row.
            "responseDateTime": FieldReader.text(result, "responseDateTime"),  # WHY: Juniper response time.
            "customerSourceID": FieldReader.text(result, "customerSourceID"),  # WHY: source identifier.
            "customerUniqueTransactionID": FieldReader.text(result, "customerUniqueTransactionID"),  # WHY: transaction.
            "retrievedAt": retrieved_at,  # WHY: the run time in UTC.
        }

    @classmethod
    def links(cls, result: dict[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each file link. The link itself is masked."""
        data = cls._data(result)  # WHY: the lists sit under data in the example.
        shared = cls._shared(result, retrieved_at)  # WHY: the reply fields repeat on each row.
        return [  # WHY: one row for each link object.
            {
                "snapshotDate": FieldReader.text(item, "snapshotDate"),  # WHY: the snapshot date.
                "urlMasked": cls.mask_url(FieldReader.text(item, "url")),  # WHY: the link, without its signature.
                "urlValidFromDateTime": FieldReader.text(item, "urlValidFromDateTime"),  # WHY: validity start.
                "urlValidToDateTime": FieldReader.text(item, "urlValidToDateTime"),  # WHY: validity end.
                **shared,  # WHY: the reply fields.
            }
            for item in FieldReader.items(data, "links")  # WHY: only objects are link rows.
        ]

    @classmethod
    def no_data(cls, result: dict[str, Any], retrieved_at: str) -> list[dict[str, str]]:
        """Return one row for each snapshot date that Juniper reports as having no data."""
        data = cls._data(result)  # WHY: the lists sit under data in the example.
        shared = cls._shared(result, retrieved_at)  # WHY: the reply fields repeat on each row.
        return [  # WHY: one row for each no-data object.
            {
                "snapshotDate": FieldReader.text(item, "snapshotDate"),  # WHY: the snapshot date.
                "message": FieldReader.text(item, "message"),  # WHY: the reason that Juniper gives.
                **shared,  # WHY: the reply fields.
            }
            for item in FieldReader.items(data, "noDataFound")  # WHY: only objects are no-data rows.
        ]
