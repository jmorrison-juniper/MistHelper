"""Prove audit scope and expiry isolation for issue #3484 with synthetic JSONL only."""

from __future__ import annotations  # Keep annotations independent from import order.

import hashlib  # Compute independent expected digests without a production row shaper.
import inspect  # Verify the required keyword-only organization contract directly.
import json  # Write synthetic temporary trails in stored order.
import logging  # Record synthetic file actions without stored addresses.
from pathlib import Path  # Restrict every audit fixture to the test temporary directory.
from typing import Any  # Stored audit records use mixed JSON attribution types.
from unittest.mock import Mock  # Prove invalid scope opens and reads no trail.

import pytest  # Exercise bounded, legacy, damaged-input, and inference contracts.

from src.upgrade_portal.compare import lock_audit  # Test the real audit reader and unchanged direct inference API.

logger = logging.getLogger(__name__)  # Keep audit test records separate from application records.


class AuditTrail:  # Own synthetic source records and independent expected event tables.
    """Hold interleaved organizations, reused site text, and distinct synthetic audit addresses."""

    _expected_events = (  # Keep independent expected events separate from every source record constructor.
        ("release", "second-site", "A-close", "other", False),  # Newest matching actual release.
        ("take", "shared-site", "A-next", "next", False),  # Later matching actual take.
        ("expire", "shared-site", "A-next", "holder", True),  # Earlier holder expires at the later matching moment.
        ("takeover", "second-site", "A-other", "other", False),  # Independent second-site hold.
        ("take", "shared-site", "A-start", "holder", False),  # Original matching holder.
    )

    def __init__(self, directory: Path) -> None:  # Build one temporary trail for each test.
        """Create matching holds interleaved with foreign and unattributed actions."""
        logger.info("Build one synthetic organization audit trail")  # Record fixture construction.
        self.path = directory / "issue-3484-audit.jsonl"  # Never resolve a production audit path.
        self.records = [  # Keep stored-order input independent from the expected event table.
            self.event(*values)
            for values in [  # Keep the exact stored order independent from inference.
                ("org-3484-a", "shared-site", "take", "A-start", "holder"),
                ("org-3484-b", "shared-site", "release", "FOREIGN-release", "foreign"),
                ("org-3484-a", "second-site", "takeover", "A-other", "other"),
                (None, "shared-site", "take", "FOREIGN-unattributed", "unattributed"),
                ("org-3484-a", "shared-site", "take", "A-next", "next"),
                ("org-3484-b", "shared-site", "take", "FOREIGN-next", "foreign"),
                ("org-3484-a", "second-site", "release", "A-close", "other"),
            ]
        ]
        self.records.extend(  # Newer foreign input must consume no bounded matching position.
            self.event("org-3484-b", "shared-site", "release", f"FOREIGN-new-{number}", "foreign")
            for number in range(10)
        )  # Foreign trailing rows must consume no bounded positions.
        self.write()  # Write only this test's synthetic records.
        logger.debug("Built one synthetic audit trail with %s input records", len(self.records))  # Safe count.

    @staticmethod
    def event(  # Preserve stored attribution and synthetic addresses for disclosure checks.
        org_id: Any, site_id: str, action: str, moment: str, actor: str
    ) -> dict[str, Any]:
        """Return one synthetic stored event with addresses absent from all public expectations."""
        logger.info("Build one synthetic stored audit event")  # Record the data transformation.
        row = {  # These reserved addresses exist only in synthetic temporary input.
            "org_id": org_id,
            "site_id": site_id,
            "action": action,
            "occurred_at": moment,
            "actor_email": actor + ".audit@example.invalid",  # Give each hold a distinct independent digest.
            "previous_actor_email": "previous.audit@example.invalid",  # Prove digest-only previous-holder output.
        }
        logger.debug("Built one synthetic stored audit event with %s fields", len(row))  # Report no address.
        return row  # Expected public fields come from a separate event table.

    def write(self) -> None:  # Persist synthetic input in stored order without a production source.
        """Write the current synthetic trail to this test's temporary path."""
        logger.info("Write the synthetic temporary audit trail")  # Record the file action before it starts.
        text = "\n".join(json.dumps(row) for row in self.records) + "\n"  # Preserve input order and line boundaries.
        self.path.write_text(text, encoding="utf-8")  # This path belongs to pytest's isolated temporary directory.
        logger.debug("Wrote %s synthetic audit records", len(self.records))  # Report only the input count.

    @staticmethod
    def expected(site_id: str = "") -> list[dict[str, Any]]:  # Keep complete expected answers independent.
        """Return explicitly ordered expected public events, not production-shaped source rows."""
        logger.info("Build the independent expected audit event table")  # Record the expected-data transformation.
        previous = hashlib.blake2s(b"previous.audit@example.invalid", digest_size=8).hexdigest()  # Independent digest.
        result = [  # Keep expected public events independent from production shaping and inference.
            {  # Use explicit expected attribution and the established digest algorithm only.
                "action": action,
                "org_id": "org-3484-a",
                "site_id": site,
                "occurred_at": moment,
                "actor_digest": hashlib.blake2s((actor + ".audit@example.invalid").encode(), digest_size=8).hexdigest(),
                "previous_digest": "" if inferred else previous,
                "inferred": inferred,  # An expiry has no previous actor.
            }
            for action, site, moment, actor, inferred in AuditTrail._expected_events  # Use independent literal events.
            if not site_id or site == site_id
        ]  # Optional intersection.
        logger.debug("Built %s independent expected audit events", len(result))  # Report a safe count.
        return result  # No expected event uses audit_row or mark_expiries.


