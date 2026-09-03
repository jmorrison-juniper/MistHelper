"""Serves Mist Cloud health to a monitoring system.

Why:
    A monitoring system polls a target and compares one number against one
    threshold. Mist Cloud publishes its health through a REST API that needs a
    token, a page loop, and a rate limit budget, so a monitoring system cannot
    read it. This package reads Mist Cloud on a timer, holds the last reading,
    and serves that reading two ways.

    `PrometheusRenderer` answers an HTTP scrape at `/metrics`. This is the
    primary path, because it needs no MIB, no registered enterprise number, and
    no privileged port.

    `SnmpPassPersistResponder` answers a Net-SNMP `pass_persist` request on
    standard input. This path keeps the SNMP workflow of a NOC that has one.
    `snmpd` owns port 161 and the community string, so MistHelper holds neither.

    The design carries the object set of `tmunzer/mist_snmp_gateway`, which is
    MIT licensed and which the author calls a proof of concept. The store, the
    transport, and the OID layout are new. See issue #2243 for the assessment.
"""

from src.metrics_gateway.cache import MetricsCache
from src.metrics_gateway.catalog import MetricCatalog, MetricDefinition, MetricKind, MetricScope
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader
from src.metrics_gateway.prometheus import PrometheusRenderer
from src.metrics_gateway.samples import MetricSample, MetricSnapshot
from src.metrics_gateway.service import GatewaySettings, build_cache, start_refresh_thread
from src.metrics_gateway.snmp import OidTree, SnmpPassPersistResponder
from src.metrics_gateway.web import create_app

__all__ = [
    "GatewaySettings",
    "MetricCatalog",
    "MetricDefinition",
    "MetricKind",
    "MetricSample",
    "MetricScope",
    "MetricSnapshot",
    "MetricsCache",
    "MistMetricsCollector",
    "MistStatsReader",
    "OidTree",
    "PrometheusRenderer",
    "SnmpPassPersistResponder",
    "build_cache",
    "create_app",
    "start_refresh_thread",
]
