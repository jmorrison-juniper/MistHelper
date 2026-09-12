"""Unit tests for extracted global assignments builder service."""

import collections
import datetime
from concurrent import futures
from types import SimpleNamespace

from src.refactors.serial_cc.global_assignments_builder import GlobalAssignmentsBuilderService


def test_builder_populates_common_aliases_and_symbols():
    imports = {
        "datetime": datetime,
        "concurrent.futures": futures,
        "collections": collections,
    }

    def add_fallbacks(global_vars):
        global_vars.setdefault("fuzz", "fallback-fuzz")

    result = GlobalAssignmentsBuilderService.execute(imports, add_fallbacks)

    assert result["datetime"] is datetime
    assert result["timezone"] is datetime.timezone
    assert result["timedelta"] is datetime.timedelta
    assert result["ThreadPoolExecutor"] is futures.ThreadPoolExecutor
    assert result["as_completed"] is futures.as_completed
    assert result["concurrent"] is futures
    assert result["defaultdict"] is collections.defaultdict
    assert result["fuzz"] == "fallback-fuzz"


def test_builder_preserves_sdk_aliases():
    fake_mistapi = SimpleNamespace(api="api-v1")
    fake_paramiko = SimpleNamespace(SSHClient=object)
    fake_redexpect = SimpleNamespace(spawn=lambda *_args, **_kwargs: None)
    imports = {
        "mistapi": fake_mistapi,
        "paramiko": fake_paramiko,
        "redexpect": fake_redexpect,
    }

    result = GlobalAssignmentsBuilderService.execute(imports, lambda _global_vars: None)

    assert result["mistapi"] is fake_mistapi
    assert result["paramiko"] is fake_paramiko
    assert result["redexpect"] is fake_redexpect