class AuditCase:  # Share class-owned temporary input without another test support file.
    """Provide synthetic audit input and strict public-output checks."""

    @staticmethod
    def inferred_take(rows: list[dict[str, Any]]) -> None:  # Keep matching expiry expectations independent.
        """Require the earlier holder's attribution at the later matching take."""
        logger.info("Check the independent matching expiry fields")  # Record the evidence transformation.
        assert [row["action"] for row in rows] == ["take", "expire"]  # Older context must survive the result limit.
        assert [row["inferred"] for row in rows] == [False, True]  # Insert exactly one expiry before the actual take.
        digest = hashlib.blake2s(  # Identify the earlier holder without a production shaper.
            b"holder.audit@example.invalid", digest_size=8
        ).hexdigest()  # Independent earlier actor.
        actual = {  # Compare all four matching attributes without production-shaped expectations.
            field: rows[1][field] for field in ("org_id", "site_id", "occurred_at", "actor_digest")
        }
        assert actual == {  # Preserve earlier attribution and the later matching moment.
            "org_id": "org-3484-a",
            "site_id": "shared-site",
            "occurred_at": "A-next",
            "actor_digest": digest,
        }
        assert rows[1]["previous_digest"] == ""  # An inferred expiry names no previous holder.
        logger.debug("Checked six independent matching expiry fields")  # Report no stored address or row.

    @pytest.fixture
    def audit_trail(self, tmp_path: Path) -> AuditTrail:  # Keep fixture construction inside a class.
        """Return a synthetic trail isolated from checkout and production data."""
        return AuditTrail(tmp_path)  # The root fixture and unit socket guard remain active.

    @staticmethod
    def public(rows: list[dict[str, Any]]) -> None:  # Inspect complete public rows for raw or foreign content.
        """Require exact public fields and digest-only addresses on actual and inferred rows."""
        logger.info("Check complete synthetic audit output")  # Record the assertion action.
        fields = {  # No stored address or owner field can enter public audit output.
            "action",
            "org_id",
            "site_id",
            "occurred_at",
            "actor_digest",
            "previous_digest",
            "inferred",
        }
        for row in rows:  # Each actual or inferred event must keep the existing public output shape.
            assert set(row) == fields and row["org_id"] == "org-3484-a"  # No source fields or foreign attribution.
            assert "@" not in json.dumps(row) and "FOREIGN" not in json.dumps(row)  # No raw address or foreign moment.
            digest = row["actor_digest"]  # Check the established digest representation without the production helper.
            assert len(digest) == 16 and set(digest) <= set(  # Preserve the established one-way representation.
                "0123456789abcdef"
            )  # Require a lowercase hexadecimal digest.
        logger.debug("Checked %s complete public audit rows", len(rows))  # Report only the output count.


