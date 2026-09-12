"""Cover the WLAN RADIUS timer manager, which writes authentication settings.

The manager owns menu 148. It reads WLANs from three sources. It then writes a
new timer set to one of three Mist API endpoints. A wrong endpoint choice or a
lost error branch changes the authentication behavior of a live WLAN.

These tests cover the template matching rules, the RADIUS detection rules, the
input boundaries, and every API error branch. Every Mist API call is mocked.
"""

from __future__ import annotations  # WHY: allow the PEP 604 union syntax in the annotations.

import logging  # WHY: the debug toggle changes the root logger level.
import sys  # WHY: patch.dict on sys.modules injects the fake MistHelper module.
from typing import Any  # WHY: the fixtures return loosely typed doubles.
from unittest.mock import MagicMock, patch  # WHY: MagicMock builds the doubles, patch swaps them.

import pytest  # WHY: the fixtures and the raises helper come from pytest.

from src.refactors import wlanradius_timer_manager as wrtm  # WHY: patch the module globals.
from src.refactors.wlanradius_timer_manager import (  # WHY: the module under test.
    WLANRadiusTimerManager,
    _MistHelperProxy,
)


def _response(status_code: int, data: Any = None) -> MagicMock:
    """Build a stand-in for a mistapi response with a status code and a body."""
    response = MagicMock()  # WHY: the caller reads only two attributes.
    response.status_code = status_code  # WHY: every branch under test keys off the status.
    response.data = data  # WHY: the success branch decodes this body.
    return response  # WHY: the test then assigns it to a mocked API call.


@pytest.fixture
def fake_mh() -> Any:
    """Install a fake MistHelper module so the lazy proxy resolves to a double."""
    fake = MagicMock()  # WHY: the proxy reads arbitrary attributes from this module.
    fake.apisession = MagicMock()  # WHY: every Mist API call takes the session first.
    fake.InputUtils = MagicMock()  # WHY: the prompts call InputUtils.safe_input.
    fake.InputUtils.safe_input = MagicMock(return_value="")  # WHY: a real string supports strip.
    with patch.dict(sys.modules, {"MistHelper": fake}):  # WHY: the proxy imports by name.
        yield fake  # WHY: the test body runs with the fake in place.


@pytest.fixture
def api() -> Any:
    """Replace the mistapi module inside the manager so no call reaches the network."""
    fake_api = MagicMock()  # WHY: one double covers every nested API path.
    with patch.object(wrtm, "mistapi", fake_api):  # WHY: the module calls mistapi by global name.
        yield fake_api  # WHY: the test body wires the specific endpoint it needs.


@pytest.fixture
def manager() -> WLANRadiusTimerManager:
    """Build a manager with a site and an org already resolved."""
    instance = WLANRadiusTimerManager()  # WHY: the default constructor sets the timer defaults.
    instance.site_id = "site-1"  # WHY: most helpers need a site to scope the lookup.
    instance.org_id = "org-1"  # WHY: the org scopes the template and the org WLAN lookups.
    instance.site_name = "Lab"  # WHY: the inheritance labels embed the site name.
    return instance  # WHY: each test then sets only the state it needs.


class TestProxy:
    """Cover the lazy proxy that breaks the import cycle with MistHelper."""

    def test_the_proxy_forwards_an_attribute_to_the_live_module(self, fake_mh: Any) -> None:
        """A broken proxy would resolve a stale session after an interactive login."""
        fake_mh.apisession = "the-session"  # WHY: a unique value proves the forward happened.
        assert _MistHelperProxy().apisession == "the-session"  # WHY: the proxy must read it live.

    def test_the_proxy_reads_the_value_at_call_time(self, fake_mh: Any) -> None:
        """A cached value would ignore a re-login, so every later write would fail."""
        proxy = _MistHelperProxy()  # WHY: build the proxy before the value changes.
        fake_mh.apisession = "first"  # WHY: the first bound value.
        assert proxy.apisession == "first"  # WHY: read it once to prime any accidental cache.
        fake_mh.apisession = "second"  # WHY: simulate a re-login rebinding the session.
        assert proxy.apisession == "second"  # WHY: the proxy must see the new value.


class TestUsesRadiusAuth:
    """Cover the RADIUS detection rule, which decides whether a WLAN is editable."""

    def test_an_auth_server_list_counts_as_radius(self, manager: WLANRadiusTimerManager) -> None:
        """A missed RADIUS WLAN never appears in the picker, so the operator cannot fix it."""
        assert manager._uses_radius_auth({"auth_servers": [{"host": "1.1.1.1"}]}) is True

    def test_an_empty_auth_server_list_does_not_count(self, manager: WLANRadiusTimerManager) -> None:
        """An empty list means no RADIUS server, so the timers have no effect."""
        assert manager._uses_radius_auth({"auth_servers": []}) is False

    def test_radsec_enabled_counts_as_radius(self, manager: WLANRadiusTimerManager) -> None:
        """RadSec is RADIUS over TLS, so it obeys the same timers."""
        assert manager._uses_radius_auth({"radsec": {"enabled": True}}) is True

    def test_radsec_disabled_does_not_count(self, manager: WLANRadiusTimerManager) -> None:
        """A disabled RadSec block must not pull a PSK WLAN into the picker."""
        assert manager._uses_radius_auth({"radsec": {"enabled": False}}) is False

    def test_a_non_dict_radsec_block_is_ignored(self, manager: WLANRadiusTimerManager) -> None:
        """A malformed record must not raise and stop the whole discovery pass."""
        assert manager._uses_radius_auth({"radsec": "broken"}) is False

    @pytest.mark.parametrize("auth_type", ["eap", "eap192"])
    def test_an_eap_auth_type_counts_as_radius(self, manager: WLANRadiusTimerManager, auth_type: str) -> None:
        """Both EAP types use 802.1X, so both depend on the RADIUS timers."""
        assert manager._uses_radius_auth({"auth": {"type": auth_type}}) is True

    def test_a_psk_auth_type_does_not_count(self, manager: WLANRadiusTimerManager) -> None:
        """A PSK WLAN has no RADIUS server, so editing its timers would confuse the operator."""
        assert manager._uses_radius_auth({"auth": {"type": "psk"}}) is False

    def test_a_non_dict_auth_block_is_ignored(self, manager: WLANRadiusTimerManager) -> None:
        """A malformed record must not raise and stop the whole discovery pass."""
        assert manager._uses_radius_auth({"auth": "broken"}) is False

    def test_an_empty_wlan_does_not_count(self, manager: WLANRadiusTimerManager) -> None:
        """A record with no auth keys must not reach the editor."""
        assert manager._uses_radius_auth({}) is False


