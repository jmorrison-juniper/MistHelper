"""Read operation of the Juniper Service Asset API, run in batches of 300 serial numbers or fewer."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log before each batch and each pass.
from dataclasses import dataclass, field  # WHY: a mutable result that collects replies across passes.
from typing import Any  # WHY: asset records are loosely typed dictionaries.

from src.operations.exporting.juniper_rma.api.gateway import (  # WHY: gateway and its error.
    JuniperGatewayClient,
    JuniperTransportError,
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: the envelope builder and the reply reader.
    RequestMessageBuilder,
    ResponseOutcome,
    ResponseStatusReader,
)

logger = logging.getLogger(__name__)  # WHY: module logger for each batch and pass.


@dataclass
class AssetQueryResult:
    """Collected results of the asset read, including partial results after a failure."""

    assets: list[dict[str, Any]] = field(default_factory=list)  # WHY: asset records from every reply.
    not_found: list[tuple[str, str]] = field(default_factory=list)  # WHY: serial and message pairs Juniper rejected.
    not_processed: tuple[str, ...] = ()  # WHY: numbers that never received an answer.
    failed_serials: list[str] = field(default_factory=list)  # WHY: numbers in a batch that returned a fault.
    problems: list[str] = field(default_factory=list)  # WHY: reasons that make the run incomplete.

    @property
    def is_complete(self) -> bool:  # WHY: the run status depends on this.
        """Return True when every number received an answer and no problem occurred."""
        return not self.not_processed and not self.failed_serials and not self.problems  # WHY: all three must be empty.


class JuniperAssetService:
    """Query the asset details operation in batches and repeat the not-processed numbers."""

    BATCH_SIZE = 300  # WHY: fault 991 rejects more than 300 serial numbers in one request.
    MAX_PASSES = 3  # WHY: repeat the not-processed numbers for at most three passes (contract).
    PATH = "queryAssetsDetails"  # WHY: operation path under the Asset base address.
    BULK_PATH = "queryAssetsBulkData"  # WHY: operation path for the bulk snapshot file links.

    def __init__(
        self,
        gateway: JuniperGatewayClient,
        builder: RequestMessageBuilder,
        reader: ResponseStatusReader,
        base_url: str,
    ) -> None:
        """Store the collaborators and the Asset base address."""
        self._gateway = gateway  # WHY: every call goes through the gateway.
        self._builder = builder  # WHY: envelopes come from the builder.
        self._reader = reader  # WHY: replies are read by the status reader.
        self._base_url = base_url  # WHY: the checked Asset base address.

    def query_batch(self, serials: list[str]) -> ResponseOutcome:
        """Send one request for the serial numbers and return the outcome."""
        logger.info("Juniper asset read: %d serial numbers in this request", len(serials))  # WHY: count only.
        reply = self._gateway.post(  # WHY: one checked call with retries.
            self.PATH,
            self._base_url,
            self.PATH,
            lambda transaction_id: self._builder.build_assets(serials, transaction_id),
        )
        if reply.http_status in ResponseStatusReader.GATEWAY_MEANINGS:  # WHY: a gateway rejection has no body status.
            return ResponseStatusReader.gateway_rejection(self.PATH, reply.http_status)  # WHY: name the rejection.
        return self._reader.read_checked(self.PATH, reply)  # WHY: an HTTP error status never passes.

    def query_bulk(self, from_date: str, to_date: str) -> ResponseOutcome:
        """Return the bulk snapshot file links for one date window. The dates are YYYY-MM-DD text."""
        logger.info("Juniper asset bulk link read for one snapshot window")  # WHY: action log, no value.
        reply = self._gateway.post(  # WHY: one checked call with retries.
            self.BULK_PATH,
            self._base_url,
            self.BULK_PATH,
            lambda transaction_id: self._builder.build_bulk(from_date, to_date, transaction_id),
        )
        return ResponseStatusReader.from_reply(self.BULK_PATH, reply)  # WHY: the body status decides the outcome.

    def query_all(self, serials: list[str]) -> AssetQueryResult:
        """Query every serial number. Repeat the not-processed numbers and keep the partial results."""
        result = AssetQueryResult()  # WHY: collect results across the passes.
        pending = list(serials)  # WHY: start with every number in input order.
        for pass_number in range(1, self.MAX_PASSES + 1):  # WHY: at most three passes.
            if not pending:  # WHY: stop when nothing waits for an answer.
                break  # WHY: every number has an answer or a fault.
            logger.info("Juniper asset pass %d for %d serial numbers", pass_number, len(pending))  # WHY: count only.
            pending = self._run_pass(pending, result)  # WHY: the numbers that still need a request.
        result.not_processed = tuple(pending)  # WHY: numbers that never received an answer.
        return result  # WHY: the merged result of every pass.

    def _run_pass(self, pending: list[str], result: AssetQueryResult) -> list[str]:
        """Send each batch of one pass. Return the numbers that need another pass."""
        next_pending: list[str] = []  # WHY: collect the numbers for the next pass.
        for start in range(0, len(pending), self.BATCH_SIZE):  # WHY: walk the list in batches.
            batch = pending[start : start + self.BATCH_SIZE]  # WHY: one request per batch.
            try:  # WHY: a transport failure keeps the partial results.
                outcome = self.query_batch(batch)  # WHY: send the batch.
            except JuniperTransportError as error:  # WHY: record the failure and continue.
                result.problems.append(str(error))  # WHY: the message names the reason only.
                next_pending.extend(batch)  # WHY: the batch needs another pass.
                continue  # WHY: move on to the next batch.
            self._absorb(outcome, batch, result, next_pending)  # WHY: merge the reply into the result.
        return next_pending  # WHY: the serials that still need another pass.

    def _absorb(
        self,
        outcome: ResponseOutcome,
        batch: list[str],
        result: AssetQueryResult,
        next_pending: list[str],
    ) -> None:
        """Merge one reply into the result. A faulted batch is recorded and not retried."""
        if not outcome.is_usable:  # WHY: a fault gives no assets for this batch.
            result.failed_serials.extend(batch)  # WHY: these numbers need a fix before another request.
            result.problems.append(ResponseStatusReader.explain(outcome))  # WHY: the operator sees the reason.
            return  # WHY: nothing else to merge.
        payload = self._payload(outcome.result)  # WHY: the data object or the top level (O-6).
        raw_assets = payload.get("assets")  # WHY: asset records in the reply.
        if isinstance(raw_assets, list):  # WHY: only a list holds asset records.
            result.assets.extend(item for item in raw_assets if isinstance(item, dict))  # WHY: keep asset objects.
        result.not_found.extend(self._pairs(payload.get("invalidSerialNumbersOrSSRNs")))  # WHY: numbers not found.
        retry_pairs = self._pairs(payload.get("notProcessedSerialNumbersOrSSRNs"))  # WHY: numbers that need a retry.
        next_pending.extend(number for number, _message in retry_pairs)  # WHY: queue them for the next pass.

    @staticmethod
    def _payload(result: dict[str, Any]) -> dict[str, Any]:
        """Return the nested data object when present, otherwise the top-level result."""
        data = result.get("data")  # WHY: the example nests the result under data.
        return data if isinstance(data, dict) else result  # WHY: the schema puts the same keys at the top level.

    @staticmethod
    def _pairs(raw: Any) -> list[tuple[str, str]]:
        """Return (serial number, message) pairs from a list of result objects."""
        if not isinstance(raw, list):  # WHY: a missing or odd list gives no pairs.
            return []  # WHY: nothing to report.
        pairs: list[tuple[str, str]] = []  # WHY: collect the pairs in order.
        for item in raw:  # WHY: each item is one serial number.
            if isinstance(item, dict):  # WHY: skip anything that is not an object.
                number = str(item.get("serialNumberOrSSRN", "")).strip()  # WHY: the serial as text.
                message = str(item.get("message", "")).strip()  # WHY: the Juniper message as text.
                pairs.append((number, message))  # WHY: keep the pair.
        return pairs  # WHY: the parsed pairs.