class TestAuditReadScope(AuditCase):  # Prove mandatory scope before trail access and before output limits.
    """Require matching organization and optional site before reading or shaping a result."""

    def test_required_keyword_organization(self, audit_trail: AuditTrail) -> None:  # Prevent an unrestricted default.
        """The public reader must have no unrestricted default organization."""
        parameters = inspect.signature(lock_audit.read_audit_rows).parameters  # Inspect the real public interface.
        assert "org_id" in parameters  # Absence is a failed security contract, not a fixture import problem.
        assert parameters["org_id"].kind is inspect.Parameter.KEYWORD_ONLY  # Positional callers cannot omit scope.
        assert parameters["org_id"].default is inspect.Parameter.empty  # No empty default can widen scope.
        assert list(parameters) == ["limit", "path", "site_id", "org_id"]  # Preserve the existing positional order.
        with pytest.raises(TypeError, match="org_id"):  # Missing scope must fail before any source access.
            lock_audit.read_audit_rows(path=audit_trail.path)  # Deliberately omit the now-required authority.

    @pytest.mark.parametrize("org_id", [None, "", " \t ", 42, False, [], {}])
    def test_invalid_scope_reads_nothing(  # Invalid scope must fail before file access.
        self, audit_trail: AuditTrail, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, org_id: Any
    ) -> None:
        """Invalid organizations must explicitly log and refuse before opening or reading a trail."""
        reader = Mock(side_effect=AssertionError("Invalid audit scope must not read a trail."))  # Read guard.
        opener = Mock(side_effect=AssertionError("Invalid audit scope must not open a trail."))  # File guard.
        monkeypatch.setattr(lock_audit, "read_trail_lines", reader)  # Prove validation precedes source resolution.
        monkeypatch.setattr("builtins.open", opener)  # Prove the reader cannot access even an existing trail.
        caplog.set_level(logging.INFO, logger=lock_audit.__name__)  # Capture the safe refusal decision.
        with pytest.raises(ValueError, match="organization"):  # Invalid scope is an explicit reader refusal.
            lock_audit.read_audit_rows(path=audit_trail.path, org_id=org_id)  # Preserve incorrectly typed test input.
        assert reader.call_count == 0 and opener.call_count == 0  # No read or open occurs for an invalid organization.
        assert any("organization" in record.getMessage() for record in caplog.records)  # The refusal is observable.

    @pytest.mark.parametrize("site_id", ["", "shared-site", "second-site", "foreign-site"])
    @pytest.mark.parametrize("limit", [None, 200, 2])
    def test_exact_scoped_events(  # Check complete bounded and unbounded output against independent events.
        self, audit_trail: AuditTrail, site_id: str, limit: int | None
    ) -> None:
        """Actual full and bounded results must match the independent expected event table."""
        rows = lock_audit.read_audit_rows(  # Apply actual organization and optional site scope.
            limit=limit, path=audit_trail.path, site_id=site_id, org_id="org-3484-a"
        )  # Use the real scope and inference implementation.
        assert rows == AuditTrail.expected(site_id)[:limit]  # Foreign trailing rows consume no result positions.
        self.public(rows)  # Both actual and inferred public rows must retain digests without addresses.

    @pytest.mark.parametrize("damage", ["absent", "blank", "damaged", "nonrecord"])
    def test_missing_and_damaged_input(  # Preserve existing damaged-line and missing-file behavior.
        self, audit_trail: AuditTrail, damage: str
    ) -> None:
        """Missing files, blank lines, damaged lines, and non-record JSON retain existing safe handling."""
        logger.info("Prepare one synthetic audit input condition")  # Record the file action before it starts.
        if damage == "absent":  # No trail exists before any lock action.
            audit_trail.path.unlink()  # Remove only this test's synthetic temporary file.
        else:  # Every other condition must cost only the unusable input lines.
            suffix = {  # Unusable lines must not change matching output.
                "blank": "\n \t\n",
                "damaged": '{"action":\n',
                "nonrecord": 'null\n[]\n17\n"text"\n',
            }[
                damage
            ]  # Keep bad input independent of production.
            with audit_trail.path.open("a", encoding="utf-8") as handle:  # Append only to the temporary trail.
                handle.write(suffix)  # Exercise actual line parsing and record-shape checks.
        logger.debug("Prepared one synthetic audit input condition")  # Report no input addresses.
        rows = lock_audit.read_audit_rows(path=audit_trail.path, org_id="org-3484-a")  # Real damaged-line handling.
        assert rows == ([] if damage == "absent" else AuditTrail.expected())  # Preserve matching rows exactly.
        self.public(rows)  # No unusable or foreign input can reach public output.

    @pytest.mark.parametrize("change", ["add", "remove", "reorder"])
    def test_foreign_changes_preserve_matching_output(  # Foreign input must not affect matching inference.
        self, audit_trail: AuditTrail, change: str
    ) -> None:
        """Foreign event changes must not alter matching expiry moments, attribution, digests, or bounded positions."""
        logger.info("Change only foreign synthetic audit events")  # Record the test transformation.
        if change == "add":  # Reused site text must not connect holds across organizations.
            audit_trail.records.insert(  # A foreign takeover must not replace the selected holder.
                4, AuditTrail.event("org-3484-b", "shared-site", "takeover", "FOREIGN-new", "foreign")
            )
        elif change == "remove":  # Remove foreign and unattributed records without altering matching order.
            audit_trail.records = [  # Remove foreign input without altering matching stored order.
                row for row in audit_trail.records if row.get("org_id") == "org-3484-a"
            ]
        else:  # Move a foreign closing event before matching takes while preserving matching order.
            audit_trail.records.insert(0, audit_trail.records.pop())  # Foreign input position cannot affect inference.
        audit_trail.write()  # Persist only the modified synthetic input.
        logger.debug("Applied one foreign synthetic audit transformation")  # Report no input content.
        assert (  # Preserve exact full matching events independently.
            lock_audit.read_audit_rows(limit=None, path=audit_trail.path, org_id="org-3484-a") == AuditTrail.expected()
        )
        assert (  # Foreign actions cannot consume matching bounded positions.
            lock_audit.read_audit_rows(limit=2, path=audit_trail.path, org_id="org-3484-a") == AuditTrail.expected()[:2]
        )