class TestTemplateAssignment:
    """Cover the rules that decide whether an org template applies to this site."""

    def test_an_org_wide_template_matches(self) -> None:
        """An org-wide template covers every site, so it must always match."""
        applies = {"org_id": "org-1"}  # WHY: the org_id key marks an org-wide scope.
        assert WLANRadiusTimerManager._template_matches_org_or_site(applies, "site-1") is True

    def test_an_explicit_site_list_matches(self) -> None:
        """A direct site list is the most common assignment, so it must match."""
        applies = {"site_ids": ["site-1", "site-2"]}  # WHY: the site is listed by identifier.
        assert WLANRadiusTimerManager._template_matches_org_or_site(applies, "site-1") is True

    def test_a_site_outside_the_list_does_not_match(self) -> None:
        """A wrong match would edit a WLAN that this site never uses."""
        applies = {"site_ids": ["site-2"]}  # WHY: the site under test is absent.
        assert WLANRadiusTimerManager._template_matches_org_or_site(applies, "site-1") is False

    def test_an_empty_applies_block_does_not_match(self) -> None:
        """A template with no scope applies to nothing."""
        assert WLANRadiusTimerManager._template_matches_org_or_site({}, "site-1") is False

    def test_a_shared_site_group_matches(self) -> None:
        """A group assignment is indirect, so a lost branch hides many WLANs."""
        applies = {"sitegroup_ids": ["group-a"]}  # WHY: the template targets a site group.
        assert WLANRadiusTimerManager._template_matches_grouping(applies, ["group-a"], []) is True

    def test_a_shared_wx_tag_matches(self) -> None:
        """A tag assignment is indirect, so a lost branch hides many WLANs."""
        applies = {"wxtag_ids": ["tag-a"]}  # WHY: the template targets a Wx tag.
        assert WLANRadiusTimerManager._template_matches_grouping(applies, [], ["tag-a"]) is True

    def test_no_shared_group_or_tag_does_not_match(self) -> None:
        """A wrong match would edit a WLAN that this site never uses."""
        applies = {"sitegroup_ids": ["group-b"], "wxtag_ids": ["tag-b"]}  # WHY: no overlap.
        assert WLANRadiusTimerManager._template_matches_grouping(applies, ["group-a"], ["tag-a"]) is False

    def test_a_missing_applies_block_is_not_assigned(self, manager: WLANRadiusTimerManager) -> None:
        """A template with no scope must not pull WLANs into the picker."""
        assert manager._is_template_assigned_to_site({}) is False

    def test_a_non_dict_applies_block_is_not_assigned(self, manager: WLANRadiusTimerManager) -> None:
        """A malformed template must not raise and stop the whole discovery pass."""
        assert manager._is_template_assigned_to_site({"applies": "broken"}) is False

    def test_an_explicit_site_match_skips_the_group_rules(self, manager: WLANRadiusTimerManager) -> None:
        """The direct scope wins first, so a site with no groups still matches."""
        manager.site_info = {}  # WHY: no group or tag data is present on this site.
        template = {"applies": {"site_ids": ["site-1"]}}  # WHY: the direct list names the site.
        assert manager._is_template_assigned_to_site(template) is True

    def test_a_group_match_is_read_from_the_site_info(self, manager: WLANRadiusTimerManager) -> None:
        """The group list lives on the site record, so a lost read hides the match."""
        manager.site_info = {"sitegroup_ids": ["group-a"]}  # WHY: the site belongs to the group.
        template = {"applies": {"sitegroup_ids": ["group-a"]}}  # WHY: the template targets it.
        assert manager._is_template_assigned_to_site(template) is True

    def test_a_tag_match_is_read_from_the_site_info(self, manager: WLANRadiusTimerManager) -> None:
        """The tag list lives on the site record, so a lost read hides the match."""
        manager.site_info = {"wxtag_ids": ["tag-a"]}  # WHY: the site carries the tag.
        template = {"applies": {"wxtag_ids": ["tag-a"]}}  # WHY: the template targets it.
        assert manager._is_template_assigned_to_site(template) is True

    def test_only_the_assigned_templates_are_collected(self, manager: WLANRadiusTimerManager) -> None:
        """An unassigned template would expose a WLAN that this site never broadcasts."""
        manager.site_info = {}  # WHY: rely on the direct site list only.
        manager.wlan_templates = [  # WHY: one template matches and one does not.
            {"id": "t-yes", "applies": {"site_ids": ["site-1"]}},
            {"id": "t-no", "applies": {"site_ids": ["site-9"]}},
        ]
        manager._determine_assigned_templates()  # WHY: run the collection pass.
        assert manager.assigned_template_ids == {"t-yes"}  # WHY: only the match may survive.


