"""Prove issue #3484 with real history queries and complete synthetic responses."""

from __future__ import annotations  # Keep test annotations independent from import order.

import hashlib  # Check audit digests without the production row shaper.
import json  # Write synthetic audit records and inspect complete JSON responses.
import logging  # Record test actions without stored addresses or owner keys.
import re  # Evaluate clauses and projections from the actual AQL text.
import socket  # Refuse an unexpected connection before a test can reach a service.
from collections.abc import Iterator, Mapping  # Type temporary request and fixture boundaries.
from contextlib import contextmanager  # Give direct adapters the same signed request context.
from pathlib import Path  # Keep every synthetic audit write under the test directory.
from types import SimpleNamespace  # Supply stored privileges without a cloud client.
from typing import Any  # Synthetic records use the existing mixed JSON field types.
from unittest.mock import Mock  # Count real reader calls without replacing their behavior.

import pytest  # Run the direct response and authorization matrix.
from flask import Flask, session  # Exercise the existing signed selection authority.
from werkzeug.exceptions import HTTPException  # Inspect authoritative adapter refusal responses.
from werkzeug.test import TestResponse  # Type complete Flask responses.

from src.interfaces.portals.upgrade_portal.app.routes import (
    review,
)  # Call the production history routes and real adapters.
from src.interfaces.portals.upgrade_portal.capture import (
    store,
)  # Preserve real query types, filters, and store readers.
from src.interfaces.portals.upgrade_portal.compare import lock_audit  # Read only the synthetic temporary audit trail.
from src.interfaces.portals.upgrade_portal.runtime import (
    identity,
    lock,
)  # Preserve sign-in policy and construct a synthetic hold.

logger = logging.getLogger(__name__)  # Keep synthetic validation records separate from application records.