class TestAuditInference(AuditCase):  # Prove transitions independently of the proposed public-reader signature.
    """Keep hold state separate for each organization and site."""

    @pytest.mark.parametrize("opening", ["take", "takeover"])
    @pytest.mark.parametrize("foreign_action", ["take", "takeover", "release", "expire"])
    @pytest.mark.parametrize("organizations", [("org-3484-a", "org-3484-b"), ("42", 42), ("True", True)])
    def test_direct_mark_expiries_isolates_organizations(  # Prove a defect through the unchanged direct inference API.
        self, opening: str, foreign_action: str, organizations: tuple[str, Any]
    ) -> None:
        """The unchanged direct inference API must not join reused site text across organizations."""
        selected_org, foreign_org = organizations  # Keep valid string and incorrectly typed attribution distinct.
        records = [  # Include foreign and unattributed events between two matching actions.
            AuditTrail.event(selected_org, "shared-site", opening, "A-start", "holder"),
            AuditTrail.event(foreign_org, "shared-site", foreign_action, "FOREIGN-moment", "foreign"),
            AuditTrail.event(None, "shared-site", "release", "FOREIGN-unattributed", "unattributed"),
            AuditTrail.event(selected_org, "shared-site", "take", "A-next", "next"),
        ]
        rows = lock_audit.mark_expiries(records)  # This existing API can prove a behavioral defect before repair.
        inferred = [row for row in rows if row.get("inferred")]  # Inspect actual inferred attribution and timing.
        assert inferred == [  # The earlier selected holder expires only at the later selected take.
            {  # Independent expected raw inference output, before public digest shaping.
                "action": "expire",
                "org_id": selected_org,
                "site_id": "shared-site",
                "occurred_at": "A-next",
                "actor_email": "holder.audit@example.invalid",
                "previous_actor_email": "",
                "inferred": True,
            }
        ]  # Foreign and unattributed actions cannot close or replace the selected hold.

    @pytest.mark.parametrize("opening", ["take", "takeover", "missing"])
    def test_both_opening_actions_and_legacy_action(  # Preserve take, takeover, and missing-action inference.
        self, audit_trail: AuditTrail, opening: str
    ) -> None:
        """A later take infers one expiry after a take, takeover, or legacy missing action."""
        first = AuditTrail.event("org-3484-a", "shared-site", opening, "A-start", "holder")  # Earlier matching hold.
        if opening == "missing":  # Preserve the legacy interpretation rather than invent an unknown action.
            first.pop("action")  # A missing action has always represented a takeover.
        audit_trail.records = [  # Another site cannot change this matching hold.
            first,
            AuditTrail.event("org-3484-a", "second-site", "take", "A-other", "other"),
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-next", "next"),
        ]
        audit_trail.write()  # Persist only this test's synthetic trail.
        rows = lock_audit.read_audit_rows(  # Keep older context before the bounded output limit.
            limit=2, path=audit_trail.path, org_id="org-3484-a", site_id="shared-site"
        )
        assert [row["action"] for row in rows] == ["take", "expire"]  # Prove the actual opening-action result directly.
        self.inferred_take(rows)  # Preserve every independent matching inference assertion.
        self.public(rows)  # Public inference must still exclude stored addresses.

    @pytest.mark.parametrize("closing", ["release", "expire", "other-action"])
    def test_closing_actions_suppress_expiry(  # Keep all existing closing-action meanings.
        self, audit_trail: AuditTrail, closing: str
    ) -> None:
        """Release, explicit expiry, and existing other closing actions close only their own matching hold."""
        audit_trail.records = [  # A matching closure must prevent a later inferred expiry.
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-start", "holder"),
            AuditTrail.event("org-3484-a", "shared-site", closing, "A-close", "holder"),
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-next", "next"),
        ]
        audit_trail.write()  # Write only the synthetic matching transition sequence.
        rows = lock_audit.read_audit_rows(limit=None, path=audit_trail.path, org_id="org-3484-a")  # Scoped full read.
        assert [row["action"] for row in rows] == ["take", closing, "take"]  # No inferred expiry follows closure.
        assert [row["inferred"] for row in rows] == [False, False, False]  # Keep every row an actual action.
        self.public(rows)  # Actual closure events keep the same digest-only output.

    def test_takeover_replaces_without_an_immediate_expiry(  # A takeover must not count one ending twice.
        self, audit_trail: AuditTrail
    ) -> None:
        """A takeover replaces a hold without an expiry, but a later take expires the takeover holder."""
        audit_trail.records = [  # Only the later matching take can expire the replacement holder.
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-start", "holder"),
            AuditTrail.event("org-3484-a", "shared-site", "takeover", "A-replace", "replacement"),
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-next", "next"),
        ]
        audit_trail.write()  # Persist only the synthetic replacement sequence.
        rows = lock_audit.read_audit_rows(limit=None, path=audit_trail.path, org_id="org-3484-a")  # Scoped full read.
        assert [row["action"] for row in rows] == ["take", "expire", "takeover", "take"]  # No takeover-time expiry.
        digest = hashlib.blake2s(b"replacement.audit@example.invalid", digest_size=8).hexdigest()  # Independent actor.
        assert (rows[1]["occurred_at"], rows[1]["actor_digest"]) == ("A-next", digest)  # Expire the replacement holder.
        assert [row["inferred"] for row in rows] == [False, True, False, False]  # Infer only the later matching expiry.
        self.public(rows)  # Preserve digest-only output for both opening actions.

    def test_old_context_survives_many_foreign_events(  # Keep older matching context beyond visible limits.
        self, audit_trail: AuditTrail
    ) -> None:
        """Foreign events beyond the limit must not remove older matching context or change expiry attribution."""
        audit_trail.records = [  # Open the selected hold before all later foreign events.
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-start", "holder")
        ]
        audit_trail.records.extend(  # Foreign releases cannot close the selected hold.
            AuditTrail.event("org-3484-b", "shared-site", "release", f"FOREIGN-{number}", "foreign")
            for number in range(250)
        )  # Exceed the default limit.
        audit_trail.records.append(  # Only this later matching take identifies the selected expiry.
            AuditTrail.event("org-3484-a", "shared-site", "take", "A-next", "next")
        )
        audit_trail.write()  # Store the complete synthetic context before any bounded read.
        rows = lock_audit.read_audit_rows(  # Apply the visible limit only after matching inference.
            limit=2, path=audit_trail.path, org_id="org-3484-a", site_id="shared-site"
        )
        assert [row["action"] for row in rows] == ["take", "expire"]  # Foreign actions cannot suppress the expiry.
        assert [row["occurred_at"] for row in rows] == ["A-next", "A-next"]  # Foreign moments cannot alter timing.
        digest = hashlib.blake2s(b"holder.audit@example.invalid", digest_size=8).hexdigest()  # Earlier matching actor.
        assert rows[1]["actor_digest"] == digest and rows[1]["inferred"] is True  # Retain older matching attribution.
        self.public(rows)  # No foreign moment or stored address reaches the bounded output.


