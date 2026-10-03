"""Safe row and payload construction for picker results."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.


class PickerRuntime:
    """Hold shared picker state and normalize response records."""

    _apisession: object  # Every picker behavior uses the authenticated SDK session.
    _org_id: str  # Organization-scope reads use the trusted portal identifier.
    _device_cache: dict[str, tuple[float, list[dict[str, object]]]]  # Device reads use the short cache.

    def _records(self, response: object) -> list[dict[str, object]]:
        """Return dictionary rows from one SDK response."""
        data = getattr(response, "data", [])  # Mist SDK responses store data on this attribute.
        if isinstance(data, dict):  # Some stats responses wrap rows in one object.
            data = data.get("results") or data.get("items") or data.get("sdkclients") or []  # Read known list keys.
        if not isinstance(data, list):  # Unknown response shapes cannot fill a picker.
            return []  # Refuse the unknown shape safely.
        return [dict(item) for item in data if isinstance(item, dict)]  # Copy mapping rows only.

    def _payload(self, rows: list[dict[str, object]], empty_reason: str) -> dict[str, object]:
        """Return the stable picker response shape."""
        rows.sort(key=lambda row: str(row.get("label") or "").casefold())  # Keep operator lists stable.
        reason = None if rows else empty_reason  # Explain only an empty result.
        return {"rows": rows, "total_count": len(rows), "reason": reason}  # Return the contract fields.

    def _row(
        self,
        record: dict[str, object],
        label_fields: tuple[str, ...],
        detail_fields: tuple[str, ...],
        family: str | None,
    ) -> dict[str, object]:
        """Return one normalized picker row."""
        identifier = str(record.get("id") or record.get("mac") or "")  # Select a stable picker value.
        label = self._first_text(record, label_fields) or identifier  # Prefer an operator-readable label.
        detail = self._first_text(record, detail_fields)  # Add bounded identification detail.
        return {"id": identifier, "label": label, "family": family, "detail": detail}  # Keep the page contract.

    @staticmethod
    def _first_text(record: dict[str, object], fields: tuple[str, ...]) -> str:
        """Return the first non-empty field text."""
        for field in fields:  # Search preferred display fields in order.
            value = str(record.get(field) or "").strip()  # Normalize missing values.
            if value:  # The first useful value wins.
                return value  # Return operator-readable text.
        return ""  # No configured field held text.

    @staticmethod
    def _device_family(record: dict[str, object]) -> str | None:
        """Return the utility family for one device."""
        device_type = str(record.get("type") or "").casefold()  # Mist sends AP, switch, or gateway.
        model = str(record.get("model") or "").casefold()  # Gateway model text separates SRX and SSR.
        families = {"ap": "ap", "switch": "ex"}  # Direct device types have fixed utility families.
        if device_type in families:  # Access points and switches need no model check.
            return families[device_type]  # Return the fixed catalog family.
        if device_type == "gateway":  # Gateways use one of two utility families.
            return "srx" if "srx" in model else "ssr"  # Select the family from model text.
        return None  # Unknown types have no utility list.