class SyntheticStore:  # Own the data, AQL evaluator, and safe connection boundary.
    """Evaluate real store queries against two synthetic organizations."""

    class Rows:  # Keep record construction separate from independent result expectations.
        """Build source records with unique foreign content."""

        @staticmethod
        def common(org_id: Any, site_id: str, number: int) -> dict[str, Any]:  # Build stored attribution.
            """Return shared stored fields without deriving any expected result."""
            logger.info("Build one synthetic history record")  # Record the transformation before it starts.
            selected = org_id == "org-3484-a"  # Only one organization supplies selected markers.
            label = "Selected Alpha" if site_id == "site-3484-a1" else "Selected Beta"  # Distinguish both sites.
            row = {  # Preserve labels and addresses so complete-response checks can detect disclosure.
                "org_id": org_id,
                "site_id": site_id,  # Reused site text must not authorize a foreign record.
                "site_name": label if selected else f"FOREIGN-SITE-{number}",  # Make foreign labels unique.
                "actor_email": "selected.operator@example.invalid" if selected else "FOREIGN-actor@example.invalid",
                "schema_version": 1,
                "tier": "basic",  # Supply the current history projection fields.
            }
            if org_id == "missing-org":  # Include a record with no organization field at all.
                row.pop("org_id")  # Missing attribution must not match a selected organization.
            logger.debug("Built one synthetic history record with %s fields", len(row))  # Report only a count.
            return row  # The actual query decides whether this record belongs in a result.

        @staticmethod
        def capture(org_id: Any, site_id: str, number: int) -> dict[str, Any]:  # Build a capture source row.
            """Return a complete capture with a distinguishable count and moment."""
            logger.info("Build one synthetic capture")  # Record the transformation before it starts.
            selected = org_id == "org-3484-a"  # Separate selected and foreign identifiers and moments.
            row = dict(SyntheticStore.Rows.common(org_id, site_id, number))  # Keep stored attribution intact.
            row["capture_id"] = (  # Detect foreign identifiers.
                f"cap-a-{number}" if selected else f"cap-FOREIGN-{number}"
            )  # Detect foreign identifiers.
            row["role"], row["capture_status"], row["capture_state"] = "pre", "complete", "verified"  # Readable states.
            row["started_at"] = (  # Detect foreign moments.
                f"2026-09-01T10:{number:02d}:00Z" if selected else "2099-11-03T17:43:31Z"
            )  # Detect dates.
            row["finished_at"] = (  # Detect foreign moments.
                f"2026-09-01T11:{number:02d}:00Z" if selected else "2099-11-03T18:43:31Z"
            )  # Detect dates.
            row["duration_seconds"], row["stored_size_bytes"] = 3600, number if selected else 87391  # Detect counters.
            row["counts"] = {"devices_total": number if selected else 87391, "access_points": number}  # Stored counts.
            logger.debug("Built one synthetic capture with %s fields", len(row))  # Report no stored content.
            return row  # Real count and page queries must apply scope to this record.

        @staticmethod
        def run(org_id: Any, site_id: str, number: int) -> dict[str, Any]:  # Build a single-site run.
            """Return a run whose actual target list supplies its projected count."""
            logger.info("Build one synthetic run")  # Record the transformation before it starts.
            selected = org_id == "org-3484-a"  # Make account, moment, and link content distinguishable.
            row = dict(SyntheticStore.Rows.common(org_id, site_id, number))  # Keep stored attribution intact.
            row["run_id"] = f"run-a-{number}" if selected else f"run-FOREIGN-{number}"  # Detect foreign identifiers.
            row["state"], row["cloud_account"] = (  # Detect foreign account content.
                "complete",
                "Selected account" if selected else "FOREIGN-account",
            )
            row["created_at"] = (  # Detect foreign moments.
                f"2026-09-02T10:{number:02d}:00Z" if selected else "2099-11-04T17:43:31Z"
            )  # Detect dates.
            row["updated_at"] = (  # Detect foreign moments.
                f"2026-09-02T11:{number:02d}:00Z" if selected else "2099-11-04T18:43:31Z"
            )  # Detect dates.
            row["targets"] = [{} for _number in range(number if selected else 17)]  # Exercise actual LENGTH projection.
            row["pre_capture_id"] = f"cap-a-{number}" if selected else "cap-FOREIGN-before"  # Detect hidden links.
            row["post_capture_id"] = "" if selected else "cap-FOREIGN-after"  # Detect hidden comparison links.
            logger.debug("Built one synthetic run with %s targets", len(row["targets"]))  # Report a safe count.
            return row  # The real run query must also exclude aggregate operation records.

        @staticmethod
        def operation(org_id: Any, sites: list[str], number: int) -> dict[str, Any]:  # Build an aggregate row.
            """Return an operation stored in the same collection as single-site runs."""
            logger.info("Build one synthetic operation")  # Record the transformation before it starts.
            selected = org_id == "org-3484-a"  # Foreign operations must not enter the selected section.
            row = dict(SyntheticStore.Rows.common(org_id, sites[0], number))  # Preserve organization attribution.
            row["operation_id"] = (  # Detect foreign identifiers.
                f"op-a-{number}" if selected else f"op-FOREIGN-{number}"
            )  # Detect foreign identifiers.
            labels = {"site-3484-a1": "Selected Alpha", "site-3484-a2": "Selected Beta"}  # Independent site labels.
            row["site_ids"] = sites  # Exercise membership in the actual operation site list.
            row["site_names"] = {site: labels.get(site, "FOREIGN-operation-site") for site in sites}  # Detect labels.
            row["state"], row["cloud_account"] = (  # Detect foreign account content.
                "complete",
                "Selected account" if selected else "FOREIGN-op-account",
            )
            row["created_at"] = (  # Detect foreign moments.
                f"2026-09-05T10:{number:02d}:00Z" if selected else "2099-11-05T17:43:31Z"
            )  # Detect dates.
            row["updated_at"] = (  # Detect foreign moments.
                f"2026-09-05T11:{number:02d}:00Z" if selected else "2099-11-05T18:43:31Z"
            )  # Detect dates.
            row["owner"] = "another-synthetic-owner"  # Only one selected operation receives the current owner.
            row["children"] = [{"device_family": family} for family in ("ap", "ap", "switch")]  # Exercise UNIQUE.
            logger.debug("Built one synthetic operation for %s sites", len(sites))  # Report only a count.
            return row  # The real OperationQuery supplies organization and optional site membership.

        @staticmethod
        def audit(org_id: Any, site_id: str, action: str, moment: str) -> dict[str, Any]:  # Build a trail record.
            """Return an audit address that differs from every capture and run address."""
            logger.info("Build one synthetic audit record")  # Record the transformation before it starts.
            row = {  # These addresses belong only to a temporary synthetic trail.
                "org_id": org_id,
                "site_id": site_id,
                "action": action,
                "occurred_at": moment,
                "actor_email": (
                    "selected.audit@example.invalid" if org_id == "org-3484-a" else "FOREIGN-audit@example.invalid"
                ),  # Digests must not disclose a foreign operator.
                "previous_actor_email": "previous.audit@example.invalid",  # Detect raw previous addresses.
            }
            logger.debug("Built one synthetic audit record with %s fields", len(row))  # Report no address.
            return row  # Only matching organization and site records can affect audit inference.

    class Aql:  # Apply only restrictions that occur in the actual source query.
        """Evaluate the small AQL grammar used by the real history readers."""

        class Input:  # Keep deliberate source changes separate from actual query evaluation.
            """Own foreign source mutations and separate injected-interface probes."""

            @staticmethod
            def site_page(  # Keep expected site identifiers independent from actual queries.
                form: str, window: tuple[int, int]
            ) -> list[str]:  # Keep expected site identifiers independent.
                """Apply the expected window to explicitly listed selected-site identifiers."""
                logger.info("Build the independent expected site page")  # Record the expected-data transformation.
                identifiers = {  # Do not derive expected membership from a production shaper or source fixture.
                    "capture": ["cap-a-5", "cap-a-3", "cap-a-1"],
                    "run": ["run-a-5", "run-a-3", "run-a-1"],
                }
                page = identifiers[form][window[1] : window[1] + window[0]]  # Retain explicit order before slicing.
                logger.debug("The independent expected site page contains %s rows", len(page))  # Safe count.
                return page  # The response must match these independently supplied identifiers.

            @staticmethod
            def windows(  # Require exact page binds from actual source queries.
                calls: list[tuple[str, dict[str, Any]]], expected: tuple[int, int], count: int
            ) -> None:
                """Check real LIMIT binds without deriving them from route parsing."""
                logger.info("Check the actual synthetic source windows")  # Record the evidence transformation.
                binds = [values for query, values in calls if "LIMIT @offset" in query]  # Actual page queries only.
                windows = [(values["limit"], values["offset"]) for values in binds]  # Preserve supplied source bounds.
                assert windows == [expected] * count  # Require exact window values and exact page-query count.
                logger.debug("Checked %s actual source windows", len(windows))  # Report only the checked count.

            class Seams:  # These trusted compatibility readers supply no organization-isolation evidence.
                """Record exact site-only and windowed calls without a store."""

                def __init__(self) -> None:  # Keep each compatibility test's calls independent.
                    """Start with no recorded seam call."""
                    self.calls: list[tuple[str, int, int]] = []  # Preserve supplied arguments for exact assertions.

                def site_only(self, site_id: str) -> list[dict[str, Any]]:  # Preserve the legacy injected seam.
                    """Record a site-only call and return no synthetic history."""
                    logger.info("Record one synthetic site-only history seam call")  # Record the test action.
                    self.calls.append((site_id, 25, 0))  # No added organization or window argument can reach this seam.
                    logger.debug("Recorded %s synthetic seam calls", len(self.calls))  # Report only a safe count.
                    return []  # Compatibility evidence never substitutes for the real-query isolation evidence.

                def with_window(  # Preserve the existing trusted windowed seam.
                    self, site_id: str, limit: int = 25, offset: int = 0
                ) -> list[dict[str, Any]]:
                    """Record a windowed call and return no synthetic history."""
                    logger.info("Record one synthetic windowed history seam call")  # Record the test action.
                    self.calls.append((site_id, limit, offset))  # Keep supplied windows and picker defaults.
                    logger.debug("Recorded %s synthetic seam calls", len(self.calls))  # Report only a safe count.
                    return []  # No fake scope restriction is added to the real query path.

            @staticmethod
            def change_foreign(queries: SyntheticStore.Aql, change: str) -> None:  # Alter input, never query behavior.
                """Change foreign source data while preserving the selected source records."""
                logger.info("Change only foreign synthetic history records")  # Record the source transformation.
                records = queries.records  # Work only with this test's in-memory input.
                if change == "add":  # New foreign records would consume an unrestricted first page.
                    records["upgrade_captures"].append(  # Put new foreign captures before selected pages.
                        SyntheticStore.Rows.capture("org-3484-b", "site-3484-a1", 91)
                    )
                    records["upgrade_runs"].append(  # Put new foreign runs before selected pages.
                        SyntheticStore.Rows.run("org-3484-b", "site-3484-a1", 91)
                    )
                elif change == "remove":  # Keep selected source records unchanged while removing foreign input.
                    queries.records = {  # Alter source input without adding an evaluator restriction.
                        name: [row for row in rows if row.get("org_id") == "org-3484-a"]
                        for name, rows in records.items()
                    }  # This changes input, not the evaluator.
                else:  # A different stored order must not affect the actual query's selected sort order.
                    for rows in records.values():  # Reverse only synthetic input order.
                        rows.reverse()  # The actual SORT clause must restore matching order.
                logger.debug("Applied one foreign synthetic source transformation")  # Report no stored row content.

        def __init__(self, records: dict[str, list[dict[str, Any]]]) -> None:  # Keep independent source records.
            """Keep collections and the exact executed query text and binds."""
            self.records = records  # Tests can alter foreign input without altering expected selected results.
            self.calls: list[tuple[str, dict[str, Any]]] = []  # Preserve both COUNT and page query evidence.

        @staticmethod
        def filtered(  # Apply only filters that actually occur in the source query.
            rows: list[dict[str, Any]], clause: str, binds: Mapping[str, Any]
        ) -> list[dict[str, Any]]:
            """Apply one filter only when the query contains that actual clause."""
            logger.info("Evaluate one actual synthetic query filter")  # Record the transformation.
            match = re.fullmatch(r"FILTER doc\.(\w+) == @(\w+)", clause)  # Read actual field and bind names.
            if match:  # An omitted organization clause must leave foreign input in the result.
                result = [row for row in rows if row.get(match[1]) == binds[match[2]]]  # Use actual bound values.
            elif clause == "FILTER doc.operation_id == null":  # Preserve the real single-site exclusion.
                result = [row for row in rows if row.get("operation_id") is None]  # Exclude aggregate records.
            elif clause == "FILTER doc.operation_id != null":  # Preserve the operation reader's inclusion.
                result = [row for row in rows if row.get("operation_id") is not None]  # Keep aggregates only.
            elif clause == "FILTER @site_id IN doc.site_ids":  # Operations hold site lists, not one site.
                result = [row for row in rows if binds["site_id"] in row.get("site_ids", [])]  # Narrow membership.
            else:  # An unknown clause must fail rather than produce a self-agreeing answer.
                raise AssertionError("The synthetic reader does not support this actual filter.")  # Fail clearly.
            logger.debug("The actual synthetic filter retained %s rows", len(result))  # Report only a count.
            return result  # No missing restriction is supplied by this evaluator.

        @staticmethod
        def projected(rows: list[dict[str, Any]], clause: str) -> list[dict[str, Any]]:  # Read RETURN expressions.
            """Project actual fields and aggregate expressions from the query text."""
            logger.info("Evaluate one actual synthetic query projection")  # Record the transformation.
            fields = re.findall(r"(\w+):doc\.(\w+)", clause)  # Do not copy production projection field constants.
            result = [{name: row.get(field) for name, field in fields} for row in rows]  # Apply actual field pairs.
            for source, target in zip(rows, result, strict=True):  # Add only expressions present in RETURN.
                if "device_count:LENGTH(doc.targets)" in clause:  # Use the real stored target list.
                    target["device_count"] = len(source.get("targets") or [])  # Preserve the run count contract.
                if "families:UNIQUE(doc.children[*].device_family)" in clause:  # Preserve aggregate projection.
                    target["families"] = list(  # Preserve the actual UNIQUE projection.
                        dict.fromkeys(child["device_family"] for child in source.get("children", []))
                    )  # Remove repeated families.
            logger.debug("The actual synthetic projection produced %s rows", len(result))  # Report a safe count.
            return result  # Expected results remain separate literals in the tests.

        def execute(self, query: str, bind_vars: Mapping[str, Any]) -> list[Any]:  # Execute the real query text.
            """Apply filters, sorting, counts, windows, and projections in actual clause order."""
            logger.info("Evaluate one actual synthetic history query")  # Record the source read.
            self.calls.append((query, dict(bind_vars)))  # Retain exact binds rather than a canned query answer.
            collection = re.search(r"FOR doc IN (\w+)", query)  # Read the collection named by the real query.
            assert isinstance(collection, re.Match)  # Fail if a source query stops using the supported grammar.
            rows = list(self.records[collection[1]])  # Start with both organizations and unattributed input.
            for clause in (line.strip() for line in query.splitlines()):  # Obey actual query clause order.
                if clause.startswith("FILTER "):  # Apply only filters present before each following action.
                    rows = self.filtered(rows, clause, bind_vars)  # An absent org filter remains absent.
                elif clause.startswith("SORT "):  # Preserve descending time and secondary operation ordering.
                    fields = re.findall(r"doc\.(\w+) DESC", clause)  # Read the actual sort fields.
                    rows.sort(  # Preserve the actual descending sort fields.
                        key=lambda row: tuple(str(row.get(field) or "") for field in fields), reverse=True
                    )
                elif clause.startswith("COLLECT "):  # COUNT must see every matching row before any page window.
                    logger.debug("The actual synthetic count returned %s", len(rows))  # Report the exact total.
                    return [len(rows)]  # Do not derive a total from a previously clipped page.
                elif clause.startswith("LIMIT "):  # Use the real query's bound page window.
                    offset = bind_vars["offset"] if "@offset" in clause else 0  # Operations have no offset.
                    rows = rows[offset : offset + bind_vars["limit"]]  # Apply LIMIT at its actual position.
                elif clause.startswith("RETURN {"):  # Respect the actual stored-field projection.
                    rows = self.projected(rows, clause)  # Preserve LENGTH and UNIQUE expressions when present.
            logger.debug("The actual synthetic page returned %s rows", len(rows))  # Report a safe result count.
            return rows  # No adapter or production filter builder is replaced.

    class Readers:  # Keep live connection and operation interfaces within one synthetic owner.
        """Supply a synthetic handle and a real operation query."""

        def __init__(self, database: SyntheticStore) -> None:  # Keep the source handle for isolated reads.
            """Retain only the synthetic database for both reader interfaces."""
            self.database = database  # This object can never return a live database handle.
            self.connections = 0  # Refusal tests must prove zero attempts to resolve a database.

        def connect(self) -> SyntheticStore | None:  # Replace only the external database connection boundary.
            """Return the synthetic handle or an explicitly unavailable source."""
            logger.info("Resolve the synthetic history database")  # Record the source action before it starts.
            self.connections += 1  # Include failed source resolution in refusal evidence.
            result = self.database if self.database.available else None  # Preserve actual outage behavior.
            logger.debug("The synthetic history database is available: %s", result is not None)  # Safe result.
            return result  # Never read configuration, credentials, or a production store.

        def operations(self, org_id: str, site_id: str = "", limit: int = 25) -> Any:  # Preserve the operation seam.
            """Run the real operation reader with its real query type."""
            logger.info("Read synthetic operations through the real store reader")  # Record the source action.
            result = store.list_operations(  # Keep real operation query construction and evaluation.
                store.OperationQuery(org_id=org_id, site_id=site_id, limit=limit)
            )
            logger.debug("The real operation reader returned %s synthetic rows", len(result.operations))  # Safe count.
            return result  # The actual operation clauses determine membership and ordering.

        @staticmethod
        def collections() -> dict[str, list[dict[str, Any]]]:  # Build shared input without deriving expected pages.
            """Create both selected sites and foreign or missing attribution in shared collections."""
            logger.info("Build the shared synthetic capture and run collections")  # Record fixture construction.
            selected = [  # Populate both selected sites without filtering a query answer.
                ("org-3484-a", "site-3484-a1" if number % 2 else "site-3484-a2", number) for number in range(1, 7)
            ]  # Include two selected sites with three rows each.
            foreign = [  # Include empty, missing, and mismatched attribution in shared input.
                (org, "site-3484-a1", 82 + index)
                for index, org in enumerate(("org-3484-b", None, "", "missing-org", "org-unrelated"))
            ]  # Reuse selected site text across scope.
            foreign.insert(0, ("org-3484-b", "site-3484-b1", 81))  # Include a real foreign site intersection.
            records = {  # The actual AQL clauses must narrow these shared collections.
                "upgrade_captures": [SyntheticStore.Rows.capture(*values) for values in selected + foreign],
                "upgrade_runs": [SyntheticStore.Rows.run(*values) for values in selected + foreign]
                + [
                    SyntheticStore.Rows.operation("org-3484-a", ["site-3484-a1", "site-3484-a2"], 2),
                    SyntheticStore.Rows.operation("org-3484-a", ["site-3484-a2"], 1),
                    SyntheticStore.Rows.operation("org-3484-b", ["site-3484-b1"], 87),
                    SyntheticStore.Rows.operation(None, ["site-3484-a1"], 88),
                ],  # Unattributed operation input.
            }
            logger.debug("Built %s synthetic history collections", len(records))  # Report a safe count.
            return records  # The actual query clauses must perform all source narrowing.

        def isolate(self, monkeypatch: pytest.MonkeyPatch) -> None:  # Protect every external source boundary.
            """Keep real readers while counting source resolution and refusing network access."""
            logger.info("Isolate the real history source boundaries")  # Record safe fixture setup.
            store.reset_connection()  # Drop any handle from another test before the first query.
            monkeypatch.setattr(store, "connect_database", self.connect)  # Resolve a synthetic handle only.
            self.database.loader = Mock(wraps=review.load_optional_module)  # Count actual optional resolution.
            monkeypatch.setattr(review, "load_optional_module", self.database.loader)  # Keep actual imports active.
            self.database.reads = {}  # Preserve four separate zero-read counters for authoritative refusals.
            for name in ("capture", "run", "operation", "audit"):  # Count resolution, not an agreeing fake result.
                attribute = "audit_history_rows" if name == "audit" else name + "_lister"  # Existing boundaries.
                probe = Mock(wraps=getattr(review, attribute))  # Preserve the complete production implementation.
                self.database.reads[name] = probe  # Keep each source count independently observable.
                monkeypatch.setattr(review, attribute, probe)  # Never replace an adapter or query builder.
            network = Mock(  # Refuse any unexpected service connection.
                side_effect=AssertionError("A history contract must not open a network connection.")
            )
            monkeypatch.setattr(socket.socket, "connect", network)  # Stop direct service access.
            monkeypatch.setattr(socket, "create_connection", network)  # Stop indirect service access.
            logger.debug("Isolated four real history source boundaries")  # Report no stored row or credential.

    def __init__(self, directory: Path) -> None:  # Construct the two-organization source fixture.
        """Create selected, foreign, unattributed, and aggregate records."""
        logger.info("Build the two-organization synthetic history sources")  # Record fixture construction.
        records = self.Readers.collections()  # The fixture does not pre-filter shared source collections.
        self.aql, self.readers, self.available = self.Aql(records), self.Readers(self), True  # Keep isolated state.
        self.trail = directory / "issue-3484-history.jsonl"  # Never resolve a checkout or production audit path.
        audit = [  # Interleave attribution before the real audit reader applies scope.
            self.Rows.audit(org, site, action, moment)
            for org, site, action, moment in [
                ("org-3484-a", "site-3484-a1", "take", "2026-09-03T10:01:00Z"),
                ("org-3484-b", "site-3484-a1", "take", "2099-11-06T17:43:31Z"),
                ("org-3484-a", "site-3484-a2", "takeover", "2026-09-03T10:02:00Z"),
                (None, "site-3484-a1", "release", "2099-11-06T18:43:31Z"),
                ("org-3484-a", "site-3484-a1", "take", "2026-09-03T10:03:00Z"),
                ("org-3484-a", "site-3484-a2", "release", "2026-09-03T10:04:00Z"),
            ]
        ]
        self.trail.write_text("\n".join(json.dumps(row) for row in audit), encoding="utf-8")  # Write synthetic input.
        logger.debug("Built %s synthetic collections and one temporary audit trail", len(records))  # Safe summary.

    def bind(  # Preserve real adapters and replace only external source boundaries.
        self, app: Flask, monkeypatch: pytest.MonkeyPatch, owner: identity.SessionOwner
    ) -> None:
        """Keep real history readers while replacing every external source boundary."""
        logger.info("Bind the synthetic history sources to the real portal")  # Record fixture setup.
        self.readers.isolate(monkeypatch)  # Never resolve a live database, network, or cached source handle.
        app.config.pop("CAPTURE_LISTER", None)  # Force the real capture adapter rather than an agreeing stand-in.
        app.config.pop("RUN_LISTER", None)  # Force the real run adapter and its existing call shape.
        app.config["OPERATION_LISTER"] = self.readers.operations  # Call the real query against synthetic data.
        monkeypatch.setattr(lock_audit, "audit_trail_path", lambda: self.trail)  # Restrict audit reads to temp input.
        self.lock_probe = Mock(side_effect=AssertionError("History must not read a site lock."))  # Enforce free reads.
        app.config["SITE_LOCK_READER"] = self.lock_probe  # Any route lock lookup must fail this contract.
        for row in self.aql.records["upgrade_runs"]:  # Set the owner of one selected operation only.
            if row.get("operation_id") == "op-a-2":  # Preserve visibility of another session's matching operation.
                row["owner"] = owner.key  # The complete rendered response must omit this server-only value.
        logger.debug("Bound four synthetic history sources with real capture and run adapters")  # Safe summary.