class TestOrgWlanCollection:
    """Cover the org WLAN filter, which tags each WLAN with its inheritance source."""

    def test_a_wlan_without_a_template_is_skipped(self, manager: WLANRadiusTimerManager) -> None:
        """An untemplated org WLAN does not reach this site, so it must not be listed."""
        assert manager._collect_assigned_org_wlan({"id": "w1"}) is False
        assert manager.org_wlans == []  # WHY: the skip must not append.

    def test_a_wlan_on_an_unassigned_template_is_skipped(self, manager: WLANRadiusTimerManager) -> None:
        """A WLAN from another site would be edited by mistake."""
        manager.assigned_template_ids = {"t-yes"}  # WHY: only this template applies here.
        assert manager._collect_assigned_org_wlan({"id": "w1", "template_id": "t-no"}) is False

    def test_a_wlan_on_an_assigned_template_is_kept(self, manager: WLANRadiusTimerManager) -> None:
        """A lost keep would hide every org WLAN from the picker."""
        manager.assigned_template_ids = {"t-yes"}  # WHY: this template applies here.
        manager.wlan_templates = [{"id": "t-yes", "name": "Corp"}]  # WHY: supply the display name.
        wlan = {"id": "w1", "template_id": "t-yes"}  # WHY: the WLAN points at the template.
        assert manager._collect_assigned_org_wlan(wlan) is True
        assert manager.org_wlans == [wlan]  # WHY: the WLAN must reach the list.

    def test_the_metadata_names_the_source_template(self, manager: WLANRadiusTimerManager) -> None:
        """The operator needs the template name to judge the blast radius of a change."""
        manager.wlan_templates = [{"id": "t-yes", "name": "Corp"}]  # WHY: supply the display name.
        wlan: dict[str, Any] = {"id": "w1"}  # WHY: start from a bare record.
        manager._add_org_wlan_metadata(wlan, "t-yes")  # WHY: apply the inheritance tags.
        assert wlan["_inheritance_level"] == "org_wlan_with_template"  # WHY: drives the write path.
        assert wlan["_wlan_template_id"] == "t-yes"  # WHY: records the source template.
        assert wlan["_wlan_template_name"] == "Corp"  # WHY: the display name for the prompt.

    def test_an_unknown_template_falls_back_to_a_safe_name(self, manager: WLANRadiusTimerManager) -> None:
        """A missing template must not raise during the display pass."""
        manager.wlan_templates = []  # WHY: the referenced template is absent.
        wlan: dict[str, Any] = {"id": "w1"}  # WHY: start from a bare record.
        manager._add_org_wlan_metadata(wlan, "t-gone")  # WHY: apply the inheritance tags.
        assert wlan["_wlan_template_name"] == "Unknown Template"  # WHY: the safe fallback.

    def test_a_template_without_a_name_falls_back(self, manager: WLANRadiusTimerManager) -> None:
        """A nameless template must not print an empty label."""
        manager.wlan_templates = [{"id": "t-yes"}]  # WHY: the record carries no name key.
        wlan: dict[str, Any] = {"id": "w1"}  # WHY: start from a bare record.
        manager._add_org_wlan_metadata(wlan, "t-yes")  # WHY: apply the inheritance tags.
        assert wlan["_wlan_template_name"] == "Unknown Template"  # WHY: the safe fallback.

    def test_a_failed_org_wlan_fetch_leaves_the_list_empty(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A silent failure would look like a site with no RADIUS WLANs."""
        api.api.v1.orgs.wlans.listOrgWlans.return_value = _response(503)  # WHY: the API is down.
        manager._fetch_and_filter_org_wlans()  # WHY: run the fetch and filter pass.
        assert manager.org_wlans == []  # WHY: no WLAN may be invented from a failed call.

    def test_a_successful_org_wlan_fetch_keeps_the_assigned_wlans(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A lost filter would list a WLAN that this site never broadcasts."""
        manager.assigned_template_ids = {"t-yes"}  # WHY: only this template applies here.
        rows = [{"id": "w1", "template_id": "t-yes"}, {"id": "w2", "template_id": "t-no"}]
        api.api.v1.orgs.wlans.listOrgWlans.return_value = _response(200, rows)  # WHY: two records.
        manager._fetch_and_filter_org_wlans()  # WHY: run the fetch and filter pass.
        assert [w["id"] for w in manager.org_wlans] == ["w1"]  # WHY: only the assigned one survives.


class TestSiteAndTemplateFetch:
    """Cover the three API reads, because each one has a distinct failure branch."""

    def test_the_site_info_is_cached_on_success(self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any) -> None:
        """The site name and the template identifier drive every later step."""
        body = {"name": "Lab A", "sitetemplate_id": "st-1"}  # WHY: a normal site record.
        api.api.v1.sites.sites.getSiteInfo.return_value = _response(200, body)  # WHY: a good read.
        assert manager._fetch_site_info() is True  # WHY: the caller continues on True.
        assert manager.site_name == "Lab A"  # WHY: the prompts print this name.
        assert manager.site_template_id == "st-1"  # WHY: the template read needs this value.

    def test_a_site_without_a_name_uses_a_safe_default(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A nameless site must not print an empty banner."""
        api.api.v1.sites.sites.getSiteInfo.return_value = _response(200, {})  # WHY: an empty record.
        assert manager._fetch_site_info() is True  # WHY: an empty record is still usable.
        assert manager.site_name == "Unknown Site"  # WHY: the safe fallback.
        assert manager.site_template_id is None  # WHY: no template means no template read.

    def test_a_failed_site_info_read_aborts(self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any) -> None:
        """Continuing without site info would send a write to the wrong endpoint."""
        api.api.v1.sites.sites.getSiteInfo.return_value = _response(404)  # WHY: the site is gone.
        assert manager._fetch_site_info() is False  # WHY: the caller must stop.

    def test_an_exception_during_the_site_info_read_aborts(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A network error must return False, not crash the menu."""
        api.api.v1.sites.sites.getSiteInfo.side_effect = OSError("no route")  # WHY: a dead link.
        assert manager._fetch_site_info() is False  # WHY: the caller must stop.

    def test_the_site_wlans_are_cached_on_success(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A lost cache would hide every site-level WLAN from the picker."""
        api.api.v1.sites.wlans.listSiteWlans.return_value = _response(200, [{"id": "w1"}])
        manager._fetch_site_wlans()  # WHY: run the site WLAN read.
        assert manager.site_wlans == [{"id": "w1"}]  # WHY: the record must reach the cache.

    def test_a_failed_site_wlan_read_leaves_the_cache_empty(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """The workflow continues on a partial read, so the cache must stay empty."""
        api.api.v1.sites.wlans.listSiteWlans.return_value = _response(500)  # WHY: a server error.
        manager._fetch_site_wlans()  # WHY: run the site WLAN read.
        assert manager.site_wlans == []  # WHY: no WLAN may be invented from a failed call.

    def test_an_exception_during_the_site_wlan_read_is_contained(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A network error must not stop the template and the org reads."""
        api.api.v1.sites.wlans.listSiteWlans.side_effect = OSError("no route")  # WHY: a dead link.
        manager._fetch_site_wlans()  # WHY: the call must swallow the error.
        assert manager.site_wlans == []  # WHY: the cache stays empty.

    def test_a_template_map_is_flattened_to_a_list(self) -> None:
        """The API returns a map, but the picker needs an ordered list."""
        data = {"wlans": {"a": {"id": "w1"}, "b": {"id": "w2"}}}  # WHY: the API map shape.
        result = WLANRadiusTimerManager._extract_template_wlans(data)  # WHY: flatten the map.
        assert [w["id"] for w in result] == ["w1", "w2"]  # WHY: both records must survive.

    def test_a_template_without_wlans_returns_an_empty_list(self) -> None:
        """A template with no WLANs must not raise during the flatten pass."""
        assert WLANRadiusTimerManager._extract_template_wlans({}) == []

    def test_an_empty_wlan_map_returns_an_empty_list(self) -> None:
        """An empty map must not raise during the flatten pass."""
        assert WLANRadiusTimerManager._extract_template_wlans({"wlans": {}}) == []

    def test_a_failed_template_read_keeps_the_default_name(self, manager: WLANRadiusTimerManager) -> None:
        """A partial read must not label the WLANs with a wrong template."""
        manager._apply_site_template_response(_response(403))  # WHY: the read was rejected.
        assert manager.template_name is None  # WHY: no name may be recorded.
        assert manager.site_template_wlans == []  # WHY: no WLAN may be recorded.

    def test_a_successful_template_read_records_the_name_and_the_wlans(self, manager: WLANRadiusTimerManager) -> None:
        """The operator needs the template name to judge the blast radius of a change."""
        body = {"name": "Std", "wlans": {"a": {"id": "w1"}}}  # WHY: a normal template record.
        manager._apply_site_template_response(_response(200, body))  # WHY: apply the response.
        assert manager.template_name == "Std"  # WHY: the display name for the prompt.
        assert manager.site_template_wlans == [{"id": "w1"}]  # WHY: the WLAN must reach the cache.

    def test_a_template_with_no_wlans_still_records_the_name(self, manager: WLANRadiusTimerManager) -> None:
        """The name is useful even when the template holds no WLAN."""
        manager._apply_site_template_response(_response(200, {"name": "Std"}))  # WHY: no WLAN map.
        assert manager.template_name == "Std"  # WHY: the name must still be recorded.
        assert manager.site_template_wlans == []  # WHY: no WLAN may be invented.

    def test_a_site_without_a_template_skips_the_template_read(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A needless API call wastes the rate budget on every run."""
        manager.site_template_id = None  # WHY: this site has no template.
        manager._fetch_site_template_wlans()  # WHY: run the template read.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.assert_not_called()

    def test_an_exception_during_the_template_read_is_contained(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A network error must not stop the org read that follows."""
        manager.site_template_id = "st-1"  # WHY: a template read is required.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.side_effect = OSError("no route")
        manager._fetch_site_template_wlans()  # WHY: the call must swallow the error.
        assert manager.site_template_wlans == []  # WHY: the cache stays empty.

    def test_the_wlan_templates_are_cached_on_success(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A lost cache would hide every org WLAN from the picker."""
        api.api.v1.orgs.templates.listOrgTemplates.return_value = _response(200, [{"id": "t1"}])
        manager._fetch_wlan_templates()  # WHY: run the template list read.
        assert manager.wlan_templates == [{"id": "t1"}]  # WHY: the record must reach the cache.

    def test_a_failed_template_list_read_leaves_the_cache_empty(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """The workflow continues on a partial read, so the cache must stay empty."""
        api.api.v1.orgs.templates.listOrgTemplates.return_value = _response(500)  # WHY: an error.
        manager._fetch_wlan_templates()  # WHY: run the template list read.
        assert manager.wlan_templates == []  # WHY: no template may be invented.

    def test_an_exception_during_the_org_read_is_contained(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A network error must not crash the menu after two good reads."""
        api.api.v1.orgs.templates.listOrgTemplates.side_effect = OSError("no route")
        manager._fetch_org_wlans()  # WHY: the call must swallow the error.
        assert manager.org_wlans == []  # WHY: the cache stays empty.

    def test_the_three_reads_run_in_order(self, manager: WLANRadiusTimerManager) -> None:
        """A skipped source would hide a whole class of WLAN from the picker."""
        with (
            patch.object(manager, "_fetch_site_wlans") as site_spy,
            patch.object(manager, "_fetch_site_template_wlans") as template_spy,
            patch.object(manager, "_fetch_org_wlans") as org_spy,
        ):
            manager._fetch_all_wlans()  # WHY: run the aggregate read.
        assert site_spy.called and template_spy.called and org_spy.called


class TestRadiusFilters:
    """Cover the filters that label each WLAN with its inheritance source."""

    def test_a_site_wlan_is_labeled_with_the_site_name(self, manager: WLANRadiusTimerManager) -> None:
        """The label tells the operator which endpoint the write will reach."""
        manager.site_wlans = [{"id": "w1", "auth_servers": [{"host": "1.1.1.1"}]}]  # WHY: RADIUS.
        result = manager._filter_site_wlans()  # WHY: run the site filter.
        assert result[0]["_inheritance_level"] == "site"  # WHY: drives the site write path.
        assert result[0]["_inheritance_source"] == "Site: Lab"  # WHY: names the source.

    def test_a_non_radius_site_wlan_is_dropped(self, manager: WLANRadiusTimerManager) -> None:
        """A PSK WLAN has no RADIUS timers, so editing it would confuse the operator."""
        manager.site_wlans = [{"id": "w1", "auth": {"type": "psk"}}]  # WHY: no RADIUS signal.
        assert manager._filter_site_wlans() == []  # WHY: the record must be dropped.

    def test_a_template_wlan_carries_the_template_identifier(self, manager: WLANRadiusTimerManager) -> None:
        """The write path needs the template identifier to target the update."""
        manager.template_name = "Std"  # WHY: the label embeds the template name.
        manager.site_template_id = "st-1"  # WHY: the write path reads this value.
        manager.site_template_wlans = [{"id": "w1", "radsec": {"enabled": True}}]  # WHY: RADIUS.
        result = manager._filter_site_template_wlans()  # WHY: run the template filter.
        assert result[0]["_inheritance_level"] == "site_template"  # WHY: drives the write path.
        assert result[0]["_template_id"] == "st-1"  # WHY: the write path targets this template.
        assert result[0]["_inheritance_source"] == "Site Template: Std"  # WHY: names the source.

    def test_a_non_radius_template_wlan_is_dropped(self, manager: WLANRadiusTimerManager) -> None:
        """A PSK WLAN has no RADIUS timers, so editing it would confuse the operator."""
        manager.site_template_wlans = [{"id": "w1"}]  # WHY: no RADIUS signal at all.
        assert manager._filter_site_template_wlans() == []  # WHY: the record must be dropped.

    def test_an_org_wlan_is_labeled_with_the_template_name(self, manager: WLANRadiusTimerManager) -> None:
        """The operator needs the template name to judge the blast radius of a change."""
        manager.org_wlans = [  # WHY: a RADIUS WLAN already tagged with its template name.
            {"id": "w1", "auth": {"type": "eap"}, "_wlan_template_name": "Corp"}
        ]
        result = manager._filter_org_wlans()  # WHY: run the org filter.
        assert result[0]["_inheritance_source"] == "Org WLAN using template: Corp"

    def test_an_org_wlan_without_a_template_name_uses_a_safe_label(self, manager: WLANRadiusTimerManager) -> None:
        """A missing name must not print an empty label."""
        manager.org_wlans = [{"id": "w1", "auth": {"type": "eap"}}]  # WHY: the tag is absent.
        result = manager._filter_org_wlans()  # WHY: run the org filter.
        assert result[0]["_inheritance_source"] == "Org WLAN using template: Unknown Template"

    def test_the_three_sources_are_merged_in_order(self, manager: WLANRadiusTimerManager) -> None:
        """The picker numbers the WLANs, so a reorder would select the wrong record."""
        manager.site_wlans = [{"id": "site-w", "auth_servers": [1]}]  # WHY: one site WLAN.
        manager.site_template_wlans = [{"id": "tmpl-w", "auth_servers": [1]}]  # WHY: one template.
        manager.org_wlans = [{"id": "org-w", "auth_servers": [1]}]  # WHY: one org WLAN.
        manager._filter_radius_wlans()  # WHY: run the merge.
        assert [w["id"] for w in manager.all_radius_wlans] == ["site-w", "tmpl-w", "org-w"]


class TestWlanSelection:
    """Cover the picker boundaries, because a wrong index edits the wrong WLAN."""

    @pytest.fixture(autouse=True)
    def _three_wlans(self, manager: WLANRadiusTimerManager) -> None:
        """Give the picker three WLANs so the range checks have real edges."""
        manager.all_radius_wlans = [{"id": "w1"}, {"id": "w2"}, {"id": "w3"}]  # WHY: three rows.

    def _pick(self, manager: WLANRadiusTimerManager, answer: str) -> bool:
        """Run the picker with a fixed answer and return its result."""
        with patch.object(manager, "_read_wlan_selection_input", return_value=answer):
            return manager._prompt_wlan_selection()  # WHY: drive the branch under test.

    def test_the_quit_answer_aborts(self, manager: WLANRadiusTimerManager) -> None:
        """The operator must be able to leave without editing a WLAN."""
        assert self._pick(manager, "q") is False  # WHY: the caller must stop.
        assert manager.selected_wlan is None  # WHY: no WLAN may be selected.

    def test_the_first_index_selects_the_first_wlan(self, manager: WLANRadiusTimerManager) -> None:
        """An off-by-one error would edit the wrong WLAN."""
        assert self._pick(manager, "1") is True  # WHY: the caller continues on True.
        assert manager.selected_wlan == {"id": "w1"}  # WHY: the first row must be chosen.

    def test_the_last_index_selects_the_last_wlan(self, manager: WLANRadiusTimerManager) -> None:
        """An off-by-one error would reject a valid last choice."""
        assert self._pick(manager, "3") is True  # WHY: the caller continues on True.
        assert manager.selected_wlan == {"id": "w3"}  # WHY: the last row must be chosen.

    def test_the_index_above_the_range_is_rejected(self, manager: WLANRadiusTimerManager) -> None:
        """An accepted overflow would raise an index error inside the editor."""
        assert self._pick(manager, "4") is False  # WHY: the caller must stop.
        assert manager.selected_wlan is None  # WHY: no WLAN may be selected.

    def test_the_zero_index_is_rejected(self, manager: WLANRadiusTimerManager) -> None:
        """Zero maps to index minus one, which would select the last WLAN by mistake."""
        assert self._pick(manager, "0") is False  # WHY: the caller must stop.
        assert manager.selected_wlan is None  # WHY: no WLAN may be selected.

    def test_a_negative_index_is_rejected(self, manager: WLANRadiusTimerManager) -> None:
        """A negative index would wrap to the end of the list."""
        assert self._pick(manager, "-1") is False  # WHY: the caller must stop.
        assert manager.selected_wlan is None  # WHY: no WLAN may be selected.

    def test_a_non_numeric_answer_is_rejected(self, manager: WLANRadiusTimerManager) -> None:
        """A typing mistake must not crash the menu."""
        assert self._pick(manager, "abc") is False  # WHY: the caller must stop.
        assert manager.selected_wlan is None  # WHY: no WLAN may be selected.

    def test_an_empty_answer_is_rejected(self, manager: WLANRadiusTimerManager) -> None:
        """An empty entry must not crash the menu."""
        assert self._pick(manager, "") is False  # WHY: the caller must stop.

    def test_the_reader_normalizes_the_answer(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """An upper-case quit answer must work the same as the lower-case one."""
        fake_mh.InputUtils.safe_input.return_value = "  Q  "  # WHY: padded and upper case.
        assert manager._read_wlan_selection_input() == "q"  # WHY: trimmed and lowered.

    def test_the_selected_wlan_accessor_rejects_an_empty_selection(self, manager: WLANRadiusTimerManager) -> None:
        """A silent None would send a write with no target identifier."""
        with pytest.raises(AssertionError):  # WHY: the guard must stop the caller.
            manager._get_selected_wlan()


class TestValuePrompts:
    """Cover the timer boundaries, because a bad value changes the authentication behavior."""

    @pytest.fixture(autouse=True)
    def _selected(self, manager: WLANRadiusTimerManager) -> None:
        """Select a WLAN so every prompt has a current value to fall back on."""
        manager.selected_wlan = {  # WHY: the prompts read the current values from this record.
            "auth_servers_timeout": 7,
            "auth_servers_retries": 3,
            "auth_server_selection": "unordered",
            "fast_dot1x_timers": True,
        }

    @pytest.mark.parametrize("answer,expected", [("1", 1), ("30", 30), ("15", 15)])
    def test_a_timeout_inside_the_range_is_accepted(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str, expected: int
    ) -> None:
        """Both edges of the range are valid, so a tight check would reject a good value."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the typed value.
        manager._prompt_timeout()  # WHY: run the prompt.
        assert manager.new_timeout == expected  # WHY: the value must be stored as typed.

    @pytest.mark.parametrize("answer", ["0", "31", "-5"])
    def test_a_timeout_outside_the_range_falls_back(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str
    ) -> None:
        """An out-of-range timeout would break the authentication for every client."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the bad value.
        manager._prompt_timeout()  # WHY: run the prompt.
        assert manager.new_timeout == 7  # WHY: the current value must survive.

    def test_an_empty_timeout_answer_keeps_the_current_value(
        self, manager: WLANRadiusTimerManager, fake_mh: Any
    ) -> None:
        """The prompt promises that a blank entry keeps the current value."""
        fake_mh.InputUtils.safe_input.return_value = "  "  # WHY: whitespace only.
        manager._prompt_timeout()  # WHY: run the prompt.
        assert manager.new_timeout == 7  # WHY: the current value must survive.

    @pytest.mark.parametrize("answer,expected", [("0", 0), ("10", 10), ("5", 5)])
    def test_a_retry_count_inside_the_range_is_accepted(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str, expected: int
    ) -> None:
        """Zero retries is valid, so a truthiness check would reject a good value."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the typed value.
        manager._prompt_retries()  # WHY: run the prompt.
        assert manager.new_retries == expected  # WHY: the value must be stored as typed.

    @pytest.mark.parametrize("answer", ["-1", "11"])
    def test_a_retry_count_outside_the_range_falls_back(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str
    ) -> None:
        """Too many retries multiplies the timeout and stalls the client."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the bad value.
        manager._prompt_retries()  # WHY: run the prompt.
        assert manager.new_retries == 3  # WHY: the current value must survive.

    def test_an_empty_retry_answer_keeps_the_current_value(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """The prompt promises that a blank entry keeps the current value."""
        fake_mh.InputUtils.safe_input.return_value = ""  # WHY: an empty entry.
        manager._prompt_retries()  # WHY: run the prompt.
        assert manager.new_retries == 3  # WHY: the current value must survive.

    @pytest.mark.parametrize("answer", ["ordered", "unordered", "ORDERED"])
    def test_a_valid_selection_mode_is_accepted(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str
    ) -> None:
        """The mode is case insensitive, so an upper-case entry must work."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the typed value.
        manager._prompt_selection()  # WHY: run the prompt.
        assert manager.new_selection == answer.lower()  # WHY: stored in the normalized form.

    def test_an_invalid_selection_mode_falls_back(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """An unknown mode would be rejected by the API and waste a write."""
        fake_mh.InputUtils.safe_input.return_value = "random"  # WHY: an unsupported mode.
        manager._prompt_selection()  # WHY: run the prompt.
        assert manager.new_selection == "unordered"  # WHY: the current value must survive.

    @pytest.mark.parametrize("answer,expected", [("true", True), ("false", False)])
    def test_a_valid_fast_timer_answer_is_accepted(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str, expected: bool
    ) -> None:
        """The flag changes the 802.1X retry pace, so both answers must work."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: supply the typed value.
        manager._prompt_fast_timers()  # WHY: run the prompt.
        assert manager.new_fast is expected  # WHY: the value must be stored as typed.

    def test_an_invalid_fast_timer_answer_falls_back(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """An unknown answer must keep the current flag, not clear it."""
        fake_mh.InputUtils.safe_input.return_value = "maybe"  # WHY: an unsupported answer.
        manager._prompt_fast_timers()  # WHY: run the prompt.
        assert manager.new_fast is True  # WHY: the current value must survive.

    def test_all_four_prompts_run_in_order(self, manager: WLANRadiusTimerManager) -> None:
        """A skipped prompt would write a stale value to a live WLAN."""
        with (
            patch.object(manager, "_prompt_timeout") as timeout_spy,
            patch.object(manager, "_prompt_retries") as retries_spy,
            patch.object(manager, "_prompt_selection") as selection_spy,
            patch.object(manager, "_prompt_fast_timers") as fast_spy,
        ):
            assert manager._prompt_new_values() is True  # WHY: the caller continues on True.
        assert timeout_spy.called and retries_spy.called  # WHY: both number prompts must run.
        assert selection_spy.called and fast_spy.called  # WHY: both mode prompts must run.

    def test_a_bad_value_aborts_the_prompt_sequence(self, manager: WLANRadiusTimerManager) -> None:
        """A raised error must return False, not crash the menu."""
        with patch.object(manager, "_prompt_timeout", side_effect=ValueError("bad")):
            assert manager._prompt_new_values() is False  # WHY: the caller must stop.


class TestConfirmAndPayload:
    """Cover the confirmation guard and the payload, which reach a live WLAN."""

    def test_the_exact_keyword_confirms(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """A lost guard would write to a live WLAN with no operator consent."""
        fake_mh.InputUtils.safe_input.return_value = "APPLY"  # WHY: the exact keyword.
        assert manager._confirm_changes() is True  # WHY: the write may proceed.

    def test_surrounding_whitespace_is_trimmed(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """A trailing space must not reject a correct confirmation."""
        fake_mh.InputUtils.safe_input.return_value = "  APPLY  "  # WHY: padded entry.
        assert manager._confirm_changes() is True  # WHY: the write may proceed.

    @pytest.mark.parametrize("answer", ["apply", "yes", "y", "", "APPLYY"])
    def test_any_other_answer_cancels(self, manager: WLANRadiusTimerManager, fake_mh: Any, answer: str) -> None:
        """A loose check would let a stray keypress change a live WLAN."""
        fake_mh.InputUtils.safe_input.return_value = answer  # WHY: a wrong keyword.
        assert manager._confirm_changes() is False  # WHY: the write must not proceed.

    def test_the_payload_carries_only_the_four_timer_fields(self, manager: WLANRadiusTimerManager) -> None:
        """An extra field would overwrite unrelated WLAN settings."""
        manager.new_timeout = 9  # WHY: a distinct value proves the field is threaded.
        manager.new_retries = 4  # WHY: a distinct value proves the field is threaded.
        manager.new_selection = "unordered"  # WHY: a distinct value proves the field is threaded.
        manager.new_fast = True  # WHY: a distinct value proves the field is threaded.
        assert manager._build_update_payload() == {  # WHY: the exact body the API receives.
            "auth_servers_timeout": 9,
            "auth_servers_retries": 4,
            "auth_server_selection": "unordered",
            "fast_dot1x_timers": True,
        }


class TestApplyChangesDispatch:
    """Cover the endpoint choice, because a wrong endpoint edits the wrong scope."""

    @pytest.mark.parametrize(
        "level,method",
        [
            ("site", "_update_site_wlan"),
            ("site_template", "_update_site_template_wlan"),
            ("org_wlan_with_template", "_update_org_wlan"),
        ],
    )
    def test_each_inheritance_level_reaches_its_own_endpoint(
        self, manager: WLANRadiusTimerManager, level: str, method: str
    ) -> None:
        """A wrong endpoint would change a WLAN at the wrong scope."""
        manager.selected_wlan = {"id": "w1", "_inheritance_level": level}  # WHY: set the scope.
        with patch.object(manager, method) as write_spy:  # WHY: watch the expected writer.
            manager._apply_changes()  # WHY: run the dispatch.
        assert write_spy.called  # WHY: the matching writer must run.

    def test_an_unknown_level_writes_nothing(self, manager: WLANRadiusTimerManager) -> None:
        """A silent fall-through would look like a successful change."""
        manager.selected_wlan = {"id": "w1", "_inheritance_level": "mystery"}  # WHY: bad scope.
        with (
            patch.object(manager, "_update_site_wlan") as site_spy,
            patch.object(manager, "_update_site_template_wlan") as template_spy,
            patch.object(manager, "_update_org_wlan") as org_spy,
        ):
            manager._apply_changes()  # WHY: run the dispatch.
        assert not (site_spy.called or template_spy.called or org_spy.called)

    def test_an_api_failure_is_contained(self, manager: WLANRadiusTimerManager) -> None:
        """A raised error must not crash the menu after the confirmation."""
        manager.selected_wlan = {"id": "w1", "_inheritance_level": "site"}  # WHY: set the scope.
        with patch.object(manager, "_update_site_wlan", side_effect=OSError("no route")):
            manager._apply_changes()  # WHY: the call must swallow the error.


class TestSiteWlanUpdate:
    """Cover the site WLAN write, which is the most direct of the three endpoints."""

    def test_a_successful_write_sends_the_payload(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A dropped field would leave the WLAN on a stale timer."""
        manager.selected_wlan = {"id": "w1", "ssid": "Corp"}  # WHY: the write targets this WLAN.
        manager.new_timeout = 9  # WHY: a distinct value proves the payload is threaded.
        api.api.v1.sites.wlans.updateSiteWlan.return_value = _response(200)  # WHY: a good write.
        manager._update_site_wlan()  # WHY: run the write.
        args = api.api.v1.sites.wlans.updateSiteWlan.call_args.args  # WHY: read the call.
        assert args[1] == "site-1" and args[2] == "w1"  # WHY: the write must target this WLAN.
        assert args[3]["auth_servers_timeout"] == 9  # WHY: the new value must be sent.

    def test_a_failed_write_is_reported(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any, capsys: Any
    ) -> None:
        """A silent failure would let the operator believe the change landed."""
        manager.selected_wlan = {"id": "w1", "ssid": "Corp"}  # WHY: the write targets this WLAN.
        api.api.v1.sites.wlans.updateSiteWlan.return_value = _response(400)  # WHY: a rejection.
        manager._update_site_wlan()  # WHY: run the write.
        assert "Failed to update WLAN: HTTP 400" in capsys.readouterr().out


class TestSiteTemplateWlanUpdate:
    """Cover the template write, which changes every site that uses the template."""

    def test_a_missing_template_identifier_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A write with no template target would raise inside the API layer."""
        manager.selected_wlan = {"id": "w1"}  # WHY: the template tag is absent.
        manager._update_site_template_wlan()  # WHY: run the write.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.assert_not_called()

    def test_a_missing_wlan_identifier_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A write with no WLAN target would change the wrong record."""
        manager.selected_wlan = {"_template_id": "st-1"}  # WHY: the WLAN identifier is absent.
        manager._update_site_template_wlan()  # WHY: run the write.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.assert_not_called()

    def test_a_failed_template_read_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """Writing without the current document would erase the other WLANs."""
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(404)
        assert manager._fetch_site_template_for_update("st-1") is None  # WHY: the caller stops.
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.assert_not_called()

    def test_a_template_without_a_wlan_map_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """Writing to a template with no WLAN map would raise a key error."""
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, {})
        assert manager._fetch_site_template_for_update("st-1") is None  # WHY: the caller stops.

    def test_a_wlan_map_of_the_wrong_type_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A list where a map belongs would raise during the scan."""
        body = {"wlans": ["not-a-map"]}  # WHY: the API returned an unexpected shape.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, body)
        assert manager._fetch_site_template_for_update("st-1") is None  # WHY: the caller stops.

    def test_a_valid_template_document_is_returned(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """The caller mutates this document in place, so it must be the live one."""
        body = {"wlans": {"a": {"id": "w1"}}}  # WHY: a normal template document.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, body)
        assert manager._fetch_site_template_for_update("st-1") is body  # WHY: the same object.

    def test_the_matching_wlan_is_updated_in_place(self, manager: WLANRadiusTimerManager) -> None:
        """A copy would be discarded, so the write would send the old values."""
        manager.new_timeout = 9  # WHY: a distinct value proves the payload is applied.
        document = {"wlans": {"a": {"id": "w1"}, "b": {"id": "w2"}}}  # WHY: two WLANs.
        assert manager._apply_wlan_update_to_template(document, "w2") is True
        assert document["wlans"]["b"]["auth_servers_timeout"] == 9  # WHY: only w2 changes.
        assert "auth_servers_timeout" not in document["wlans"]["a"]  # WHY: w1 must be untouched.

    def test_a_missing_wlan_reports_no_match(self, manager: WLANRadiusTimerManager) -> None:
        """A false match would send an unchanged document and look successful."""
        document = {"wlans": {"a": {"id": "w1"}}}  # WHY: the target WLAN is absent.
        assert manager._apply_wlan_update_to_template(document, "w-gone") is False

    def test_a_successful_template_write_sends_the_whole_document(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """Sending a partial document would erase the other WLANs in the template."""
        document = {"wlans": {"a": {"id": "w1"}}}  # WHY: the mutated document.
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.return_value = _response(200)
        manager._write_site_template_update("st-1", document, {"id": "w1", "ssid": "Corp"})
        args = api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.call_args.args
        assert args[3] is document  # WHY: the full document must be sent.

    def test_a_failed_template_write_is_reported(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any, capsys: Any
    ) -> None:
        """A silent failure would let the operator believe the change landed."""
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.return_value = _response(409)
        manager._write_site_template_update("st-1", {"wlans": {}}, {"id": "w1"})
        assert "Failed to update site template: HTTP 409" in capsys.readouterr().out

    def test_a_wlan_missing_from_the_template_skips_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """Writing an unchanged document would waste a call and look successful."""
        manager.selected_wlan = {"id": "w-gone", "_template_id": "st-1"}  # WHY: absent WLAN.
        body = {"wlans": {"a": {"id": "w1"}}}  # WHY: the template holds a different WLAN.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, body)
        manager._update_site_template_wlan()  # WHY: run the write.
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.assert_not_called()

    def test_a_failed_template_read_inside_the_update_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """Writing without the current document would erase the other WLANs."""
        manager.selected_wlan = {"id": "w1", "_template_id": "st-1"}  # WHY: a valid target.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(500)
        manager._update_site_template_wlan()  # WHY: run the write.
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.assert_not_called()

    def test_a_complete_template_update_reaches_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A broken chain would leave the template on a stale timer."""
        manager.selected_wlan = {"id": "w1", "_template_id": "st-1"}  # WHY: a valid target.
        body = {"wlans": {"a": {"id": "w1"}}}  # WHY: the template holds the target WLAN.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, body)
        api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.return_value = _response(200)
        manager._update_site_template_wlan()  # WHY: run the write.
        assert api.api.v1.orgs.sitetemplates.updateOrgSiteTemplate.called


class TestOrgWlanUpdate:
    """Cover the org WLAN write, which changes every site that uses the template."""

    def test_a_missing_wlan_identifier_stops_the_write(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A write with no target would change the wrong record."""
        manager.selected_wlan = {"ssid": "Corp"}  # WHY: the identifier is absent.
        manager._update_org_wlan()  # WHY: run the write.
        api.api.v1.orgs.wlans.updateOrgWlan.assert_not_called()

    def test_a_valid_write_sends_the_payload(self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any) -> None:
        """A dropped field would leave the WLAN on a stale timer."""
        manager.selected_wlan = {"id": "w1", "ssid": "Corp"}  # WHY: the write targets this WLAN.
        manager.new_retries = 4  # WHY: a distinct value proves the payload is threaded.
        api.api.v1.orgs.wlans.updateOrgWlan.return_value = _response(200)  # WHY: a good write.
        manager._update_org_wlan()  # WHY: run the write.
        args = api.api.v1.orgs.wlans.updateOrgWlan.call_args.args  # WHY: read the call.
        assert args[1] == "org-1" and args[2] == "w1"  # WHY: the write must target this WLAN.
        assert args[3]["auth_servers_retries"] == 4  # WHY: the new value must be sent.

    def test_a_successful_result_names_the_base_template(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The operator needs the template name to judge the blast radius of a change."""
        wlan = {"ssid": "Corp", "_wlan_template_name": "Std"}  # WHY: the tagged record.
        manager._report_org_wlan_update_result(_response(200), wlan, "w1")  # WHY: report it.
        assert "Std" in capsys.readouterr().out  # WHY: the name must reach the operator.

    def test_a_successful_result_without_a_template_name_uses_a_safe_label(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """A missing name must not print an empty label."""
        manager._report_org_wlan_update_result(_response(200), {"ssid": "Corp"}, "w1")
        assert "Unknown" in capsys.readouterr().out  # WHY: the safe fallback.

    def test_a_failed_result_is_reported(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A silent failure would let the operator believe the change landed."""
        manager._report_org_wlan_update_result(_response(403), {"ssid": "Corp"}, "w1")
        assert "Failed to update org WLAN: HTTP 403" in capsys.readouterr().out


class TestDiscoveryGuards:
    """Cover the four abort points, because each one protects a later step."""

    def test_no_site_choice_aborts(self, manager: WLANRadiusTimerManager) -> None:
        """Continuing without a site would send a write with no target."""
        with patch.object(manager, "_select_site", return_value=False):
            assert manager._discover_radius_wlans() is False  # WHY: the caller must stop.

    def test_no_org_identifier_aborts(self, manager: WLANRadiusTimerManager) -> None:
        """The template reads need the org, so continuing would raise."""
        with (
            patch.object(manager, "_select_site", return_value=True),
            patch.object(manager, "_get_org_id", return_value=False),
        ):
            assert manager._discover_radius_wlans() is False  # WHY: the caller must stop.

    def test_a_failed_site_info_read_aborts(self, manager: WLANRadiusTimerManager) -> None:
        """The template resolution needs the site record, so continuing would raise."""
        with (
            patch.object(manager, "_select_site", return_value=True),
            patch.object(manager, "_get_org_id", return_value=True),
            patch.object(manager, "_fetch_site_info", return_value=False),
        ):
            assert manager._discover_radius_wlans() is False  # WHY: the caller must stop.

    def test_no_radius_wlan_aborts(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """An empty picker would ask the operator to choose from nothing."""
        with (
            patch.object(manager, "_select_site", return_value=True),
            patch.object(manager, "_get_org_id", return_value=True),
            patch.object(manager, "_fetch_site_info", return_value=True),
            patch.object(manager, "_fetch_all_wlans"),
            patch.object(manager, "_filter_radius_wlans"),
        ):
            assert manager._discover_radius_wlans() is False  # WHY: the caller must stop.
        assert "No WLANs using RADIUS" in capsys.readouterr().out  # WHY: tell the operator why.

    def test_a_found_radius_wlan_continues(self, manager: WLANRadiusTimerManager) -> None:
        """A wrong abort would hide every editable WLAN from the operator."""
        manager.all_radius_wlans = [{"id": "w1"}]  # WHY: one candidate is enough.
        with (
            patch.object(manager, "_select_site", return_value=True),
            patch.object(manager, "_get_org_id", return_value=True),
            patch.object(manager, "_fetch_site_info", return_value=True),
            patch.object(manager, "_fetch_all_wlans"),
            patch.object(manager, "_filter_radius_wlans"),
        ):
            assert manager._discover_radius_wlans() is True  # WHY: the caller continues.


class TestManageWorkflow:
    """Cover the top-level order, because a skipped guard would write without consent."""

    def _patched(self, manager: WLANRadiusTimerManager, **overrides: Any) -> Any:
        """Patch every step of the workflow and return the mock map."""
        names = [  # WHY: the full ordered step list of the manage workflow.
            "_enable_debug_if_requested",
            "_discover_radius_wlans",
            "_display_wlans",
            "_prompt_wlan_selection",
            "_display_current_config",
            "_prompt_new_values",
            "_display_behavior_impact",
            "_display_proposed_changes",
            "_confirm_changes",
            "_apply_changes",
            "_print_completion_message",
        ]
        defaults = {name: True for name in names}  # WHY: every guard passes unless overridden.
        defaults.update(overrides)  # WHY: the caller flips the guard under test.
        patchers = {  # WHY: hold the started patchers so the test can read the spies.
            name: patch.object(manager, name, return_value=defaults[name]) for name in names
        }
        return patchers  # WHY: the caller enters each patcher itself.

    def _run(self, manager: WLANRadiusTimerManager, **overrides: Any) -> dict[str, Any]:
        """Run manage with every step mocked and return the started spies."""
        patchers = self._patched(manager, **overrides)  # WHY: build the patcher map.
        spies = {name: patcher.start() for name, patcher in patchers.items()}  # WHY: activate.
        try:
            manager.manage()  # WHY: drive the workflow under test.
        finally:
            for patcher in patchers.values():  # WHY: always restore the real methods.
                patcher.stop()
        return spies  # WHY: the test asserts on the call record.

    def test_a_failed_discovery_stops_before_the_picker(self, manager: WLANRadiusTimerManager) -> None:
        """Showing an empty picker would confuse the operator."""
        spies = self._run(manager, _discover_radius_wlans=False)  # WHY: fail the first guard.
        assert not spies["_display_wlans"].called  # WHY: the picker must not run.

    def test_a_cancelled_pick_stops_before_the_editor(self, manager: WLANRadiusTimerManager) -> None:
        """Editing with no selection would raise inside the prompts."""
        spies = self._run(manager, _prompt_wlan_selection=False)  # WHY: cancel the pick.
        assert not spies["_prompt_new_values"].called  # WHY: the editor must not run.

    def test_a_bad_value_stops_before_the_confirmation(self, manager: WLANRadiusTimerManager) -> None:
        """Confirming an unparsed value would write a stale timer."""
        spies = self._run(manager, _prompt_new_values=False)  # WHY: fail the value prompts.
        assert not spies["_confirm_changes"].called  # WHY: the confirmation must not run.

    def test_a_declined_confirmation_stops_before_the_write(self, manager: WLANRadiusTimerManager) -> None:
        """A write without consent would change a live WLAN by mistake."""
        spies = self._run(manager, _confirm_changes=False)  # WHY: decline the confirmation.
        assert not spies["_apply_changes"].called  # WHY: the write must not run.

    def test_a_full_pass_reaches_the_write_and_the_completion(self, manager: WLANRadiusTimerManager) -> None:
        """A broken chain would leave the WLAN on a stale timer."""
        spies = self._run(manager)  # WHY: every guard passes.
        assert spies["_apply_changes"].called  # WHY: the write must run.
        assert spies["_print_completion_message"].called  # WHY: tell the operator it finished.


class TestSummaryFields:
    """Cover the summary row, because a wrong default hides the real WLAN state."""

    def test_a_complete_wlan_keeps_every_value(self, manager: WLANRadiusTimerManager) -> None:
        """A dropped field would show a default in place of the live setting."""
        wlan = {  # WHY: a fully populated record with values that differ from the defaults.
            "ssid": "Corp",
            "id": "w1",
            "enabled": True,
            "_inheritance_level": "site",
            "_inheritance_source": "Site: Lab",
            "auth_servers_timeout": 9,
            "auth_servers_retries": 4,
            "auth_server_selection": "unordered",
            "fast_dot1x_timers": True,
            "auth_servers": [{"host": "1.1.1.1"}, {"host": "2.2.2.2"}],
            "radsec": {"enabled": True},
        }
        fields = manager._extract_wlan_summary_fields(wlan)  # WHY: build the summary row.
        assert fields["ssid"] == "Corp" and fields["wlan_id"] == "w1"  # WHY: identity fields.
        assert fields["timeout"] == 9 and fields["retries"] == 4  # WHY: the live timer values.
        assert fields["selection"] == "unordered" and fields["fast_timers"] is True
        assert fields["server_count"] == 2  # WHY: the operator counts the failover targets.
        assert fields["radsec_enabled"] is True  # WHY: RadSec changes the transport.

    def test_an_empty_wlan_uses_the_documented_defaults(self, manager: WLANRadiusTimerManager) -> None:
        """A wrong default would tell the operator the WLAN has a setting it lacks."""
        fields = manager._extract_wlan_summary_fields({})  # WHY: a bare record.
        assert fields["ssid"] == "Unknown SSID" and fields["wlan_id"] == "Unknown ID"
        assert fields["enabled"] is False and fields["inheritance"] == "unknown"
        assert fields["timeout"] == 5 and fields["retries"] == 2  # WHY: the Mist defaults.
        assert fields["selection"] == "ordered" and fields["fast_timers"] is False
        assert fields["server_count"] == 0 and fields["radsec_enabled"] is False

    def test_a_null_auth_server_list_counts_as_zero(self, manager: WLANRadiusTimerManager) -> None:
        """A null list must not raise during the length count."""
        assert manager._extract_wlan_summary_fields({"auth_servers": None})["server_count"] == 0

    def test_a_non_dict_radsec_block_reports_disabled(self, manager: WLANRadiusTimerManager) -> None:
        """A malformed record must not raise during the display pass."""
        assert manager._extract_wlan_summary_fields({"radsec": "broken"})["radsec_enabled"] is False

    def test_a_summary_row_names_the_ssid_and_the_index(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The operator picks by index, so both values must appear together."""
        manager._display_single_wlan(2, {"ssid": "Corp", "id": "w1"})  # WHY: render one row.
        out = capsys.readouterr().out  # WHY: read the printed row.
        assert "[2] SSID: Corp" in out and "ID: w1" in out  # WHY: index and identity.

    def test_a_disabled_wlan_is_labeled_disabled(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """Editing a disabled WLAN has no effect, so the operator must see the state."""
        manager._display_single_wlan(1, {"enabled": False})  # WHY: render one row.
        assert "Status: Disabled" in capsys.readouterr().out  # WHY: the state must be visible.

    def test_an_enabled_wlan_is_labeled_enabled(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A wrong label would hide that the change reaches live clients."""
        manager._display_single_wlan(1, {"enabled": True})  # WHY: render one row.
        assert "Status: Enabled" in capsys.readouterr().out  # WHY: the state must be visible.

    def test_the_list_numbers_every_wlan_from_one(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The picker reads a 1-based index, so the list must start at one."""
        manager.all_radius_wlans = [{"ssid": "A"}, {"ssid": "B"}]  # WHY: two rows.
        manager._display_wlans()  # WHY: render the full list.
        out = capsys.readouterr().out  # WHY: read the printed list.
        assert "[1] SSID: A" in out and "[2] SSID: B" in out  # WHY: both rows must be numbered.

    def test_the_current_config_shows_the_live_values(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The operator compares the old values against the new ones before consenting."""
        manager.selected_wlan = {  # WHY: values that differ from the defaults.
            "ssid": "Corp",
            "_inheritance_level": "site",
            "auth_servers_timeout": 9,
            "auth_servers_retries": 4,
        }
        manager._display_current_config()  # WHY: render the current configuration.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "auth_servers_timeout: 9 seconds" in out  # WHY: the live timeout.
        assert "auth_servers_retries: 4" in out  # WHY: the live retry count.


class TestBehaviorImpact:
    """Cover the impact math, because the operator consents based on these numbers."""

    @pytest.fixture(autouse=True)
    def _new_values(self, manager: WLANRadiusTimerManager) -> None:
        """Set a distinct timer pair so the arithmetic is visible in the output."""
        manager.new_timeout = 5  # WHY: five seconds for each attempt.
        manager.new_retries = 3  # WHY: three attempts against each server.

    def test_the_per_server_worst_case_is_the_product(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A wrong product would understate the outage the operator is about to cause."""
        manager.selected_wlan = {"auth_servers": [{"host": "1.1.1.1"}]}  # WHY: one server.
        manager._display_behavior_impact()  # WHY: render the impact block.
        assert "Maximum time per server: 15 seconds" in capsys.readouterr().out

    def test_a_single_server_reports_the_single_server_block(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """A failover block would promise a redundancy this WLAN does not have."""
        manager.selected_wlan = {"auth_servers": [{"host": "1.1.1.1"}]}  # WHY: one server.
        manager._display_behavior_impact()  # WHY: render the impact block.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "Single Server Behavior:" in out  # WHY: the correct block for one server.
        assert "Maximum authentication failure time: 15 seconds" in out

    def test_a_wlan_without_servers_assumes_one_server(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A zero count would multiply the worst case to zero and hide the risk."""
        manager.selected_wlan = {}  # WHY: no auth server list at all.
        manager._display_behavior_impact()  # WHY: render the impact block.
        assert "Configured servers: 1" in capsys.readouterr().out  # WHY: the safe assumption.

    def test_the_ordered_mode_reports_a_failover_sequence(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The ordered mode always retries the primary first, which changes the total."""
        manager.new_selection = "ordered"  # WHY: the sequential mode.
        manager.selected_wlan = {"auth_servers": [{"host": "1"}, {"host": "2"}]}  # WHY: two.
        manager._display_behavior_impact()  # WHY: render the impact block.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "Failover Behavior (ordered mode):" in out  # WHY: the correct block.
        assert "Maximum time if all servers fail: 30 seconds" in out  # WHY: 5 x 3 x 2.

    def test_the_unordered_mode_reports_load_balancing(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The unordered mode has no primary, so a failover promise would be wrong."""
        manager.new_selection = "unordered"  # WHY: the load-balanced mode.
        manager.selected_wlan = {"auth_servers": [{"host": "1"}, {"host": "2"}]}  # WHY: two.
        manager._display_behavior_impact()  # WHY: render the impact block.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "Load Balancing Behavior (unordered mode):" in out  # WHY: the correct block.
        assert "No server preference" in out  # WHY: no primary exists in this mode.

    def test_the_enabled_fast_timers_report_the_derived_periods(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """The derived periods are half the timeout, so a wrong divisor misleads the operator."""
        manager.new_fast = True  # WHY: enable the fast 802.1X timers.
        manager.selected_wlan = {}  # WHY: no other setting matters for this block.
        manager._display_behavior_impact()  # WHY: render the impact block.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "Fast 802.1X Timers (ENABLED):" in out  # WHY: the correct block.
        assert "quiet-period: 2.5 seconds" in out  # WHY: five divided by two.

    def test_the_disabled_fast_timers_report_the_standard_defaults(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """The standard defaults are much slower, so the operator must see them."""
        manager.new_fast = False  # WHY: keep the standard 802.1X timers.
        manager.selected_wlan = {}  # WHY: no other setting matters for this block.
        manager._display_behavior_impact()  # WHY: render the impact block.
        out = capsys.readouterr().out  # WHY: read the printed block.
        assert "Standard 802.1X Timers (DISABLED):" in out  # WHY: the correct block.
        assert "quiet-period: ~60 seconds" in out  # WHY: the standard default.

    def test_the_client_experience_names_the_all_server_total_only_when_it_applies(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """A single-server WLAN has no all-server total, so printing one would confuse."""
        manager.selected_wlan = {"auth_servers": [{"host": "1"}]}  # WHY: one server.
        manager._display_behavior_impact()  # WHY: render the impact block.
        assert "All servers fail" not in capsys.readouterr().out  # WHY: the line must be absent.

    def test_the_client_experience_reports_the_all_server_total_for_many_servers(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """The all-server total is the true worst case the clients will feel."""
        manager.selected_wlan = {"auth_servers": [{"host": "1"}, {"host": "2"}]}  # WHY: two.
        manager._display_behavior_impact()  # WHY: render the impact block.
        assert "All servers fail: ~30 seconds" in capsys.readouterr().out  # WHY: 5 x 3 x 2.


class TestProposedChangesAndWarnings:
    """Cover the blast-radius warnings, which are the last guard before a write."""

    def test_each_field_shows_the_old_and_the_new_value(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """The operator consents to a change, so both values must appear."""
        manager.selected_wlan = {"auth_servers_timeout": 5, "auth_servers_retries": 2}
        manager.new_timeout = 9  # WHY: a distinct new value.
        manager.new_retries = 4  # WHY: a distinct new value.
        manager._display_proposed_changes()  # WHY: render the change summary.
        out = capsys.readouterr().out  # WHY: read the printed summary.
        assert "auth_servers_timeout: 5 -> 9" in out  # WHY: the old and the new timeout.
        assert "auth_servers_retries: 2 -> 4" in out  # WHY: the old and the new retry count.

    def test_a_missing_field_shows_the_documented_default_as_the_old_value(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:
        """A blank old value would hide what the WLAN uses today."""
        manager.selected_wlan = {}  # WHY: the record carries no timer keys.
        manager.new_timeout = 9  # WHY: a distinct new value.
        manager._display_proposed_changes()  # WHY: render the change summary.
        assert "auth_servers_timeout: 5 -> 9" in capsys.readouterr().out  # WHY: the Mist default.

    def test_a_site_wlan_prints_no_blast_radius_warning(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A needless warning trains the operator to ignore the real one."""
        manager.selected_wlan = {"_inheritance_level": "site"}  # WHY: a site-only WLAN.
        manager._print_inheritance_warning()  # WHY: render the warning block.
        assert "WARNING" not in capsys.readouterr().out  # WHY: no warning applies here.

    def test_a_site_template_wlan_warns_about_every_site(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """Without the warning the operator changes every site that uses the template."""
        manager.selected_wlan = {  # WHY: a WLAN inherited from a shared site template.
            "_inheritance_level": "site_template",
            "_inheritance_source": "Site Template: Std",
        }
        manager._print_inheritance_warning()  # WHY: render the warning block.
        out = capsys.readouterr().out  # WHY: read the printed warning.
        assert "WARNING" in out and "Site Template: Std" in out  # WHY: name the template.
        assert "ALL sites using this template" in out  # WHY: state the blast radius.

    def test_an_org_wlan_warns_and_names_the_template(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """Without the warning the operator changes every site that uses the template."""
        manager.selected_wlan = {  # WHY: a WLAN inherited from an org WLAN template.
            "_inheritance_level": "org_wlan_with_template",
            "_inheritance_source": "Org WLAN using template: Corp",
            "_wlan_template_name": "Corp",
        }
        manager._print_inheritance_warning()  # WHY: render the warning block.
        out = capsys.readouterr().out  # WHY: read the printed warning.
        assert "WARNING" in out and "Corp" in out  # WHY: name the template.
        assert "assigned sites" in out  # WHY: the default assignment label.

    def test_an_org_wlan_names_a_known_assignment(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A named assignment tells the operator exactly which sites change."""
        manager.selected_wlan = {  # WHY: a WLAN with a recorded assignment list.
            "_inheritance_level": "org_wlan_with_template",
            "_org_template_assignment": "Lab, Branch",
            "_wlan_template_name": "Corp",
        }
        manager._print_inheritance_warning()  # WHY: render the warning block.
        assert "Lab, Branch" in capsys.readouterr().out  # WHY: name the affected sites.

    def test_an_unknown_level_prints_no_warning(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """An unrecognized level reaches no write, so no warning applies."""
        manager.selected_wlan = {"_inheritance_level": "mystery"}  # WHY: an unknown level.
        manager._print_inheritance_warning()  # WHY: render the warning block.
        assert "WARNING" not in capsys.readouterr().out  # WHY: no warning applies here.

    def test_the_completion_message_reports_success(self, manager: WLANRadiusTimerManager, capsys: Any) -> None:
        """A silent finish would leave the operator unsure whether the write landed."""
        manager._print_completion_message()  # WHY: render the closing message.
        assert "completed successfully" in capsys.readouterr().out  # WHY: confirm the finish.


class TestContextSetup:
    """Cover the debug toggle and the two identifier lookups that open the workflow."""

    def test_the_debug_toggle_stays_off_by_default(self, manager: WLANRadiusTimerManager) -> None:
        """Raising the level without consent would flood the log on every run."""
        before = logging.getLogger().level  # WHY: record the level to compare against.
        manager._enable_debug_if_requested()  # WHY: run the toggle with debug off.
        assert logging.getLogger().level == before  # WHY: the level must not change.
        assert manager.original_log_level is None  # WHY: no level was saved to restore.

    def test_the_debug_toggle_saves_the_level_before_raising_it(self) -> None:
        """Without the saved level the caller cannot restore the operator's setting."""
        instance = WLANRadiusTimerManager(debug=True)  # WHY: request the verbose mode.
        root = logging.getLogger()  # WHY: the toggle changes the root logger.
        before = root.level  # WHY: record the level to restore after the test.
        try:
            instance._enable_debug_if_requested()  # WHY: run the toggle with debug on.
            assert instance.original_log_level == before  # WHY: the old level must be saved.
            assert root.level == logging.DEBUG  # WHY: the new level must be verbose.
        finally:
            root.setLevel(before)  # WHY: never leak a level change into the other tests.

    def test_a_chosen_site_is_recorded(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """A lost identifier would send every later write to the wrong site."""
        fake_mh.PromptUtils.select_site_with_logging.return_value = "site-9"  # WHY: a choice.
        assert manager._select_site() is True  # WHY: the caller continues on True.
        assert manager.site_id == "site-9"  # WHY: the choice must be recorded.

    def test_an_empty_site_choice_aborts(self, manager: WLANRadiusTimerManager, fake_mh: Any, capsys: Any) -> None:
        """Continuing without a site would send a write with no target."""
        fake_mh.PromptUtils.select_site_with_logging.return_value = ""  # WHY: no choice made.
        assert manager._select_site() is False  # WHY: the caller must stop.
        assert "No site selected" in capsys.readouterr().out  # WHY: tell the operator why.

    def test_a_resolved_org_is_recorded(self, manager: WLANRadiusTimerManager, fake_mh: Any) -> None:
        """A lost identifier would send the template reads to the wrong org."""
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-9"  # WHY: cached.
        assert manager._get_org_id() is True  # WHY: the caller continues on True.
        assert manager.org_id == "org-9"  # WHY: the value must be recorded.

    def test_an_unresolved_org_aborts(self, manager: WLANRadiusTimerManager, fake_mh: Any, capsys: Any) -> None:
        """The template reads need the org, so continuing would raise."""
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = None  # WHY: no org.
        assert manager._get_org_id() is False  # WHY: the caller must stop.
        assert "Unable to determine organization ID" in capsys.readouterr().out

    def test_a_template_read_reaches_the_response_handler(
        self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any
    ) -> None:
        """A lost handler call would drop every template WLAN from the picker."""
        manager.site_template_id = "st-1"  # WHY: a template read is required.
        body = {"name": "Std", "wlans": {"a": {"id": "w1"}}}  # WHY: a normal template record.
        api.api.v1.orgs.sitetemplates.getOrgSiteTemplate.return_value = _response(200, body)
        manager._fetch_site_template_wlans()  # WHY: run the template read.
        assert manager.site_template_wlans == [{"id": "w1"}]  # WHY: the WLAN must be cached.

    def test_the_org_read_runs_all_three_steps(self, manager: WLANRadiusTimerManager, fake_mh: Any, api: Any) -> None:
        """A skipped step would hide every org WLAN from the picker."""
        with (
            patch.object(manager, "_fetch_wlan_templates") as templates_spy,
            patch.object(manager, "_determine_assigned_templates") as assigned_spy,
            patch.object(manager, "_fetch_and_filter_org_wlans") as filter_spy,
        ):
            manager._fetch_org_wlans()  # WHY: run the aggregate org read.
        assert templates_spy.called and assigned_spy.called and filter_spy.called