class TestAuditLegacyLimits(AuditCase):  # Preserve existing slice meanings without an unrestricted read path.
    """Keep bounded/full equivalence and zero, negative, and None slice behavior."""

    @pytest.mark.parametrize("limit", [0, -1, -3, None])
    def test_legacy_slice_semantics(  # Preserve zero, negative, and None final slices.
        self, audit_trail: AuditTrail, limit: int | None
    ) -> None:
        """Scope and infer the complete matching sequence before the existing final Python slice."""
        rows = lock_audit.read_audit_rows(  # Apply explicit scope before the original legacy slice.
            limit=limit, path=audit_trail.path, org_id="org-3484-a"
        )  # Scoped legacy read.
        assert rows == AuditTrail.expected()[:limit]  # Preserve the exact original zero, negative, and None semantics.
        self.public(rows)  # Even unbounded or negative-limit output must contain only matching public rows.

    @pytest.mark.parametrize("site_id", ["", "shared-site", "second-site"])
    @pytest.mark.parametrize("limit", [1, 2, 4, 200])
    def test_bounded_equals_independent_full_result(  # Both reader paths must retain exactly the same matching events.
        self, audit_trail: AuditTrail, site_id: str, limit: int
    ) -> None:
        """A positive bounded page must equal the newest matching rows from the full independent event table."""
        full = lock_audit.read_audit_rows(  # Verify full output independently before comparing bounded output.
            limit=None, path=audit_trail.path, site_id=site_id, org_id="org-3484-a"
        )
        bounded = lock_audit.read_audit_rows(  # Foreign input must consume no visible matching position.
            limit=limit, path=audit_trail.path, site_id=site_id, org_id="org-3484-a"
        )
        assert full == AuditTrail.expected(site_id)  # Verify the full answer independently before comparing paths.
        assert bounded == AuditTrail.expected(site_id)[:limit] and bounded == full[:limit]  # Exact bounded equivalence.
        self.public(bounded)  # Both paths retain the original public fields and digest representation.

    def test_private_scoped_reader(self, audit_trail: AuditTrail) -> None:  # Prevent an obsolete unrestricted alias.
        """Direct private calls must use explicit organization scope without an obsolete compatibility alias."""
        rows = lock_audit._read_limited_audit_rows(  # Direct private calls must still supply explicit scope.
            2, audit_trail.path, "shared-site", org_id="org-3484-a"
        )
        assert (  # Keep independent bounded event expectations.
            rows == AuditTrail.expected("shared-site")[:2]
        )  # Private bounded calls must not recreate unrestricted scope.
        assert (  # Require both organization and site membership.
            lock_audit._row_in_scope({"org_id": "org-3484-a", "site_id": "shared-site"}, "org-3484-a", "shared-site")
            is True
        )  # Match both required dimensions.
        assert (  # Reused site text must not supply foreign organization scope.
            lock_audit._row_in_scope({"org_id": "org-3484-b", "site_id": "shared-site"}, "org-3484-a", "shared-site")
            is False
        )  # Reused site text cannot supply scope.
        assert (  # Unattributed records must remain outside every selected organization.
            lock_audit._row_in_scope({"site_id": "shared-site"}, "org-3484-a", "") is False
        )  # No missing attribution.