class HistoryCase:  # Share class-owned synthetic fixtures without a support-module or conftest edit.
    """Provide an active signed selection and independent response checks."""

    class Evidence:  # Keep expected data separate from source builders and production shapers.
        """Check complete responses and exact source-query scope."""

        @staticmethod
        def clean(text: str) -> None:  # Check all HTML attributes, links, embedded fields, and JSON content.
            """Require absence of every unique foreign content category and raw audit address."""
            logger.info("Check the complete history response for foreign content")  # Record the assertion action.
            foreign_digest = hashlib.blake2s(  # Detect foreign audit content without the production shaper.
                b"foreign-audit@example.invalid", digest_size=8
            ).hexdigest()
            previous_digest = hashlib.blake2s(  # Verify digest-only previous-holder output independently.
                b"previous.audit@example.invalid", digest_size=8
            ).hexdigest()
            for marker in (  # Check the complete response, including hidden values.
                "FOREIGN",
                "2099-",
                "87391",
                foreign_digest,  # Cover labels, dates, counts, and digests.
                "selected.audit@example.invalid",
                "previous.audit@example.invalid",
            ):
                assert marker not in text, "The complete response contains foreign or raw audit content."  # No leaks.
            assert previous_digest in text or "history-audit-row-" not in text  # Keep digest-only audit output.
            logger.debug("The complete history response passed six content checks")  # Report a safe summary.

        @staticmethod
        def html_rows(text: str, kind: str) -> list[str]:  # Inspect every row attribute, not only visible cells.
            """Return ordered identifiers from a complete rendered response."""
            logger.info("Read row identifiers from the complete synthetic response")  # Record the transformation.
            prefix = {  # Use literal interface identifiers rather than production constants.
                "capture": "history-row-",
                "run": "history-run-row-",
                "operation": "history-operation-row-",
            }[
                kind
            ]  # Use independent literal interface identifiers.
            rows = re.findall('data-testid="' + prefix + r'([^"]+)"', text)  # Preserve server-rendered order.
            logger.debug(  # Report only the count of complete-response identifiers.
                "The complete synthetic response contains %s matching row identifiers", len(rows)
            )
            return rows  # Test methods compare these identifiers with explicit independent expectations.

        @staticmethod
        def json_rows(response: TestResponse, kind: str) -> tuple[int, list[str]]:  # Read complete JSON history.
            """Return the exact total and ordered identifiers from the real response."""
            logger.info("Read the complete synthetic JSON history response")  # Record the transformation.
            body = response.get_json()  # Inspect the actual envelope rather than a fake lister result.
            assert isinstance(body, dict) and set(body) == {kind + "s", "total"}  # Preserve the existing envelope.
            rows = body[kind + "s"]  # Keep complete rows available for the separate content checks.
            result = body["total"], [row[kind + "_id"] for row in rows]  # Read actual membership and ordering.
            logger.debug("The synthetic JSON history contains %s rows of %s", len(rows), body["total"])  # Safe counts.
            return result  # Expected totals never come from the source fixture's own filtered answer.

        @staticmethod
        def no_reads(database: SyntheticStore) -> None:  # Prove an authoritative refusal prevents all sources.
            """Require zero capture, run, operation, audit, module, and database calls."""
            assert {name: probe.call_count for name, probe in database.reads.items()} == {  # Four separate counts.
                "capture": 0,
                "run": 0,
                "operation": 0,
                "audit": 0,
            }  # No reader resolves on a refused request.
            assert database.readers.connections == 0  # An empty or unavailable store cannot authorize a request.
            assert database.aql.calls == []  # No actual query can run before the selection decision.
            assert database.loader.call_count == 0  # Refusal must also precede optional module access.

        @staticmethod
        def queries(database: SyntheticStore, site_id: str = "") -> None:  # Inspect actual COUNT and LIMIT evidence.
            """Require organization and optional site filters before both count and page boundaries."""
            logger.info("Check actual synthetic history query clauses and binds")  # Record query verification.
            assert len(database.aql.calls) >= 2  # Successful real adapters must execute count and page queries.
            for query, binds in database.aql.calls:  # Include real operation membership queries in the same check.
                org_clause = "FILTER doc.org_id == @org_id"  # An independent required source restriction.
                assert binds.get("org_id") == "org-3484-a" and org_clause in query  # Require the signed selection.
                boundary = "COLLECT" if "COLLECT" in query else "LIMIT"  # Check count and page independently.
                assert query.index(org_clause) < query.index(boundary)  # Reject filtering after the source boundary.
                if site_id:  # A site restriction must narrow the organization before counts and page windows.
                    site_clause = (  # Operations use membership while single-site records use equality.
                        "FILTER @site_id IN doc.site_ids"
                        if "operation_id != null" in query
                        else "FILTER doc.site_id == @site_id"
                    )  # Operations use membership in their actual site list.
                    assert binds["site_id"] == site_id and site_clause in query  # Require the requested site.
                    assert query.index(site_clause) < query.index(boundary)  # Reject late site filtering.
                else:  # An organization-wide read must not infer a site from its first record.
                    assert "site_id" not in binds  # Require both selected sites to remain eligible.
            logger.debug("Checked %s actual scoped history queries", len(database.aql.calls))  # Safe count.

    @pytest.fixture
    def history_case(  # Keep the real authority inside one isolated synthetic request fixture.
        self, portal_app: Flask, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> Iterator[HistoryCase]:
        """Use an isolated application, signed session, synthetic store, and temporary audit trail."""
        logger.info("Prepare the isolated issue 3484 history contract")  # Record fixture setup.
        self.app, self.database = portal_app, SyntheticStore(tmp_path)  # Keep all data inside this test.
        owner = identity.build_owner("session.3484@example.invalid", identity.issue_browser_id())  # Safe session.
        self.record = identity.OperatorSession(  # Register a safe sign-in without a cloud client.
            owner=owner,
            cloud_session=SimpleNamespace(privileges=[]),
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        )
        identity.SESSION_REGISTRY.register(self.record)  # The real sign-in guard must find this exact browser pair.
        self.database.bind(self.app, monkeypatch, owner)  # Replace external boundaries, not the actual query path.
        self.client = self.app.test_client()  # Use the real Flask response without a server or a browser.
        self.client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Supply the browser half of sign-in.
        with self.client.session_transaction() as browser_session:  # Keep selection in the signed session only.
            browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Supply the registry half of sign-in.
        self.scope()  # Begin with an explicit selection that permits both synthetic organizations.
        logger.debug("Prepared one signed synthetic history contract with four isolated sources")  # Safe summary.
        try:  # Registry and database cache cleanup must also occur after a failed assertion.
            yield self  # The grouped test methods use only this isolated fixture.
        finally:  # Prevent this fixture from authorizing or supplying a source to any later test.
            identity.SESSION_REGISTRY.drop(owner.key)  # Remove the synthetic sign-in record.
            store.reset_connection()  # Remove any handle a real reader cached during the test.

    def scope(  # Test saved selections without fixture normalization or guessed scope.
        self, chosen: Any = "org-3484-a", permitted: tuple[str, ...] | None = ("org-3484-a", "org-3484-b")
    ) -> None:
        """Set the signed selection and current privileges without request-query authorization."""
        logger.info("Set the synthetic signed history scope")  # Record the selection change.
        self.record.cloud_session.privileges = (  # Preserve empty versus unavailable privileges.
            None if permitted is None else [{"org_id": org_id} for org_id in permitted]
        )  # Retain the distinction between empty and unavailable.
        with self.client.session_transaction() as browser_session:  # Write only this synthetic client's session.
            if chosen == "missing-selection":  # A missing field differs from an explicitly stored None.
                browser_session.pop("selected_org_id", None)  # Prove the route never chooses the first privilege.
            else:  # Incorrect types must remain incorrect so the real resolver must reject them.
                browser_session["selected_org_id"] = chosen  # Do not normalize the fixture's test input.
        logger.debug("Set one synthetic selection with known privileges: %s", permitted is not None)  # Safe result.

    def get(self, path: str, accept: str = "application/json") -> TestResponse:  # Drive real request handling.
        """Return the complete real response with an explicit preference."""
        logger.info("Request the real history route with synthetic sources")  # Record the request before it starts.
        response = self.client.get(path, headers={"Accept": accept})  # No server or network transport is used.
        logger.debug("The real synthetic history request returned status %s", response.status_code)  # Safe result.
        return response  # Test methods inspect the full response rather than one visible cell.

    @contextmanager
    def context(self) -> Iterator[None]:  # Preserve the signed authority for direct adapter calls.
        """Give a direct real adapter the same browser cookie and signed selection."""
        logger.info("Prepare one signed synthetic adapter request context")  # Record request setup.
        with self.client.session_transaction() as saved:  # Copy this test client's signed values only.
            values = dict(saved)  # Do not read another session or shared feature context.
        cookie = f"{identity.BROWSER_ID_COOKIE}={self.record.owner.browser_id}"  # Use the synthetic browser only.
        with self.app.test_request_context(  # A query conflict cannot replace signed request scope.
            "/history?org_id=org-3484-b", headers={"Cookie": cookie}
        ):
            session.update(values)  # Preserve invalid selections as well as valid selections for the real guard.
            logger.debug("Prepared one signed synthetic adapter request context")  # Report no owner key.
            yield  # A query organization cannot replace these signed values.


class TestSelectedOrgHistory(HistoryCase):  # Prove complete organization-wide content, totals, and pages.
    """Keep all four history cards inside the selected organization."""

    @pytest.mark.parametrize(
        "chosen,permitted,query",
        [
            ("org-3484-a", ("org-3484-a", "org-3484-b"), ""),
            ("  org-3484-a  ", ("org-3484-a", "org-3484-b"), "?org_id=org-3484-b&org=org-3484-b"),
            ("org-3484-a", ("org-3484-a",), "?org_id=org-3484-b"),
            ("org-3484-a", None, "?org_id=org-3484-b"),
        ],
    )
    def test_complete_cards(  # Prove exact independent content in all four cards.
        self, history_case: HistoryCase, chosen: str, permitted: tuple[str, ...] | None, query: str
    ) -> None:
        """Check full HTML, independent row order, exact counts, sites, ownership, and audit digests."""
        history_case.scope(chosen, permitted)  # Use the real authority with padded and unavailable-privilege cases.
        response = history_case.get("/history" + query)  # Exercise the real no-site request form.
        assert response.status_code == 200  # Valid selections must retain the successful page.
        text = response.get_data(as_text=True)  # Include every hidden attribute, link, and embedded value.
        self.Evidence.clean(text)  # No foreign marker or raw audit address can appear anywhere.
        captures = "cap-a-6 cap-a-5 cap-a-4 cap-a-3 cap-a-2 cap-a-1".split()  # Independent literal capture order.
        assert self.Evidence.html_rows(text, "capture") == captures  # Both selected sites participate.
        runs = "run-a-6 run-a-5 run-a-4 run-a-3 run-a-2 run-a-1".split()  # Independent literal single-site run order.
        assert self.Evidence.html_rows(text, "run") == runs  # Aggregates do not enter single-site run rows.
        assert self.Evidence.html_rows(text, "operation") == ["op-a-2", "op-a-1"]  # Preserve exact operation order.
        assert "6 captures." in text and "Selected Alpha" in text and "Selected Beta" in text  # Exact selected scope.
        assert 'data-organization-id="org-3484-a"' in text  # Controls use the normalized validated selection.
        assert 'href="/upgrade/org/jobs/op-a-2"' in text  # Keep the current session's progress link.
        assert 'href="/upgrade/org/jobs/op-a-1"' not in text  # Keep another session's matching operation unlinked.
        assert history_case.record.owner.key not in text and "another-synthetic-owner" not in text  # Server-only keys.
        audit_card = text.split('data-testid="history-audit-table"')[1].split("</table>")[0]  # Inspect its whole card.
        actions = "release take expire takeover take".split()  # Independent literal matching audit action order.
        assert re.findall(r"badge-(take|release|takeover|expire)\"", audit_card) == actions  # Exact scoped audit order.
        assert "site-3484-a1" in audit_card and "site-3484-a2" in audit_card  # Audit includes both selected sites.
        self.Evidence.queries(history_case.database)  # Inspect organization binds before COUNT and LIMIT.

    @pytest.mark.parametrize(
        "path,kind,expected",
        [
            ("/api/sites/site-3484-a1/history", "capture", ["cap-a-5", "cap-a-3", "cap-a-1"]),
            ("/api/sites/site-3484-a2/history", "capture", ["cap-a-6", "cap-a-4", "cap-a-2"]),
            ("/api/sites/site-3484-a1/runs/history", "run", ["run-a-5", "run-a-3", "run-a-1"]),
            ("/api/sites/site-3484-a2/runs/history", "run", ["run-a-6", "run-a-4", "run-a-2"]),
        ],
    )
    def test_complete_json(  # Prove real source totals and complete JSON membership.
        self, history_case: HistoryCase, path: str, kind: str, expected: list[str]
    ) -> None:
        """Require exact totals and membership in complete JSON from the real capture and run adapters."""
        response = history_case.get(path + "?org_id=org-3484-b")  # Conflicting query scope must be ignored.
        assert response.status_code == 200  # Both existing APIs remain successful for a valid selection.
        assert self.Evidence.json_rows(response, kind) == (3, expected)  # Count all matching rows before pagination.
        self.Evidence.clean(response.get_data(as_text=True))  # Inspect the complete serialized response.
        self.Evidence.queries(history_case.database, path.split("/")[3])  # Require both organization and site binds.
        assert len(history_case.database.aql.calls) == 2  # Count and page must use the same actual restrictions.
        if kind == "run":  # Preserve the real device-count projection and aggregate exclusion.
            expected_counts = [5, 3, 1] if "a1" in path else [6, 4, 2]  # Independent literal target counts.
            assert [row["device_count"] for row in response.get_json()["runs"]] == expected_counts  # Actual LENGTH.

    @pytest.mark.parametrize(
        "path",
        [
            "/history",
            "/history?site_id=site-3484-a1",
            "/api/sites/site-3484-a1/history",
            "/api/sites/site-3484-a1/runs/history",
        ],
    )
    def test_empty_selected_org(self, history_case: HistoryCase, path: str) -> None:  # Refuse foreign replacement data.
        """Foreign populated sources must not replace empty selected history."""
        logger.info("Remove selected records from the synthetic history sources")  # Record the test transformation.
        history_case.database.aql.records = {  # Empty only selected input while retaining populated foreign sources.
            name: [row for row in rows if row.get("org_id") != "org-3484-a"]
            for name, rows in history_case.database.aql.records.items()
        }  # Keep foreign data.
        history_case.database.trail.write_text(  # Keep populated foreign audit input in the temporary trail.
            json.dumps(SyntheticStore.Rows.audit("org-3484-b", "site-3484-b1", "take", "2099-11-06T17:43:31Z")),
            encoding="utf-8",
        )  # Temp trail only.
        logger.debug("Selected synthetic history is empty in all four sources")  # Report the safe result.
        response = history_case.get(path)  # Exercise every empty response form with populated foreign input.
        assert response.status_code == 200  # Empty matching history remains successful, not an authorization refusal.
        text = response.get_data(as_text=True)  # Inspect the complete response.
        self.Evidence.clean(text)  # Exclude foreign content, not just visible rows.
        if path.startswith("/history"):  # Each card must retain its existing empty state.
            assert "0 captures." in text  # Foreign captures cannot contribute to the total.
            assert "The portal found no stored capture." in text  # Preserve the existing capture empty state.
            for marker in ("history-run-empty", "history-operation-empty", "history-audit-empty"):  # Keep empty cards.
                assert f'data-testid="{marker}"' in text  # All other cards must state matching emptiness.
        else:  # Both JSON APIs must report a correct successful empty intersection.
            kind = "run" if "/runs/" in path else "capture"  # Select the existing response field.
            assert self.Evidence.json_rows(response, kind) == (0, [])  # No foreign fallback row or total.

    @pytest.mark.parametrize(
        "path,kind,pages",
        [
            ("/history", "capture", [["cap-a-6"], ["cap-a-5"], []]),
            ("/api/sites/site-3484-a1/history", "capture", [["cap-a-5"], ["cap-a-3"], []]),
            ("/api/sites/site-3484-a1/runs/history", "run", [["run-a-5"], ["run-a-3"], []]),
        ],
    )
    def test_foreign_changes_preserve_pages(  # Prove stable selected totals and page boundaries.
        self, history_case: HistoryCase, path: str, kind: str, pages: list[list[str]]
    ) -> None:
        """Adding, removing, and reordering foreign source records must not change selected page boundaries."""
        for change in ("add", "remove", "reorder"):  # Each change would alter an unrestricted first page.
            SyntheticStore.Aql.Input.change_foreign(  # Alter input, never the actual query clauses.
                history_case.database.aql, change
            )  # Alter input, never query scope.
            for offset, expected in zip((0, 1, 20), pages, strict=True):  # Include an offset beyond the matching total.
                response = history_case.get(path + f"?limit=1&offset={offset}")  # Reauthorize each page request.
                assert response.status_code == 200  # Every authorized page remains available.
                self.Evidence.clean(response.get_data(as_text=True))  # Foreign records cannot consume page slots.
                if path == "/history":  # Check exact selected page rows and the full matching total.
                    assert self.Evidence.html_rows(response.get_data(as_text=True), kind) == expected  # Exact page.
                    assert "6 captures." in response.get_data(as_text=True)  # Totals precede every page limit.
                else:  # The two JSON APIs must retain exact site totals even beyond the end.
                    assert self.Evidence.json_rows(response, kind) == (3, expected)  # Exact count and membership.

    def test_audit_limit_is_independent(self, history_case: HistoryCase) -> None:  # Keep the audit's default window.
        """A one-capture page must not clip the scoped Audit log card to one row."""
        response = history_case.get("/history?limit=1")  # Capture and run windows do not set the audit window.
        assert response.status_code == 200  # Preserve the existing successful page.
        text = response.get_data(as_text=True)  # Inspect the complete rendered result.
        assert self.Evidence.html_rows(text, "capture") == ["cap-a-6"]  # Capture LIMIT remains one.
        assert self.Evidence.html_rows(text, "run") == ["run-a-6"]  # Run LIMIT remains one.
        assert re.findall(r'data-testid="history-audit-row-(\d+)"', text) == ["1", "2", "3", "4", "5"]  # Default audit.
        self.Evidence.clean(text)  # Audit scope must not widen when its independent limit is larger.


class TestHistoryOrgRefusals(HistoryCase):  # Prove refusal order and the unchanged identity policy.
    """Refuse invalid selections before every source resolution and read."""

    @pytest.mark.parametrize(
        "path",
        [
            "/history",
            "/history?site_id=site-3484-a1",
            "/api/sites/site-3484-a1/history",
            "/api/sites/site-3484-a1/runs/history",
        ],
    )
    @pytest.mark.parametrize("chosen", ["missing-selection", None, "", " \t ", 42, False, [], {}])
    @pytest.mark.parametrize("source", ["populated", "empty", "unavailable"])
    def test_missing_selection(  # Prove refusal before all four source boundaries.
        self, history_case: HistoryCase, path: str, chosen: Any, source: str
    ) -> None:
        """Every invalid saved selection must return the existing missing-selection envelope without source calls."""
        history_case.scope(chosen)  # Keep invalid values unchanged for the real signed-selection resolver.
        logger.info("Set synthetic source availability for a refusal contract")  # Record the test action.
        if source == "empty":  # Empty data must not replace authorization.
            history_case.database.aql.records = {"upgrade_captures": [], "upgrade_runs": []}  # In-memory only.
            history_case.database.trail.write_text("", encoding="utf-8")  # Keep the synthetic trail empty too.
        elif source == "unavailable":  # Optional readers must not resolve before a selection refusal.
            history_case.database.loader.side_effect = None  # Replace only the external module availability.
            history_case.database.loader.return_value = None  # An unavailable module must not permit an empty success.
            history_case.database.available = False  # The operation reader also has no available source.
        logger.debug("Set one synthetic refusal source state")  # Report no source content.
        response = history_case.get(path)  # Exercise each registered form with the same invalid selection.
        assert response.status_code == 400  # Missing, blank, and incorrectly typed selections share this refusal.
        assert response.get_json() == {  # Preserve the authoritative missing-selection envelope.
            "error": {"code": "org_not_chosen", "message": "Choose an organization before you read the site list."}
        }
        self.Evidence.no_reads(history_case.database)  # Require four independent zero source counts.

    @pytest.mark.parametrize(
        "path",
        [
            "/history",
            "/history?site_id=site-3484-a1",
            "/api/sites/site-3484-a1/history",
            "/api/sites/site-3484-a1/runs/history",
        ],
    )
    @pytest.mark.parametrize(
        "selection",
        [
            ("org-3484-b", ("org-3484-a",)),
            ("org-unknown", ("org-3484-a",)),
            ("org-removed", ("org-3484-a",)),
            ("org-3484-a", ()),
        ],
    )
    @pytest.mark.parametrize("source", ["populated", "empty", "unavailable"])
    def test_known_privileges(  # Prove current known membership before any source read.
        self, history_case: HistoryCase, path: str, selection: tuple[Any, ...], source: str
    ) -> None:
        """Known exclusions, removed selections, unknown selections, and empty privileges must refuse before reads."""
        history_case.scope(*selection)  # Ask the unchanged identity membership authority.
        logger.info("Prepare synthetic sources for a known-privilege refusal")  # Separate data from authorization.
        history_case.database.available = source != "unavailable"  # Source availability cannot authorize a request.
        if source == "empty":  # Empty capture, run, operation, and audit sources still require authorization.
            history_case.database.aql.records = {"upgrade_captures": [], "upgrade_runs": []}  # Synthetic data only.
            history_case.database.trail.write_text("", encoding="utf-8")  # Empty only this test's temporary trail.
        logger.debug("Prepared one synthetic known-privilege source condition")  # Do not expose source records.
        response = history_case.get(path)  # Exercise all four request forms with known privileges.
        assert response.status_code == 403  # Every known out-of-scope selection uses the existing refusal.
        assert response.get_json() == {  # Preserve the authoritative current-privilege envelope.
            "error": {"code": "org_not_permitted", "message": identity.ORG_NOT_PERMITTED_MESSAGE}
        }  # Keep authority text.
        self.Evidence.no_reads(history_case.database)  # No source may run while known membership refuses.

    @pytest.mark.parametrize(
        "path",
        [
            "/history",
            "/history?site_id=site-3484-a1",
            "/api/sites/site-3484-a1/history",
            "/api/sites/site-3484-a1/runs/history",
        ],
    )
    @pytest.mark.parametrize("accept", ["", "application/json", "text/html"])
    def test_sign_in_and_later_privilege_change(  # Preserve sign-in policy and current privilege checks.
        self, history_case: HistoryCase, path: str, accept: str
    ) -> None:
        """The sign-in guard acts first, and each later page repeats the current privilege decision."""
        history_case.scope(permitted=())  # Refuse on the first selected but excluded request.
        response = history_case.get(path, accept)  # Organization refusals remain JSON even for an HTML preference.
        assert response.status_code == 403 and response.get_json()["error"]["code"] == "org_not_permitted"  # Refusal.
        self.Evidence.no_reads(history_case.database)  # A changed privilege list permits no cached authorization.
        identity.SESSION_REGISTRY.drop(history_case.record.owner.key)  # Remove the active sign-in before the next read.
        response = history_case.get(path, accept)  # The existing sign-in guard must now act before selection.
        if accept == "text/html":  # Preserve the current browser sign-in redirect.
            assert response.status_code == identity.SIGN_IN_REDIRECT_STATUS  # Use the unchanged redirect policy.
            assert response.headers["Location"] == "/auth/signin"  # Preserve the existing sign-in destination.
        else:  # Default and explicit JSON preferences retain the existing envelope.
            assert response.status_code == 401  # No active sign-in permits history reads.
            assert response.get_json()["error"]["code"] == "not_authenticated"  # Preserve the wire refusal code.
        self.Evidence.no_reads(history_case.database)  # No sign-in refusal can resolve any history source.

    @pytest.mark.parametrize("adapter", ["capture", "run", "picker"])
    @pytest.mark.parametrize(
        "case",
        [
            (None, ("org-3484-a",), 400, "org_not_chosen"),
            (" \t ", ("org-3484-a",), 400, "org_not_chosen"),
            (42, ("org-3484-a",), 400, "org_not_chosen"),
            ("org-3484-b", ("org-3484-a",), 403, "org_not_permitted"),
            ("org-unknown", ("org-3484-a",), 403, "org_not_permitted"),
            ("org-3484-a", (), 403, "org_not_permitted"),
        ],
    )
    def test_direct_adapter_refusals(  # Direct callers cannot bypass the independent adapter boundary.
        self, history_case: HistoryCase, adapter: str, case: tuple[Any, ...]
    ) -> None:
        """Real adapters and the real site-only comparison picker must independently refuse before module access."""
        chosen, permitted, status, code = case  # Keep this grouped refusal case within the parameter limit.
        history_case.scope(chosen, permitted)  # The direct adapter cannot rely on a guarded history route.
        if adapter == "picker":  # The shared capture adapter also serves the existing comparison picker.
            response = history_case.get("/compare?site_id=site-3484-a1")  # Keep the picker's site-only call shape.
        else:  # A direct adapter must carry the authoritative refusal rather than return successful empty rows.
            reader = review.store_capture_rows if adapter == "capture" else review.store_run_rows  # Real adapters.
            with history_case.context(), pytest.raises(HTTPException) as raised:  # Flask abort carries its response.
                reader("site-3484-a1", limit=1, offset=1)  # No unavailable-reader retry can discard organization scope.
            response = raised.value.get_response()  # Inspect the carried response's existing status and envelope.
        assert response.status_code == status  # Direct refusal must preserve authoritative HTTP status.
        assert json.loads(response.get_data(as_text=True))["error"]["code"] == code  # Preserve authoritative code.
        assert history_case.database.loader.call_count == 0  # Authorize before loading an optional store module.
        assert history_case.database.readers.connections == 0 and history_case.database.aql.calls == []  # No source.

    @pytest.mark.parametrize("kind", ["capture", "run"])
    @pytest.mark.parametrize("direct", [False, True])
    def test_environment_token_policy(  # Preserve existing unavailable-privilege policy without unscoped reads.
        self, history_case: HistoryCase, kind: str, direct: bool
    ) -> None:
        """Unavailable environment-token privileges still permit an explicit selection, but never foreign records."""
        history_case.scope("  org-3484-a  ", None)  # Preserve the current unavailable-privilege policy and strip rule.
        if direct:  # Exercise the same independent authorization inside both real store adapters.
            reader = (  # Call the actual adapter without an injected capture or run approximation.
                review.store_capture_rows if kind == "capture" else review.store_run_rows
            )  # Actual source adapters.
            with history_case.context():  # The query org conflicts with the signed selection in this context.
                page = reader("site-3484-a1", limit=1, offset=1)  # Count first, then read the second matching row.
            rows = page.captures if kind == "capture" else page.runs  # Keep the actual store page shape.
            result = page.total, [row[kind + "_id"] for row in rows]  # Read real adapter output.
        else:  # The registered APIs must preserve the same environment-token policy.
            path = "/api/sites/site-3484-a1/" + ("history" if kind == "capture" else "runs/history")  # Existing paths.
            response = history_case.get(path + "?limit=1&offset=1&org_id=org-3484-b")  # Ignore query override.
            assert response.status_code == 200  # Explicit valid selection remains permitted under current policy.
            result = self.Evidence.json_rows(response, kind)  # Read actual total and membership.
            self.Evidence.clean(response.get_data(as_text=True))  # Check complete JSON for foreign content.
        assert result == (3, ["cap-a-3" if kind == "capture" else "run-a-3"])  # Exact scoped count and second row.
        self.Evidence.queries(history_case.database, "site-3484-a1")  # Verify filters before count and page.


class TestHistorySiteScope(HistoryCase):  # Verify the intersection without changing existing history controls.
    """Keep site filters, page windows, availability, and injected seam shapes."""

    @pytest.mark.parametrize(
        "site",
        [
            ("site-3484-a1", ["cap-a-5", "cap-a-3", "cap-a-1"], ["run-a-5", "run-a-3", "run-a-1"], ["op-a-2"], 3),
            (
                "site-3484-a2",
                ["cap-a-6", "cap-a-4", "cap-a-2"],
                ["run-a-6", "run-a-4", "run-a-2"],
                ["op-a-2", "op-a-1"],
                2,
            ),
            ("site-3484-b1", [], [], [], 0),
            ("site-unknown", [], [], [], 0),
        ],
    )
    @pytest.mark.parametrize("form", ["html", "capture", "run"])
    def test_site_intersections(  # A site narrows but never replaces the selected organization.
        self, history_case: HistoryCase, site: tuple[Any, ...], form: str
    ) -> None:
        """A selected organization and requested site form one intersection, including foreign and unknown sites."""
        site_id, captures, runs, operations, audit_count = site  # Keep each complete site case within five parameters.
        path = (  # Exercise all existing site request forms without site discovery.
            "/history?site_id=" + site_id
            if form == "html"
            else "/api/sites/" + site_id + ("/history" if form == "capture" else "/runs/history")
        )  # Keep all three existing site request forms.
        response = history_case.get(path)  # No site discovery or organization guess is permitted.
        assert response.status_code == 200  # Foreign and unknown sites retain successful empty intersections.
        text = response.get_data(as_text=True)  # Include attributes that legitimately repeat the requested site.
        self.Evidence.clean(text)  # Foreign stored labels, addresses, counts, and digests must remain absent.
        if form == "html":  # Verify each card independently inside the complete page.
            assert self.Evidence.html_rows(text, "capture") == captures  # Exact capture intersection and order.
            assert self.Evidence.html_rows(text, "run") == runs  # Exact run intersection and order.
            assert self.Evidence.html_rows(text, "operation") == operations  # Exact operation site membership.
            assert len(re.findall(r'data-testid="history-audit-row-\d+"', text)) == audit_count  # Exact audit scope.
            assert f'data-history-scope="site:{site_id}"' in text  # Preserve reflected request context.
        else:  # Both JSON forms require exact scoped totals and membership.
            expected = captures if form == "capture" else runs  # Use independent literal expected identifiers.
            assert self.Evidence.json_rows(response, form) == (len(expected), expected)  # Correct empty totals too.
        self.Evidence.queries(history_case.database, site_id)  # Require both filters before COUNT and LIMIT.

    @pytest.mark.parametrize(
        "query,window",
        [
            ("", (25, 0)),
            ("limit=-5&offset=-8", (1, 0)),
            ("limit=99999&offset=99999999", (200, 1000000)),
            ("limit=invalid&offset=invalid", (25, 0)),
            ("limit=1&offset=1", (1, 1)),
        ],
    )
    @pytest.mark.parametrize("form", ["html", "capture", "run"])
    def test_window_bounds_and_links(  # Preserve every current page rule inside selected scope.
        self, history_case: HistoryCase, query: str, window: tuple[int, int], form: str
    ) -> None:
        """Keep existing page defaults, clamps, nonnumeric defaults, exact totals, and site-preserving links."""
        path = (  # Keep the requested site in each page request.
            "/history?site_id=site-3484-a1&"
            if form == "html"
            else "/api/sites/site-3484-a1/" + ("history?" if form == "capture" else "runs/history?")
        )  # Exercise each existing site form.
        response = history_case.get(path + query)  # The signed organization remains authoritative for every window.
        assert response.status_code == 200  # Window parsing must not change authorization or response status.
        SyntheticStore.Aql.Input.windows(  # Check actual page binds and both HTML page queries.
            history_case.database.aql.calls, window, 2 if form == "html" else 1
        )
        self.Evidence.queries(history_case.database, "site-3484-a1")  # Scope still precedes the parsed window.
        if form == "html":  # Later-page links must preserve the site and selected page window.
            text = response.get_data(as_text=True)  # Inspect complete link attributes.
            assert "3 captures." in text  # Source totals remain independent of LIMIT and beyond-end offsets.
            if window == (1, 1):  # This middle page must offer both neighbors within the same site.
                assert "site_id=site-3484-a1" in text and "offset=2" in text and "offset=0" in text  # Neighbor scope.
                assert self.Evidence.html_rows(text, "capture") == ["cap-a-3"]  # Exact second matching capture.
        else:  # Page membership must reflect the clamped window without changing the total.
            page = SyntheticStore.Aql.Input.site_page(form, window)  # Use independent explicit site membership.
            assert self.Evidence.json_rows(response, form) == (3, page)  # Exact scoped total and page membership.

    @pytest.mark.parametrize(
        "path",
        [
            "/history",
            "/history?site_id=site-3484-a1",
            "/api/sites/site-3484-a1/history",
            "/api/sites/site-3484-a1/runs/history",
        ],
    )
    def test_read_is_lock_free_and_reauthorizes(  # Lock ownership cannot authorize or block a history read.
        self, history_case: HistoryCase, path: str
    ) -> None:
        """Another operator's hold must not block a read or preserve authorization after privilege removal."""
        logger.info("Place another operator's hold in the synthetic lock store")  # Record safe fixture preparation.
        history_case.app.config["LOCK_STORE_CLIENT"].set(  # Store another holder only in the isolated lock stand-in.
            lock.build_key("org-3484-a", "site-3484-a1"), "synthetic-other-holder", nx=True, ex=300
        )  # No Redis.
        logger.debug("Placed one synthetic hold without a network call")  # Report no lock token.
        response = history_case.get(path)  # History requires neither lock ownership nor a confirmation word.
        assert response.status_code == 200  # Keep reads available while another operator holds the site.
        assert history_case.database.lock_probe.call_count == 0  # No lock lookup occurs on any read.
        history_case.scope(permitted=())  # Remove current privileges between page requests.
        logger.info("Reset the accepted synthetic read evidence")  # Record the test-state transformation.
        for probe in history_case.database.reads.values():  # Reset only evidence counters after the accepted read.
            probe.reset_mock()  # The later refusal must produce four new zero source counts.
        history_case.database.readers.connections = 0  # Reset the synthetic connection count for the next request.
        history_case.database.aql.calls.clear()  # Separate accepted query evidence from refused request evidence.
        history_case.database.loader.reset_mock()  # Refusal must not resolve optional modules on the next page.
        logger.debug("Reset four synthetic source counters and query evidence")  # Report no source record.
        response = history_case.get(path + ("&" if "?" in path else "?") + "offset=1")  # Reauthorize the later page.
        assert response.status_code == 403 and response.get_json()["error"]["code"] == "org_not_permitted"  # Refusal.
        self.Evidence.no_reads(history_case.database)  # Cached authorization cannot permit another read.

    @pytest.mark.parametrize(
        "path", ["/history", "/api/sites/site-3484-a1/history", "/api/sites/site-3484-a1/runs/history"]
    )
    @pytest.mark.parametrize("source", ["database", "module"])
    def test_source_unavailable(  # An outage must not create an unrestricted retry.
        self, history_case: HistoryCase, path: str, source: str
    ) -> None:
        """Unavailable sources keep existing empty responses without an unrestricted retry."""
        history_case.database.available = False  # Force every real store reader onto its existing unavailable path.
        if source == "module":  # A missing optional module must preserve the real adapter's empty shape.
            history_case.database.loader.return_value = None  # Replace only module availability, not the adapter.
        response = history_case.get(path)  # A valid signed selection remains required despite the outage.
        assert response.status_code == 200  # Preserve the existing source-availability response policy.
        assert history_case.database.aql.calls == []  # No source query or unscoped fallback can run.
        if path == "/history":  # Keep truthful card-specific outage and empty displays.
            text = response.get_data(as_text=True)  # Inspect the complete unavailable-source page.
            assert "0 captures." in text and 'data-testid="history-operation-unavailable"' in text  # Existing states.
            assert self.Evidence.html_rows(text, "run") == []  # No foreign replacement run.
        else:  # Both real APIs retain the current successful empty envelope.
            kind = "run" if "/runs/" in path else "capture"  # Select the existing response field.
            assert self.Evidence.json_rows(response, kind) == (0, [])  # No unrestricted availability retry.

    @pytest.mark.parametrize("windowed", [False, True])
    def test_injected_seams_and_picker_keep_call_shapes(  # Preserve both trusted seam shapes and the site-only picker.
        self, history_case: HistoryCase, windowed: bool
    ) -> None:
        """Trusted injected site-only and windowed readers retain their calls, including the comparison picker."""
        probe = SyntheticStore.Aql.Input.Seams()  # Keep compatibility calls separate from real-query evidence.
        reader = probe.with_window if windowed else probe.site_only  # Test both existing trusted call forms.
        logger.info("Bind the trusted synthetic compatibility readers")  # Record in-memory fixture setup.
        history_case.app.config["CAPTURE_LISTER"] = reader  # Only this compatibility case injects a capture reader.
        history_case.app.config["RUN_LISTER"] = reader  # Preserve the same existing run seam shapes.
        logger.debug("Bound two trusted synthetic compatibility readers")  # Report no source row content.
        response = history_case.get("/history?site_id=site-3484-a1&limit=2&offset=1")  # Exercise history introspection.
        assert response.status_code == 200  # The repair must not expand capture or run seam signatures.
        window = (2, 1) if windowed else (25, 0)  # Keep the existing supplied windows for each injected shape.
        assert probe.calls == [("site-3484-a1", *window)] * 2  # Keep exact capture and run arguments.
        logger.info("Clear synthetic compatibility call evidence")  # Record the test-state transformation.
        probe.calls.clear()  # Separate picker calls from the two accepted history calls.
        logger.debug("Cleared synthetic compatibility call evidence")  # Report no source content.
        response = history_case.get("/compare?site_id=site-3484-a1")  # The picker still calls with the site alone.
        assert response.status_code == 200  # Preserve comparison picker availability for a valid selection.
        assert probe.calls == [("site-3484-a1", 25, 0)]  # Preserve the default window on a site-only picker call.
